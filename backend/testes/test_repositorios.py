"""Testes de CONTRATO: o mesmo teste roda no repositório em memória e no
PostgreSQL (Django ORM). Se os dois passam, dá para trocar um pelo outro."""

from dataclasses import replace
from datetime import timedelta

import pytest

from cinema.adaptadores.repositorios.django_orm import AvisoRepositoryDjango, UsuarioRepositoryDjango
from cinema.adaptadores.repositorios.memoria import AvisoRepositoryEmMemoria, UsuarioRepositoryEmMemoria
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

from .conftest import AGORA, ESTREIA_DISTANTE, ESTREIA_PROXIMA, HOJE


@pytest.fixture(params=["memoria", "postgresql"])
def repos(request):
    if request.param == "memoria":
        return UsuarioRepositoryEmMemoria(), AvisoRepositoryEmMemoria()
    request.getfixturevalue("db")  # pytest-django: banco de teste no PostgreSQL
    return UsuarioRepositoryDjango(), AvisoRepositoryDjango()


def usuario(id="u1", email="diego@exemplo.com"):
    return Usuario(id=id, nome="Diego", email=email, senha_hash="h", criado_em=AGORA,
                   preferencias=Preferencias(Tema.CLARO, Idioma.ES, TamanhoFonte.G, True))


def test_usuario_ida_e_volta(repos):
    usuarios, _ = repos
    usuarios.salvar_novo(usuario())
    lido = usuarios.buscar_por_email("diego@exemplo.com")
    assert lido == usuario()
    assert usuarios.buscar_por_id("u1") == lido
    assert usuarios.buscar_por_id("nao-existe") is None


def test_email_unico(repos):
    usuarios, _ = repos
    usuarios.salvar_novo(usuario())
    with pytest.raises(EmailJaCadastrado):
        usuarios.salvar_novo(usuario(id="u2"))


def test_atualizar_usuario(repos):
    usuarios, _ = repos
    u = usuario()
    usuarios.salvar_novo(u)
    u.atualizar_preferencias(tema=Tema.ALTO_CONTRASTE)
    u.senha_hash = "novo"
    usuarios.atualizar(u)
    lido = usuarios.buscar_por_id("u1")
    assert lido.preferencias.tema is Tema.ALTO_CONTRASTE and lido.senha_hash == "novo"


def test_avisos_contrato_completo(repos):
    usuarios, avisos = repos
    usuarios.salvar_novo(usuario())
    a1 = AvisoDeLancamento.criar(id="a1", usuario_id="u1", filme=ESTREIA_PROXIMA, agora=AGORA)
    a2 = AvisoDeLancamento.criar(id="a2", usuario_id="u1", filme=ESTREIA_DISTANTE, agora=AGORA)
    avisos.salvar_novo(a1)
    avisos.salvar_novo(a2)
    with pytest.raises(AvisoJaExiste):
        avisos.salvar_novo(replace(a1, id="a3"))

    assert avisos.buscar("u1", ESTREIA_PROXIMA.id) == a1
    assert {a.id for a in avisos.listar_do_usuario("u1")} == {"a1", "a2"}

    dia_da_estreia = ESTREIA_PROXIMA.data_lancamento
    assert avisos.pendentes_ate(HOJE) == []
    assert [a.id for a in avisos.pendentes_ate(dia_da_estreia)] == ["a1"]

    a1.marcar_enviado(AGORA + timedelta(days=10))
    avisos.atualizar(a1)
    assert avisos.pendentes_ate(dia_da_estreia) == []

    avisos.remover("a2")
    assert [a.id for a in avisos.listar_do_usuario("u1")] == ["a1"]
