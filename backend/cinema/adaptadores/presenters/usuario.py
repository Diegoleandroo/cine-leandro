from __future__ import annotations

from cinema.casos_de_uso.dtos import SessaoDeLogin
from cinema.entidades import Usuario

from .preferencias import PreferenciasPresenter


class UsuarioPresenter:
    @staticmethod
    def apresentar(u: Usuario) -> dict:
        # Repare: o senha_hash NUNCA sai daqui. O Presenter decide o que a tela vê.
        return {
            "id": u.id,
            "nome": u.nome,
            "primeiro_nome": u.nome.split()[0],
            "email": u.email,
            "criado_em": u.criado_em.isoformat(),
            "preferencias": PreferenciasPresenter.apresentar(u.preferencias),
        }

    @classmethod
    def sessao(cls, s: SessaoDeLogin) -> dict:
        return {"token": s.token, "usuario": cls.apresentar(s.usuario)}
