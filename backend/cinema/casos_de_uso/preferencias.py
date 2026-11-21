"""Casos de uso de preferências: tema visual, idioma e acessibilidade.

Sem login, a tela guarda as preferências no próprio navegador. Com login,
elas ficam na conta e acompanham o usuário em qualquer dispositivo.
"""

from __future__ import annotations

from dataclasses import dataclass

from cinema.entidades import DadosInvalidos, Idioma, Preferencias, TamanhoFonte, Tema

from .portas import UsuarioRepository


def _enum(tipo, valor, campo: str):
    try:
        return tipo(valor)
    except ValueError as erro:
        opcoes = ", ".join(e.value for e in tipo)
        raise DadosInvalidos(f"Valor inválido para {campo}. Use: {opcoes}.") from erro


@dataclass
class ObterPreferencias:
    usuarios: UsuarioRepository

    def executar(self, usuario_id: str) -> Preferencias:
        usuario = self.usuarios.buscar_por_id(usuario_id)
        return usuario.preferencias if usuario else Preferencias()


@dataclass
class AtualizarPreferencias:
    usuarios: UsuarioRepository

    def executar(
        self,
        usuario_id: str,
        *,
        tema: str | None = None,
        idioma: str | None = None,
        tamanho_fonte: str | None = None,
        reduzir_animacoes: bool | None = None,
    ) -> Preferencias:
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise DadosInvalidos("Usuário não encontrado.")
        mudancas: dict = {}
        if tema is not None:
            mudancas["tema"] = _enum(Tema, tema, "tema")
        if idioma is not None:
            mudancas["idioma"] = _enum(Idioma, idioma, "idioma")
        if tamanho_fonte is not None:
            mudancas["tamanho_fonte"] = _enum(TamanhoFonte, tamanho_fonte, "tamanho da fonte")
        if reduzir_animacoes is not None:
            mudancas["reduzir_animacoes"] = bool(reduzir_animacoes)
        usuario.atualizar_preferencias(**mudancas)
        self.usuarios.atualizar(usuario)
        return usuario.preferencias
