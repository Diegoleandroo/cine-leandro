"""Repositórios com o ORM do Django, gravando no PostgreSQL.

Cada repositório traduz Entidade <-> Model. Os casos de uso só enxergam a
porta (UsuarioRepository, AvisoRepository); não sabem que existe Django.
"""

from __future__ import annotations

from datetime import date

from django.db import IntegrityError, transaction

from cinema.adaptadores.persistencia.models import AvisoModel, UsuarioModel
from cinema.casos_de_uso.portas import AvisoRepository, UsuarioRepository
from cinema.entidades import (
    AvisoDeLancamento,
    AvisoJaExiste,
    EmailJaCadastrado,
    Idioma,
    Preferencias,
    TamanhoFonte,
    Tema,
    Usuario,
)

# ----------------------------------------------------------------- usuário


def _usuario(m: UsuarioModel) -> Usuario:
    return Usuario(
        id=m.id,
        nome=m.nome,
        email=m.email,
        senha_hash=m.senha_hash,
        criado_em=m.criado_em,
        preferencias=Preferencias(
            tema=Tema(m.tema),
            idioma=Idioma(m.idioma),
            tamanho_fonte=TamanhoFonte(m.tamanho_fonte),
            reduzir_animacoes=m.reduzir_animacoes,
        ),
    )


def _campos_usuario(u: Usuario) -> dict:
    p = u.preferencias
    return {
        "nome": u.nome,
        "email": u.email,
        "senha_hash": u.senha_hash,
        "criado_em": u.criado_em,
        "tema": p.tema.value,
        "idioma": p.idioma.value,
        "tamanho_fonte": p.tamanho_fonte.value,
        "reduzir_animacoes": p.reduzir_animacoes,
    }


class UsuarioRepositoryDjango(UsuarioRepository):
    def salvar_novo(self, usuario: Usuario) -> None:
        try:
            with transaction.atomic():
                UsuarioModel.objects.create(id=usuario.id, **_campos_usuario(usuario))
        except IntegrityError as erro:  # o índice único do PostgreSQL é a última palavra
            raise EmailJaCadastrado("Já existe uma conta com este e-mail.") from erro

    def atualizar(self, usuario: Usuario) -> None:
        UsuarioModel.objects.filter(id=usuario.id).update(**_campos_usuario(usuario))

    def buscar_por_id(self, usuario_id: str) -> Usuario | None:
        m = UsuarioModel.objects.filter(id=usuario_id).first()
        return _usuario(m) if m else None

    def buscar_por_email(self, email: str) -> Usuario | None:
        m = UsuarioModel.objects.filter(email=email).first()
        return _usuario(m) if m else None


# ----------------------------------------------------------------- aviso


def _aviso(m: AvisoModel) -> AvisoDeLancamento:
    return AvisoDeLancamento(
        id=m.id,
        usuario_id=m.usuario_id,
        filme_id=m.filme_id,
        filme_titulo=m.filme_titulo,
        data_lancamento=m.data_lancamento,
        criado_em=m.criado_em,
        enviado_em=m.enviado_em,
    )


class AvisoRepositoryDjango(AvisoRepository):
    def salvar_novo(self, aviso: AvisoDeLancamento) -> None:
        try:
            with transaction.atomic():
                AvisoModel.objects.create(
                    id=aviso.id,
                    usuario_id=aviso.usuario_id,
                    filme_id=aviso.filme_id,
                    filme_titulo=aviso.filme_titulo,
                    data_lancamento=aviso.data_lancamento,
                    criado_em=aviso.criado_em,
                    enviado_em=aviso.enviado_em,
                )
        except IntegrityError as erro:
            raise AvisoJaExiste("Você já tem um aviso para este filme.") from erro

    def atualizar(self, aviso: AvisoDeLancamento) -> None:
        AvisoModel.objects.filter(id=aviso.id).update(
            filme_titulo=aviso.filme_titulo,
            data_lancamento=aviso.data_lancamento,
            enviado_em=aviso.enviado_em,
        )

    def buscar(self, usuario_id: str, filme_id: str) -> AvisoDeLancamento | None:
        m = AvisoModel.objects.filter(usuario_id=usuario_id, filme_id=filme_id).first()
        return _aviso(m) if m else None

    def listar_do_usuario(self, usuario_id: str) -> list[AvisoDeLancamento]:
        return [_aviso(m) for m in AvisoModel.objects.filter(usuario_id=usuario_id)]

    def remover(self, aviso_id: str) -> None:
        AvisoModel.objects.filter(id=aviso_id).delete()

    def pendentes_ate(self, dia: date) -> list[AvisoDeLancamento]:
        consulta = AvisoModel.objects.filter(enviado_em__isnull=True, data_lancamento__lte=dia)
        return [_aviso(m) for m in consulta.order_by("data_lancamento")]
