from __future__ import annotations

from cinema.entidades import Preferencias


class PreferenciasPresenter:
    @staticmethod
    def apresentar(p: Preferencias) -> dict:
        return {
            "tema": p.tema.value,
            "idioma": p.idioma.value,
            "tamanho_fonte": p.tamanho_fonte.value,
            "reduzir_animacoes": p.reduzir_animacoes,
        }
