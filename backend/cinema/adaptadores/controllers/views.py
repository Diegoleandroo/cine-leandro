"""Controllers (views do Django REST Framework).

Cada controller faz só três coisas:
1. valida o FORMATO da entrada (serializer);
2. chama o caso de uso;
3. entrega o resultado ao Presenter, que monta o ViewModel (JSON).
Nenhuma regra de negócio mora aqui.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cinema.adaptadores.presenters import (
    AvisoPresenter,
    FilmePresenter,
    GeneroPresenter,
    OndeAssistirPresenter,
    PaginaPresenter,
    PreferenciasPresenter,
    TrailerPresenter,
    UsuarioPresenter,
    VitrinePresenter,
)
from cinema.casos_de_uso import CadastroEntrada as CadastroDTO
from cinema.casos_de_uso import ListaDeFilmes
from cinema.entidades import Idioma, Preferencias, TamanhoFonte, Tema

from . import esquemas
from .base import LimitePorIp, casos, hoje, idioma_da_requisicao, token_da_requisicao, usuario_logado


class ExigeLogin(APIView):
    """Base dos controllers que só funcionam com o usuário logado.

    O DRF chama initial() antes de qualquer get/post/put/delete: sem um token
    válido, o caso de uso AutenticarUsuario lança NaoAutenticado e a resposta é 401.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        request.usuario = usuario_logado(request)


def _validar(serializer_cls, dados) -> dict:
    s = serializer_cls(data=dados)
    s.is_valid(raise_exception=True)
    return s.validated_data


# ======================================================== AuthController


class Acesso(APIView):
    """Base das rotas de acesso: limite de pedidos por IP (contra robôs)."""

    throttle_classes = [LimitePorIp]
    throttle_scope = "acesso"


class CadastroView(Acesso):
    def post(self, request):
        d = _validar(esquemas.CadastroEntrada, request.data)
        prefs = None
        if d.get("preferencias"):
            p = d["preferencias"]
            prefs = Preferencias(
                tema=Tema(p.get("tema", "ESCURO")),
                idioma=Idioma(p.get("idioma", "PT")),
                tamanho_fonte=TamanhoFonte(p.get("tamanho_fonte", "M")),
                reduzir_animacoes=p.get("reduzir_animacoes", False),
            )
        sessao = casos().cadastrar.executar(CadastroDTO(d["nome"], d["email"], d["senha"], prefs))
        return Response(UsuarioPresenter.sessao(sessao), status=status.HTTP_201_CREATED)


class LoginView(Acesso):
    def post(self, request):
        d = _validar(esquemas.LoginEntrada, request.data)
        return Response(UsuarioPresenter.sessao(casos().login.executar(d["email"], d["senha"])))


class LogoutView(APIView):
    def post(self, request):
        token = token_da_requisicao(request)
        if token:
            casos().logout.executar(token)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EuView(APIView):
    def get(self, request):
        return Response(UsuarioPresenter.apresentar(usuario_logado(request)))


class RecuperarSenhaView(Acesso):
    def post(self, request):
        d = _validar(esquemas.RecuperarSenhaEntrada, request.data)
        casos().solicitar_recuperacao.executar(d["email"], casos().url_redefinir_senha)
        return Response({"mensagem": "Se houver uma conta com este e-mail, enviamos um link para redefinir a senha."})


class RedefinirSenhaView(Acesso):
    def post(self, request):
        d = _validar(esquemas.RedefinirSenhaEntrada, request.data)
        casos().redefinir_senha.executar(d["token"], d["nova_senha"])
        return Response({"mensagem": "Senha alterada. Você já pode entrar com a nova senha."})


# ======================================================== FilmesController


class FilmesView(ExigeLogin):
    def get(self, request):
        d = _validar(esquemas.ListaEntrada, request.query_params)
        idioma, pagina, lista = idioma_da_requisicao(request), d["pagina"], ListaDeFilmes(d["lista"])
        if d.get("genero"):
            resultado = casos().filtrar.executar(d["genero"], lista, idioma, pagina)
        else:
            uso = {
                ListaDeFilmes.EM_CARTAZ: casos().em_cartaz,
                ListaDeFilmes.POPULARES: casos().populares,
                ListaDeFilmes.MAIS_BEM_AVALIADOS: casos().mais_bem_avaliados,
            }[lista]
            resultado = uso.executar(idioma, pagina)
        return Response(PaginaPresenter.apresentar(resultado, hoje()))


class LancamentosView(ExigeLogin):
    def get(self, request):
        d = _validar(esquemas.ListaEntrada, request.query_params)
        resultado = casos().lancamentos.executar(idioma_da_requisicao(request), d["pagina"], d.get("genero"))
        return Response(PaginaPresenter.apresentar(resultado, hoje()))


class GenerosView(ExigeLogin):
    def get(self, request):
        return Response(GeneroPresenter.lista(casos().generos.executar(idioma_da_requisicao(request))))


class FilmeView(ExigeLogin):
    def get(self, request, filme_id: str):
        filme = casos().detalhar.executar(filme_id, idioma_da_requisicao(request))
        return Response(FilmePresenter.apresentar(filme, hoje()))


class TrailerView(ExigeLogin):
    def get(self, request, filme_id: str):
        return Response(TrailerPresenter.apresentar(casos().trailer.executar(filme_id, idioma_da_requisicao(request))))


class OndeAssistirView(ExigeLogin):
    def get(self, request, filme_id: str):
        regiao = (request.query_params.get("regiao") or "BR")[:2]
        return Response(OndeAssistirPresenter.apresentar(casos().onde_assistir.executar(filme_id, regiao)))


# ======================================================== PreferenciasController


class PreferenciasView(ExigeLogin):
    def get(self, request):
        usuario = request.usuario
        return Response(PreferenciasPresenter.apresentar(casos().obter_preferencias.executar(usuario.id)))

    def put(self, request):
        usuario = request.usuario
        d = _validar(esquemas.PreferenciasEntrada, request.data)
        prefs = casos().atualizar_preferencias.executar(usuario.id, **d)
        return Response(PreferenciasPresenter.apresentar(prefs))

    patch = put


# ======================================================== AvisosController


class AvisosView(ExigeLogin):
    def get(self, request):
        usuario = request.usuario
        return Response(AvisoPresenter.lista(casos().meus_avisos.executar(usuario.id), hoje()))

    def post(self, request):
        usuario = request.usuario
        d = _validar(esquemas.AvisoEntrada, request.data)
        aviso = casos().ativar_aviso.executar(usuario.id, d["filme_id"], usuario.preferencias.idioma)
        return Response(AvisoPresenter.apresentar(aviso, hoje()), status=status.HTTP_201_CREATED)


class AvisoView(ExigeLogin):
    def delete(self, request, filme_id: str):
        usuario = request.usuario
        casos().cancelar_aviso.executar(usuario.id, filme_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ======================================================== vitrine (pública)


class VitrineView(APIView):
    """Pôsteres dos próximos lançamentos para a tela de Entrar.

    É a única rota de filmes SEM login, e por isso usa um Presenter que devolve
    só o necessário para desenhar a vitrine.
    """

    def get(self, request):
        pagina = casos().lancamentos.executar(idioma_da_requisicao(request), 1)
        return Response(VitrinePresenter.apresentar(pagina))


# ======================================================== sistema


class SistemaView(APIView):
    def get(self, request):
        return Response(casos().descrever_sistema())
