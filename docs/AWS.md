# ☁️ Publicando o Cine Leandro na AWS

Este guia leva o sistema do seu computador para a internet. Cada peça da AWS
substitui uma peça que você já usa localmente:

| No seu computador            | Na AWS                                          | Para quê                                    |
|------------------------------|-------------------------------------------------|---------------------------------------------|
| `docker compose` (backend)   | **Amazon ECR** + **ECS Express Mode** (Fargate) | Rodar o container do Django                 |
| PostgreSQL local             | **Amazon RDS for PostgreSQL**                   | Banco gerenciado, com backup automático     |
| `npm run build` + nginx      | **Amazon S3** + **Amazon CloudFront**           | Entregar o React pelo mundo, com HTTPS      |
| `CINEMA_EMAIL=log`           | **Amazon SES**                                  | Enviar os e-mails de estreia de verdade     |
| `manage.py disparar_avisos`  | **EventBridge Scheduler**                       | Rodar o aviso uma vez por dia               |
| arquivo `.env`               | **Secrets Manager**                             | Guardar senha do banco, chave do Django e do TMDB |

```
 Usuário ──HTTPS──► CloudFront ──/*──────► S3 (React)
                         │
                         └──/api/*──► ECS Express (Django + Gunicorn) ──► RDS PostgreSQL
                                             │        │
                                             │        └──► TMDB (filmes reais)
                     EventBridge (1x/dia) ───┘        └──► SES (e-mails)
```

> **Por que ECS Express Mode e não App Runner?** O App Runner deixou de aceitar novos
> clientes em 30/04/2026, e a própria AWS recomenda o ECS Express Mode no lugar dele.
> Ele cria sozinho o load balancer, o HTTPS, o auto scaling e os logs.

---

## 💰 Antes de tudo: custos

Contas novas (desde julho de 2025) recebem **créditos** em vez dos antigos "12 meses grátis".
Mesmo assim, configure um alerta de gastos **antes** de criar qualquer coisa:

1. Console → **Billing and Cost Management → Budgets → Create budget**.
2. Escolha *Monthly cost budget*, valor **US$ 5**, e coloque seu e-mail.

O que custa dinheiro aqui, mesmo parado: o **load balancer** que o ECS Express cria e o
**banco RDS** ligado. Quando terminar de estudar, apague o serviço do ECS e o banco (passo 9).

---

## Passo 0 — Ferramentas

- Uma conta AWS e o **AWS CLI v2** configurado (`aws configure`).
- **Docker** instalado.
- Escolha uma região e use sempre a mesma (o guia usa `us-east-1`). Preencha `infra/aws/config.sh`.

## Passo 1 — Banco: Amazon RDS for PostgreSQL

1. Console → **RDS → Create database** → *Easy create* → **PostgreSQL**.
2. Tamanho: o menor disponível (*Free tier* / `db.t4g.micro`).
3. Nome do banco: `cinema`. Usuário: `cinema`. Gere uma senha forte e guarde.
4. **Public access: No** (o banco só é acessado de dentro da AWS).
5. Anote o *endpoint*. Sua `DATABASE_URL` fica:
   `postgres://cinema:SENHA@ENDPOINT:5432/cinema`

> Alternativa: o **Aurora PostgreSQL Serverless** também entrou no plano gratuito em 2026.
> Para o Django não muda nada: é a mesma `DATABASE_URL`.

## Passo 2 — Segredos: AWS Secrets Manager

Console → **Secrets Manager → Store a new secret → Other type of secret**, nome
`cine-leandro/django`, com três chaves:

| Chave               | Valor                                                     |
|---------------------|-----------------------------------------------------------|
| `DJANGO_SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DATABASE_URL`      | a URL do passo 1                                          |
| `TMDB_TOKEN`        | o token de leitura do TMDB (começa com `eyJ`)             |

Copie o ARN completo do segredo (ele termina com 6 letras aleatórias, como `cine-leandro/django-AbCdEf`)
para `infra/aws/container-backend.json`. Cada variável aponta para uma chave do segredo no formato
`ARN:NOME_DA_CHAVE::` — é assim que o ECS lê uma chave específica de um segredo JSON.

## Passo 3 — E-mail: Amazon SES

1. Console → **SES → Identities → Create identity**: verifique o e-mail (ou domínio) remetente.
2. Contas novas começam no **sandbox**: só enviam para e-mails verificados. Para testar,
   verifique também o seu e-mail pessoal. Para enviar a qualquer pessoa, peça
   *Request production access* no painel do SES.

## Passo 4 — Imagem do backend no Amazon ECR

```bash
./infra/aws/1_publicar_backend.sh
```

O script cria o repositório, faz login, constrói a imagem para `linux/amd64` e envia.

## Passo 5 — Backend no ECS Express Mode

### 5.1 Funções (IAM roles)

O Express Mode precisa de duas funções; o tutorial oficial mostra os comandos:
<https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-getting-started.html>

- **Execution role** (`ecsTaskExecutionRole`): política gerenciada `AmazonECSTaskExecutionRolePolicy`
  **+** a política `infra/aws/politica-execucao-segredos.json` (para ler o Secrets Manager).
- **Infrastructure role** (`ecsInfrastructureRoleForExpressServices`): política gerenciada
  `AmazonECSInfrastructureRoleforExpressGatewayServices`.
- **Task role** (opcional, mas necessária para o SES): crie `cineLeandroTaskRole` com a
  política `infra/aws/politica-tarefa.json`. É ela que o código do Django usa para chamar o SES.

### 5.2 Criar o serviço

Edite `infra/aws/container-backend.json` (imagem, ARNs, domínios) e rode:

```bash
aws ecs create-express-gateway-service \
  --service-name cine-leandro-backend \
  --execution-role-arn arn:aws:iam::CONTA:role/ecsTaskExecutionRole \
  --infrastructure-role-arn arn:aws:iam::CONTA:role/ecsInfrastructureRoleForExpressServices \
  --task-role-arn arn:aws:iam::CONTA:role/cineLeandroTaskRole \
  --primary-container file://infra/aws/container-backend.json \
  --health-check-path /api/saude \
  --monitor-resources DEPLOYMENT
```

Quando o status ficar **ACTIVE**, o console mostra o endereço HTTPS do serviço.
Teste: `curl https://ENDERECO-DO-SERVICO/api/saude` → `{"status": "ok"}`.

> Se o health check falhar com erro de banco, o *security group* do RDS precisa aceitar a
> porta 5432 vindo do *security group* do serviço ECS (RDS → Connectivity → Security groups).

As migrations rodam sozinhas quando o container sobe (veja o `CMD` do `backend/Dockerfile`).

## Passo 6 — Frontend: S3 + CloudFront

1. **S3 → Create bucket** com o nome de `BUCKET_FRONTEND` (bloqueio de acesso público **ligado**).
2. **CloudFront → Create distribution**:
   - *Origin*: o bucket S3, com **Origin access control (OAC)** — o CloudFront oferece atualizar a política do bucket.
   - *Default root object*: `index.html`.
3. Adicione uma **segunda origem**: o endereço do serviço ECS Express (HTTPS only).
4. Crie um **behavior** `/api/*` apontando para essa origem:
   - *Allowed methods*: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
   - *Cache policy*: **CachingDisabled**
   - *Origin request policy*: **AllViewerExceptHostHeader**
5. Em **Error pages**, para os códigos 403 e 404: resposta `/index.html` com código **200**
   (é o que faz o React Router funcionar ao recarregar uma página).
6. Atualize `DJANGO_ALLOWED_HOSTS`, `URL_FRONTEND` e `CORS_ALLOWED_ORIGINS` com o domínio
   `xxxx.cloudfront.net` e publique:

```bash
./infra/aws/2_publicar_frontend.sh
```

Como o React e a API saem do **mesmo domínio** do CloudFront, o navegador nem precisa de CORS.

## Passo 7 — Aviso diário: EventBridge Scheduler

1. Console → **EventBridge → Schedules → Create schedule**.
2. Recorrente, expressão cron `0 9 * * ? *`, fuso **America/Sao_Paulo** (todo dia às 9h).
3. Alvo: **ECS RunTask** → cluster e *task definition* do serviço `cine-leandro-backend`,
   launch type **FARGATE**, mesmas subnets e security group do serviço.
4. Em *Container overrides*, comando:
   `["python", "manage.py", "disparar_avisos"]`
5. Deixe o console criar a função de execução do agendador.

## Passo 8 — Publicar uma nova versão

```bash
./infra/aws/1_publicar_backend.sh    # envia a nova imagem ao ECR
./infra/aws/2_publicar_frontend.sh   # publica o React
```

Depois, no console do **ECS**, abra o serviço `cine-leandro-backend` e clique em **Update**
para fazer o deploy da nova imagem (pela linha de comando é o
`aws ecs update-express-gateway-service`; rode `aws ecs update-express-gateway-service help`
para ver as opções da sua versão do CLI). O Express Mode troca os containers sem tirar o site do ar.

## Passo 9 — Desligar tudo (para não pagar)

1. ECS → apague o serviço Express (isso remove o load balancer que ele criou).
2. RDS → apague o banco (pode tirar um *snapshot* final antes).
3. CloudFront → desative e apague a distribuição; S3 → esvazie e apague o bucket.
4. EventBridge → apague o agendamento.

---

### Problemas comuns

| Sintoma                                   | Causa provável                                                      |
|-------------------------------------------|---------------------------------------------------------------------|
| `400 Bad Request` em todas as rotas       | Domínio faltando em `DJANGO_ALLOWED_HOSTS`                          |
| Serviço reiniciando sem parar             | `DATABASE_URL` errada ou security group do RDS bloqueando o ECS     |
| Página em branco ao recarregar `/filme/…` | Faltou o erro 403/404 → `/index.html` no CloudFront                 |
| E-mail não chega                          | SES em sandbox: o destinatário também precisa estar verificado      |
| `exec format error` no ECS                | Imagem construída para ARM: use `--platform linux/amd64`            |
