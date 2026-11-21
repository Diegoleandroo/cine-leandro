"""Casos de uso de conta: cadastrar, entrar, sair e recuperar a senha."""

from __future__ import annotations

from dataclasses import dataclass

from cinema.entidades import (
    CredenciaisInvalidas,
    MuitasTentativas,
    NaoAutenticado,
    TokenInvalido,
    Usuario,
    normalizar_email,
)

from .dtos import CadastroEntrada, SessaoDeLogin
from .mensagens import email_recuperacao
from .portas import (
    GeradorDeIds,
    GeradorDeToken,
    HasherDeSenha,
    LimiteDeTentativas,
    Relogio,
    ServicoDeEmail,
    TokenDeRecuperacao,
    UsuarioRepository,
)


def _carimbo(usuario: Usuario) -> str:
    """Muda quando a senha muda: o link de recuperação vira lixo depois de usado."""
    return usuario.senha_hash[-16:]


@dataclass
class CadastrarConta:
    usuarios: UsuarioRepository
    hasher: HasherDeSenha
    tokens: GeradorDeToken
    ids: GeradorDeIds
    relogio: Relogio

    def executar(self, entrada: CadastroEntrada) -> SessaoDeLogin:
        usuario = Usuario.criar(
            id=self.ids.novo_id(),
            nome=entrada.nome,
            email=entrada.email,
            senha=entrada.senha,
            hasher=self.hasher,
            agora=self.relogio.agora(),
            preferencias=entrada.preferencias,
        )
        self.usuarios.salvar_novo(usuario)  # garante e-mail único
        return SessaoDeLogin(token=self.tokens.emitir(usuario.id), usuario=usuario)


@dataclass
class FazerLogin:
    usuarios: UsuarioRepository
    hasher: HasherDeSenha
    tokens: GeradorDeToken
    limite: LimiteDeTentativas | None = None

    def executar(self, email: str, senha: str) -> SessaoDeLogin:
        chave = (email or "").strip().lower()
        # Depois de várias senhas erradas, a conta fica bloqueada por um tempo,
        # MESMO com a senha certa: quem testa senhas em massa não descobre qual acertou.
        if self.limite and self.limite.bloqueado(chave):
            raise MuitasTentativas("Muitas tentativas de login. Espere 15 minutos e tente de novo.")
        try:
            usuario = self.usuarios.buscar_por_email(normalizar_email(email))
        except Exception:  # e-mail mal formatado: mesma resposta, sem dar pistas
            usuario = None
        if usuario is None or not self.hasher.conferir(senha, usuario.senha_hash):
            if self.limite:
                self.limite.registrar_falha(chave)
            raise CredenciaisInvalidas("E-mail ou senha incorretos.")
        if self.limite:
            self.limite.limpar(chave)
        return SessaoDeLogin(token=self.tokens.emitir(usuario.id), usuario=usuario)


@dataclass
class FazerLogout:
    tokens: GeradorDeToken

    def executar(self, token: str) -> None:
        self.tokens.revogar(token)


@dataclass
class AutenticarUsuario:
    """Descobre quem é o dono do token. Usado pelos controllers das rotas privadas."""

    usuarios: UsuarioRepository
    tokens: GeradorDeToken

    def executar(self, token: str | None) -> Usuario:
        if not token:
            raise NaoAutenticado("Entre na sua conta para continuar.")
        try:
            usuario_id = self.tokens.ler(token)
        except TokenInvalido as erro:
            raise NaoAutenticado("Sua sessão expirou. Entre novamente.") from erro
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NaoAutenticado("Conta não encontrada. Entre novamente.")
        return usuario


@dataclass
class SolicitarRecuperacaoDeSenha:
    usuarios: UsuarioRepository
    tokens: TokenDeRecuperacao
    email: ServicoDeEmail

    def executar(self, email: str, url_redefinir: str) -> None:
        """Sempre "dá certo" para quem pede: não revelamos se o e-mail existe."""
        try:
            usuario = self.usuarios.buscar_por_email(normalizar_email(email))
        except Exception:
            return
        if usuario is None:
            return
        token = self.tokens.emitir(usuario.id, _carimbo(usuario))
        assunto, texto = email_recuperacao(usuario, f"{url_redefinir}?token={token}")
        self.email.enviar(usuario.email, assunto, texto)


@dataclass
class RedefinirSenha:
    usuarios: UsuarioRepository
    tokens: TokenDeRecuperacao
    hasher: HasherDeSenha

    def executar(self, token: str, nova_senha: str) -> None:
        usuario_id, carimbo = self.tokens.ler(token)
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None or _carimbo(usuario) != carimbo:
            raise TokenInvalido("Este link já foi usado ou expirou. Peça um novo.")
        usuario.trocar_senha(nova_senha, self.hasher)
        self.usuarios.atualizar(usuario)
