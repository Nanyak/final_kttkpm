FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_PORT=8007

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev gcc pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 -r requirements.txt

COPY . .

RUN mkdir -p data/models data/faiss

EXPOSE 8007
CMD sh -c "python manage.py makemigrations behavior --noinput && python manage.py migrate --noinput && python manage.py seed_data && python manage.py train_lstm && python manage.py setup_graph && python manage.py runserver 0.0.0.0:$SERVICE_PORT"
