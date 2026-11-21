import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.frameworks_drivers.django_projeto.settings")

application = get_wsgi_application()
