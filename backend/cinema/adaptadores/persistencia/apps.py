from django.apps import AppConfig


class PersistenciaConfig(AppConfig):
    name = "cinema.adaptadores.persistencia"
    label = "persistencia"
    verbose_name = "Cine Leandro — persistência (PostgreSQL)"
    default_auto_field = "django.db.models.BigAutoField"
