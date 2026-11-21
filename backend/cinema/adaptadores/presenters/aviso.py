from __future__ import annotations

from datetime import date

from cinema.entidades import AvisoDeLancamento


class AvisoPresenter:
    @staticmethod
    def apresentar(a: AvisoDeLancamento, hoje: date) -> dict:
        return {
            "id": a.id,
            "filme_id": a.filme_id,
            "filme_titulo": a.filme_titulo,
            "data_lancamento": a.data_lancamento.isoformat(),
            "dias_para_estreia": max(0, (a.data_lancamento - hoje).days),
            "enviado": a.enviado,
            "enviado_em": a.enviado_em.isoformat() if a.enviado_em else None,
        }

    @classmethod
    def lista(cls, avisos: list[AvisoDeLancamento], hoje: date) -> list[dict]:
        return [cls.apresentar(a, hoje) for a in avisos]
