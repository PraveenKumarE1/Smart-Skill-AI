# Personal AI — Local JARVIS Assistant

A privacy-first personal AI assistant that runs on your computer. It combines a local web interface, Ollama-powered chat, persistent memory, notes, tasks, voice input/output, local document search and a lightweight 3D-style animated assistant orb.

## Features
- 🤖 Local LLM chat with Ollama (default: llama3.2)
- 🧠 Persistent personal memory stored locally in JSON
- 🧠 Local semantic vector retrieval using an Ollama embedding model
- 📚 Offline document brain for PDF, DOCX, TXT, MD and CSV
- 📝 Private notes
- ✅ Local task manager with completion state
- 🎙 Browser voice input using Web Speech API
- 🔊 Browser voice output using SpeechSynthesis
- ✨ Animated assistant orb / JARVIS-style UI
- 📡 Ollama and semantic-model health status
- 📴 Offline-first UI, memory, notes, tasks and document storage
- 🔐 No cloud API key required

## Run locally
1. Install Python 3.10+
2. Open a terminal in this folder
3. Install packages:
   `pip install -r requirements.txt`
4. Install Ollama
5. Download the chat model:
   `ollama pull llama3.2`
6. Download the local embedding model:
   `ollama pull nomic-embed-text`
7. Start the app:
   `python app.py`
8. Open `http://127.0.0.1:5000`

## Configuration
- `OLLAMA_MODEL` — local chat model, default `llama3.2`
- `OLLAMA_EMBED_MODEL` — local embedding model, default `nomic-embed-text`
- `OLLAMA_URL` — default `http://127.0.0.1:11434/api/chat`

PowerShell example:
```powershell
$env:OLLAMA_MODEL="llama3.2"
$env:OLLAMA_EMBED_MODEL="nomic-embed-text"
python app.py
```

## Semantic memory
The assistant now creates local embedding vectors with Ollama and stores them in `data/vectors.json`. Questions are converted to vectors and matched with cosine similarity against document chunks.

If the embedding model is unavailable, the application automatically falls back to local keyword retrieval. No document is sent to a cloud embedding service.

To rebuild vectors after changing the embedding model:
```powershell
Invoke-WebRequest -Method POST http://127.0.0.1:5000/api/semantic/rebuild
```

## Local document brain
Upload PDF, DOCX, TXT, MD or CSV files from the sidebar. Files are extracted and indexed locally. Relevant chunks are retrieved with semantic vector search and supplied to the local Ollama model.

For offline PDF/DOCX support, `PyMuPDF` and `python-docx` are installed from the requirements file.

## Offline behavior
The interface, memory, notes, tasks and stored documents do not require internet access. Full natural-language generation and semantic embeddings require local Ollama models. If Ollama is stopped, the app uses a small offline fallback response and keyword document retrieval.

## Privacy
Data is stored under `personal-ai/data/`. Memory, notes, tasks, documents and vector indexes are intended to remain on your computer and should not be committed to Git.

## Roadmap
- Streaming local responses
- PDF page-level citations
- SQLite/FAISS-style local vector storage
- Optional calendar/reminder integrations
- Desktop packaging

This project is designed as a local personal assistant, not a cloud-hosted service.
