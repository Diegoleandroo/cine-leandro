"""Gateways de catálogo: TMDB (com a internet simulada), local, plano B e cache."""

import json
from datetime import date
from pathlib import Path

import httpx

from cinema.adaptadores.gateways.catalogo_com_cache import CatalogoComCache
from cinema.adaptadores.gateways.catalogo_com_fallback import CatalogoComFallback
from cinema.adaptadores.gateways.catalogo_local import CatalogoLocal
from cinema.adaptadores.gateways.catalogo_tmdb import CatalogoTmdb
from cinema.casos_de_uso.dtos import ListaDeFilmes
from cinema.entidades import Idioma

from .conftest import CatalogoFalso

ARQUIVO_LOCAL = Path(__file__).resolve().parents[1] / "dados" / "catalogo_local.json"


def tmdb_simulado(registro: list):
    """Responde como o TMDB, sem internet, e anota o que foi pedido."""

    def responder(req: httpx.Request) -> httpx.Response:
        registro.append(req)
        caminho = req.url.path.removeprefix("/3")
        if caminho == "/genre/movie/list":
            return httpx.Response(200, json={"genres": [{"id": 878, "name": "Ficção científica"}]})
        if caminho in ("/movie/upcoming", "/discover/movie", "/movie/popular"):
            return httpx.Response(200, json={"page": 1, "total_pages": 900, "results": [
                {"id": 99, "title": "Filme Novo", "overview": "Sinopse.", "release_date": "2026-12-18",
                 "vote_average": 7.456, "genre_ids": [878, 1], "poster_path": "/p.jpg", "backdrop_path": None}]})
        if caminho == "/movie/99":
            return httpx.Response(200, json={
                "id": 99, "title": "Filme Novo", "overview": "Sinopse.", "release_date": "2026-12-10",
                "runtime": 142, "vote_average": 7.4, "genres": [{"id": 878, "name": "Ficção científica"}],
                "release_dates": {"results": [{"iso_3166_1": "BR", "release_dates": [
                    {"type": 3, "release_date": "2026-12-18T00:00:00.000Z", "certification": "12"}]}]}})
        if caminho == "/movie/99/videos":
            return httpx.Response(200, json={"results": [
                {"site": "Vimeo", "type": "Trailer", "key": "nao"},
                {"site": "YouTube", "type": "Teaser", "key": "teaser1", "iso_639_1": "pt", "name": "Teaser"},
                {"site": "YouTube", "type": "Trailer", "key": "trailer1", "iso_639_1": "en", "name": "Trailer", "official": True}]})
        if caminho == "/movie/99/watch/providers":
            return httpx.Response(200, json={"id": 99, "results": {
                "BR": {"link": "https://www.themoviedb.org/movie/99/watch?locale=BR",
                       "flatrate": [{"provider_id": 337, "provider_name": "Disney Plus", "logo_path": "/d.jpg", "display_priority": 5},
                                    {"provider_id": 8, "provider_name": "Netflix", "logo_path": "/n.jpg", "display_priority": 1}],
                       "ads": [{"provider_id": 999, "provider_name": "Pluto TV", "logo_path": None, "display_priority": 9}],
                       "rent": [{"provider_id": 2, "provider_name": "Apple TV", "logo_path": "/a.jpg", "display_priority": 3}]},
                "US": {"flatrate": [{"provider_id": 15, "provider_name": "Hulu", "display_priority": 1}]}}})
        return httpx.Response(404, json={})

    return responder


def criar_tmdb(registro):
    return CatalogoTmdb(token="falso", cliente=httpx.Client(transport=httpx.MockTransport(tmdb_simulado(registro))),
                        hoje=lambda: date(2026, 11, 15))


def test_tmdb_converte_lista_para_entidades():
    registro = []
    pagina = criar_tmdb(registro).listar(ListaDeFilmes.LANCAMENTOS, Idioma.PT)
    f = pagina.filmes[0]
    assert (f.id, f.titulo, f.nota, f.data_lancamento) == ("tmdb-99", "Filme Novo", 7.5, date(2026, 12, 18))
    assert [g.nome for g in f.generos] == ["Ficção científica"]  # gênero desconhecido (1) é ignorado
    assert f.poster_url.endswith("/p.jpg") and f.fundo_url is None
    assert pagina.total_paginas == 500  # o TMDB não passa da página 500
    pedido = registro[0]  # a lista; depois vem a busca dos nomes dos gêneros
    assert pedido.url.path.endswith("/movie/upcoming")
    assert pedido.url.params["region"] == "BR" and pedido.url.params["language"] == "pt-BR"
    assert pedido.headers["Authorization"] == "Bearer falso"


def test_tmdb_filtro_por_genero_usa_discover():
    registro = []
    criar_tmdb(registro).listar(ListaDeFilmes.LANCAMENTOS, Idioma.EN, genero_id=878)
    p = registro[0].url.params
    assert registro[0].url.path.endswith("/discover/movie")
    assert p["with_genres"] == "878" and p["release_date.gte"] == "2026-11-16" and p["language"] == "en-US"


def test_tmdb_detalhes_usa_data_e_classificacao_do_brasil():
    f = criar_tmdb([]).detalhes("tmdb-99", Idioma.PT)
    assert f.data_lancamento == date(2026, 12, 18) and f.classificacao == "12" and f.duracao_min == 142
    assert criar_tmdb([]).detalhes("local-matrix", Idioma.PT) is None
    assert criar_tmdb([]).detalhes("tmdb-12345", Idioma.PT) is None  # 404


def test_tmdb_trailers_so_youtube_trailer_oficial_primeiro():
    assert [t.chave for t in criar_tmdb([]).trailers("tmdb-99", Idioma.PT)] == ["trailer1", "teaser1"]


def test_catalogo_local_tem_classicos_reais_e_generos_traduzidos():
    local = CatalogoLocal(ARQUIVO_LOCAL)
    titulos = [f.titulo for f in local.listar(ListaDeFilmes.POPULARES, Idioma.PT).filmes]
    assert "Cidade de Deus" in titulos and "O Poderoso Chefão" in titulos
    assert any(g.nome == "Science Fiction" for g in local.generos(Idioma.EN))
    assert local.detalhes("local-matrix", Idioma.PT).duracao_min == 136
    so_ficcao = local.listar(ListaDeFilmes.POPULARES, Idioma.PT, genero_id=878).filmes
    assert all(any(g.id == 878 for g in f.generos) for f in so_ficcao)
    json.loads(ARQUIVO_LOCAL.read_text(encoding="utf-8"))  # JSON válido


def test_plano_b_quando_o_tmdb_cai():
    class Quebrado(CatalogoFalso):
        nome = "TMDB"

        def listar(self, *a, **k):
            raise httpx.ConnectError("sem internet")

    catalogo = CatalogoComFallback(Quebrado(), CatalogoLocal(ARQUIVO_LOCAL))
    assert catalogo.listar(ListaDeFilmes.POPULARES, Idioma.PT).filmes
    assert catalogo.usando_reserva and "plano B" in catalogo.nome
    # um id local é buscado na reserva mesmo com o principal funcionando
    assert catalogo.detalhes("local-matrix", Idioma.PT).titulo == "Matrix"


def test_cache_evita_chamadas_repetidas():
    class CacheSimples(dict):
        def set(self, k, v, t):
            self[k] = v

    falso = CatalogoFalso()
    catalogo = CatalogoComCache(falso, CacheSimples())
    for _ in range(3):
        catalogo.listar(ListaDeFilmes.POPULARES, Idioma.PT)
        catalogo.detalhes("tmdb-1", Idioma.PT)
    assert falso.chamadas == 2
    catalogo.listar(ListaDeFilmes.POPULARES, Idioma.EN)  # outro idioma, outra chave
    assert falso.chamadas == 3


def test_tmdb_onde_assistir_no_brasil():
    o = criar_tmdb([]).onde_assistir("tmdb-99", "BR")
    assert [p.nome for p in o.assinatura] == ["Netflix", "Disney Plus"]  # ordem de destaque
    assert o.assinatura[0].logo_url.endswith("/w92/n.jpg")
    assert [p.nome for p in o.gratis] == ["Pluto TV"] and o.gratis[0].logo_url is None
    assert [p.nome for p in o.aluguel] == ["Apple TV"] and o.compra == ()
    assert o.link.endswith("locale=BR")
    assert not criar_tmdb([]).onde_assistir("tmdb-99", "PT").disponivel  # país sem dados
    assert not criar_tmdb([]).onde_assistir("local-matrix", "BR").disponivel
