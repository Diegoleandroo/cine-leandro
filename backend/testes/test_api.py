"""A API de ponta a ponta: HTTP → Controller → Caso de uso → PostgreSQL → Presenter."""

import pytest
from rest_framework.test import APIClient

from cinema.adaptadores.controllers.base import configurar
from cinema.adaptadores.email.servicos import EmailPorLog
from cinema.frameworks_drivers.config import Config
from cinema.frameworks_drivers.container import Container

from .conftest import ESTREIA_PROXIMA, CatalogoFalso, RelogioFixo


class CacheDesligado:
    def get(self, chave, padrao=None):
        return padrao

    def set(self, *a):
        pass


@pytest.fixture
def api(db):
    container = Container(Config(segredo="segredo-de-teste-com-32-caracteres!"), catalogo=CatalogoFalso(),
                          email=EmailPorLog(), relogio=RelogioFixo(), cache=CacheDesligado())
    configurar(container.casos_de_uso())
    cliente = APIClient()
    cliente.container = container
    return cliente


def entrar(api, email="diego@exemplo.com"):
    r = api.post("/api/auth/cadastro", {"nome": "Diego Leandro", "email": email, "senha": "cinema123",
                                        "preferencias": {"idioma": "EN"}}, format="json")
    assert r.status_code == 201, r.json()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['token']}")
    return r.json()


def test_cadastro_login_eu_e_logout(api):
    corpo = entrar(api)
    assert "senha_hash" not in corpo["usuario"]  # o Presenter nunca expõe o hash
    assert corpo["usuario"]["preferencias"]["idioma"] == "EN"
    assert api.get("/api/auth/eu").json()["primeiro_nome"] == "Diego"
    assert api.post("/api/auth/logout").status_code == 204
    assert api.get("/api/auth/eu").status_code == 401

    api.credentials()
    r = api.post("/api/auth/login", {"email": "DIEGO@exemplo.com", "senha": "cinema123"}, format="json")
    assert r.status_code == 200 and r.json()["token"]
    assert api.post("/api/auth/login", {"email": "diego@exemplo.com", "senha": "errada999"}, format="json").status_code == 401


def test_erros_de_formato_e_de_regra_tem_status_diferentes(api):
    r = api.post("/api/auth/cadastro", {"nome": "Diego"}, format="json")
    assert r.status_code == 422 and r.json()["erro"] == "formato_invalido" and "email" in r.json()["campos"]
    r = api.post("/api/auth/cadastro", {"nome": "Diego", "email": "d@e.com", "senha": "curta"}, format="json")
    assert r.status_code == 422 and r.json()["erro"] == "dados_invalidos"
    entrar(api)
    r = api.post("/api/auth/cadastro", {"nome": "Outro", "email": "diego@exemplo.com", "senha": "cinema123"}, format="json")
    assert r.status_code == 409


def test_filmes_exigem_login(api):
    for rota in ["/api/filmes", "/api/filmes/lancamentos", "/api/filmes/generos", "/api/filmes/tmdb-1",
                 "/api/filmes/tmdb-1/trailer", "/api/filmes/tmdb-1/onde-assistir"]:
        r = api.get(rota)
        assert r.status_code == 401 and r.json()["erro"] == "nao_autenticado", rota
    api.credentials(HTTP_AUTHORIZATION="Bearer token-falso")
    assert api.get("/api/filmes").status_code == 401
    # telas públicas continuam abertas
    api.credentials()
    assert api.get("/api/sistema").status_code == 200
    assert api.post("/api/auth/login", {"email": "x@y.com", "senha": "errada123"}, format="json").status_code == 401


def test_onde_assistir(api):
    entrar(api)
    r = api.get("/api/filmes/tmdb-1/onde-assistir").json()
    assert r["disponivel"] and r["fonte"] == "JustWatch"
    assert [g["tipo"] for g in r["grupos"]] == ["ASSINATURA", "ALUGUEL", "COMPRA"]
    assert r["grupos"][0]["provedores"] == [{"id": 8, "nome": "Netflix", "logo_url": "https://img/netflix.png"}]
    assert api.get("/api/filmes/tmdb-2/onde-assistir").json() == {
        "regiao": "BR", "disponivel": False, "link": None, "grupos": [], "fonte": "JustWatch"}
    assert api.get("/api/filmes/tmdb-404/onde-assistir").status_code == 404


def test_filmes_listas_generos_detalhe_e_trailer(api):
    entrar(api)
    r = api.get("/api/filmes?lista=POPULARES")
    assert r.status_code == 200 and len(r.json()["filmes"]) == 3
    assert api.get("/api/filmes?genero=878").json()["filmes"][0]["generos"][0]["id"] == 878
    lancamentos = api.get("/api/filmes/lancamentos").json()["filmes"]
    assert lancamentos[0]["id"] == ESTREIA_PROXIMA.id and lancamentos[0]["dias_para_estreia"] == 10
    assert api.get("/api/filmes/generos?idioma=EN").json()[1]["nome"] == "Science Fiction"
    assert api.get("/api/filmes/tmdb-1").json()["ja_lancado"] is True
    assert api.get("/api/filmes/tmdb-404").status_code == 404
    trailer = api.get("/api/filmes/tmdb-1/trailer").json()
    assert trailer["disponivel"] and "youtube-nocookie.com/embed/abcPT" in trailer["trailer"]["url_embed"]
    assert api.get("/api/filmes?pagina=0").status_code == 422


def test_preferencias_exigem_login(api):
    assert api.get("/api/preferencias").status_code == 401
    entrar(api)
    r = api.put("/api/preferencias", {"tema": "ALTO_CONTRASTE", "reduzir_animacoes": True}, format="json")
    assert r.json() == {"tema": "ALTO_CONTRASTE", "idioma": "EN", "tamanho_fonte": "M", "reduzir_animacoes": True}
    assert api.put("/api/preferencias", {"tema": "ROSA"}, format="json").status_code == 422


def test_avisos_de_lancamento_e_disparo(api):
    assert api.post("/api/avisos", {"filme_id": ESTREIA_PROXIMA.id}, format="json").status_code == 401
    entrar(api)
    r = api.post("/api/avisos", {"filme_id": ESTREIA_PROXIMA.id}, format="json")
    assert r.status_code == 201 and r.json()["dias_para_estreia"] == 10
    assert api.post("/api/avisos", {"filme_id": ESTREIA_PROXIMA.id}, format="json").status_code == 409
    assert api.post("/api/avisos", {"filme_id": "tmdb-1"}, format="json").status_code == 409  # já lançado
    assert api.post("/api/avisos", {"filme_id": "<script>"}, format="json").status_code == 422
    assert len(api.get("/api/avisos").json()) == 1

    container = api.container
    container.relogio.avancar(days=10)
    assert container.disparar_avisos().executar() == 1
    para, assunto, _ = container.email.enviados[-1]
    assert para == "diego@exemplo.com" and "out now" in assunto  # o usuário escolheu inglês
    assert api.get("/api/avisos").json()[0]["enviado"] is True

    assert api.delete(f"/api/avisos/{ESTREIA_PROXIMA.id}").status_code == 204
    assert api.delete(f"/api/avisos/{ESTREIA_PROXIMA.id}").status_code == 404


def test_recuperacao_de_senha_pela_api(api):
    entrar(api)
    api.credentials()
    r = api.post("/api/auth/recuperar-senha", {"email": "diego@exemplo.com"}, format="json")
    assert r.status_code == 200
    texto = api.container.email.enviados[-1][2]
    token = texto.split("token=")[1].split()[0]
    assert "/redefinir-senha?token=" in texto
    assert api.post("/api/auth/redefinir-senha", {"token": token, "nova_senha": "novaSenha1"}, format="json").status_code == 200
    assert api.post("/api/auth/login", {"email": "diego@exemplo.com", "senha": "novaSenha1"}, format="json").status_code == 200
    assert api.post("/api/auth/redefinir-senha", {"token": token, "nova_senha": "outra1234"}, format="json").status_code == 400


def test_saude_e_sistema(api):
    assert api.get("/api/saude").json() == {"status": "ok"}
    # o load balancer da AWS chama com o IP interno como Host: precisa passar
    assert api.get("/api/saude", HTTP_HOST="10.0.3.17").status_code == 200
    assert api.get("/api/sistema", HTTP_HOST="10.0.3.17").status_code == 400  # o resto continua protegido
    camadas = api.get("/api/sistema").json()["camadas"]
    assert [c["nome"] for c in camadas] == ["Entities", "Use Cases", "Interface Adapters", "Frameworks & Drivers"]


def test_vitrine_e_publica_e_mostra_so_o_minimo(api):
    r = api.get("/api/vitrine")  # sem login
    assert r.status_code == 200
    filmes = r.json()["filmes"]
    # só lançamentos COM pôster (o tmdb-3 não tem pôster; o tmdb-1 já foi lançado)
    assert filmes == [{"titulo": "Estreia Próxima", "poster_url": "https://image.tmdb.org/t/p/w500/estreia.jpg",
                       "data_lancamento": ESTREIA_PROXIMA.data_lancamento.isoformat()}]


# ------------------------------------------------ proteção contra força bruta


def test_login_bloqueia_a_conta_depois_de_5_senhas_erradas(api):
    entrar(api)
    api.credentials()
    for _ in range(5):
        r = api.post("/api/auth/login", {"email": "diego@exemplo.com", "senha": "errada000"}, format="json")
        assert r.status_code == 401
    r = api.post("/api/auth/login", {"email": "diego@exemplo.com", "senha": "cinema123"}, format="json")
    assert r.status_code == 429
    assert r.json()["erro"] == "muitas_tentativas"


def test_mesmo_ip_tem_limite_de_pedidos_por_minuto(api):
    for i in range(20):  # e-mails diferentes: aqui o que conta é o IP
        r = api.post("/api/auth/login", {"email": f"robo{i}@exemplo.com", "senha": "x1234567"}, format="json")
        assert r.status_code == 401
    r = api.post("/api/auth/login", {"email": "robo99@exemplo.com", "senha": "x1234567"}, format="json")
    assert r.status_code == 429
    assert r.json()["erro"] == "muitas_tentativas"
    assert int(r["Retry-After"]) > 0
    # outro IP (atrás do nginx, vem no X-Forwarded-For) não é afetado
    r = api.post("/api/auth/login", {"email": "diego@exemplo.com", "senha": "x1234567"}, format="json",
                 HTTP_X_FORWARDED_FOR="203.0.113.7")
    assert r.status_code == 401


def test_api_manda_cabecalhos_de_seguranca(api):
    r = api.get("/api/vitrine")
    assert r["X-Content-Type-Options"] == "nosniff"
    assert r["X-Frame-Options"] == "DENY"
