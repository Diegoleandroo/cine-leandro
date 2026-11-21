"""Rotas da API (/api/...)."""

from django.urls import path

from . import views

urlpatterns = [
    path("auth/cadastro", views.CadastroView.as_view()),
    path("auth/login", views.LoginView.as_view()),
    path("auth/logout", views.LogoutView.as_view()),
    path("auth/eu", views.EuView.as_view()),
    path("auth/recuperar-senha", views.RecuperarSenhaView.as_view()),
    path("auth/redefinir-senha", views.RedefinirSenhaView.as_view()),
    path("filmes", views.FilmesView.as_view()),
    path("filmes/lancamentos", views.LancamentosView.as_view()),
    path("filmes/generos", views.GenerosView.as_view()),
    path("filmes/<str:filme_id>", views.FilmeView.as_view()),
    path("filmes/<str:filme_id>/trailer", views.TrailerView.as_view()),
    path("filmes/<str:filme_id>/onde-assistir", views.OndeAssistirView.as_view()),
    path("preferencias", views.PreferenciasView.as_view()),
    path("avisos", views.AvisosView.as_view()),
    path("avisos/<str:filme_id>", views.AvisoView.as_view()),
    path("sistema", views.SistemaView.as_view()),
    path("vitrine", views.VitrineView.as_view()),  # pública: só pôsteres dos lançamentos
]
