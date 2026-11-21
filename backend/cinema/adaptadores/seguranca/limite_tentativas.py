"""Limite de senhas erradas por conta, guardado num cache.

No Docker/AWS o cache é a tabela de cache do Django no PostgreSQL: assim todos os
processos do Gunicorn enxergam a mesma contagem (o cache em memória seria um por processo).
"""

from __future__ import annotations

import hashlib

from cinema.casos_de_uso.portas import LimiteDeTentativas


class LimiteNoCache(LimiteDeTentativas):
    def __init__(self, cache, maximo: int = 5, janela_segundos: int = 15 * 60) -> None:
        self.cache = cache
        self.maximo = maximo
        self.janela = janela_segundos

    def _chave(self, chave: str) -> str:
        # Guardamos um "resumo" do e-mail, nunca o e-mail em si.
        return "login-falhas:" + hashlib.sha256(chave.encode()).hexdigest()

    def bloqueado(self, chave: str) -> bool:
        return (self.cache.get(self._chave(chave)) or 0) >= self.maximo

    def registrar_falha(self, chave: str) -> None:
        k = self._chave(chave)
        self.cache.set(k, (self.cache.get(k) or 0) + 1, self.janela)

    def limpar(self, chave: str) -> None:
        self.cache.delete(self._chave(chave))
