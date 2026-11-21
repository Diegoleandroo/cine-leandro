"""Health check para o load balancer da AWS.

O load balancer chama /api/saude usando o IP interno do container como "Host".
O Django recusaria (ALLOWED_HOSTS), então este middleware responde ANTES da
checagem de host. Ele só olha o caminho; nenhum outro endereço passa por aqui.
"""

from django.db import connection
from django.http import JsonResponse


class SaudeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/api/saude":
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return JsonResponse({"status": "ok"})
            except Exception:  # noqa: BLE001
                return JsonResponse({"status": "sem banco"}, status=503)
        return self.get_response(request)
