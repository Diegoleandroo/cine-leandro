"""Peças comuns dos controllers.

Os controllers precisam dos casos de uso já montados, mas NÃO podem importar o
container (ele mora na camada de fora). Então o container "entrega" os casos de
uso aqui na inicialização, com `configurar()`. É injeção de dependência simples.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django.core.cache import caches
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import exception_handler as tratador_padrao_drf

from cinema import casos_de_uso as uc
from cinema.adaptadores.presenters import ErroPresenter
from cinema.casos_de_uso.portas import Relogio
from cinema.entidades import ErroDeDominio, Idioma, Usuario


@dataclass
class CasosDeUso:
    cadastrar: uc.CadastrarConta
    login: uc.FazerLogin
    logout: uc.FazerLogout
    autenticar: uc.AutenticarUsuario
    solicitar_recuperacao: uc.SolicitarRecuperacaoDeSenha
    redefinir_senha: uc.RedefinirSenha
    em_cartaz: uc.ListarFilmesEmCartaz
    populares: uc.ListarPopulares
    mais_bem_avaliados: uc.ListarMaisBemAvaliados
    lancamentos: uc.ListarLancamentos
    filtrar: uc.FiltrarPorCategoria
    generos: uc.ListarGeneros
    detalhar: uc.DetalharFilme
    trailer: uc.ObterTrailer
    onde_assistir: uc.ObterOndeAssistir
    obter_preferencias: uc.ObterPreferencias
    atualizar_preferencias: uc.AtualizarPreferencias
    ativar_aviso: uc.AtivarAvisoDeLancamento
    meus_avisos: uc.ListarMeusAvisos
    cancelar_aviso: uc.CancelarAviso
    relogio: Relogio
    descrever_sistema: Callable[[], dict[str, Any]]
    url_redefinir_senha: str


_casos: CasosDeUso | None = None


def configurar(casos: CasosDeUso) -> None:
    global _casos
    _casos = casos


def casos() -> CasosDeUso:
    if _casos is None:
        raise RuntimeError("Os casos de uso não foram configurados (container não iniciou).")
    return _casos


def hoje():
    return casos().relogio.agora().date()


def token_da_requisicao(request) -> str | None:
    cabecalho = request.headers.get("Authorization", "")
    tipo, _, token = cabecalho.partition(" ")
    return token.strip() if tipo.lower() == "bearer" and token.strip() else None


def usuario_logado(request) -> Usuario:
    """Lança NaoAutenticado (vira 401) se não houver um token válido."""
    return casos().autenticar.executar(token_da_requisicao(request))


def idioma_da_requisicao(request) -> Idioma:
    valor = (request.query_params.get("idioma") or "PT").upper()
    return Idioma(valor) if valor in Idioma.__members__ else Idioma.PT


def tratar_excecao(exc, contexto):
    """Configurado em settings.REST_FRAMEWORK['EXCEPTION_HANDLER']."""
    if isinstance(exc, ErroDeDominio):
        status, corpo = ErroPresenter.dominio(exc)
        return Response(corpo, status=status)
    if isinstance(exc, Throttled):
        status, corpo = ErroPresenter.muitas_requisicoes(exc.wait)
        resposta = Response(corpo, status=status)
        resposta["Retry-After"] = str(corpo["espera_segundos"])
        return resposta
    resposta = tratador_padrao_drf(exc, contexto)
    if resposta is not None and resposta.status_code == 400 and isinstance(resposta.data, dict):
        status, corpo = ErroPresenter.validacao(resposta.data)
        return Response(corpo, status=status)
    return resposta


class LimitePorIp(ScopedRateThrottle):
    """Limita quantos pedidos de login/cadastro/recuperação um mesmo IP faz por minuto.

    Usa o cache "seguranca" (compartilhado entre os processos do Gunicorn).
    """

    cache = caches["seguranca"]
