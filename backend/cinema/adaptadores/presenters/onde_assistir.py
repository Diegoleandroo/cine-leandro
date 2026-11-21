from __future__ import annotations

from cinema.entidades import OndeAssistir, Provedor


def _provedor(p: Provedor) -> dict:
    return {"id": p.id, "nome": p.nome, "logo_url": p.logo_url}


class OndeAssistirPresenter:
    @staticmethod
    def apresentar(o: OndeAssistir) -> dict:
        return {
            "regiao": o.regiao,
            "disponivel": o.disponivel,
            "link": o.link,
            "grupos": [
                {"tipo": tipo, "provedores": [_provedor(p) for p in lista]}
                for tipo, lista in (
                    ("ASSINATURA", o.assinatura),
                    ("GRATIS", o.gratis),
                    ("ALUGUEL", o.aluguel),
                    ("COMPRA", o.compra),
                )
                if lista
            ],
            # Exigência do TMDB: a fonte destes dados precisa aparecer na tela.
            "fonte": "JustWatch",
        }
