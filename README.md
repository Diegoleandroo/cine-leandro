# 🎬 Cine Leandro v2

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Testes](https://img.shields.io/badge/testes-66%20passando-2ea44f)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-blue)

Catálogo de **filmes reais** (via TMDB) com conta de usuário, carrossel dos populares,
lançamentos, trailers, **onde assistir** (streaming legal no Brasil), filtro por categoria,
**avisos de estreia por e-mail**, temas visuais, três idiomas (PT / EN / ES) e acessibilidade —
tudo em **Arquitetura Limpa**.

O sistema **abre na tela de Entrar**: filmes, avisos e preferências só aparecem depois do login
(a API também exige o token; não é só a tela que esconde).

**Pilha:** React + Motion · Django + Django REST Framework · PostgreSQL · Docker · AWS (deploy preparado em [`docs/AWS.md`](docs/AWS.md))

---

## 🔁 O que mudou da v1 para a v2

| Peça                     | v1                         | v2                                        | Por quê                                                   |
|--------------------------|----------------------------|-------------------------------------------|-----------------------------------------------------------|
| Framework web            | FastAPI                    | **Django + DRF**                          | Django traz ORM, migrations e hash de senha prontos       |
| Validação na borda       | Pydantic                   | **Serializers do DRF**                    | É o padrão do Django REST Framework                       |
| Banco                    | SQLite (SQL na mão)        | **PostgreSQL** (ORM do Django)            | Banco de produção, com migrations versionadas             |
| Tela                     | HTML + JS puro             | **React + Vite + React Router**           | Componentes reutilizáveis e estado organizado             |
| Animações                | CSS                        | **Motion** (antiga Framer Motion)         | Transições de página, cascata, pôster que "voa"           |
| Servidor                 | Uvicorn                    | **Gunicorn**                              | Servidor WSGI padrão para Django                          |
| E-mail                   | log                        | **Amazon SES** (log em desenvolvimento)   | Envio real dos avisos                                     |
| Hospedagem               | —                          | **AWS**: ECS Express, RDS, S3, CloudFront | Veja [docs/AWS.md](docs/AWS.md)                           |
| Ficaram                  | httpx, Docker, pytest      | httpx, Docker, pytest                     | Continuam sendo a melhor escolha                          |

O que **saiu** junto com a venda de ingressos: Sala, Sessão, Reserva, Ingresso e seus casos de uso.

---

## 🧅 Arquitetura Limpa

```
backend/cinema/
├── entidades/            ⚪ Entities — Filme, Usuario, Preferencias, AvisoDeLancamento (Python puro)
├── casos_de_uso/         🟡 Use Cases — CadastrarConta, ListarLancamentos, AtivarAvisoDeLancamento…
│   ├── portas.py              interfaces: UsuarioRepository, CatalogoDeFilmes, ServicoDeEmail…
│   └── dtos.py                objetos de entrada e saída dos casos de uso
├── adaptadores/          🔵 Interface Adapters
│   ├── controllers/           views do DRF + serializers de entrada (validação de formato)
│   ├── presenters/            FilmePresenter, UsuarioPresenter, ErroPresenter… → ViewModels (JSON)
│   ├── repositorios/          Django ORM (PostgreSQL) e em memória
│   ├── persistencia/          os models do Django (tabelas) e as migrations
│   ├── gateways/              TMDB, catálogo local (plano B), fallback e cache
│   ├── seguranca/             hash de senha (Django/PBKDF2) e tokens JWT
│   └── email/                 Amazon SES e log
└── frameworks_drivers/   🟠 Django (settings, urls), config (.env) e o container que liga tudo
frontend/                 🟠 React + Motion (também é a camada de fora)
```

**Regra da Dependência:** os imports só apontam para dentro. O teste
`backend/testes/test_regra_de_dependencia.py` falha se, por exemplo, uma entidade importar Django.

O caminho de uma requisição: **Controller → Caso de uso → (portas) → Presenter → ViewModel → React**.

Os diagramas (casos de uso v3 e arquitetura) estão em [`docs/diagramas/`](docs/diagramas/).

---

## ▶️ Como rodar

### Opção A — Docker (mais simples)

```bash
docker compose up --build
```

Abra **http://localhost:8080**. Sobe PostgreSQL, Django e React juntos.

### Opção B — Na mão (para estudar cada peça)

Precisa de **Python 3.12+**, **Node 22+** e **PostgreSQL 16** rodando.

```bash
# 1. Banco
createuser -P cinema          # senha: cinema
createdb -O cinema cinema

# 2. Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt
copy env.exemplo .env          # Linux/Mac: cp env.exemplo .env
python manage.py migrate
python manage.py runserver     # http://localhost:8000/api/filmes

# 3. Frontend (outro terminal)
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

### 🎞️ Filmes reais com o TMDB

Sem chave, o sistema usa um **catálogo local com 16 clássicos reais** (sem pôsteres, trailers
nem lançamentos). Para ver o catálogo de verdade:

1. Crie uma conta em <https://www.themoviedb.org> e peça uma chave em *Configurações → API*.
2. Copie o **Token de leitura da API** (o texto longo que começa com `eyJ`).
3. No `backend/.env`: `TMDB_TOKEN=cole_aqui` e reinicie o backend.

Aparecem os filmes em cartaz no Brasil, populares, mais bem avaliados e os próximos
lançamentos, com pôster, foto de fundo, sinopse no idioma escolhido, classificação indicativa
e trailer. **Nenhum caso de uso muda.** Se o TMDB cair, o catálogo local assume sozinho.

> This product uses the TMDB API but is not endorsed or certified by TMDB.
> Os dados de "Onde assistir" vêm da **JustWatch** (via TMDB), e o crédito aparece na página do filme,
> como o TMDB exige. O Cine Leandro não exibe filmes: ele mostra onde assisti-los legalmente.

### 📬 Avisos de estreia

```bash
python manage.py disparar_avisos
```

Envia o e-mail de quem pediu aviso de um filme que estreia hoje. Em desenvolvimento o e-mail
aparece no terminal (`CINEMA_EMAIL=log`); na AWS vai pelo SES, todo dia, pelo EventBridge.

---

## ✅ Testes

```bash
cd backend
pytest
```

66 testes: regras das entidades, casos de uso, **testes de contrato** (o mesmo teste roda no
repositório em memória e no PostgreSQL), o gateway do TMDB com a internet simulada, segurança
(JWT, revogação no logout, hash, limite de tentativas no login), a API de ponta a ponta e a Regra da Dependência.
Os testes do PostgreSQL precisam do banco do passo 1 rodando (o usuário `cinema` precisa poder criar bancos: `ALTER USER cinema CREATEDB;`).

---

## 🌐 API

| Método | Rota                                | O que faz                                     | Login |
|--------|-------------------------------------|-----------------------------------------------|:-----:|
| POST   | `/api/auth/cadastro`                | Cria a conta e já entra                       |       |
| POST   | `/api/auth/login` · `/logout`       | Entra / sai (o logout revoga o token)         |       |
| GET    | `/api/auth/eu`                      | Quem está logado                              |  ✔︎   |
| POST   | `/api/auth/recuperar-senha`         | Envia o link de redefinição (vale 1 hora)     |       |
| POST   | `/api/auth/redefinir-senha`         | Troca a senha com o token do link             |       |
| GET    | `/api/filmes?lista=&genero=&pagina=`| Em cartaz, populares, mais bem avaliados      |  ✔︎   |
| GET    | `/api/filmes/lancamentos`           | Só o que ainda vai estrear                    |  ✔︎   |
| GET    | `/api/filmes/generos`               | Categorias para o filtro                      |  ✔︎   |
| GET    | `/api/filmes/<id>` · `/trailer`     | Detalhes (sinopse) e trailer                  |  ✔︎   |
| GET    | `/api/filmes/<id>/onde-assistir`    | Onde assistir no Brasil (dados da JustWatch)  |  ✔︎   |
| GET/PUT| `/api/preferencias`                 | Tema, idioma, tamanho do texto, animações     |  ✔︎   |
| GET/POST| `/api/avisos` · DELETE `/api/avisos/<id>` | Avisos de estreia                       |  ✔︎   |
| GET    | `/api/vitrine`                      | Pôsteres dos lançamentos para a tela de Entrar (só pôster, título e data) |       |
| GET    | `/api/saude` · `/api/sistema`       | Health check (AWS) e peças ativas             |       |

Todas aceitam `?idioma=PT|EN|ES`.

---

## 🔒 Segurança

- **Segredos fora do código:** o token do TMDB e a chave do Django ficam no `backend/.env`, que o
  `.gitignore` impede de ir para o GitHub. O modelo sem segredos é o `backend/env.exemplo`.
- **Senhas** guardadas só como hash (PBKDF2 do Django); mínimo de 8 caracteres com letras e números.
- **Força bruta:** 5 senhas erradas seguidas bloqueiam a conta por 15 minutos (caso de uso
  `FazerLogin` + porta `LimiteDeTentativas`), e cada IP faz no máximo 20 pedidos por minuto
  em login, cadastro e recuperação de senha. A contagem fica no PostgreSQL, compartilhada
  entre os processos do Gunicorn.
- **Login:** token JWT, revogado no logout. "Esqueci minha senha" não revela se o e-mail existe.
- **Navegador:** o nginx manda Content-Security-Policy (só carrega scripts do próprio site),
  X-Frame-Options (ninguém coloca o site dentro de outro), nosniff, Referrer-Policy e Permissions-Policy.
- **Docker:** o site só abre neste computador (`127.0.0.1:8080`), o banco não fica exposto e o
  backend roda sem ser root. Em produção (`DJANGO_DEBUG=0`) o Django se recusa a subir com a chave de teste.

---

## ♿ Acessibilidade e ✨ animações

- Três temas: **escuro**, **claro** e **alto contraste** (sem transparências, bordas grossas).
- Campos de senha com o **"olhinho"** para mostrar/ocultar o que foi digitado.
- Texto em três tamanhos; navegação completa por teclado; link "Pular para o conteúdo";
  foco sempre visível; `lang` da página muda com o idioma; o trailer fecha com **Esc**.
- **Carrossel dos populares** no topo: troca sozinho a cada 7 s, pausa com o mouse ou o foco do
  teclado, tem setas, bolinhas com barra de progresso, miniaturas "A seguir", teclas ← → e arrastar no celular.
- **Motion** anima as trocas de página, a entrada dos cartazes em cascata, o pôster que "voa"
  da grade para a página do filme, as abas, o sino do aviso e a janela do trailer.
- **"Reduzir animações"** nas Preferências desliga tudo isso — e o site também respeita o
  ajuste *reduzir movimento* do sistema operacional (`<MotionConfig reducedMotion>`).

## 🔄 Próximos passos

- **Cache compartilhado:** trocar o cache em memória do Django por Redis (ElastiCache na AWS).
- **CI/CD:** GitHub Actions rodando o `pytest` e publicando na AWS a cada push na `main`.
- **Login social:** um novo adaptador de autenticação, sem mexer nos casos de uso.

---

## 👤 Autor

**Diego Leandro** · [github.com/Diegoleandroo](https://github.com/Diegoleandroo)

Projeto de estudo de Arquitetura Limpa, do diagrama de casos de uso ao sistema rodando
(os diagramas estão em [`docs/diagramas`](docs/diagramas)).

## 📄 Licença

Código sob a licença [MIT](LICENSE). Dados e imagens de filmes: [TMDB](https://www.themoviedb.org);
onde assistir: [JustWatch](https://www.justwatch.com).
