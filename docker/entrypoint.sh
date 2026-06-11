#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting server on port $SERVICE_PORT..."
exec python manage.py runserver 0.0.0.0:$SERVICE_PORT
