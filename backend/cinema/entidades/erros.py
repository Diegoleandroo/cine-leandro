"""Erros de negócio. Cada um descreve uma regra do Cine Leandro que foi violada.

Não existe nenhum código HTTP aqui (404, 409...). Quem decide como o erro
aparece para o usuário é o ErroPresenter, na camada de adaptadores.
"""


class ErroDeDominio(Exception):
    """Uma regra de negócio foi violada."""

    codigo = "regra_violada"

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


class NaoEncontrado(ErroDeDominio):
    codigo = "nao_encontrado"


class DadosInvalidos(ErroDeDominio):
    codigo = "dados_invalidos"


class EmailJaCadastrado(ErroDeDominio):
    codigo = "email_ja_cadastrado"


class CredenciaisInvalidas(ErroDeDominio):
    codigo = "credenciais_invalidas"


class NaoAutenticado(ErroDeDominio):
    codigo = "nao_autenticado"


class TokenInvalido(ErroDeDominio):
    codigo = "token_invalido"


class FilmeJaLancado(ErroDeDominio):
    codigo = "filme_ja_lancado"


class AvisoJaExiste(ErroDeDominio):
    codigo = "aviso_ja_existe"


class MuitasTentativas(ErroDeDominio):
    """Proteção contra força bruta: muitas senhas erradas seguidas para a mesma conta."""

    codigo = "muitas_tentativas"
