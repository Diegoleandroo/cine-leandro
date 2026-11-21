"""Adaptadores de e-mail.

- EmailPorLog: para desenvolvimento e testes; escreve o e-mail no log.
- EmailSes: envia de verdade pelo Amazon SES (API v2, via boto3).
"""

from __future__ import annotations

import logging

from cinema.casos_de_uso.portas import ServicoDeEmail

log = logging.getLogger("cinema.email")


class EmailPorLog(ServicoDeEmail):
    def __init__(self) -> None:
        self.enviados: list[tuple[str, str, str]] = []

    def enviar(self, para: str, assunto: str, texto: str) -> None:
        self.enviados.append((para, assunto, texto))
        log.info("✉️  Para: %s | Assunto: %s\n%s", para, assunto, texto)


class EmailSes(ServicoDeEmail):
    """Precisa de um remetente verificado no SES e de permissão ses:SendEmail."""

    def __init__(self, remetente: str, regiao: str, cliente=None) -> None:
        if cliente is None:
            import boto3  # só importa o SDK da AWS quando o SES é usado

            cliente = boto3.client("sesv2", region_name=regiao)
        self._cliente = cliente
        self._remetente = remetente

    def enviar(self, para: str, assunto: str, texto: str) -> None:
        self._cliente.send_email(
            FromEmailAddress=self._remetente,
            Destination={"ToAddresses": [para]},
            Content={
                "Simple": {
                    "Subject": {"Data": assunto, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": texto, "Charset": "UTF-8"}},
                }
            },
        )
