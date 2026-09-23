# Personal AI — Local JARVIS Assistant

A privacy-first personal AI assistant that runs on your computer. It combines a local web interface, Ollama-powered chat, persistent memory, notes, tasks, voice input/output and a lightweight 3D-style animated assistant orb.

## Features
- 🤖 Local LLM chat with Ollama (default: llama3.2)
- 🧠 Persistent personal memory stored locally in JSON
- 📝 Private notes
- ✅ Local task manager with completion state
- 🎙 Browser voice input using Web Speech API
- 🔊 Browser voice output using SpeechSynthesis
- ✨ Animated assistant orb / JARVIS-style UI
- 📡 Health indicator for Ollama
- 📴 Offline-first UI, memory, notes and tasks
- 🔐 No cloud API key required

## Run locally
1. Install Python 3.10+
2. Open a terminal in this folder
3. Install packages:
   `pip install -r requirements.txt`
4. Optional but recommended: install Ollama and download a local model:
   `ollama pull llama3.2`
5. Start the app:
   `python app.py`
6. Open `http://127.0.0.1:5000`

## Configuration
- `OLLAMA_MODEL` — local model name, default `llama3.2`
- `OLLAMA_URL` — default `http://127.0.0.1:11434/api/chat`

Example:
```powershell
$env:OLLAMA_MODEL="llama3.2"
python app.py
```

## Offline behavior
The interface, memory, notes and task manager do not require internet access. Full natural-language generation requires a local Ollama model. If Ollama is stopped, the app automatically uses a small offline fallback response instead of failing.

## Privacy
Data is stored under `personal-ai/data/`. The memory, notes and tasks files are ignored by Git so private information is not committed.

## Roadmap
- Local document/PDF knowledge base
- Semantic/vector memory
- Streaming responses
- Optional calendar/reminder integrations
- More local model choices
- Desktop packaging

This project is designed as a local personal assistant, not a cloud-hosted service.


## Local document brain
Upload PDF, DOCX, TXT, MD or CSV files from the sidebar. Files are extracted and indexed locally. When you ask a question, relevant chunks are retrieved locally and supplied to your Ollama model. No document upload to a cloud API is required.

For offline PDF/DOCX support, `PyMuPDF` and `python-docx` are installed from the requirements file.
