#!/usr/bin/env bash
# Constrói a imagem do Django e envia para o Amazon ECR.
# Depois, o serviço do ECS Express é atualizado para a nova versão (veja docs/AWS.md, passo 5).
set -euo pipefail
cd "$(dirname "$0")"; source ./config.sh

REGISTRO="$CONTA_AWS.dkr.ecr.$AWS_REGION.amazonaws.com"
VERSAO="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M)"

aws ecr describe-repositories --repository-names "$REPO_ECR" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$REPO_ECR" --image-scanning-configuration scanOnPush=true
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REGISTRO"

# Fargate roda em x86_64 por padrão: força a plataforma (importante em Mac com chip M)
docker build --platform linux/amd64 -t "$REGISTRO/$REPO_ECR:$VERSAO" -t "$REGISTRO/$REPO_ECR:latest" ../../backend
docker push "$REGISTRO/$REPO_ECR:$VERSAO"
docker push "$REGISTRO/$REPO_ECR:latest"
echo "✅ Imagem publicada: $REGISTRO/$REPO_ECR:$VERSAO"
