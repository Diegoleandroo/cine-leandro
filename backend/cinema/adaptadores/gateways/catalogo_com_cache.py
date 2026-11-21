"""Cache na frente do catálogo (padrão Decorator).

Listas de filmes mudam pouco ao longo do dia. Guardar as respostas por alguns
minutos deixa o site mais rápido e respeita o limite de requisições do TMDB.

O `cache` é qualquer objeto com get(chave) e set(chave, valor, segundos):
o cache do Django serve (memória local, Redis, ElastiCache...).
"""

from __future__ import annotations

from cinema.casos_de_uso.dtos import ListaDeFilmes, PaginaDeFilmes
from cinema.casos_de_uso.portas import CatalogoDeFilmes
from cinema.entidades import Filme, Genero, Idioma, OndeAssistir, Trailer

_VAZIO = object()


class CatalogoComCache(CatalogoDeFilmes):
    def __init__(self, catalogo: CatalogoDeFilmes, cache, segundos: int = 600) -> None:
        self._catalogo = catalogo
        self._cache = cache
        self._segundos = segundos

    @property
    def nome(self) -> str:  # type: ignore[override]
        return self._catalogo.nome

    def _lembrar(self, chave: str, calcular):
        chave = f"catalogo:{chave}"
        valor = self._cache.get(chave, _VAZIO)
        if valor is _VAZIO:
            valor = calcular()
            if not getattr(self._catalogo, "usando_reserva", False):  # não guarda o plano B
                self._cache.set(chave, valor, self._segundos)
        return valor

    def listar(self, lista: ListaDeFilmes, idioma: Idioma, pagina: int = 1, genero_id: int | None = None) -> PaginaDeFilmes:
        return self._lembrar(
            f"lista:{lista.value}:{idioma.value}:{pagina}:{genero_id}",
            lambda: self._catalogo.listar(lista, idioma, pagina, genero_id),
        )

    def generos(self, idioma: Idioma) -> list[Genero]:
        return self._lembrar(f"generos:{idioma.value}", lambda: self._catalogo.generos(idioma))

    def detalhes(self, filme_id: str, idioma: Idioma) -> Filme | None:
        return self._lembrar(f"filme:{filme_id}:{idioma.value}", lambda: self._catalogo.detalhes(filme_id, idioma))

    def trailers(self, filme_id: str, idioma: Idioma) -> list[Trailer]:
        return self._lembrar(f"trailers:{filme_id}:{idioma.value}", lambda: self._catalogo.trailers(filme_id, idioma))

    def onde_assistir(self, filme_id: str, regiao: str) -> OndeAssistir:
        return self._lembrar(f"onde:{filme_id}:{regiao}", lambda: self._catalogo.onde_assistir(filme_id, regiao))
