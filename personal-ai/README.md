# Personal AI — Local Private Assistant

A privacy-first personal AI assistant that runs locally. It supports conversation, persistent memory, notes, and an optional local LLM through Ollama.

## Features
- Local web chat UI
- Persistent JSON memory
- Add/list/delete memories
- Notes endpoint
- Ollama integration (default model: llama3.2)
- Offline fallback responses when Ollama is unavailable
- No API key required

## Run
1. Install Python 3.10+
2. `pip install -r requirements.txt`
3. Optional: install Ollama and run `ollama pull llama3.2`
4. Start: `python app.py`
5. Open http://127.0.0.1:5000

## Environment
- `OLLAMA_MODEL` — local model name (default `llama3.2`)
- `OLLAMA_URL` — Ollama endpoint (default `http://127.0.0.1:11434`)

Personal data stays on the user's machine.