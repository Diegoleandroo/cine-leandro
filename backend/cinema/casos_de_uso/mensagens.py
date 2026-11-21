"""Textos dos e-mails, no idioma escolhido pelo usuário."""

from __future__ import annotations

from cinema.entidades import AvisoDeLancamento, Idioma, Usuario


def _data(aviso: AvisoDeLancamento, idioma: Idioma) -> str:
    d = aviso.data_lancamento
    return d.strftime("%m/%d/%Y") if idioma is Idioma.EN else d.strftime("%d/%m/%Y")


def email_estreia(usuario: Usuario, aviso: AvisoDeLancamento) -> tuple[str, str]:
    idioma = usuario.preferencias.idioma
    primeiro_nome = usuario.nome.split()[0]
    t, d = aviso.filme_titulo, _data(aviso, idioma)
    if idioma is Idioma.EN:
        return (
            f"🎬 {t} is out now!",
            f"Hi {primeiro_nome},\n\n“{t}” was released on {d}. You asked us to let you know.\n\n— Cine Leandro",
        )
    if idioma is Idioma.ES:
        return (
            f"🎬 ¡{t} ya se estrenó!",
            f"Hola {primeiro_nome}:\n\n«{t}» se estrenó el {d}. Nos pediste que te avisáramos.\n\n— Cine Leandro",
        )
    return (
        f"🎬 {t} estreou!",
        f"Olá, {primeiro_nome}!\n\n“{t}” estreou em {d}. Você pediu para ser avisado.\n\n— Cine Leandro",
    )


def email_recuperacao(usuario: Usuario, link: str) -> tuple[str, str]:
    idioma = usuario.preferencias.idioma
    if idioma is Idioma.EN:
        return ("Reset your Cine Leandro password",
                f"Use this link within 1 hour to choose a new password:\n{link}\n\nIf you didn't ask for this, ignore this e-mail.")
    if idioma is Idioma.ES:
        return ("Restablece tu contraseña de Cine Leandro",
                f"Usa este enlace en la próxima hora para elegir una nueva contraseña:\n{link}\n\nSi no lo pediste, ignora este correo.")
    return ("Redefina sua senha do Cine Leandro",
            f"Use este link na próxima 1 hora para criar uma nova senha:\n{link}\n\nSe não foi você que pediu, ignore este e-mail.")
