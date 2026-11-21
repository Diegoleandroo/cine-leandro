"""Serializers de entrada (DRF): validação de FORMATO, na borda.

Aqui só se confere o formato ("veio um e-mail?", "a página é um número?").
As regras de negócio ("a senha precisa ter 8 caracteres", "o filme não pode ter
estreado") ficam nas entidades. Essa separação é uma das lições do projeto.
"""

from rest_framework import serializers

TEMAS = ["CLARO", "ESCURO", "ALTO_CONTRASTE"]
IDIOMAS = ["PT", "EN", "ES"]
FONTES = ["P", "M", "G"]


class PreferenciasEntrada(serializers.Serializer):
    tema = serializers.ChoiceField(choices=TEMAS, required=False)
    idioma = serializers.ChoiceField(choices=IDIOMAS, required=False)
    tamanho_fonte = serializers.ChoiceField(choices=FONTES, required=False)
    reduzir_animacoes = serializers.BooleanField(required=False)


class CadastroEntrada(serializers.Serializer):
    nome = serializers.CharField(max_length=80)
    email = serializers.CharField(max_length=254)
    senha = serializers.CharField(max_length=128, trim_whitespace=False)
    preferencias = PreferenciasEntrada(required=False)


class LoginEntrada(serializers.Serializer):
    email = serializers.CharField(max_length=254)
    senha = serializers.CharField(max_length=128, trim_whitespace=False)


class RecuperarSenhaEntrada(serializers.Serializer):
    email = serializers.CharField(max_length=254)


class RedefinirSenhaEntrada(serializers.Serializer):
    token = serializers.CharField(max_length=2000)
    nova_senha = serializers.CharField(max_length=128, trim_whitespace=False)


class ListaEntrada(serializers.Serializer):
    lista = serializers.ChoiceField(
        choices=["EM_CARTAZ", "POPULARES", "MAIS_BEM_AVALIADOS"], required=False, default="EM_CARTAZ"
    )
    genero = serializers.IntegerField(required=False, min_value=1)
    pagina = serializers.IntegerField(required=False, min_value=1, max_value=500, default=1)


class AvisoEntrada(serializers.Serializer):
    filme_id = serializers.RegexField(r"^(tmdb|local)-[\w-]{1,30}$", max_length=40)
