from django.urls import include, path

# /api/saude é respondido pelo SaudeMiddleware (veja saude.py)
urlpatterns = [
    path("api/", include("cinema.adaptadores.controllers.rotas")),
]
