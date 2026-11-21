"""Relógio e gerador de ids de verdade (os testes usam versões controladas)."""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from cinema.casos_de_uso.portas import GeradorDeIds, Relogio


class RelogioDoSistema(Relogio):
    def __init__(self, fuso: str = "America/Sao_Paulo") -> None:
        self._fuso = ZoneInfo(fuso)

    def agora(self) -> datetime:
        return datetime.now(self._fuso)


class GeradorDeIdsUuid(GeradorDeIds):
    def novo_id(self) -> str:
        return uuid.uuid4().hex
