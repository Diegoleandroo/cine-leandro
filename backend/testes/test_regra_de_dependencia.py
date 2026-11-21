"""A Regra da Dependência, verificada automaticamente.

Os imports só podem apontar para dentro dos círculos. Se alguém importar Django
dentro de uma entidade, ou o container dentro de um controller, este teste quebra.
"""

import ast
from pathlib import Path

import pytest

PACOTE = Path(__file__).resolve().parents[1] / "cinema"

# camada -> o que ela NÃO pode importar
PROIBIDO = {
    "entidades": ["cinema.casos_de_uso", "cinema.adaptadores", "cinema.frameworks_drivers",
                  "django", "rest_framework", "httpx", "jwt", "boto3", "psycopg"],
    "casos_de_uso": ["cinema.adaptadores", "cinema.frameworks_drivers",
                     "django", "rest_framework", "httpx", "jwt", "boto3", "psycopg"],
    "adaptadores": ["cinema.frameworks_drivers"],
}


def imports_de(arquivo: Path) -> list[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes += [a.name for a in no.names]
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            nomes.append(no.module)
    return nomes


@pytest.mark.parametrize("camada", list(PROIBIDO))
def test_imports_so_apontam_para_dentro(camada):
    violacoes = []
    for arquivo in (PACOTE / camada).rglob("*.py"):
        for nome in imports_de(arquivo):
            if any(nome == p or nome.startswith(p + ".") for p in PROIBIDO[camada]):
                violacoes.append(f"{arquivo.relative_to(PACOTE)} importa {nome}")
    assert not violacoes, "Regra da Dependência violada:\n" + "\n".join(violacoes)
