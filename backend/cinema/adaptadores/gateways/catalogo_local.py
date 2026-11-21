"""Plano B: um catálogo de filmes reais e conhecidos guardado num arquivo JSON.

É usado quando não há chave do TMDB ou quando a internet cai. Não tem pôsteres
nem trailers (isso só o TMDB fornece) e não tem lançamentos futuros.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from cinema.casos_de_uso.dtos import ListaDeFilmes, PaginaDeFilmes
from cinema.casos_de_uso.portas import CatalogoDeFilmes
from cinema.entidades import Filme, Genero, Idioma, OndeAssistir, Trailer

POR_PAGINA = 20


class CatalogoLocal(CatalogoDeFilmes):
    nome = "Catálogo local (JSON)"

    def __init__(self, arquivo: Path) -> None:
        self._arquivo = Path(arquivo)
        self._dados: dict | None = None

    def _carregar(self) -> dict:
        if self._dados is None:
            self._dados = json.loads(self._arquivo.read_text(encoding="utf-8"))
        return self._dados

    def _nomes_generos(self, idioma: Idioma) -> dict[int, str]:
        chave = idioma.value.lower()
        return {int(g["id"]): g.get(chave) or g["pt"] for g in self._carregar()["generos"]}

    def _filmes(self, idioma: Idioma) -> list[Filme]:
        nomes = self._nomes_generos(idioma)
        return [
            Filme(
                id=f["id"],
                titulo=f["titulo"],
                sinopse=f["sinopse"],
                data_lancamento=date.fromisoformat(f["data_lancamento"]) if f.get("data_lancamento") else None,
                nota=float(f.get("nota", 0)),
                generos=tuple(Genero(g, nomes[g]) for g in f.get("generos", []) if g in nomes),
                duracao_min=f.get("duracao_min"),
                origem="local",
            )
            for f in self._carregar()["filmes"]
        ]

    def listar(self, lista: ListaDeFilmes, idioma: Idioma, pagina: int = 1, genero_id: int | None = None) -> PaginaDeFilmes:
        hoje = date.today()
        filmes = self._filmes(idioma)
        if genero_id is not None:
            filmes = [f for f in filmes if any(g.id == genero_id for g in f.generos)]
        if lista is ListaDeFilmes.LANCAMENTOS:
            filmes = sorted((f for f in filmes if not f.ja_lancado(hoje)), key=lambda f: f.data_lancamento)
        elif lista is ListaDeFilmes.MAIS_BEM_AVALIADOS:
            filmes = sorted(filmes, key=lambda f: f.nota, reverse=True)
        else:  # em cartaz / populares: o catálogo local é uma seleção de clássicos
            filmes = sorted(filmes, key=lambda f: f.titulo.lower())
        total = max(1, -(-len(filmes) // POR_PAGINA))
        inicio = (pagina - 1) * POR_PAGINA
        return PaginaDeFilmes(tuple(filmes[inicio:inicio + POR_PAGINA]), pagina, total)

    def generos(self, idioma: Idioma) -> list[Genero]:
        return [Genero(i, n) for i, n in self._nomes_generos(idioma).items()]

    def detalhes(self, filme_id: str, idioma: Idioma) -> Filme | None:
        return next((f for f in self._filmes(idioma) if f.id == filme_id), None)

    def trailers(self, filme_id: str, idioma: Idioma) -> list[Trailer]:
        return []

    def onde_assistir(self, filme_id: str, regiao: str) -> OndeAssistir:
        return OndeAssistir(regiao=regiao)  # só o TMDB sabe onde cada filme está
