from __future__ import annotations

from cinema.entidades import Trailer


class TrailerPresenter:
    @staticmethod
    def apresentar(t: Trailer | None) -> dict:
        if t is None:
            return {"disponivel": False, "trailer": None}
        return {
            "disponivel": True,
            "trailer": {"chave": t.chave, "titulo": t.titulo, "idioma": t.idioma, "url_embed": t.url_embed},
        }
