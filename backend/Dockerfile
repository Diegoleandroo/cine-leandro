# Imagem do backend (Django + DRF + Gunicorn). A mesma imagem roda localmente
# (docker compose) e na AWS (ECS Express Mode, a partir do ECR).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=cinema.frameworks_drivers.django_projeto.settings

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuário sem privilégios: o container não roda como root.
RUN useradd --create-home cinema
USER cinema

EXPOSE 8000

# Aplica as migrations e sobe o Gunicorn. Na AWS, o health check é /api/saude.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py createcachetable && gunicorn cinema.frameworks_drivers.django_projeto.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --access-logfile -"]
