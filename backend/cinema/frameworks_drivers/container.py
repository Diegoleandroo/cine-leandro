"""O container liga tudo: escolhe qual implementação vai em cada porta.

É o único lugar do sistema que conhece todas as camadas. Trocar PostgreSQL por
memória, TMDB por catálogo local ou SES por log é mudar uma variável de ambiente.
"""

from __future__ import annotations

import logging

from cinema import casos_de_uso as uc
from cinema.adaptadores.controllers.base import CasosDeUso
from cinema.adaptadores.email.servicos import EmailPorLog, EmailSes
from cinema.adaptadores.gateways.catalogo_com_cache import CatalogoComCache
from cinema.adaptadores.gateways.catalogo_com_fallback import CatalogoComFallback
from cinema.adaptadores.gateways.catalogo_local import CatalogoLocal
from cinema.adaptadores.gateways.catalogo_tmdb import CatalogoTmdb
from cinema.adaptadores.repositorios.django_orm import AvisoRepositoryDjango, UsuarioRepositoryDjango
from cinema.adaptadores.seguranca.hasher_django import HasherDjango
from cinema.adaptadores.seguranca.limite_tentativas import LimiteNoCache
from cinema.adaptadores.seguranca.token_jwt import RevogadosDjango, TokenDeRecuperacaoJwt, TokenJwt
from cinema.adaptadores.sistema import GeradorDeIdsUuid, RelogioDoSistema

from .config import RAIZ, Config

log = logging.getLogger(__name__)


class Container:
    def __init__(self, config: Config, *, usuarios=None, avisos=None, catalogo=None, email=None,
                 relogio=None, cache=None, limite=None) -> None:
        self.config = config
        self.relogio = relogio or RelogioDoSistema()
        self.ids = GeradorDeIdsUuid()
        self.usuarios = usuarios or UsuarioRepositoryDjango()
        self.avisos = avisos or AvisoRepositoryDjango()
        self.hasher = HasherDjango()
        self.tokens = TokenJwt(config.segredo, RevogadosDjango())
        self.tokens_recuperacao = TokenDeRecuperacaoJwt(config.segredo)
        self.email = email or self._escolher_email()
        self.catalogo_base = catalogo or self._escolher_catalogo()
        if cache is None:
            from django.core.cache import cache as cache_django
            cache = cache_django
        self.catalogo = CatalogoComCache(self.catalogo_base, cache)
        if limite is None:
            from django.core.cache import caches
            limite = LimiteNoCache(caches["seguranca"])
        self.limite = limite

    # ------------------------------------------------------------ escolhas

    def _escolher_catalogo(self):
        local = CatalogoLocal(RAIZ / "dados" / "catalogo_local.json")
        c = self.config
        if c.catalogo == "local" or (c.catalogo == "auto" and not c.tem_tmdb):
            return local
        if not c.tem_tmdb:
            raise RuntimeError("CINEMA_CATALOGO=tmdb, mas TMDB_TOKEN não foi definido.")
        tmdb = CatalogoTmdb(token=c.tmdb_token or None, api_key=c.tmdb_api_key or None,
                            hoje=lambda: self.relogio.agora().date())
        return CatalogoComFallback(tmdb, local)

    def _escolher_email(self):
        if self.config.email == "ses":
            return EmailSes(self.config.ses_remetente, self.config.aws_regiao)
        return EmailPorLog()

    # ------------------------------------------------------------ casos de uso

    def casos_de_uso(self) -> CasosDeUso:
        u, a, cat, r = self.usuarios, self.avisos, self.catalogo, self.relogio
        return CasosDeUso(
            cadastrar=uc.CadastrarConta(u, self.hasher, self.tokens, self.ids, r),
            login=uc.FazerLogin(u, self.hasher, self.tokens, self.limite),
            logout=uc.FazerLogout(self.tokens),
            autenticar=uc.AutenticarUsuario(u, self.tokens),
            solicitar_recuperacao=uc.SolicitarRecuperacaoDeSenha(u, self.tokens_recuperacao, self.email),
            redefinir_senha=uc.RedefinirSenha(u, self.tokens_recuperacao, self.hasher),
            em_cartaz=uc.ListarFilmesEmCartaz(cat),
            populares=uc.ListarPopulares(cat),
            mais_bem_avaliados=uc.ListarMaisBemAvaliados(cat),
            lancamentos=uc.ListarLancamentos(cat, r),
            filtrar=uc.FiltrarPorCategoria(cat),
            generos=uc.ListarGeneros(cat),
            detalhar=uc.DetalharFilme(cat),
            trailer=uc.ObterTrailer(cat),
            onde_assistir=uc.ObterOndeAssistir(cat),
            obter_preferencias=uc.ObterPreferencias(u),
            atualizar_preferencias=uc.AtualizarPreferencias(u),
            ativar_aviso=uc.AtivarAvisoDeLancamento(a, cat, self.ids, r),
            meus_avisos=uc.ListarMeusAvisos(a),
            cancelar_aviso=uc.CancelarAviso(a),
            relogio=r,
            descrever_sistema=self.descrever,
            url_redefinir_senha=f"{self.config.url_frontend}/redefinir-senha",
        )

    def disparar_avisos(self) -> uc.DispararAvisosDeEstreia:
        return uc.DispararAvisosDeEstreia(self.avisos, self.usuarios, self.email, self.relogio)

    def descrever(self) -> dict:
        """Usado pela página "Como funciona": mostra as peças ativas agora."""
        nome = lambda o: type(o).__name__  # noqa: E731
        return {
            "catalogo": self.catalogo.nome,
            "tem_tmdb": self.config.tem_tmdb,
            "camadas": [
                {"nome": "Entities", "pasta": "cinema/entidades",
                 "itens": ["Filme", "Usuario", "Preferencias", "AvisoDeLancamento", "Genero", "Trailer"]},
                {"nome": "Use Cases", "pasta": "cinema/casos_de_uso",
                 "itens": ["CadastrarConta", "FazerLogin", "ListarLancamentos", "FiltrarPorCategoria",
                           "ObterTrailer", "ObterOndeAssistir", "AtualizarPreferencias", "AtivarAvisoDeLancamento", "…"]},
                {"nome": "Interface Adapters", "pasta": "cinema/adaptadores",
                 "itens": [nome(self.usuarios), nome(self.avisos), type(self.catalogo_base).__name__,
                           "CatalogoComCache", nome(self.hasher), nome(self.tokens), nome(self.email),
                           "Controllers (DRF)", "Presenters"]},
                {"nome": "Frameworks & Drivers", "pasta": "cinema/frameworks_drivers · frontend",
                 "itens": ["Django + DRF", "PostgreSQL", "React + Motion", "Gunicorn",
                           "AWS (ECS, RDS, S3, CloudFront, SES)"]},
            ],
        }
