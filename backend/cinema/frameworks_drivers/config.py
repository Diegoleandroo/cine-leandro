"""Configuração lida das variáveis de ambiente (e do arquivo .env, se existir).

Na AWS, essas variáveis vêm da definição do serviço no ECS e do Secrets Manager.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]  # pasta backend/


def carregar_env(arquivo: Path = RAIZ / ".env") -> None:
    """Lê o .env sem sobrescrever variáveis que já existem no ambiente."""
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def _lista(valor: str) -> list[str]:
    return [v.strip() for v in valor.split(",") if v.strip()]


@dataclass(frozen=True)
class Config:
    segredo: str = "dev-inseguro-troque-em-producao"
    debug: bool = True
    hosts: list[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])
    banco_url: str = "postgres://cinema:cinema@localhost:5432/cinema"
    cors: list[str] = field(default_factory=lambda: ["http://localhost:5173"])
    catalogo: str = "auto"  # auto | local | tmdb
    tmdb_token: str = ""
    tmdb_api_key: str = ""
    email: str = "log"  # log | ses
    ses_remetente: str = ""
    aws_regiao: str = "us-east-1"
    url_frontend: str = "http://localhost:5173"
    limite_acesso: str = "20/min"
    proxies: int = 1

    @property
    def tem_tmdb(self) -> bool:
        return bool(self.tmdb_token or self.tmdb_api_key)

    @classmethod
    def do_ambiente(cls) -> Config:
        carregar_env()
        e = os.environ.get
        return cls(
            segredo=e("DJANGO_SECRET_KEY", cls.segredo),
            debug=e("DJANGO_DEBUG", "1") in ("1", "true", "True"),
            hosts=_lista(e("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")),
            banco_url=e("DATABASE_URL", cls.banco_url),
            cors=_lista(e("CORS_ALLOWED_ORIGINS", "http://localhost:5173")),
            limite_acesso=e("LIMITE_ACESSO", "20/min"),
            proxies=int(e("NUM_PROXIES", "1")),
            catalogo=e("CINEMA_CATALOGO", "auto").lower(),
            tmdb_token=e("TMDB_TOKEN", "").strip(),
            tmdb_api_key=e("TMDB_API_KEY", "").strip(),
            email=e("CINEMA_EMAIL", "log").lower(),
            ses_remetente=e("SES_REMETENTE", ""),
            aws_regiao=e("AWS_REGION", "us-east-1"),
            url_frontend=e("URL_FRONTEND", "http://localhost:5173").rstrip("/"),
        )
