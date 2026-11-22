FROM python:3.12.16-slim@sha256:05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177

WORKDIR /app
COPY requirements.txt .
RUN apt update && apt install -y curl && pip install --no-cache-dir -r requirements.txt && apt clean

COPY app.py .

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
