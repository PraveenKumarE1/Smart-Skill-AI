from flask import Flask, jsonify, request, send_from_directory
import json, os, re
from datetime import datetime
import requests

BASE=os.path.dirname(os.path.abspath(__file__))
DATA_DIR=os.path.join(BASE,'data')
MEMORY_FILE=os.path.join(DATA_DIR,'memory.json')
NOTES_FILE=os.path.join(DATA_DIR,'notes.json')
TASKS_FILE=os.path.join(DATA_DIR,'tasks.json')
DOC_DIR=os.path.join(DATA_DIR,'documents')
DOCS_FILE=os.path.join(DATA_DIR,'documents.json')
os.makedirs(DATA_DIR,exist_ok=True)
os.makedirs(DOC_DIR,exist_ok=True)
app=Flask(__name__,static_folder='static')

def load_json(path,default):
    if not os.path.exists(path): return default
    try:
        with open(path,'r',encoding='utf-8') as f: return json.load(f)
    except (OSError,json.JSONDecodeError): return default

def save_json(path,data):
    with open(path,'w',encoding='utf-8') as f: json.dump(data,f,indent=2,ensure_ascii=False)



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
    terms=set(re.findall(r'\w+',query.lower()))
    scored=[]
    for d in docs:
        for chunk in d.get('chunks',[]):
            words=re.findall(r'\w+',chunk.lower())
            score=sum(words.count(t) for t in terms)
            if score: scored.append((score,d['name'],chunk))
    scored.sort(key=lambda x:x[0],reverse=True)
    return scored[:limit]

def fallback(message):
    q=message.lower()
    if any(x in q for x in ['hello','hi','hey']): return 'Hello! I am your local Personal AI. I can chat, remember information, save notes and manage tasks.'
    if 'offline' in q: return 'I am in offline mode. The interface, memory, notes and tasks work without internet. Start Ollama for local LLM answers.'
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
            '\n\nOpen tasks:\n'+task_text)
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
        r=requests.get(os.getenv('OLLAMA_URL','http://127.0.0.1:11434/api/tags').replace('/api/chat','/api/tags'),timeout=2)
        online=r.ok
    except Exception: online=False
    return jsonify({'ollama':online,'model':model,'offline_ready':True})

@app.route('/api/chat',methods=['POST'])
def chat():
    data=request.get_json(silent=True) or {}
    message=str(data.get('message','')).strip()
    if not message: return jsonify({'error':'Message is required'}),400
    docs=retrieve_documents(message)
    reply,local_model,model=ollama_reply(message,load_json(MEMORY_FILE,[]),load_json(NOTES_FILE,[]),load_json(TASKS_FILE,[]),docs)
    return jsonify({'reply':reply,'local_model':local_model,'model':model,'sources':[{'name':n,'score':s} for s,n,_ in docs]})

@app.route('/api/memory',methods=['GET','POST','DELETE'])
def memory():
    memories=load_json(MEMORY_FILE,[])
    if request.method=='GET': return jsonify(memories)
    data=request.get_json(silent=True) or {}
    if request.method=='POST':
        text=str(data.get('text','')).strip()
        if not text: return jsonify({'error':'Memory text is required'}),400
        item={'id':int(datetime.now().timestamp()*1000),'text':text,'created_at':datetime.now().isoformat()}
        memories.append(item); save_json(MEMORY_FILE,memories); return jsonify(item),201
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
    data=request.get_json(silent=True) or {}
    task_id=data.get('id')
    if request.method=='POST':
        title=str(data.get('title','')).strip()
        if not title: return jsonify({'error':'Task title is required'}),400
        item={'id':int(datetime.now().timestamp()*1000),'title':title,'done':False,'created_at':datetime.now().isoformat()}
        tasks.append(item); save_json(TASKS_FILE,tasks); return jsonify(item),201
    if request.method=='PATCH':
        for t in tasks:
            if str(t.get('id'))==str(task_id):
                t['done']=bool(data.get('done',not t.get('done')))
                save_json(TASKS_FILE,tasks); return jsonify(t)
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
        item={'id':int(datetime.now().timestamp()*1000),'name':safe,'size':os.path.getsize(path),'created_at':datetime.now().isoformat(),'chunks':split_chunks(text)}
        docs=[d for d in docs if d.get('name')!=safe]; docs.append(item); save_json(DOCS_FILE,docs)
        return jsonify({'id':item['id'],'name':item['name'],'chunks':len(item['chunks'])}),201
    data=request.get_json(silent=True) or {}; doc_id=data.get('id')
    target=next((d for d in docs if str(d.get('id'))==str(doc_id)),None)
    if target:
        try: os.remove(os.path.join(DOC_DIR,target['name']))
        except OSError: pass
        docs=[d for d in docs if str(d.get('id'))!=str(doc_id)]; save_json(DOCS_FILE,docs)
    return jsonify({'ok':True})

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000,debug=True)
