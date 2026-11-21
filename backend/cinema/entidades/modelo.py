"""O modelo do Cine Leandro v2: filmes reais, usuário, preferências e avisos.

Regras de negócio que moram aqui (e em nenhum outro lugar):
- o nome tem pelo menos 2 caracteres;
- o e-mail precisa ter um formato válido (a unicidade é garantida pelo caso de uso);
- a senha tem no mínimo 8 caracteres, com pelo menos uma letra e um número;
- só se cria aviso para filme que ainda não foi lançado;
- um aviso é enviado uma única vez.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from enum import Enum

from .erros import DadosInvalidos, FilmeJaLancado

TAMANHO_MINIMO_SENHA = 8
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------- valores


class Tema(str, Enum):
    CLARO = "CLARO"
    ESCURO = "ESCURO"
    ALTO_CONTRASTE = "ALTO_CONTRASTE"


class Idioma(str, Enum):
    PT = "PT"
    EN = "EN"
    ES = "ES"


class TamanhoFonte(str, Enum):
    P = "P"
    M = "M"
    G = "G"


# ---------------------------------------------------------------- filmes


@dataclass(frozen=True)
class Genero:
    id: int
    nome: str


@dataclass(frozen=True)
class Trailer:
    chave: str  # identificador do vídeo no YouTube
    titulo: str
    idioma: str = ""

    @property
    def url_embed(self) -> str:
        return f"https://www.youtube-nocookie.com/embed/{self.chave}"


@dataclass(frozen=True)
class Provedor:
    """Um serviço onde o filme pode ser visto: Netflix, Prime Video, Globoplay..."""

    id: int
    nome: str
    logo_url: str | None = None


@dataclass(frozen=True)
class OndeAssistir:
    """Onde o filme está disponível legalmente numa região (dados da JustWatch, via TMDB).

    O Cine Leandro não exibe o filme: ele mostra onde assistir e leva o usuário até lá.
    """

    regiao: str
    link: str | None = None  # página do filme no TMDB, com os links para cada serviço
    assinatura: tuple[Provedor, ...] = ()  # incluso na assinatura (Netflix, Max...)
    gratis: tuple[Provedor, ...] = ()  # grátis, com ou sem anúncios
    aluguel: tuple[Provedor, ...] = ()
    compra: tuple[Provedor, ...] = ()

    @property
    def disponivel(self) -> bool:
        return bool(self.assinatura or self.gratis or self.aluguel or self.compra)


@dataclass(frozen=True)
class Filme:
    id: str
    titulo: str
    sinopse: str
    data_lancamento: date | None = None
    nota: float = 0.0  # 0 a 10, média do público
    generos: tuple[Genero, ...] = ()
    duracao_min: int | None = None
    classificacao: str = ""
    poster_url: str | None = None
    fundo_url: str | None = None
    origem: str = "local"

    def ja_lancado(self, hoje: date) -> bool:
        """Sem data conhecida, o filme é tratado como já lançado."""
        return self.data_lancamento is None or self.data_lancamento <= hoje

    def dias_para_estreia(self, hoje: date) -> int:
        if self.ja_lancado(hoje):
            return 0
        return (self.data_lancamento - hoje).days  # type: ignore[operator]


# ---------------------------------------------------------------- usuário


@dataclass(frozen=True)
class Preferencias:
    tema: Tema = Tema.ESCURO
    idioma: Idioma = Idioma.PT
    tamanho_fonte: TamanhoFonte = TamanhoFonte.M
    reduzir_animacoes: bool = False


def validar_senha(senha: str) -> None:
    if len(senha) < TAMANHO_MINIMO_SENHA:
        raise DadosInvalidos(f"A senha precisa ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")
    if not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        raise DadosInvalidos("A senha precisa ter pelo menos uma letra e um número.")


def normalizar_email(email: str) -> str:
    email = email.strip().lower()
    if not _EMAIL.match(email):
        raise DadosInvalidos("Informe um e-mail válido.")
    return email


@dataclass
class Usuario:
    id: str
    nome: str
    email: str
    senha_hash: str
    criado_em: datetime
    preferencias: Preferencias = field(default_factory=Preferencias)

    @classmethod
    def criar(
        cls,
        *,
        id: str,
        nome: str,
        email: str,
        senha: str,
        hasher,  # HasherDeSenha (porta): a entidade não sabe qual algoritmo é usado
        agora: datetime,
        preferencias: Preferencias | None = None,
    ) -> Usuario:
        nome = " ".join(nome.split())
        if len(nome) < 2:
            raise DadosInvalidos("Informe seu nome (pelo menos 2 letras).")
        email = normalizar_email(email)
        validar_senha(senha)
        return cls(
            id=id,
            nome=nome,
            email=email,
            senha_hash=hasher.gerar(senha),
            criado_em=agora,
            preferencias=preferencias or Preferencias(),
        )

    def trocar_senha(self, nova_senha: str, hasher) -> None:
        validar_senha(nova_senha)
        self.senha_hash = hasher.gerar(nova_senha)

    def atualizar_preferencias(self, **mudancas) -> None:
        self.preferencias = replace(self.preferencias, **mudancas)


# ---------------------------------------------------------------- avisos


@dataclass
class AvisoDeLancamento:
    id: str
    usuario_id: str
    filme_id: str
    filme_titulo: str
    data_lancamento: date
    criado_em: datetime
    enviado_em: datetime | None = None

    @classmethod
    def criar(cls, *, id: str, usuario_id: str, filme: Filme, agora: datetime) -> AvisoDeLancamento:
        if filme.ja_lancado(agora.date()):
            raise FilmeJaLancado(f"“{filme.titulo}” já foi lançado. Não há estreia para avisar.")
        return cls(
            id=id,
            usuario_id=usuario_id,
            filme_id=filme.id,
            filme_titulo=filme.titulo,
            data_lancamento=filme.data_lancamento,  # type: ignore[arg-type]
            criado_em=agora,
        )

    @property
    def enviado(self) -> bool:
        return self.enviado_em is not None

    def deve_ser_enviado(self, hoje: date) -> bool:
        return not self.enviado and self.data_lancamento <= hoje

    def marcar_enviado(self, agora: datetime) -> None:
        if not self.enviado:
            self.enviado_em = agora
