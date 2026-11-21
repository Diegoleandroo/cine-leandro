"""Portas: as interfaces que os casos de uso precisam do mundo externo.

Os casos de uso dependem SÓ destas abstrações. Quem as implementa são os
adaptadores (Django ORM + PostgreSQL, memória, TMDB, Amazon SES, JWT...).
É assim que trocamos banco, catálogo ou e-mail sem tocar numa regra de negócio.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

from cinema.entidades import AvisoDeLancamento, Filme, Genero, Idioma, OndeAssistir, Trailer, Usuario

from .dtos import ListaDeFilmes, PaginaDeFilmes

# ----------------------------------------------------------- repositórios


class UsuarioRepository(ABC):
    @abstractmethod
    def salvar_novo(self, usuario: Usuario) -> None:
        """Lança EmailJaCadastrado se o e-mail já existir (mesmo numa corrida)."""

    @abstractmethod
    def atualizar(self, usuario: Usuario) -> None: ...

    @abstractmethod
    def buscar_por_id(self, usuario_id: str) -> Usuario | None: ...

    @abstractmethod
    def buscar_por_email(self, email: str) -> Usuario | None: ...


class AvisoRepository(ABC):
    @abstractmethod
    def salvar_novo(self, aviso: AvisoDeLancamento) -> None:
        """Lança AvisoJaExiste se o usuário já pediu aviso deste filme."""

    @abstractmethod
    def atualizar(self, aviso: AvisoDeLancamento) -> None: ...

    @abstractmethod
    def buscar(self, usuario_id: str, filme_id: str) -> AvisoDeLancamento | None: ...

    @abstractmethod
    def listar_do_usuario(self, usuario_id: str) -> list[AvisoDeLancamento]: ...

    @abstractmethod
    def remover(self, aviso_id: str) -> None: ...

    @abstractmethod
    def pendentes_ate(self, dia: date) -> list[AvisoDeLancamento]:
        """Avisos ainda não enviados de filmes que estreiam até `dia`."""


# ----------------------------------------------------------- gateways


class CatalogoDeFilmes(ABC):
    """De onde vêm os filmes reais (TMDB) ou o plano B (catálogo local)."""

    nome: str = "catálogo"

    @abstractmethod
    def listar(
        self, lista: ListaDeFilmes, idioma: Idioma, pagina: int = 1, genero_id: int | None = None
    ) -> PaginaDeFilmes: ...

    @abstractmethod
    def generos(self, idioma: Idioma) -> list[Genero]: ...

    @abstractmethod
    def detalhes(self, filme_id: str, idioma: Idioma) -> Filme | None: ...

    @abstractmethod
    def trailers(self, filme_id: str, idioma: Idioma) -> list[Trailer]: ...

    @abstractmethod
    def onde_assistir(self, filme_id: str, regiao: str) -> OndeAssistir:
        """Serviços de streaming, aluguel e compra do filme na região (ex.: "BR")."""


# ----------------------------------------------------------- segurança


class HasherDeSenha(ABC):
    """Transforma a senha num hash. O núcleo não sabe se é PBKDF2, bcrypt..."""

    @abstractmethod
    def gerar(self, senha: str) -> str: ...

    @abstractmethod
    def conferir(self, senha: str, senha_hash: str) -> bool: ...


class GeradorDeToken(ABC):
    """Tokens de acesso (login)."""

    @abstractmethod
    def emitir(self, usuario_id: str) -> str: ...

    @abstractmethod
    def ler(self, token: str) -> str:
        """Devolve o id do usuário. Lança TokenInvalido se expirou, foi revogado ou é falso."""

    @abstractmethod
    def revogar(self, token: str) -> None: ...


class TokenDeRecuperacao(ABC):
    """Token de uso único para redefinir a senha (vai no link do e-mail)."""

    @abstractmethod
    def emitir(self, usuario_id: str, carimbo: str) -> str: ...

    @abstractmethod
    def ler(self, token: str) -> tuple[str, str]:
        """Devolve (usuario_id, carimbo). Lança TokenInvalido se expirou ou é falso."""


# ----------------------------------------------------------- serviços


class ServicoDeEmail(ABC):
    @abstractmethod
    def enviar(self, para: str, assunto: str, texto: str) -> None: ...


class Relogio(ABC):
    """Abstrair o relógio deixa os testes controlarem o 'agora'."""

    @abstractmethod
    def agora(self) -> datetime: ...


class GeradorDeIds(ABC):
    @abstractmethod
    def novo_id(self) -> str: ...


class LimiteDeTentativas(ABC):
    """Conta as senhas erradas de cada conta por um tempo (proteção contra força bruta)."""

    @abstractmethod
    def bloqueado(self, chave: str) -> bool: ...

    @abstractmethod
    def registrar_falha(self, chave: str) -> None: ...

    @abstractmethod
    def limpar(self, chave: str) -> None: ...
