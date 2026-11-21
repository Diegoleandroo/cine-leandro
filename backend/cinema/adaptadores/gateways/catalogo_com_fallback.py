"""Plano B automático: se o TMDB falhar, o catálogo local responde."""

from __future__ import annotations

import logging

from cinema.casos_de_uso.dtos import ListaDeFilmes, PaginaDeFilmes
from cinema.casos_de_uso.portas import CatalogoDeFilmes
from cinema.entidades import Filme, Genero, Idioma, OndeAssistir, Trailer

log = logging.getLogger(__name__)


class CatalogoComFallback(CatalogoDeFilmes):
    def __init__(self, principal: CatalogoDeFilmes, reserva: CatalogoDeFilmes) -> None:
        self._principal = principal
        self._reserva = reserva
        self.nome = principal.nome
        self.usando_reserva = False

    def _tentar(self, metodo: str, *args):
        try:
            resultado = getattr(self._principal, metodo)(*args)
            self.nome, self.usando_reserva = self._principal.nome, False
            return resultado
        except Exception as erro:  # noqa: BLE001 - qualquer falha externa aciona o plano B
            log.warning("Falha em %s (%s); usando %s.", self._principal.nome, erro, self._reserva.nome)
            self.nome, self.usando_reserva = f"{self._reserva.nome} (plano B)", True
            return getattr(self._reserva, metodo)(*args)

    def listar(self, lista: ListaDeFilmes, idioma: Idioma, pagina: int = 1, genero_id: int | None = None) -> PaginaDeFilmes:
        return self._tentar("listar", lista, idioma, pagina, genero_id)

    def generos(self, idioma: Idioma) -> list[Genero]:
        return self._tentar("generos", idioma)

    def detalhes(self, filme_id: str, idioma: Idioma) -> Filme | None:
        # Um id "local-..." não existe no TMDB: nesse caso o principal devolve None.
        return self._tentar("detalhes", filme_id, idioma) or self._reserva.detalhes(filme_id, idioma)

    def trailers(self, filme_id: str, idioma: Idioma) -> list[Trailer]:
        return self._tentar("trailers", filme_id, idioma)

    def onde_assistir(self, filme_id: str, regiao: str) -> OndeAssistir:
        return self._tentar("onde_assistir", filme_id, regiao)
