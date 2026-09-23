FROM python:3.11-slim

WORKDIR /app
COPY personal-ai/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY personal-ai/ ./

ENV PORT=10000
CMD sh -c "gunicorn --bind 0.0.0.0:$PORT app:app"
