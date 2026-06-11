FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_PORT=8008

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 -r requirements.txt

COPY . .

RUN mkdir -p data/faiss

EXPOSE 8008
# No DB migrations — rag_service has no models.
# build_faiss_index fetches live product data from product_service.
CMD sh -c "python manage.py build_faiss_index && python manage.py runserver 0.0.0.0:$SERVICE_PORT"
