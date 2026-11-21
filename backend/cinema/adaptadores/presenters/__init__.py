"""Presenters: transformam o resultado dos casos de uso em ViewModels.

Um ViewModel é exatamente o JSON que a tela (React) recebe: datas já em texto,
campos calculados prontos (duração "2h 49min", dias para a estreia...).
A tela não precisa conhecer as entidades.
"""

from .aviso import AvisoPresenter
from .erro import ErroPresenter
from .filme import FilmePresenter, GeneroPresenter, PaginaPresenter
from .onde_assistir import OndeAssistirPresenter
from .preferencias import PreferenciasPresenter
from .trailer import TrailerPresenter
from .usuario import UsuarioPresenter
from .vitrine import VitrinePresenter

__all__ = [
    "AvisoPresenter",
    "ErroPresenter",
    "FilmePresenter",
    "GeneroPresenter",
    "OndeAssistirPresenter",
    "PaginaPresenter",
    "PreferenciasPresenter",
    "TrailerPresenter",
    "UsuarioPresenter",
    "VitrinePresenter",
]
