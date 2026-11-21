"""DTOs: os objetos que entram e saem dos casos de uso.

O Controller monta um DTO de entrada; o caso de uso devolve um DTO de saída
(ou uma entidade); o Presenter transforma isso no JSON da tela (ViewModel).
Nenhum deles sabe o que é HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from cinema.entidades import Filme, Preferencias, Usuario


class ListaDeFilmes(str, Enum):
    EM_CARTAZ = "EM_CARTAZ"
    POPULARES = "POPULARES"
    MAIS_BEM_AVALIADOS = "MAIS_BEM_AVALIADOS"
    LANCAMENTOS = "LANCAMENTOS"


@dataclass(frozen=True)
class PaginaDeFilmes:
    filmes: tuple[Filme, ...]
    pagina: int = 1
    total_paginas: int = 1


@dataclass(frozen=True)
class CadastroEntrada:
    nome: str
    email: str
    senha: str
    preferencias: Preferencias | None = None  # as que o visitante já tinha escolhido


@dataclass(frozen=True)
class SessaoDeLogin:
    token: str
    usuario: Usuario
