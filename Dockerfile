FROM python:3.15.2-slim@sha256:fd2aef5e0d8438208de9fe154ab5b331a2428fc0c9838d41611e611fd7a80d85

WORKDIR /app
COPY requirements.txt .
RUN apt update && apt install -y curl && pip install --no-cache-dir -r requirements.txt && apt clean

COPY app.py .

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
