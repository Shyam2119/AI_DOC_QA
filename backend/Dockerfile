FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libssl-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV HF_HOME=/app/model_cache
RUN python download_models.py

RUN mkdir -p uploads vector_stores

EXPOSE 5000

CMD ["sh", "-c", "python init_db.py && gunicorn -w 1 --threads 2 --timeout 120 -b 0.0.0.0:5000 'run:app'"]
