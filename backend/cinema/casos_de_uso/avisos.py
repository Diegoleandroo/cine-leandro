"""Casos de uso de avisos de lançamento."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from cinema.entidades import AvisoDeLancamento, AvisoJaExiste, Idioma, NaoEncontrado

from .mensagens import email_estreia
from .portas import (
    AvisoRepository,
    CatalogoDeFilmes,
    GeradorDeIds,
    Relogio,
    ServicoDeEmail,
    UsuarioRepository,
)

log = logging.getLogger(__name__)


@dataclass
class AtivarAvisoDeLancamento:
    avisos: AvisoRepository
    catalogo: CatalogoDeFilmes
    ids: GeradorDeIds
    relogio: Relogio

    def executar(self, usuario_id: str, filme_id: str, idioma: Idioma = Idioma.PT) -> AvisoDeLancamento:
        filme = self.catalogo.detalhes(filme_id, idioma)
        if filme is None:
            raise NaoEncontrado("Filme não encontrado.")
        if self.avisos.buscar(usuario_id, filme.id) is not None:
            raise AvisoJaExiste(f"Você já vai ser avisado da estreia de “{filme.titulo}”.")
        aviso = AvisoDeLancamento.criar(
            id=self.ids.novo_id(), usuario_id=usuario_id, filme=filme, agora=self.relogio.agora()
        )
        self.avisos.salvar_novo(aviso)
        return aviso


@dataclass
class ListarMeusAvisos:
    avisos: AvisoRepository

    def executar(self, usuario_id: str) -> list[AvisoDeLancamento]:
        return sorted(self.avisos.listar_do_usuario(usuario_id), key=lambda a: a.data_lancamento)


@dataclass
class CancelarAviso:
    avisos: AvisoRepository

    def executar(self, usuario_id: str, filme_id: str) -> None:
        aviso = self.avisos.buscar(usuario_id, filme_id)
        if aviso is None:
            raise NaoEncontrado("Você não tem aviso para este filme.")
        self.avisos.remover(aviso.id)


@dataclass
class DispararAvisosDeEstreia:
    """Roda uma vez por dia (EventBridge na AWS, ou `manage.py disparar_avisos`)."""

    avisos: AvisoRepository
    usuarios: UsuarioRepository
    email: ServicoDeEmail
    relogio: Relogio

    def executar(self) -> int:
        agora = self.relogio.agora()
        enviados = 0
        for aviso in self.avisos.pendentes_ate(agora.date()):
            if not aviso.deve_ser_enviado(agora.date()):
                continue
            usuario = self.usuarios.buscar_por_id(aviso.usuario_id)
            if usuario is None:
                continue
            assunto, texto = email_estreia(usuario, aviso)
            try:
                self.email.enviar(usuario.email, assunto, texto)
            except Exception:  # um e-mail com problema não derruba os outros
                log.exception("Falha ao avisar %s sobre %s", usuario.email, aviso.filme_titulo)
                continue
            aviso.marcar_enviado(agora)
            self.avisos.atualizar(aviso)
            enviados += 1
        return enviados
