from flask import Flask, jsonify, request, send_from_directory
import json, os, re, math
from datetime import datetime
import requests

BASE=os.path.dirname(os.path.abspath(__file__))
DATA_DIR=os.path.join(BASE,'data')
MEMORY_FILE=os.path.join(DATA_DIR,'memory.json')
NOTES_FILE=os.path.join(DATA_DIR,'notes.json')
TASKS_FILE=os.path.join(DATA_DIR,'tasks.json')
DOC_DIR=os.path.join(DATA_DIR,'documents')
DOCS_FILE=os.path.join(DATA_DIR,'documents.json')
VECTORS_FILE=os.path.join(DATA_DIR,'vectors.json')
os.makedirs(DATA_DIR,exist_ok=True)
os.makedirs(DOC_DIR,exist_ok=True)
app=Flask(__name__,static_folder='static')
app.config['MAX_CONTENT_LENGTH']=15*1024*1024

def load_json(path,default):
    if not os.path.exists(path): return default
    try:
        with open(path,'r',encoding='utf-8') as f: return json.load(f)
    except (OSError,json.JSONDecodeError): return default

def save_json(path,data):
    with open(path,'w',encoding='utf-8') as f: json.dump(data,f,indent=2,ensure_ascii=False)

def ollama_base():
    url=os.getenv('OLLAMA_URL','http://127.0.0.1:11434/api/chat')
    return url.rsplit('/api/',1)[0]

def embedding_model():
    return os.getenv('OLLAMA_EMBED_MODEL','nomic-embed-text')

def create_embedding(text):
    """Create a local vector with Ollama. Returns None if the embedding model is unavailable."""
    try:
        r=requests.post(
            ollama_base()+'/api/embeddings',
            json={'model':embedding_model(),'prompt':text},
            timeout=60
        )
        r.raise_for_status()
        vec=r.json().get('embedding')
        if isinstance(vec,list) and vec:
            return [float(x) for x in vec]
    except Exception:
        return None
    return None

def cosine_similarity(a,b):
    if not a or not b or len(a)!=len(b): return 0.0
    dot=sum(x*y for x,y in zip(a,b))
    na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

def extract_text(path,filename):
    ext=os.path.splitext(filename.lower())[1]
    if ext=='.pdf':
        import fitz
        doc=fitz.open(path)
        return '\n'.join(page.get_text() for page in doc)
    if ext=='.docx':
        from docx import Document
        return '\n'.join(p.text for p in Document(path).paragraphs)
    if ext in ('.txt','.md','.csv'):
        with open(path,'r',encoding='utf-8',errors='ignore') as f: return f.read()
    raise ValueError('Supported files: PDF, DOCX, TXT, MD, CSV')

def split_chunks(text,size=1200):
    text=re.sub(r'\s+',' ',text).strip()
    return [text[i:i+size] for i in range(0,len(text),size)] if text else []

def retrieve_documents(query,limit=4):
    docs=load_json(DOCS_FILE,[])
    vectors=load_json(VECTORS_FILE,[])
    qvec=create_embedding(query)
    scored=[]
    if qvec:
        for item in vectors:
            score=cosine_similarity(qvec,item.get('vector',[]))
            if score>0:
                scored.append((score,item.get('name',''),item.get('chunk','')))
        scored.sort(key=lambda x:x[0],reverse=True)
        if scored:
            return scored[:limit]
    # Safe local fallback if the embedding model is not installed.
    terms=set(re.findall(r'\w+',query.lower()))
    for d in docs:
        for chunk in d.get('chunks',[]):
            words=re.findall(r'\w+',chunk.lower())
            score=sum(words.count(t) for t in terms)
            if score: scored.append((float(score),d['name'],chunk))
    scored.sort(key=lambda x:x[0],reverse=True)
    return scored[:limit]

def rebuild_vectors():
    vectors=[]
    docs=load_json(DOCS_FILE,[])
    for d in docs:
        for chunk in d.get('chunks',[]):
            vec=create_embedding(chunk)
            if vec:
                vectors.append({'name':d['name'],'chunk':chunk,'vector':vec})
    save_json(VECTORS_FILE,vectors)
    return len(vectors)

def fallback(message):
    q=message.lower()
    if any(x in q for x in ['hello','hi','hey']): return 'Hello! I am your local Personal AI. I can chat, remember information, save notes and manage tasks.'
    if 'offline' in q: return 'I am in offline mode. The interface, memory, notes and tasks work without internet. Start Ollama for local AI and semantic search.'
    if 'who are you' in q: return 'I am your private Personal AI: a local-first assistant designed to keep your data on your computer.'
    return 'I am running without a local language model. Start Ollama with a local model for full AI responses.'

def ollama_reply(message,memories,notes,tasks,documents=None):
    model=os.getenv('OLLAMA_MODEL','llama3.2')
    url=os.getenv('OLLAMA_URL','http://127.0.0.1:11434/api/chat')
    memory_text='\n'.join('- '+m['text'] for m in memories[-20:]) or '- No saved memories'
    task_text='\n'.join('- '+t['title'] for t in tasks if not t.get('done')) or '- No open tasks'
    doc_context='\n\n'.join('[Document: '+name+']\n'+chunk for _,name,chunk in (documents or []))
    system=('You are a private local personal AI assistant. Be concise, practical and honest. '
            'Use supplied memory only when relevant. You can suggest actions, but never claim an action happened unless the application performed it. '
            'The UI can manage memories, notes and tasks.\n\nKnown memory:\n'+memory_text+
            '\n\nOpen tasks:\n'+task_text+
            ('\n\nRelevant local documents:\n'+doc_context if doc_context else ''))
    try:
        r=requests.post(url,json={'model':model,'stream':False,'messages':[
            {'role':'system','content':system},{'role':'user','content':message}]},timeout=90)
        r.raise_for_status()
        return r.json()['message']['content'],True,model
    except Exception:
        return fallback(message),False,model

@app.route('/')
def index(): return send_from_directory(BASE,'index.html')

@app.route('/api/health')
def health():
    model=os.getenv('OLLAMA_MODEL','llama3.2')
    try:
        r=requests.get(ollama_base()+'/api/tags',timeout=2)
        online=r.ok
    except Exception: online=False
    semantic=False
    if online:
        try:
            r=requests.get(ollama_base()+'/api/tags',timeout=2)
            names=[m.get('name','') for m in r.json().get('models',[])]
            semantic=any(embedding_model() in n for n in names)
        except Exception: pass
    return jsonify({'ollama':online,'model':model,'embedding_model':embedding_model(),'semantic_memory':semantic,'offline_ready':True})

@app.route('/api/chat',methods=['POST'])
def chat():
    data=request.get_json(silent=True) or {}
    message=str(data.get('message','')).strip()
    if not message: return jsonify({'error':'Message is required'}),400
    docs=retrieve_documents(message)
    reply,local_model,model=ollama_reply(message,load_json(MEMORY_FILE,[]),load_json(NOTES_FILE,[]),load_json(TASKS_FILE,[]),docs)
    return jsonify({'reply':reply,'local_model':local_model,'model':model,'semantic_search':bool(docs and any(s<=1.01 for s,_,_ in docs)),'sources':[{'name':n,'score':round(s,4)} for s,n,_ in docs]})

@app.route('/api/memory',methods=['GET','POST','DELETE'])
def memory():
    memories=load_json(MEMORY_FILE,[])
    if request.method=='GET': return jsonify(memories)
    data=request.get_json(silent=True) or {}
    if request.method=='POST':
        text=str(data.get('text','')).strip()
        if not text: return jsonify({'error':'Memory text is required'}),400
        item={'id':int(datetime.now().timestamp()*1000),'text':text,'created_at':datetime.now().isoformat()}
        memories.append(item); save_json(MEMORY_FILE,memories)
        return jsonify(item),201
    memory_id=data.get('id'); save_json(MEMORY_FILE,[m for m in memories if str(m.get('id'))!=str(memory_id)])
    return jsonify({'ok':True})

@app.route('/api/notes',methods=['GET','POST'])
def notes():
    notes=load_json(NOTES_FILE,[])
    if request.method=='GET': return jsonify(notes)
    data=request.get_json(silent=True) or {}; text=str(data.get('text','')).strip()
    if not text: return jsonify({'error':'Note text is required'}),400
    note={'id':int(datetime.now().timestamp()*1000),'text':text,'created_at':datetime.now().isoformat()}
    notes.append(note); save_json(NOTES_FILE,notes); return jsonify(note),201

@app.route('/api/tasks',methods=['GET','POST','PATCH','DELETE'])
def tasks():
    tasks=load_json(TASKS_FILE,[])
    if request.method=='GET': return jsonify(tasks)
    data=request.get_json(silent=True) or {}; task_id=data.get('id')
    if request.method=='POST':
        title=str(data.get('title','')).strip()
        if not title: return jsonify({'error':'Task title is required'}),400
        item={'id':int(datetime.now().timestamp()*1000),'title':title,'done':False,'created_at':datetime.now().isoformat()}
        tasks.append(item); save_json(TASKS_FILE,tasks); return jsonify(item),201
    if request.method=='PATCH':
        for t in tasks:
            if str(t.get('id'))==str(task_id):
                t['done']=bool(data.get('done',not t.get('done'))); save_json(TASKS_FILE,tasks); return jsonify(t)
        return jsonify({'error':'Task not found'}),404
    save_json(TASKS_FILE,[t for t in tasks if str(t.get('id'))!=str(task_id)])
    return jsonify({'ok':True})

@app.route('/api/documents',methods=['GET','POST','DELETE'])
def documents():
    docs=load_json(DOCS_FILE,[])
    if request.method=='GET':
        return jsonify([{'id':d['id'],'name':d['name'],'size':d['size'],'chunks':len(d.get('chunks',[])),'created_at':d['created_at']} for d in docs])
    if request.method=='POST':
        if 'file' not in request.files: return jsonify({'error':'Choose a file'}),400
        f=request.files['file']
        if not f.filename: return jsonify({'error':'Choose a file'}),400
        ext=os.path.splitext(f.filename.lower())[1]
        if ext not in ('.pdf','.docx','.txt','.md','.csv'): return jsonify({'error':'Supported: PDF, DOCX, TXT, MD, CSV'}),400
        safe=re.sub(r'[^a-zA-Z0-9._-]','_',f.filename)
        path=os.path.join(DOC_DIR,safe); f.save(path)
        try: text=extract_text(path,safe)
        except Exception as e:
            try: os.remove(path)
            except OSError: pass
            return jsonify({'error':'Could not read file: '+str(e)}),400
        chunks=split_chunks(text)
        item={'id':int(datetime.now().timestamp()*1000),'name':safe,'size':os.path.getsize(path),'created_at':datetime.now().isoformat(),'chunks':chunks}
        docs=[d for d in docs if d.get('name')!=safe]; docs.append(item); save_json(DOCS_FILE,docs)
        vectors=load_json(VECTORS_FILE,[])
        vectors=[v for v in vectors if v.get('name')!=safe]
        for chunk in chunks:
            vec=create_embedding(chunk)
            if vec: vectors.append({'name':safe,'chunk':chunk,'vector':vec})
        save_json(VECTORS_FILE,vectors)
        return jsonify({'id':item['id'],'name':item['name'],'chunks':len(chunks),'semantic_vectors':sum(1 for v in vectors if v.get('name')==safe)}),201
    data=request.get_json(silent=True) or {}; doc_id=data.get('id')
    target=next((d for d in docs if str(d.get('id'))==str(doc_id)),None)
    if target:
        try: os.remove(os.path.join(DOC_DIR,target['name']))
        except OSError: pass
        docs=[d for d in docs if str(d.get('id'))!=str(doc_id)]; save_json(DOCS_FILE,docs)
        vectors=[v for v in load_json(VECTORS_FILE,[]) if v.get('name')!=target['name']]
        save_json(VECTORS_FILE,vectors)
    return jsonify({'ok':True})

@app.route('/api/semantic/rebuild',methods=['POST'])
def semantic_rebuild():
    count=rebuild_vectors()
    return jsonify({'ok':True,'vectors':count,'embedding_model':embedding_model()})

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000,debug=True)
