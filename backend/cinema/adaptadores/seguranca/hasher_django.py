"""Hash de senha usando o sistema do próprio Django (PBKDF2 com salt, por padrão).

O núcleo só conhece a porta HasherDeSenha. Trocar por Argon2 ou bcrypt é
mudar a configuração PASSWORD_HASHERS do Django, sem tocar no núcleo.
"""

from __future__ import annotations

from django.contrib.auth.hashers import check_password, make_password

from cinema.casos_de_uso.portas import HasherDeSenha


class HasherDjango(HasherDeSenha):
    def gerar(self, senha: str) -> str:
        return make_password(senha)

    def conferir(self, senha: str, senha_hash: str) -> bool:
        return check_password(senha, senha_hash)
