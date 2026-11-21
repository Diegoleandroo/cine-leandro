"""Tabelas do PostgreSQL, descritas com o ORM do Django.

Estes "models" NÃO são as entidades. São só o formato de gravação.
Quem traduz um para o outro são os repositórios em `repositorios/django_orm.py`.
"""

from django.db import models


class UsuarioModel(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    nome = models.CharField(max_length=80)
    email = models.EmailField(max_length=254, unique=True)  # 2ª trava contra e-mail duplicado
    senha_hash = models.CharField(max_length=255)
    criado_em = models.DateTimeField()
    tema = models.CharField(max_length=20, default="ESCURO")
    idioma = models.CharField(max_length=2, default="PT")
    tamanho_fonte = models.CharField(max_length=1, default="M")
    reduzir_animacoes = models.BooleanField(default=False)

    class Meta:
        db_table = "usuario"


class AvisoModel(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    usuario = models.ForeignKey(UsuarioModel, on_delete=models.CASCADE, related_name="avisos")
    filme_id = models.CharField(max_length=40)
    filme_titulo = models.CharField(max_length=200)
    data_lancamento = models.DateField()
    criado_em = models.DateTimeField()
    enviado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "aviso_de_lancamento"
        constraints = [
            models.UniqueConstraint(fields=["usuario", "filme_id"], name="um_aviso_por_filme_por_usuario"),
        ]
        indexes = [models.Index(fields=["enviado_em", "data_lancamento"], name="aviso_pendente_idx")]


class TokenRevogadoModel(models.Model):
    """Tokens de quem fez logout. Guardamos só o id do token (jti), nunca o token."""

    jti = models.CharField(primary_key=True, max_length=64)
    expira_em = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "token_revogado"
