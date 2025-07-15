FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kapaladaru.py .

# Create directories for volumes
RUN mkdir -p /movies /checked

# Environment variables with defaults
ENV MOVIES_DIR=/movies
ENV CHECKED_DIR=/checked
ENV OLLAMA_ENDPOINT=http://localhost:11434
ENV OLLAMA_MODEL=llama3.2
ENV NTFY_URL=https://ntfy.sh/mytopic
ENV CHECK_INTERVAL=3600
ENV RUN_ONCE=false

CMD ["python", "-u", "kapaladaru.py"]