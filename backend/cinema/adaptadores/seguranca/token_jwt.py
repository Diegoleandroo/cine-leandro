"""Tokens JWT (PyJWT) para login e para o link de recuperação de senha.

- Token de acesso: dura 7 dias; o logout coloca o id do token (jti) numa lista de revogados.
- Token de recuperação: dura 1 hora e carrega um "carimbo" da senha atual, então
  deixa de valer assim que a senha é trocada (uso único).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import jwt

from cinema.casos_de_uso.portas import GeradorDeToken, TokenDeRecuperacao
from cinema.entidades import TokenInvalido

ALGORITMO = "HS256"


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class RevogadosEmMemoria:
    def __init__(self) -> None:
        self._jtis: set[str] = set()

    def adicionar(self, jti: str, expira_em: datetime) -> None:
        self._jtis.add(jti)

    def contem(self, jti: str) -> bool:
        return jti in self._jtis


class RevogadosDjango:
    """Lista de revogados no PostgreSQL (tabela token_revogado)."""

    def adicionar(self, jti: str, expira_em: datetime) -> None:
        from cinema.adaptadores.persistencia.models import TokenRevogadoModel

        TokenRevogadoModel.objects.update_or_create(jti=jti, defaults={"expira_em": expira_em})
        TokenRevogadoModel.objects.filter(expira_em__lt=_agora()).delete()  # faxina

    def contem(self, jti: str) -> bool:
        from cinema.adaptadores.persistencia.models import TokenRevogadoModel

        return TokenRevogadoModel.objects.filter(jti=jti).exists()


class TokenJwt(GeradorDeToken):
    def __init__(self, segredo: str, revogados, duracao: timedelta = timedelta(days=7),
                 agora: Callable[[], datetime] = _agora) -> None:
        self._segredo = segredo
        self._revogados = revogados
        self._duracao = duracao
        self._agora = agora

    def emitir(self, usuario_id: str) -> str:
        agora = self._agora()
        carga = {"sub": usuario_id, "jti": uuid.uuid4().hex, "tipo": "acesso",
                 "iat": agora, "exp": agora + self._duracao}
        return jwt.encode(carga, self._segredo, algorithm=ALGORITMO)

    def _decodificar(self, token: str) -> dict:
        try:
            carga = jwt.decode(token, self._segredo, algorithms=[ALGORITMO],
                               options={"require": ["sub", "jti", "exp"]})
        except jwt.PyJWTError as erro:
            raise TokenInvalido("Token inválido ou expirado.") from erro
        if carga.get("tipo") != "acesso":
            raise TokenInvalido("Token inválido.")
        return carga

    def ler(self, token: str) -> str:
        carga = self._decodificar(token)
        if self._revogados.contem(carga["jti"]):
            raise TokenInvalido("Esta sessão foi encerrada.")
        return carga["sub"]

    def revogar(self, token: str) -> None:
        try:
            carga = self._decodificar(token)
        except TokenInvalido:
            return  # já não vale nada
        self._revogados.adicionar(carga["jti"], datetime.fromtimestamp(carga["exp"], timezone.utc))


class TokenDeRecuperacaoJwt(TokenDeRecuperacao):
    def __init__(self, segredo: str, duracao: timedelta = timedelta(hours=1),
                 agora: Callable[[], datetime] = _agora) -> None:
        self._segredo = segredo
        self._duracao = duracao
        self._agora = agora

    def emitir(self, usuario_id: str, carimbo: str) -> str:
        agora = self._agora()
        carga = {"sub": usuario_id, "carimbo": carimbo, "tipo": "recuperacao",
                 "iat": agora, "exp": agora + self._duracao}
        return jwt.encode(carga, self._segredo, algorithm=ALGORITMO)

    def ler(self, token: str) -> tuple[str, str]:
        try:
            carga = jwt.decode(token, self._segredo, algorithms=[ALGORITMO])
        except jwt.PyJWTError as erro:
            raise TokenInvalido("Este link expirou ou é inválido. Peça um novo.") from erro
        if carga.get("tipo") != "recuperacao":
            raise TokenInvalido("Este link é inválido.")
        return carga["sub"], carga["carimbo"]
