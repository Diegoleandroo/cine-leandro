"""Casos de uso com dublês em memória: rápidos e sem infraestrutura."""

from datetime import timedelta

import pytest

from cinema import casos_de_uso as uc
from cinema.casos_de_uso import CadastroEntrada, ListaDeFilmes
from cinema.entidades import (
    AvisoJaExiste,
    CredenciaisInvalidas,
    DadosInvalidos,
    EmailJaCadastrado,
    FilmeJaLancado,
    Idioma,
    NaoAutenticado,
    NaoEncontrado,
    Preferencias,
    Tema,
    TokenInvalido,
)

from .conftest import ESTREIA_DISTANTE, ESTREIA_PROXIMA, FICCAO


def cadastrar(p, email="diego@exemplo.com", senha="cinema123", prefs=None):
    return uc.CadastrarConta(p.usuarios, p.hasher, p.tokens, p.ids, p.relogio).executar(
        CadastroEntrada("Diego Leandro", email, senha, prefs)
    )


# ------------------------------------------------------------------- conta


def test_cadastro_ja_entra_logado_e_guarda_as_preferencias_do_visitante(pecas):
    sessao = cadastrar(pecas, prefs=Preferencias(tema=Tema.CLARO, idioma=Idioma.EN))
    autenticado = uc.AutenticarUsuario(pecas.usuarios, pecas.tokens).executar(sessao.token)
    assert autenticado.email == "diego@exemplo.com"
    assert autenticado.preferencias.idioma is Idioma.EN


def test_email_nao_pode_repetir_nem_mudando_maiusculas(pecas):
    cadastrar(pecas)
    with pytest.raises(EmailJaCadastrado):
        cadastrar(pecas, email="DIEGO@exemplo.com ")


def test_login_com_senha_errada_ou_email_inexistente_da_a_mesma_resposta(pecas):
    cadastrar(pecas)
    login = uc.FazerLogin(pecas.usuarios, pecas.hasher, pecas.tokens)
    assert login.executar("diego@exemplo.com", "cinema123").usuario.nome == "Diego Leandro"
    for email, senha in [("diego@exemplo.com", "errada123"), ("ninguem@exemplo.com", "cinema123"), ("lixo", "x")]:
        with pytest.raises(CredenciaisInvalidas):
            login.executar(email, senha)


def test_logout_invalida_o_token(pecas):
    token = cadastrar(pecas).token
    autenticar = uc.AutenticarUsuario(pecas.usuarios, pecas.tokens)
    autenticar.executar(token)
    uc.FazerLogout(pecas.tokens).executar(token)
    with pytest.raises(NaoAutenticado):
        autenticar.executar(token)
    with pytest.raises(NaoAutenticado):
        autenticar.executar(None)


def test_recuperar_senha_manda_link_de_uso_unico(pecas):
    cadastrar(pecas)
    uc.SolicitarRecuperacaoDeSenha(pecas.usuarios, pecas.recuperacao, pecas.email).executar(
        "diego@exemplo.com", "http://site/redefinir-senha")
    para, assunto, texto = pecas.email.enviados[-1]
    assert para == "diego@exemplo.com" and "Redefina" in assunto
    token = texto.split("token=")[1].split()[0]

    redefinir = uc.RedefinirSenha(pecas.usuarios, pecas.recuperacao, pecas.hasher)
    redefinir.executar(token, "novaSenha9")
    uc.FazerLogin(pecas.usuarios, pecas.hasher, pecas.tokens).executar("diego@exemplo.com", "novaSenha9")
    with pytest.raises(TokenInvalido):  # o mesmo link não serve de novo
        redefinir.executar(token, "outraSenha9")


def test_recuperar_senha_de_email_desconhecido_nao_denuncia_nada(pecas):
    uc.SolicitarRecuperacaoDeSenha(pecas.usuarios, pecas.recuperacao, pecas.email).executar(
        "ninguem@exemplo.com", "http://site/redefinir-senha")
    assert pecas.email.enviados == []


# ------------------------------------------------------------------- preferências


def test_atualizar_preferencias_valida_os_valores(pecas):
    usuario = cadastrar(pecas).usuario
    atualizar = uc.AtualizarPreferencias(pecas.usuarios)
    prefs = atualizar.executar(usuario.id, tema="ALTO_CONTRASTE", tamanho_fonte="G", reduzir_animacoes=True)
    assert prefs.tema is Tema.ALTO_CONTRASTE and prefs.reduzir_animacoes
    assert uc.ObterPreferencias(pecas.usuarios).executar(usuario.id) == prefs
    with pytest.raises(DadosInvalidos):
        atualizar.executar(usuario.id, idioma="FR")


# ------------------------------------------------------------------- filmes


def test_lancamentos_so_traz_o_que_nao_estreou_do_mais_proximo_ao_mais_distante(pecas):
    pagina = uc.ListarLancamentos(pecas.catalogo, pecas.relogio).executar(Idioma.PT)
    assert [f.id for f in pagina.filmes] == [ESTREIA_PROXIMA.id, ESTREIA_DISTANTE.id]


def test_filtrar_por_categoria(pecas):
    pagina = uc.FiltrarPorCategoria(pecas.catalogo).executar(FICCAO.id, ListaDeFilmes.POPULARES)
    assert {f.id for f in pagina.filmes} == {"tmdb-1", "tmdb-3"}


def test_generos_em_ordem_alfabetica_no_idioma_pedido(pecas):
    assert [g.nome for g in uc.ListarGeneros(pecas.catalogo).executar(Idioma.EN)] == ["Drama", "Science Fiction"]


def test_detalhar_filme_inexistente(pecas):
    with pytest.raises(NaoEncontrado):
        uc.DetalharFilme(pecas.catalogo).executar("tmdb-999")


def test_trailer_prefere_o_idioma_do_usuario(pecas):
    obter = uc.ObterTrailer(pecas.catalogo)
    assert obter.executar("tmdb-1", Idioma.PT).chave == "abcPT"
    assert obter.executar("tmdb-1", Idioma.ES).chave == "abcEN"  # sem espanhol: o primeiro que houver
    assert obter.executar("tmdb-2", Idioma.PT) is None


# ------------------------------------------------------------------- avisos


def test_ativar_listar_e_cancelar_aviso(pecas):
    usuario = cadastrar(pecas).usuario
    ativar = uc.AtivarAvisoDeLancamento(pecas.avisos, pecas.catalogo, pecas.ids, pecas.relogio)
    ativar.executar(usuario.id, ESTREIA_DISTANTE.id)
    ativar.executar(usuario.id, ESTREIA_PROXIMA.id)
    with pytest.raises(AvisoJaExiste):
        ativar.executar(usuario.id, ESTREIA_PROXIMA.id)
    with pytest.raises(FilmeJaLancado):
        ativar.executar(usuario.id, "tmdb-1")

    meus = uc.ListarMeusAvisos(pecas.avisos).executar(usuario.id)
    assert [a.filme_id for a in meus] == [ESTREIA_PROXIMA.id, ESTREIA_DISTANTE.id]

    uc.CancelarAviso(pecas.avisos).executar(usuario.id, ESTREIA_DISTANTE.id)
    assert len(uc.ListarMeusAvisos(pecas.avisos).executar(usuario.id)) == 1
    with pytest.raises(NaoEncontrado):
        uc.CancelarAviso(pecas.avisos).executar(usuario.id, ESTREIA_DISTANTE.id)


def test_disparar_avisos_manda_no_dia_da_estreia_e_uma_vez_so(pecas):
    usuario = cadastrar(pecas, prefs=Preferencias(idioma=Idioma.ES)).usuario
    uc.AtivarAvisoDeLancamento(pecas.avisos, pecas.catalogo, pecas.ids, pecas.relogio).executar(
        usuario.id, ESTREIA_PROXIMA.id)
    disparar = uc.DispararAvisosDeEstreia(pecas.avisos, pecas.usuarios, pecas.email, pecas.relogio)

    assert disparar.executar() == 0  # ainda faltam 10 dias
    pecas.relogio.avancar(days=10)
    assert disparar.executar() == 1
    para, assunto, _ = pecas.email.enviados[-1]
    assert para == usuario.email and "ya se estrenó" in assunto  # no idioma do usuário
    pecas.relogio.avancar(days=1)
    assert disparar.executar() == 0  # não repete


def test_falha_num_email_nao_impede_os_outros(pecas):
    class EmailInstavel:
        def __init__(self):
            self.enviados = []

        def enviar(self, para, assunto, texto):
            if para.startswith("falha"):
                raise ConnectionError("SES fora do ar")
            self.enviados.append(para)

    email = EmailInstavel()
    ativar = uc.AtivarAvisoDeLancamento(pecas.avisos, pecas.catalogo, pecas.ids, pecas.relogio)
    for endereco in ["falha@exemplo.com", "ok@exemplo.com"]:
        ativar.executar(cadastrar(pecas, email=endereco).usuario.id, ESTREIA_PROXIMA.id)
    pecas.relogio.avancar(days=10)
    disparar = uc.DispararAvisosDeEstreia(pecas.avisos, pecas.usuarios, email, pecas.relogio)
    assert disparar.executar() == 1
    assert email.enviados == ["ok@exemplo.com"]
    assert len(pecas.avisos.pendentes_ate(pecas.relogio.agora().date() + timedelta(days=1))) == 1  # tenta amanhã


def test_onde_assistir_sem_repeticao_e_filme_inexistente(pecas):
    onde = uc.ObterOndeAssistir(pecas.catalogo).executar("tmdb-1", "br")
    assert onde.disponivel and onde.regiao == "BR"
    assert [p.nome for p in onde.assinatura] == ["Netflix"]  # o catálogo mandou repetido
    assert [p.nome for p in onde.aluguel] == ["Prime Video"]
    assert not uc.ObterOndeAssistir(pecas.catalogo).executar("tmdb-2").disponivel
    with pytest.raises(NaoEncontrado):
        uc.ObterOndeAssistir(pecas.catalogo).executar("tmdb-999")


# ------------------------------------------------ limite de tentativas (força bruta)


def _login_com_limite(pecas):
    from cinema.adaptadores.seguranca.limite_tentativas import LimiteNoCache

    from .conftest import CacheDeDicionario

    uc.CadastrarConta(pecas.usuarios, pecas.hasher, pecas.tokens, pecas.ids, pecas.relogio).executar(
        uc.CadastroEntrada("Diego Leandro", "diego@exemplo.com", "cinema123"))
    cache = CacheDeDicionario()
    return uc.FazerLogin(pecas.usuarios, pecas.hasher, pecas.tokens, LimiteNoCache(cache, maximo=5)), cache


def test_cinco_senhas_erradas_bloqueiam_a_conta_mesmo_com_a_senha_certa(pecas):
    from cinema.entidades import CredenciaisInvalidas, MuitasTentativas

    login, _ = _login_com_limite(pecas)
    for _ in range(5):
        with pytest.raises(CredenciaisInvalidas):
            login.executar("diego@exemplo.com", "errada000")
    with pytest.raises(MuitasTentativas):
        login.executar("Diego@Exemplo.com ", "cinema123")  # mesma conta, escrita diferente


def test_login_certo_zera_a_contagem_e_o_email_nao_fica_guardado(pecas):
    from cinema.entidades import CredenciaisInvalidas

    login, cache = _login_com_limite(pecas)
    for _ in range(4):
        with pytest.raises(CredenciaisInvalidas):
            login.executar("diego@exemplo.com", "errada000")
    assert all("diego" not in chave for chave in cache.dados)
    login.executar("diego@exemplo.com", "cinema123")
    assert cache.dados == {}
    for _ in range(4):  # depois de acertar, tem as 5 chances de novo
        with pytest.raises(CredenciaisInvalidas):
            login.executar("diego@exemplo.com", "errada000")
    assert login.executar("diego@exemplo.com", "cinema123").usuario.nome == "Diego Leandro"
