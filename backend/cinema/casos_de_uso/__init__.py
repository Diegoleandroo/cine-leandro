"""Camada 2: Use Cases.

O que o sistema faz. Depende só das entidades e das portas (interfaces).
Nada de Django, PostgreSQL, HTTP ou AWS por aqui.
"""

from .avisos import AtivarAvisoDeLancamento, CancelarAviso, DispararAvisosDeEstreia, ListarMeusAvisos
from .conta import (
    AutenticarUsuario,
    CadastrarConta,
    FazerLogin,
    FazerLogout,
    RedefinirSenha,
    SolicitarRecuperacaoDeSenha,
)
from .dtos import CadastroEntrada, ListaDeFilmes, PaginaDeFilmes, SessaoDeLogin
from .filmes import (
    DetalharFilme,
    FiltrarPorCategoria,
    ListarFilmesEmCartaz,
    ListarGeneros,
    ListarLancamentos,
    ListarMaisBemAvaliados,
    ListarPopulares,
    ObterOndeAssistir,
    ObterTrailer,
)
from .preferencias import AtualizarPreferencias, ObterPreferencias

__all__ = [
    "AtivarAvisoDeLancamento",
    "AtualizarPreferencias",
    "AutenticarUsuario",
    "CadastrarConta",
    "CadastroEntrada",
    "CancelarAviso",
    "DetalharFilme",
    "DispararAvisosDeEstreia",
    "FazerLogin",
    "FazerLogout",
    "FiltrarPorCategoria",
    "ListaDeFilmes",
    "ListarFilmesEmCartaz",
    "ListarGeneros",
    "ListarLancamentos",
    "ListarMaisBemAvaliados",
    "ListarMeusAvisos",
    "ListarPopulares",
    "ObterOndeAssistir",
    "ObterPreferencias",
    "ObterTrailer",
    "PaginaDeFilmes",
    "RedefinirSenha",
    "SessaoDeLogin",
    "SolicitarRecuperacaoDeSenha",
]
