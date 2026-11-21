"""Gateway para a API do TMDB (The Movie Database): filmes reais.

Traduz o JSON do TMDB para as entidades Filme, Genero e Trailer. O caso de uso
nunca vê o formato do TMDB: se amanhã você trocar por outra API, só esta classe muda.

Uso gratuito para projetos não comerciais, com crédito ao TMDB:
"This product uses the TMDB API but is not endorsed or certified by TMDB."
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import httpx

from cinema.casos_de_uso.dtos import ListaDeFilmes, PaginaDeFilmes
from cinema.casos_de_uso.portas import CatalogoDeFilmes
from cinema.entidades import Filme, Genero, Idioma, OndeAssistir, Provedor, Trailer

URL_BASE = "https://api.themoviedb.org/3"
URL_POSTER = "https://image.tmdb.org/t/p/w500"
URL_FUNDO = "https://image.tmdb.org/t/p/w1280"
URL_LOGO = "https://image.tmdb.org/t/p/w92"
PREFIXO = "tmdb-"

LINGUA = {Idioma.PT: "pt-BR", Idioma.EN: "en-US", Idioma.ES: "es-ES"}

# Listas prontas do TMDB (sem filtro de categoria)
ENDPOINT = {
    ListaDeFilmes.EM_CARTAZ: "/movie/now_playing",
    ListaDeFilmes.POPULARES: "/movie/popular",
    ListaDeFilmes.MAIS_BEM_AVALIADOS: "/movie/top_rated",
    ListaDeFilmes.LANCAMENTOS: "/movie/upcoming",
}


class CatalogoTmdb(CatalogoDeFilmes):
    nome = "TMDB (The Movie Database)"

    def __init__(
        self,
        *,
        token: str | None = None,
        api_key: str | None = None,
        regiao: str = "BR",
        cliente: httpx.Client | None = None,
        hoje: Callable[[], date] = date.today,
    ) -> None:
        if not token and not api_key:
            raise ValueError("Informe TMDB_TOKEN ou TMDB_API_KEY para usar o TMDB.")
        self._token = token
        self._api_key = api_key
        self._regiao = regiao
        self._cliente = cliente or httpx.Client(timeout=10)
        self._hoje = hoje
        self._generos_cache: dict[Idioma, dict[int, str]] = {}

    # ------------------------------------------------------------ porta

    def listar(
        self, lista: ListaDeFilmes, idioma: Idioma, pagina: int = 1, genero_id: int | None = None
    ) -> PaginaDeFilmes:
        lingua = LINGUA[idioma]
        if genero_id is None:
            params: dict[str, Any] = {"language": lingua, "page": pagina}
            if lista in (ListaDeFilmes.EM_CARTAZ, ListaDeFilmes.LANCAMENTOS):
                params["region"] = self._regiao
            dados = self._get(ENDPOINT[lista], **params)
        else:
            dados = self._get("/discover/movie", **self._filtro_discover(lista, lingua, pagina, genero_id))
        nomes = self._mapa_generos(idioma)
        filmes = tuple(self._resumo(item, nomes) for item in dados.get("results", []))
        total = min(int(dados.get("total_pages") or 1), 500)  # o TMDB não passa da página 500
        return PaginaDeFilmes(filmes, int(dados.get("page") or pagina), total)

    def generos(self, idioma: Idioma) -> list[Genero]:
        return [Genero(i, n) for i, n in self._mapa_generos(idioma).items()]

    def detalhes(self, filme_id: str, idioma: Idioma) -> Filme | None:
        numero = self._numero(filme_id)
        if numero is None:
            return None
        try:
            d = self._get(f"/movie/{numero}", language=LINGUA[idioma], append_to_response="release_dates")
        except httpx.HTTPStatusError as erro:
            if erro.response.status_code == 404:
                return None
            raise
        return self._completo(d)

    def trailers(self, filme_id: str, idioma: Idioma) -> list[Trailer]:
        numero = self._numero(filme_id)
        if numero is None:
            return []
        # Pede os vídeos no idioma escolhido e também em inglês (quase sempre há trailer em inglês).
        codigo = LINGUA[idioma].split("-")[0]
        d = self._get(
            f"/movie/{numero}/videos",
            language=LINGUA[idioma],
            include_video_language=f"{codigo},en,null",
        )
        videos = [
            v for v in d.get("results", [])
            if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser") and v.get("key")
        ]
        # Trailers oficiais primeiro, teasers depois.
        videos.sort(key=lambda v: (v.get("type") != "Trailer", not v.get("official", False)))
        return [Trailer(chave=v["key"], titulo=v.get("name") or "Trailer", idioma=v.get("iso_639_1") or "") for v in videos]

    def onde_assistir(self, filme_id: str, regiao: str) -> OndeAssistir:
        """Dados da JustWatch, via TMDB. A JustWatch PRECISA ser creditada na tela."""
        numero = self._numero(filme_id)
        if numero is None:
            return OndeAssistir(regiao=regiao)
        d = self._get(f"/movie/{numero}/watch/providers").get("results", {}).get(regiao, {})

        def provedores(*chaves: str) -> tuple[Provedor, ...]:
            itens = [p for chave in chaves for p in d.get(chave, []) or []]
            itens.sort(key=lambda p: p.get("display_priority", 999))
            return tuple(
                Provedor(
                    id=int(p["provider_id"]),
                    nome=p.get("provider_name") or "Serviço",
                    logo_url=f"{URL_LOGO}{p['logo_path']}" if p.get("logo_path") else None,
                )
                for p in itens if p.get("provider_id") is not None
            )

        return OndeAssistir(
            regiao=regiao,
            link=d.get("link"),
            assinatura=provedores("flatrate"),
            gratis=provedores("free", "ads"),
            aluguel=provedores("rent"),
            compra=provedores("buy"),
        )

    # ------------------------------------------------------------ detalhes internos

    def _filtro_discover(self, lista: ListaDeFilmes, lingua: str, pagina: int, genero_id: int) -> dict[str, Any]:
        """O TMDB não filtra as listas prontas por gênero, então usamos /discover."""
        hoje = self._hoje()
        p: dict[str, Any] = {"language": lingua, "page": pagina, "with_genres": genero_id, "include_adult": "false"}
        if lista is ListaDeFilmes.EM_CARTAZ:
            p |= {
                "region": self._regiao,
                "with_release_type": "2|3",  # estreia limitada ou nos cinemas
                "release_date.gte": (hoje - timedelta(days=45)).isoformat(),
                "release_date.lte": hoje.isoformat(),
                "sort_by": "popularity.desc",
            }
        elif lista is ListaDeFilmes.LANCAMENTOS:
            p |= {
                "region": self._regiao,
                "with_release_type": "2|3",
                "release_date.gte": (hoje + timedelta(days=1)).isoformat(),
                "sort_by": "primary_release_date.asc",
            }
        elif lista is ListaDeFilmes.MAIS_BEM_AVALIADOS:
            p |= {"sort_by": "vote_average.desc", "vote_count.gte": 500}
        else:
            p |= {"sort_by": "popularity.desc"}
        return p

    def _mapa_generos(self, idioma: Idioma) -> dict[int, str]:
        if idioma not in self._generos_cache:
            dados = self._get("/genre/movie/list", language=LINGUA[idioma])
            self._generos_cache[idioma] = {g["id"]: g["name"] for g in dados.get("genres", [])}
        return self._generos_cache[idioma]

    def _get(self, caminho: str, **params: Any) -> dict[str, Any]:
        headers = {"accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        else:
            params["api_key"] = self._api_key
        resposta = self._cliente.get(f"{URL_BASE}{caminho}", params=params, headers=headers)
        resposta.raise_for_status()
        return resposta.json()

    @staticmethod
    def _numero(filme_id: str) -> int | None:
        if not filme_id.startswith(PREFIXO) or not filme_id[len(PREFIXO):].isdigit():
            return None
        return int(filme_id[len(PREFIXO):])

    @staticmethod
    def _data(texto: str | None) -> date | None:
        try:
            return date.fromisoformat(texto) if texto else None
        except ValueError:
            return None

    def _resumo(self, d: dict[str, Any], nomes: dict[int, str]) -> Filme:
        return Filme(
            id=f"{PREFIXO}{d['id']}",
            titulo=d.get("title") or d.get("original_title") or "Sem título",
            sinopse=d.get("overview") or "",
            data_lancamento=self._data(d.get("release_date")),
            nota=round(float(d.get("vote_average") or 0), 1),
            generos=tuple(Genero(g, nomes[g]) for g in d.get("genre_ids", []) if g in nomes),
            poster_url=f"{URL_POSTER}{d['poster_path']}" if d.get("poster_path") else None,
            fundo_url=f"{URL_FUNDO}{d['backdrop_path']}" if d.get("backdrop_path") else None,
            origem="tmdb",
        )

    def _completo(self, d: dict[str, Any]) -> Filme:
        resumo = self._resumo({**d, "genre_ids": []}, {})
        return Filme(
            **{**resumo.__dict__,
               "generos": tuple(Genero(g["id"], g["name"]) for g in d.get("genres", [])),
               "duracao_min": int(d["runtime"]) if d.get("runtime") else None,
               "classificacao": self._classificacao(d),
               "data_lancamento": self._data_no_brasil(d) or resumo.data_lancamento},
        )

    def _do_pais(self, d: dict[str, Any]) -> list[dict[str, Any]]:
        for pais in d.get("release_dates", {}).get("results", []):
            if pais.get("iso_3166_1") == self._regiao:
                return pais.get("release_dates", [])
        return []

    def _classificacao(self, d: dict[str, Any]) -> str:
        """Classificação indicativa do Brasil (L, 10, 12, 14, 16, 18)."""
        for lancamento in self._do_pais(d):
            if lancamento.get("certification"):
                return lancamento["certification"]
        return ""

    def _data_no_brasil(self, d: dict[str, Any]) -> date | None:
        """Data de estreia nos cinemas do Brasil (tipos 2 e 3), se o TMDB souber."""
        datas = [
            self._data((l.get("release_date") or "")[:10])
            for l in self._do_pais(d) if l.get("type") in (2, 3)
        ]
        datas = [x for x in datas if x]
        return min(datas) if datas else None
