"""python manage.py disparar_avisos

Envia os e-mails de estreia do dia. Na AWS, o EventBridge Scheduler roda este
comando uma vez por dia como uma tarefa do ECS.
"""

from django.core.management.base import BaseCommand

from cinema.frameworks_drivers.config import Config
from cinema.frameworks_drivers.container import Container


class Command(BaseCommand):
    help = "Envia os avisos de estreia dos filmes que lançam hoje (ou antes, se ficaram pendentes)."

    def handle(self, *args, **options):
        enviados = Container(Config.do_ambiente()).disparar_avisos().executar()
        self.stdout.write(self.style.SUCCESS(f"{enviados} aviso(s) de estreia enviado(s)."))
