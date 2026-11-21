from django.apps import AppConfig


class CinemaAppConfig(AppConfig):
    name = "cinema.frameworks_drivers.django_app"
    label = "cinema_app"
    verbose_name = "Cine Leandro"

    def ready(self) -> None:
        # Quando o Django sobe, o container monta os casos de uso e entrega aos controllers.
        from cinema.adaptadores.controllers.base import configurar
        from cinema.frameworks_drivers.config import Config
        from cinema.frameworks_drivers.container import Container

        configurar(Container(Config.do_ambiente()).casos_de_uso())
