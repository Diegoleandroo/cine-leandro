"""Casos de uso de filmes: listas, lançamentos, categorias, sinopse e trailer."""

from __future__ import annotations

from dataclasses import dataclass

from cinema.entidades import Filme, Genero, Idioma, NaoEncontrado, OndeAssistir, Trailer

from .dtos import ListaDeFilmes, PaginaDeFilmes
from .portas import CatalogoDeFilmes, Relogio


@dataclass
class _ListarFilmes:
    catalogo: CatalogoDeFilmes
    lista = ListaDeFilmes.EM_CARTAZ

    def executar(self, idioma: Idioma = Idioma.PT, pagina: int = 1) -> PaginaDeFilmes:
        return self.catalogo.listar(self.lista, idioma, max(1, pagina))


class ListarFilmesEmCartaz(_ListarFilmes):
    lista = ListaDeFilmes.EM_CARTAZ


class ListarPopulares(_ListarFilmes):
    lista = ListaDeFilmes.POPULARES


class ListarMaisBemAvaliados(_ListarFilmes):
    lista = ListaDeFilmes.MAIS_BEM_AVALIADOS


@dataclass
class ListarLancamentos:
    """Só filmes que ainda vão estrear, do mais próximo para o mais distante."""

    catalogo: CatalogoDeFilmes
    relogio: Relogio

    def executar(self, idioma: Idioma = Idioma.PT, pagina: int = 1, genero_id: int | None = None) -> PaginaDeFilmes:
        hoje = self.relogio.agora().date()
        resultado = self.catalogo.listar(ListaDeFilmes.LANCAMENTOS, idioma, max(1, pagina), genero_id)
        futuros = sorted(
            (f for f in resultado.filmes if not f.ja_lancado(hoje)),
            key=lambda f: (f.data_lancamento, f.titulo.lower()),
        )
        return PaginaDeFilmes(tuple(futuros), resultado.pagina, resultado.total_paginas)


@dataclass
class FiltrarPorCategoria:
    catalogo: CatalogoDeFilmes

    def executar(
        self,
        genero_id: int,
        lista: ListaDeFilmes = ListaDeFilmes.POPULARES,
        idioma: Idioma = Idioma.PT,
        pagina: int = 1,
    ) -> PaginaDeFilmes:
        return self.catalogo.listar(lista, idioma, max(1, pagina), genero_id)


@dataclass
class ListarGeneros:
    catalogo: CatalogoDeFilmes

    def executar(self, idioma: Idioma = Idioma.PT) -> list[Genero]:
        return sorted(self.catalogo.generos(idioma), key=lambda g: g.nome.lower())


@dataclass
class DetalharFilme:
    catalogo: CatalogoDeFilmes

    def executar(self, filme_id: str, idioma: Idioma = Idioma.PT) -> Filme:
        filme = self.catalogo.detalhes(filme_id, idioma)
        if filme is None:
            raise NaoEncontrado("Filme não encontrado.")
        return filme


@dataclass
class ObterTrailer:
    catalogo: CatalogoDeFilmes

    def executar(self, filme_id: str, idioma: Idioma = Idioma.PT) -> Trailer | None:
        """O primeiro trailer no idioma pedido; se não houver, o primeiro que existir."""
        trailers = self.catalogo.trailers(filme_id, idioma)
        if not trailers:
            return None
        codigo = {"PT": "pt", "EN": "en", "ES": "es"}[idioma.value]
        no_idioma = [t for t in trailers if t.idioma.startswith(codigo)]
        return (no_idioma or trailers)[0]


@dataclass
class ObterOndeAssistir:
    """Mostra onde o filme pode ser assistido legalmente (assinatura, grátis, aluguel, compra).

    Regra: os serviços aparecem na ordem de destaque e sem repetição dentro de cada grupo.
    """

    catalogo: CatalogoDeFilmes

    def executar(self, filme_id: str, regiao: str = "BR") -> OndeAssistir:
        if self.catalogo.detalhes(filme_id, Idioma.PT) is None:
            raise NaoEncontrado("Filme não encontrado.")
        o = self.catalogo.onde_assistir(filme_id, regiao.upper())

        def unicos(provedores):
            vistos, lista = set(), []
            for p in provedores:
                if p.id not in vistos:
                    vistos.add(p.id)
                    lista.append(p)
            return tuple(lista)

        return OndeAssistir(
            regiao=o.regiao,
            link=o.link,
            assinatura=unicos(o.assinatura),
            gratis=unicos(o.gratis),
            aluguel=unicos(o.aluguel),
            compra=unicos(o.compra),
        )
