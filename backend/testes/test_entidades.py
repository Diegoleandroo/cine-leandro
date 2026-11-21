"""Regras de negócio puras: sem banco, sem Django, sem internet."""

from datetime import date, datetime, timedelta

import pytest

from cinema.entidades import (
    AvisoDeLancamento,
    DadosInvalidos,
    Filme,
    FilmeJaLancado,
    Idioma,
    Preferencias,
    Tema,
    Usuario,
)

from .conftest import AGORA, ESTREIA_PROXIMA, HOJE, HasherFalso


def criar_usuario(**extra):
    dados = dict(id="u1", nome="  Diego   Leandro ", email=" Diego@Exemplo.COM ", senha="cinema123",
                 hasher=HasherFalso(), agora=AGORA)
    dados.update(extra)
    return Usuario.criar(**dados)


def test_usuario_normaliza_nome_e_email_e_nao_guarda_a_senha():
    u = criar_usuario()
    assert u.nome == "Diego Leandro"
    assert u.email == "diego@exemplo.com"
    assert "cinema123" not in u.senha_hash
    assert u.preferencias == Preferencias()


@pytest.mark.parametrize("senha", ["curta1", "somenteletras", "1234567890"])
def test_senha_precisa_de_8_caracteres_com_letra_e_numero(senha):
    with pytest.raises(DadosInvalidos):
        criar_usuario(senha=senha)


@pytest.mark.parametrize("email", ["sem-arroba", "a@b", "x @y.com"])
def test_email_precisa_ser_valido(email):
    with pytest.raises(DadosInvalidos):
        criar_usuario(email=email)


def test_nome_curto_e_recusado():
    with pytest.raises(DadosInvalidos):
        criar_usuario(nome=" A ")


def test_atualizar_preferencias_muda_so_o_que_foi_pedido():
    u = criar_usuario()
    u.atualizar_preferencias(tema=Tema.ALTO_CONTRASTE)
    assert u.preferencias.tema is Tema.ALTO_CONTRASTE
    assert u.preferencias.idioma is Idioma.PT


def test_filme_sabe_se_ja_foi_lancado():
    amanha = Filme("x", "X", "", HOJE + timedelta(days=1))
    assert not amanha.ja_lancado(HOJE)
    assert amanha.dias_para_estreia(HOJE) == 1
    assert Filme("y", "Y", "", HOJE).ja_lancado(HOJE)
    assert Filme("z", "Z", "", None).ja_lancado(HOJE)  # sem data: tratado como lançado


def test_aviso_so_para_filme_que_ainda_nao_estreou():
    aviso = AvisoDeLancamento.criar(id="a1", usuario_id="u1", filme=ESTREIA_PROXIMA, agora=AGORA)
    assert aviso.data_lancamento == ESTREIA_PROXIMA.data_lancamento
    with pytest.raises(FilmeJaLancado):
        AvisoDeLancamento.criar(id="a2", usuario_id="u1", filme=Filme("v", "Velho", "", date(2000, 1, 1)), agora=AGORA)


def test_aviso_e_enviado_uma_unica_vez():
    aviso = AvisoDeLancamento.criar(id="a1", usuario_id="u1", filme=ESTREIA_PROXIMA, agora=AGORA)
    estreia = ESTREIA_PROXIMA.data_lancamento
    assert not aviso.deve_ser_enviado(estreia - timedelta(days=1))
    assert aviso.deve_ser_enviado(estreia)
    aviso.marcar_enviado(datetime(2026, 11, 25, 8, 0))
    primeiro = aviso.enviado_em
    aviso.marcar_enviado(datetime(2026, 11, 26, 8, 0))
    assert aviso.enviado_em == primeiro
    assert not aviso.deve_ser_enviado(estreia + timedelta(days=3))
