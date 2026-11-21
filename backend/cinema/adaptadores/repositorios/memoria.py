"""Repositórios em memória: rápidos, sem banco. Usados nos testes de casos de uso
e nos testes de contrato (o mesmo teste roda aqui e no PostgreSQL)."""

from __future__ import annotations

import copy
from datetime import date

from cinema.casos_de_uso.portas import AvisoRepository, UsuarioRepository
from cinema.entidades import AvisoDeLancamento, AvisoJaExiste, EmailJaCadastrado, Usuario


class UsuarioRepositoryEmMemoria(UsuarioRepository):
    def __init__(self) -> None:
        self._dados: dict[str, Usuario] = {}

    def salvar_novo(self, usuario: Usuario) -> None:
        if any(u.email == usuario.email for u in self._dados.values()):
            raise EmailJaCadastrado("Já existe uma conta com este e-mail.")
        self._dados[usuario.id] = copy.deepcopy(usuario)

    def atualizar(self, usuario: Usuario) -> None:
        self._dados[usuario.id] = copy.deepcopy(usuario)

    def buscar_por_id(self, usuario_id: str) -> Usuario | None:
        u = self._dados.get(usuario_id)
        return copy.deepcopy(u) if u else None

    def buscar_por_email(self, email: str) -> Usuario | None:
        for u in self._dados.values():
            if u.email == email:
                return copy.deepcopy(u)
        return None


class AvisoRepositoryEmMemoria(AvisoRepository):
    def __init__(self) -> None:
        self._dados: dict[str, AvisoDeLancamento] = {}

    def salvar_novo(self, aviso: AvisoDeLancamento) -> None:
        if self.buscar(aviso.usuario_id, aviso.filme_id):
            raise AvisoJaExiste("Você já tem um aviso para este filme.")
        self._dados[aviso.id] = copy.deepcopy(aviso)

    def atualizar(self, aviso: AvisoDeLancamento) -> None:
        self._dados[aviso.id] = copy.deepcopy(aviso)

    def buscar(self, usuario_id: str, filme_id: str) -> AvisoDeLancamento | None:
        for a in self._dados.values():
            if a.usuario_id == usuario_id and a.filme_id == filme_id:
                return copy.deepcopy(a)
        return None

    def listar_do_usuario(self, usuario_id: str) -> list[AvisoDeLancamento]:
        return [copy.deepcopy(a) for a in self._dados.values() if a.usuario_id == usuario_id]

    def remover(self, aviso_id: str) -> None:
        self._dados.pop(aviso_id, None)

    def pendentes_ate(self, dia: date) -> list[AvisoDeLancamento]:
        return [
            copy.deepcopy(a)
            for a in self._dados.values()
            if a.enviado_em is None and a.data_lancamento <= dia
        ]
