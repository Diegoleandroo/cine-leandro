from __future__ import annotations

from cinema.casos_de_uso.dtos import PaginaDeFilmes


class VitrinePresenter:
    """ViewModel PÚBLICO da tela de Entrar: só pôster, título e data de estreia.

    Como qualquer pessoa (mesmo sem login) recebe este JSON, ele mostra o mínimo:
    nada de sinopse, notas, ids internos ou dados de conta.
    """

    MAXIMO = 18

    @classmethod
    def apresentar(cls, pagina: PaginaDeFilmes) -> dict:
        com_poster = [f for f in pagina.filmes if f.poster_url][: cls.MAXIMO]
        return {
            "filmes": [
                {
                    "titulo": f.titulo,
                    "poster_url": f.poster_url,
                    "data_lancamento": f.data_lancamento.isoformat() if f.data_lancamento else None,
                }
                for f in com_poster
            ]
        }
