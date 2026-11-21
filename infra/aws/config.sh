# Configuração usada pelos scripts de deploy. Preencha depois de criar os recursos (docs/AWS.md).
export AWS_REGION="us-east-1"
export CONTA_AWS="123456789012"                 # aws sts get-caller-identity --query Account --output text
export REPO_ECR="cine-leandro-backend"
export BUCKET_FRONTEND="cine-leandro-frontend-SEU-NOME"
export DISTRIBUICAO_CLOUDFRONT="E1234567890ABC"  # id da distribuição do CloudFront
