FROM python:3.11-slim

WORKDIR /app
COPY personal-ai/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY personal-ai/ ./

ENV PORT=10000
ENV OLLAMA_URL=http://127.0.0.1:11434/api/chat

CMD sh -c "gunicorn --bind 0.0.0.0:$PORT app:app"
