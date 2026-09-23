from flask import Flask, jsonify, request, send_from_directory
import json, os, re, math, ast, operator
from datetime import datetime

BASE=os.path.dirname(os.path.abspath(__file__))
DATA_DIR=os.path.join(BASE,"data")
MEMORY_FILE=os.path.join(DATA_DIR,"memory.json")
NOTES_FILE=os.path.join(DATA_DIR,"notes.json")
TASKS_FILE=os.path.join(DATA_DIR,"tasks.json")
DOC_DIR=os.path.join(DATA_DIR,"documents")
DOCS_FILE=os.path.join(DATA_DIR,"documents.json")
os.makedirs(DATA_DIR,exist_ok=True)
os.makedirs(DOC_DIR,exist_ok=True)

app=Flask(__name__,static_folder="static")
app.config["MAX_CONTENT_LENGTH"]=15*1024*1024

def load_json(path,default):
    if not os.path.exists(path): return default
    try:
        with open(path,"r",encoding="utf-8") as f: return json.load(f)
    except (OSError,json.JSONDecodeError): return default

def save_json(path,data):
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False)

def extract_text(path,filename):
    ext=os.path.splitext(filename.lower())[1]
    if ext==".pdf":
        import fitz
        doc=fitz.open(path)
        return "\n".join(page.get_text() for page in doc)
    if ext==".docx":
        from docx import Document
        return "\n".join(p.text for p in Document(path).paragraphs)
    if ext in (".txt",".md",".csv"):
        with open(path,"r",encoding="utf-8",errors="ignore") as f: return f.read()
    raise ValueError("Supported files: PDF, DOCX, TXT, MD, CSV")

def split_chunks(text,size=1200):
    text=re.sub(r"\s+"," ",text).strip()
    return [text[i:i+size] for i in range(0,len(text),size)] if text else []

def tokens(text):
    return set(re.findall(r"[a-zA-Z0-9]+",text.lower()))

def retrieve_documents(query,limit=4):
    scored=[]
    q=tokens(query)
    for d in load_json(DOCS_FILE,[]):
        for chunk in d.get("chunks",[]):
            w=tokens(chunk)
            overlap=len(q&w)
            if overlap:
                # Simple local relevance score: term overlap + phrase bonus.
                score=overlap/max(1,len(q))
                if query.lower() in chunk.lower(): score+=0.75
                scored.append((score,d["name"],chunk))
    scored.sort(key=lambda x:x[0],reverse=True)
    return scored[:limit]

# Safe calculator: only arithmetic, no eval().
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,
     ast.Div:operator.truediv,ast.Pow:operator.pow,ast.Mod:operator.mod,
     ast.USub:operator.neg}
def calculate(expr):
    expr=expr.replace("^","**").replace("×","*").replace("÷","/")
    if len(expr)>100 or not re.fullmatch(r"[0-9+*/().%\-\s]+(?:\*\*)?[0-9+*/().%\-\s]*",expr):
        raise ValueError("invalid")
    def walk(node):
        if isinstance(node,ast.Expression): return walk(node.body)
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)): return node.value
        if isinstance(node,ast.BinOp) and type(node.op) in OPS:
            a,b=walk(node.left),walk(node.right)
            if abs(a)>1e12 or abs(b)>1e12: raise ValueError("large")
            return OPS[type(node.op)](a,b)
        if isinstance(node,ast.UnaryOp) and type(node.op) in OPS: return OPS[type(node.op)](walk(node.operand))
        raise ValueError("invalid")
    value=walk(ast.parse(expr,mode="eval"))
    if isinstance(value,(int,float)) and math.isfinite(value): return value
    raise ValueError("invalid")

def find_sentence_answer(query,docs):
    q=tokens(query)
    candidates=[]
    for score,name,chunk in docs:
        for sentence in re.split(r"(?<=[.!?])\s+",chunk):
            overlap=len(q & tokens(sentence))
            if overlap: candidates.append((overlap,score,name,sentence.strip()))
    candidates.sort(key=lambda x:(x[0],x[1]),reverse=True)
    return candidates[0] if candidates else None

def offline_ai(message):
    msg=message.strip()
    q=msg.lower()
    memories=load_json(MEMORY_FILE,[])
    notes=load_json(NOTES_FILE,[])
    tasks=load_json(TASKS_FILE,[])
    docs=retrieve_documents(msg)

    # Memory commands
    m=re.match(r"^(remember|memorize|save this)\s*[:,-]?\s*(.+)$",msg,re.I)
    if m:
        text=m.group(2).strip()
        item={"id":int(datetime.now().timestamp()*1000),"text":text,"created_at":datetime.now().isoformat()}
        memories.append(item); save_json(MEMORY_FILE,memories)
        return "Got it. I saved that to your local memory.", "memory"

    if q in {"hello","hi","hey","hello there","good morning","good evening"}:
        return "Hello! I’m your offline Personal AI. I run locally without Ollama, Gemini, OpenAI, or any API.", "greeting"

    if "who are you" in q or "what are you" in q:
        return "I’m your Offline Personal AI. I use local rules, retrieval, memory, document search, task awareness and a safe calculator—no cloud AI required.", "identity"

    if "what time" in q or q=="time":
        return "Your computer time is " + datetime.now().strftime("%I:%M %p") + ".", "time"

    if "what date" in q or q=="date" or "today's date" in q:
        return "Today is " + datetime.now().strftime("%A, %d %B %Y") + ".", "date"

    # Calculator
    calc=q
    for prefix in ("calculate ","what is ","solve "):
        if calc.startswith(prefix): calc=calc[len(prefix):].strip(); break
    if re.fullmatch(r"[0-9+*/().%\-\s×÷^]+",calc) and any(c.isdigit() for c in calc):
        try:
            value=calculate(calc)
            return f"The answer is {value:g}.", "calculator"
        except Exception: pass

    if "my memories" in q or "what do you remember" in q or q=="memory":
        if not memories: return "Your local memory is empty.", "memory"
        return "Here’s what I remember:\n" + "\n".join("• "+m["text"] for m in memories[-10:]), "memory"

    if "my tasks" in q or "open tasks" in q or "what should i work on" in q:
        open_tasks=[t["title"] for t in tasks if not t.get("done")]
        if not open_tasks: return "You have no open tasks. Add one from the Tasks panel.", "tasks"
        return "Your open tasks:\n" + "\n".join(f"• {x}" for x in open_tasks[:10]), "tasks"

    if "my notes" in q or "show notes" in q:
        if not notes: return "You have no saved notes.", "notes"
        return "Your latest notes:\n" + "\n".join("• "+n["text"] for n in notes[-8:]), "notes"

    if docs:
        answer=find_sentence_answer(msg,docs)
        if answer:
            _,_,name,sentence=answer
            return f"From {name}: {sentence}", "document"

    if "study plan" in q or "study" in q and "plan" in q:
        return ("Try this focused plan: 25 min concept study → 5 min break → 25 min problems → "
                "5 min break → 20 min revision → 10 min self-test."), "study"

    if "help" in q or "what can you do" in q:
        return ("I can work offline with local memory, notes, tasks, PDF/DOCX/TXT/MD/CSV search, "
                "calculations, date/time, study planning and simple commands. Try: 'remember my Java exam is Friday'."),
                "help"

    # Lightweight local intent matching.
    if "thank" in q: return "You’re welcome. I’m ready whenever you need me.", "social"
    if "good night" in q: return "Good night. Your local data remains on this machine.", "social"
    if "offline" in q: return "Offline mode is active. No AI API or Ollama process is required.", "system"

    return ("I’m running in offline mode. I don’t have a cloud language model, so I won’t pretend "
            "to generate an answer I cannot compute locally. Try a calculation, memory command, "
            "task query, document question, or ask 'what can you do?'."), "fallback"

@app.route("/")
def index(): return send_from_directory(BASE,"index.html")

@app.route("/api/health")
def health():
    return jsonify({"offline_ai":True,"provider":"Local Offline AI","ollama":False,
                    "gemini":False,"api_required":False,"documents_local":True})

@app.route("/api/chat",methods=["POST"])
def chat():
    data=request.get_json(silent=True) or {}
    message=str(data.get("message","")).strip()
    if not message: return jsonify({"error":"Message is required"}),400
    reply,intent=offline_ai(message)
    docs=retrieve_documents(message)
    return jsonify({"reply":reply,"provider":"Local Offline AI","local_model":True,
                    "model":"offline-rule-retrieval-engine","intent":intent,
                    "semantic_search":bool(docs),
                    "sources":[{"name":n,"score":round(s,4)} for s,n,_ in docs]})

@app.route("/api/memory",methods=["GET","POST","DELETE"])
def memory():
    memories=load_json(MEMORY_FILE,[])
    if request.method=="GET": return jsonify(memories)
    data=request.get_json(silent=True) or {}
    if request.method=="POST":
        text=str(data.get("text","")).strip()
        if not text: return jsonify({"error":"Memory text is required"}),400
        item={"id":int(datetime.now().timestamp()*1000),"text":text,"created_at":datetime.now().isoformat()}
        memories.append(item); save_json(MEMORY_FILE,memories); return jsonify(item),201
    memory_id=data.get("id"); save_json(MEMORY_FILE,[m for m in memories if str(m.get("id"))!=str(memory_id)])
    return jsonify({"ok":True})

@app.route("/api/notes",methods=["GET","POST"])
def notes():
    notes=load_json(NOTES_FILE,[])
    if request.method=="GET": return jsonify(notes)
    data=request.get_json(silent=True) or {}; text=str(data.get("text","")).strip()
    if not text: return jsonify({"error":"Note text is required"}),400
    note={"id":int(datetime.now().timestamp()*1000),"text":text,"created_at":datetime.now().isoformat()}
    notes.append(note); save_json(NOTES_FILE,notes); return jsonify(note),201

@app.route("/api/tasks",methods=["GET","POST","PATCH","DELETE"])
def tasks():
    tasks=load_json(TASKS_FILE,[])
    if request.method=="GET": return jsonify(tasks)
    data=request.get_json(silent=True) or {}; task_id=data.get("id")
    if request.method=="POST":
        title=str(data.get("title","")).strip()
        if not title: return jsonify({"error":"Task title is required"}),400
        item={"id":int(datetime.now().timestamp()*1000),"title":title,"done":False,"created_at":datetime.now().isoformat()}
        tasks.append(item); save_json(TASKS_FILE,tasks); return jsonify(item),201
    if request.method=="PATCH":
        for t in tasks:
            if str(t.get("id"))==str(task_id):
                t["done"]=bool(data.get("done",not t.get("done"))); save_json(TASKS_FILE,tasks); return jsonify(t)
        return jsonify({"error":"Task not found"}),404
    save_json(TASKS_FILE,[t for t in tasks if str(t.get("id"))!=str(task_id)])
    return jsonify({"ok":True})

@app.route("/api/documents",methods=["GET","POST","DELETE"])
def documents():
    docs=load_json(DOCS_FILE,[])
    if request.method=="GET":
        return jsonify([{"id":d["id"],"name":d["name"],"size":d["size"],"chunks":len(d.get("chunks",[])),"created_at":d["created_at"]} for d in docs])
    if request.method=="POST":
        if "file" not in request.files: return jsonify({"error":"Choose a file"}),400
        f=request.files["file"]
        if not f.filename: return jsonify({"error":"Choose a file"}),400
        ext=os.path.splitext(f.filename.lower())[1]
        if ext not in (".pdf",".docx",".txt",".md",".csv"): return jsonify({"error":"Supported: PDF, DOCX, TXT, MD, CSV"}),400
        safe=re.sub(r"[^a-zA-Z0-9._-]","_",f.filename)
        path=os.path.join(DOC_DIR,safe); f.save(path)
        try: text=extract_text(path,safe)
        except Exception as e:
            try: os.remove(path)
            except OSError: pass
            return jsonify({"error":"Could not read file: "+str(e)}),400
        chunks=split_chunks(text)
        item={"id":int(datetime.now().timestamp()*1000),"name":safe,"size":os.path.getsize(path),
              "created_at":datetime.now().isoformat(),"chunks":chunks}
        docs=[d for d in docs if d.get("name")!=safe]; docs.append(item); save_json(DOCS_FILE,docs)
        return jsonify({"id":item["id"],"name":item["name"],"chunks":len(chunks),"semantic_vectors":0}),201
    data=request.get_json(silent=True) or {}; doc_id=data.get("id")
    target=next((d for d in docs if str(d.get("id"))==str(doc_id)),None)
    if target:
        try: os.remove(os.path.join(DOC_DIR,target["name"]))
        except OSError: pass
        docs=[d for d in docs if str(d.get("id"))!=str(doc_id)]; save_json(DOCS_FILE,docs)
    return jsonify({"ok":True})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")),debug=False)
