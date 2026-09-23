# Personal AI — Local JARVIS Assistant

A privacy-first personal AI assistant that runs locally, with a Render-ready Docker deployment configuration.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/PraveenKumarE1/Smart-Skill-AI)

## Features
- 🤖 Local LLM chat with Ollama (default: llama3.2)
- 🧠 Persistent personal memory stored locally in JSON
- 🧠 Local semantic vector retrieval using an Ollama embedding model
- 📚 Offline document brain for PDF, DOCX, TXT, MD and CSV
- 📝 Private notes
- ✅ Local task manager
- 🎙 Browser voice input
- 🔊 Browser voice output
- ✨ JARVIS-style animated UI
- 🔐 Local-first privacy

## Public deployment

The repository includes `Dockerfile` and `render.yaml` for Render. Render supports Docker-based web services and gives deployed services a public `onrender.com` URL. 

**Important:** the current AI engine is Ollama-local. A public Render deployment needs Ollama hosted separately or a hosted LLM/embedding provider configured through environment variables. The Render web service alone does not make a local Ollama process available.

### Deploy
1. Click **Deploy to Render** above.
2. Connect your GitHub account if requested.
3. Select the `personal-ai` service configuration.
4. Deploy the web service.
5. Configure a hosted AI backend before expecting cloud AI responses.

## Run locally
1. Install Python 3.10+
2. Install dependencies:
   `pip install -r requirements.txt`
3. Install Ollama.
4. Run:
   `ollama pull llama3.2`
   `ollama pull nomic-embed-text`
5. Start:
   `python app.py`
6. Open `http://127.0.0.1:5000`.

## Privacy

Local mode stores memory, notes, tasks, documents and vector indexes under `personal-ai/data/`. These files should not be committed to Git.
