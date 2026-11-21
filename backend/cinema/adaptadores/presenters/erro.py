"""Traduz erros de negócio em respostas HTTP.

As entidades só dizem "qual regra foi violada" (o `codigo`). Aqui, na borda,
decidimos que isso vira 404, 409, 422...
"""

from __future__ import annotations

from cinema.entidades import ErroDeDominio

STATUS = {
    "nao_encontrado": 404,
    "dados_invalidos": 422,
    "email_ja_cadastrado": 409,
    "credenciais_invalidas": 401,
    "nao_autenticado": 401,
    "token_invalido": 400,
    "filme_ja_lancado": 409,
    "aviso_ja_existe": 409,
    "muitas_tentativas": 429,
}


class ErroPresenter:
    @staticmethod
    def dominio(erro: ErroDeDominio) -> tuple[int, dict]:
        return STATUS.get(erro.codigo, 400), {"erro": erro.codigo, "mensagem": erro.mensagem}

    @staticmethod
    def validacao(detalhes: dict) -> tuple[int, dict]:
        """Erros de formato vindos dos serializers do DRF."""
        campos = {campo: [str(m) for m in (msgs if isinstance(msgs, list) else [msgs])]
                  for campo, msgs in detalhes.items()}
        primeira = next(iter(campos.values()), ["Dados inválidos."])[0]
        return 422, {"erro": "formato_invalido", "mensagem": primeira, "campos": campos}

    @staticmethod
    def muitas_requisicoes(espera: float | None) -> tuple[int, dict]:
        """Limite por endereço IP (DRF throttling) estourado."""
        segundos = int(espera or 60)
        return 429, {"erro": "muitas_tentativas", "espera_segundos": segundos,
                     "mensagem": f"Muitas tentativas seguidas. Espere {segundos} segundos e tente de novo."}

    @staticmethod
    def inesperado() -> tuple[int, dict]:
        return 500, {"erro": "erro_interno", "mensagem": "Algo deu errado do nosso lado. Tente de novo."}
