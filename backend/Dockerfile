FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads vector_stores

EXPOSE 5000

CMD ["sh", "-c", "python init_db.py && gunicorn -w 2 -b 0.0.0.0:5000 'run:app'"]
