FROM python:3.15.2-slim@sha256:3c5426211a36454d7a58b31e306cfefaac2c63b016e9f1a067b652ec602a4d15

WORKDIR /app
COPY requirements.txt .
RUN apt update && apt install -y curl && pip install --no-cache-dir -r requirements.txt && apt clean

COPY app.py .

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
