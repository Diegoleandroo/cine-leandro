from __future__ import annotations

from datetime import date

from cinema.casos_de_uso.dtos import PaginaDeFilmes
from cinema.entidades import Filme, Genero


def _duracao(minutos: int | None) -> str | None:
    if not minutos:
        return None
    h, m = divmod(minutos, 60)
    return f"{h}h {m:02d}min" if h else f"{m}min"


class GeneroPresenter:
    @staticmethod
    def apresentar(g: Genero) -> dict:
        return {"id": g.id, "nome": g.nome}

    @classmethod
    def lista(cls, generos: list[Genero]) -> list[dict]:
        return [cls.apresentar(g) for g in generos]


class FilmePresenter:
    @staticmethod
    def apresentar(f: Filme, hoje: date) -> dict:
        return {
            "id": f.id,
            "titulo": f.titulo,
            "sinopse": f.sinopse,
            "data_lancamento": f.data_lancamento.isoformat() if f.data_lancamento else None,
            "ano": f.data_lancamento.year if f.data_lancamento else None,
            "ja_lancado": f.ja_lancado(hoje),
            "dias_para_estreia": f.dias_para_estreia(hoje),
            "nota": f.nota,
            "generos": [GeneroPresenter.apresentar(g) for g in f.generos],
            "duracao_min": f.duracao_min,
            "duracao_texto": _duracao(f.duracao_min),
            "classificacao": f.classificacao,
            "poster_url": f.poster_url,
            "fundo_url": f.fundo_url,
            "origem": f.origem,
        }


class PaginaPresenter:
    @staticmethod
    def apresentar(p: PaginaDeFilmes, hoje: date) -> dict:
        return {
            "filmes": [FilmePresenter.apresentar(f, hoje) for f in p.filmes],
            "pagina": p.pagina,
            "total_paginas": p.total_paginas,
        }
