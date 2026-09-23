from flask import Flask, jsonify, request, send_from_directory
import json, os
from datetime import datetime
import requests

BASE=os.path.dirname(os.path.abspath(__file__))
DATA_DIR=os.path.join(BASE,'data')
MEMORY_FILE=os.path.join(DATA_DIR,'memory.json')
NOTES_FILE=os.path.join(DATA_DIR,'notes.json')
os.makedirs(DATA_DIR,exist_ok=True)
app=Flask(__name__,static_folder='static')

def load_json(path,default):
    if not os.path.exists(path): return default
    try:
        with open(path,'r',encoding='utf-8') as f: return json.load(f)
    except (OSError,json.JSONDecodeError): return default

def save_json(path,data):
    with open(path,'w',encoding='utf-8') as f: json.dump(data,f,indent=2,ensure_ascii=False)

def fallback(message):
    q=message.lower()
    if any(x in q for x in ['hello','hi','hey']): return 'Hello! I am your local Personal AI. Ask me something or tell me what to remember.'
    if 'offline' in q: return 'I am running in offline fallback mode. Install Ollama and a local model for stronger answers.'
    return 'I am running without a local language model. Start Ollama with a local model for full AI responses.'

def ollama_reply(message,memories):
    model=os.getenv('OLLAMA_MODEL','llama3.2')
    url=os.getenv('OLLAMA_URL','http://127.0.0.1:11434/api/chat')
    memory_text='\n'.join('- '+m['text'] for m in memories[-20:]) or '- No saved memories'
    system=('You are a helpful private personal AI assistant. Be concise, practical and honest. '+
            'Use the supplied memory only when relevant. Never claim an action you did not perform.\n\n'+
            'Known user memory:\n'+memory_text)
    try:
        r=requests.post(url,json={'model':model,'stream':False,'messages':[{'role':'system','content':system},{'role':'user','content':message}]},timeout=90)
        r.raise_for_status()
        return r.json()['message']['content'],True
    except Exception:
        return fallback(message),False

@app.route('/')
def index(): return send_from_directory(BASE,'index.html')

@app.route('/api/chat',methods=['POST'])
def chat():
    data=request.get_json(silent=True) or {}
    message=str(data.get('message','')).strip()
    if not message: return jsonify({'error':'Message is required'}),400
    reply,local_model=ollama_reply(message,load_json(MEMORY_FILE,[]))
    return jsonify({'reply':reply,'local_model':local_model})

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

if __name__=='__main__': app.run(host='127.0.0.1',port=5000,debug=True)