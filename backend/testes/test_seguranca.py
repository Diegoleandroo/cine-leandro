"""Tokens JWT e hash de senha."""

from datetime import datetime, timedelta, timezone

import pytest

from cinema.adaptadores.seguranca.hasher_django import HasherDjango
from cinema.adaptadores.seguranca.token_jwt import RevogadosEmMemoria, TokenDeRecuperacaoJwt, TokenJwt
from cinema.entidades import TokenInvalido

SEGREDO = "segredo-de-teste-com-32-caracteres!"


def test_token_de_acesso_ida_volta_e_expiracao():
    agora = [datetime(2026, 11, 15, tzinfo=timezone.utc)]
    tokens = TokenJwt(SEGREDO, RevogadosEmMemoria(), timedelta(days=7), agora=lambda: agora[0])
    token = tokens.emitir("u1")
    assert tokens.ler(token) == "u1"
    with pytest.raises(TokenInvalido):
        TokenJwt("outro-segredo-com-32-caracteres!!!", RevogadosEmMemoria()).ler(token)
    agora[0] -= timedelta(days=8)  # emitido há mais de 7 dias
    with pytest.raises(TokenInvalido):
        tokens.ler(tokens.emitir("u1"))


def test_token_de_recuperacao_nao_serve_para_login():
    recuperacao = TokenDeRecuperacaoJwt(SEGREDO).emitir("u1", "carimbo")
    with pytest.raises(TokenInvalido):
        TokenJwt(SEGREDO, RevogadosEmMemoria()).ler(recuperacao)
    acesso = TokenJwt(SEGREDO, RevogadosEmMemoria()).emitir("u1")
    with pytest.raises(TokenInvalido):
        TokenDeRecuperacaoJwt(SEGREDO).ler(acesso)


@pytest.mark.django_db
def test_revogacao_fica_gravada_no_postgresql():
    from cinema.adaptadores.seguranca.token_jwt import RevogadosDjango

    tokens = TokenJwt(SEGREDO, RevogadosDjango())
    token = tokens.emitir("u1")
    tokens.revogar(token)
    with pytest.raises(TokenInvalido):
        TokenJwt(SEGREDO, RevogadosDjango()).ler(token)  # outra instância, mesmo banco


def test_hasher_do_django_usa_salt():
    h = HasherDjango()
    a, b = h.gerar("cinema123"), h.gerar("cinema123")
    assert a != b and a.startswith("pbkdf2_sha256$")
    assert h.conferir("cinema123", a) and not h.conferir("errada", a)
