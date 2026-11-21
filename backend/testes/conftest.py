"""Peças falsas (dublês) para os testes: relógio parado e catálogo controlado."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from cinema.adaptadores.email.servicos import EmailPorLog
from cinema.adaptadores.repositorios.memoria import AvisoRepositoryEmMemoria, UsuarioRepositoryEmMemoria
from cinema.adaptadores.seguranca.token_jwt import RevogadosEmMemoria, TokenDeRecuperacaoJwt, TokenJwt
from cinema.casos_de_uso.dtos import ListaDeFilmes, PaginaDeFilmes
from cinema.casos_de_uso.portas import CatalogoDeFilmes, GeradorDeIds, HasherDeSenha, Relogio
from cinema.entidades import Filme, Genero, Idioma, OndeAssistir, Provedor, Trailer

AGORA = datetime(2026, 11, 15, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
HOJE = AGORA.date()

FICCAO, DRAMA = Genero(878, "Ficção científica"), Genero(18, "Drama")
CLASSICO = Filme("tmdb-1", "Clássico", "Já lançado.", date(1999, 3, 31), 8.7, (FICCAO,))
ESTREIA_PROXIMA = Filme("tmdb-2", "Estreia Próxima", "Lança em 10 dias.", HOJE + timedelta(days=10), 0, (DRAMA,),
                        poster_url="https://image.tmdb.org/t/p/w500/estreia.jpg")
ESTREIA_DISTANTE = Filme("tmdb-3", "Estreia Distante", "Lança em 60 dias.", HOJE + timedelta(days=60), 0, (FICCAO,))


class RelogioFixo(Relogio):
    def __init__(self, agora: datetime = AGORA) -> None:
        self.momento = agora

    def agora(self) -> datetime:
        return self.momento

    def avancar(self, **kwargs) -> None:
        self.momento += timedelta(**kwargs)


class IdsSequenciais(GeradorDeIds):
    def __init__(self) -> None:
        self.n = 0

    def novo_id(self) -> str:
        self.n += 1
        return f"id{self.n:04d}"


class HasherFalso(HasherDeSenha):
    """Rápido e previsível (o de verdade, PBKDF2, é lento de propósito)."""

    def gerar(self, senha: str) -> str:
        return f"hash::{senha[::-1]}::{len(senha)}"

    def conferir(self, senha: str, senha_hash: str) -> bool:
        return self.gerar(senha) == senha_hash


class CatalogoFalso(CatalogoDeFilmes):
    nome = "Catálogo falso"

    def __init__(self, filmes=(CLASSICO, ESTREIA_DISTANTE, ESTREIA_PROXIMA)) -> None:
        self.filmes = list(filmes)
        self.chamadas = 0

    def listar(self, lista, idioma, pagina=1, genero_id=None):
        self.chamadas += 1
        filmes = [f for f in self.filmes if genero_id is None or any(g.id == genero_id for g in f.generos)]
        if lista is ListaDeFilmes.LANCAMENTOS:
            filmes = [f for f in filmes if f.data_lancamento and f.data_lancamento > HOJE - timedelta(days=5)]
        return PaginaDeFilmes(tuple(filmes), pagina, 1)

    def generos(self, idioma):
        self.chamadas += 1
        return [DRAMA, FICCAO] if idioma is Idioma.PT else [replace(DRAMA, nome="Drama"), replace(FICCAO, nome="Science Fiction")]

    def detalhes(self, filme_id, idioma):
        self.chamadas += 1
        return next((f for f in self.filmes if f.id == filme_id), None)

    def trailers(self, filme_id, idioma):
        self.chamadas += 1
        if filme_id != "tmdb-1":
            return []
        return [Trailer("abcEN", "Official Trailer", "en"), Trailer("abcPT", "Trailer Dublado", "pt")]

    def onde_assistir(self, filme_id, regiao):
        self.chamadas += 1
        if filme_id != "tmdb-1" or regiao != "BR":
            return OndeAssistir(regiao=regiao)
        netflix, prime = Provedor(8, "Netflix", "https://img/netflix.png"), Provedor(119, "Prime Video")
        return OndeAssistir(regiao="BR", link="https://www.themoviedb.org/movie/1/watch?locale=BR",
                            assinatura=(netflix, netflix), aluguel=(prime,), compra=(prime,))


@pytest.fixture
def relogio():
    return RelogioFixo()


@pytest.fixture
def pecas(relogio):
    """Tudo o que os casos de uso precisam, em memória."""
    revogados = RevogadosEmMemoria()

    class P:
        pass

    p = P()
    p.relogio = relogio
    p.ids = IdsSequenciais()
    p.usuarios = UsuarioRepositoryEmMemoria()
    p.avisos = AvisoRepositoryEmMemoria()
    p.hasher = HasherFalso()
    p.tokens = TokenJwt("segredo-de-teste-com-32-caracteres!", revogados)
    p.recuperacao = TokenDeRecuperacaoJwt("segredo-de-teste-com-32-caracteres!")
    p.email = EmailPorLog()
    p.catalogo = CatalogoFalso()
    return p


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Cria também a tabela de cache usada pelo limite de tentativas."""
    from django.core.management import call_command

    with django_db_blocker.unblock():
        call_command("createcachetable", verbosity=0)


class CacheDeDicionario:
    """Cache falso (get/set/delete) para testar o LimiteNoCache sem banco."""

    def __init__(self) -> None:
        self.dados = {}

    def get(self, chave, padrao=None):
        return self.dados.get(chave, padrao)

    def set(self, chave, valor, segundos=None):
        self.dados[chave] = valor

    def delete(self, chave):
        self.dados.pop(chave, None)
