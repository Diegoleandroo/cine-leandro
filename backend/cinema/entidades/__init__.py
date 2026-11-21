"""Camada 1: Entities. As regras do negócio, em Python puro.

Não importa nada de Django, PostgreSQL, HTTP ou AWS.
"""

from .erros import (
    AvisoJaExiste,
    CredenciaisInvalidas,
    DadosInvalidos,
    EmailJaCadastrado,
    ErroDeDominio,
    FilmeJaLancado,
    MuitasTentativas,
    NaoAutenticado,
    NaoEncontrado,
    TokenInvalido,
)
from .modelo import (
    TAMANHO_MINIMO_SENHA,
    AvisoDeLancamento,
    Filme,
    Genero,
    Idioma,
    OndeAssistir,
    Preferencias,
    Provedor,
    TamanhoFonte,
    Tema,
    Trailer,
    Usuario,
    normalizar_email,
    validar_senha,
)

__all__ = [
    "TAMANHO_MINIMO_SENHA",
    "AvisoDeLancamento",
    "AvisoJaExiste",
    "CredenciaisInvalidas",
    "DadosInvalidos",
    "EmailJaCadastrado",
    "ErroDeDominio",
    "Filme",
    "FilmeJaLancado",
    "Genero",
    "Idioma",
    "MuitasTentativas",
    "NaoAutenticado",
    "NaoEncontrado",
    "OndeAssistir",
    "Preferencias",
    "Provedor",
    "TamanhoFonte",
    "Tema",
    "TokenInvalido",
    "Trailer",
    "Usuario",
    "normalizar_email",
    "validar_senha",
]
