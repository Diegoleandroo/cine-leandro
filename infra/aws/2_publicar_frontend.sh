#!/usr/bin/env bash
# Compila o React e publica no S3; o CloudFront entrega para o mundo.
set -euo pipefail
cd "$(dirname "$0")"; source ./config.sh

(cd ../../frontend && npm ci && npm run build)

# Arquivos com hash no nome podem ficar em cache por 1 ano; o index.html nunca.
aws s3 sync ../../frontend/dist "s3://$BUCKET_FRONTEND" --delete \
  --exclude index.html --cache-control "public,max-age=31536000,immutable"
aws s3 cp ../../frontend/dist/index.html "s3://$BUCKET_FRONTEND/index.html" \
  --cache-control "no-cache"
aws cloudfront create-invalidation --distribution-id "$DISTRIBUICAO_CLOUDFRONT" --paths "/index.html" >/dev/null
echo "✅ Frontend publicado no S3 e cache do CloudFront atualizado."
