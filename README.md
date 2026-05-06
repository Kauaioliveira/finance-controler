# Finance Controler

Produto interno para operacao financeira, com backend em `FastAPI + LangChain + PostgreSQL/pgvector` e frontend em `React + TypeScript + Vite`.

O projeto hoje cobre dois fluxos principais:

- assistente contabil com RAG para documentos internos
- cockpit financeiro para importar `CSV`, categorizar transacoes, revisar resultados e gerar relatorios persistidos

Guia tecnico detalhado:

- [docs/GUIA_DO_COLEGA.md](</C:\Projects\Python aplicação teste\docs\GUIA_DO_COLEGA.md>)

## Arquitetura

```text
backend/
  alembic/
  app/
  requirements.txt
frontend/
  src/
  package.json
docker/
docs/
scripts/
compose.yaml
```

### Backend

- `FastAPI` como camada HTTP
- `LangChain` no fluxo de chat com documentos
- `PostgreSQL + pgvector` para persistencia relacional e busca vetorial
- `JWT + RBAC` com papeis `admin`, `analyst` e `viewer`
- `Alembic` para migracoes

### Frontend

- `React + TypeScript + Vite`
- `React Router`
- `Context + reducer` para sessao
- cliente HTTP unico com refresh automatico de token
- interface operacional para login, importacao, revisao e relatorio

## Requisitos

- Python 3.14+
- Node.js 20+
- Docker Desktop

## Setup rapido

Na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
cd frontend
npm.cmd install
cd ..
copy backend\.env.example .env
```

Variaveis mais importantes no [`.env`](</C:\Projects\Python aplicação teste\.env>):

- `OPENAI_API_KEY`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ALLOWED_ORIGINS`
- `SEED_ADMIN_EMAIL`
- `SEED_ADMIN_PASSWORD`

Observacoes:

- o backend aceita `.env` tanto na raiz quanto em `backend/.env`
- o frontend usa [frontend/.env.example](</C:\Projects\Python aplicação teste\frontend\.env.example>) para apontar a API
- em ambiente real, troque imediatamente os valores default de seed e segredo JWT

## Banco e migracoes

Suba o PostgreSQL com `pgvector`:

```powershell
docker compose up -d postgres
```

Rode a migracao inicial:

```powershell
cd backend
..\.venv\Scripts\alembic.exe upgrade head
```

Se preferir copiar exatamente:

```powershell
Set-Location "C:\Projects\Python aplicação teste\backend"
..\.venv\Scripts\alembic.exe upgrade head
```

Importante:

- no ambiente local, o bootstrap da app tambem garante criacao de schema e seed do primeiro admin
- o `Alembic` passa a ser o caminho recomendado para evolucao do schema

## Rodando o backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010 --reload
```

Documentacao da API:

- [http://127.0.0.1:8010/docs](http://127.0.0.1:8010/docs)

## Rodando o frontend

```powershell
cd frontend
npm.cmd run dev
```

Aplicacao web:

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

## Seed inicial

Em ambiente local, a aplicacao cria:

- empresa default: `Finance Controler`
- usuario admin default:
  - email: `admin@finance-controler.local`
  - senha: `Admin123!`

Troque isso fora de ambiente local.

## Endpoints principais

### Auth e usuarios

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /users`
- `POST /users`
- `PATCH /users/{user_id}`
- `PATCH /users/{user_id}/password`
- `PATCH /users/{user_id}/status`

### Documentos e chat contabil

- `POST /chat`
- `GET /sessions/{session_id}/history`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `DELETE /documents/{document_id}`
- `POST /documents/{document_id}/reindex`

### Operacao financeira

- `GET /finance/categories`
- `POST /finance/imports`
- `GET /finance/imports`
- `GET /finance/imports/{import_id}`
- `GET /finance/imports/{import_id}/transactions`
- `PATCH /finance/imports/{import_id}/transactions/{transaction_id}`
- `POST /finance/imports/{import_id}/finalize`
- `GET /finance/imports/{import_id}/report`
- `POST /finance/analyze`
  - endpoint legado de preview

## Fluxo operacional

1. Fazer login no frontend.
2. Importar um `CSV` de transacoes.
3. Deixar a API categorizar e persistir a importacao.
4. Revisar categorias e notas na tela de review.
5. Finalizar a importacao.
6. Consultar o relatorio persistido.

## Testes

Primeira bateria de testes ja incluida no projeto:

- contratos principais da API
- auth, seguranca JWT e regras de acesso
- parser financeiro
- fluxo de imports, review e relatorio com mocks estaveis
- regras centrais de `AuthService` e `UserService`

Comandos principais:

### Windows

```powershell
.\rodar-testes.bat
```

Ou direto:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests --cov=backend\app --cov-report=term-missing
```

### macOS / Linux

```bash
./scripts/test-backend.sh
```

Ou:

```bash
make test-backend
```

Baseline atual da primeira bateria:

- `33` testes passando
- cobertura inicial do backend em `58%`

Observacao:

- essa cobertura ainda nao mira o projeto inteiro; ela cobre primeiro as areas de maior risco e mais valor de negocio
- a proxima fase natural e expandir para documentos/RAG, repositórios com banco e frontend

## Arquivo de exemplo

Para testes rapidos:

- [docs/examples/transactions-sample.csv](</C:\Projects\Python aplicação teste\docs\examples\transactions-sample.csv>)

## Atalhos

### Windows

- [validar-ambiente.bat](</C:\Projects\Python aplicação teste\validar-ambiente.bat>)
- [abrir-api.bat](</C:\Projects\Python aplicação teste\abrir-api.bat>)
- [abrir-frontend.bat](</C:\Projects\Python aplicação teste\abrir-frontend.bat>)
- [abrir-tudo.bat](</C:\Projects\Python aplicação teste\abrir-tudo.bat>)
- [rodar-testes.bat](</C:\Projects\Python aplicação teste\rodar-testes.bat>)
- [parar-tudo.bat](</C:\Projects\Python aplicação teste\parar-tudo.bat>)

### macOS

- [setup-mac.command](</C:\Projects\Python aplicação teste\setup-mac.command>)
- [validar-ambiente.command](</C:\Projects\Python aplicação teste\validar-ambiente.command>)
- [abrir-api.command](</C:\Projects\Python aplicação teste\abrir-api.command>)
- [abrir-frontend.command](</C:\Projects\Python aplicação teste\abrir-frontend.command>)
- [abrir-tudo.command](</C:\Projects\Python aplicação teste\abrir-tudo.command>)
- [rodar-testes.command](</C:\Projects\Python aplicação teste\rodar-testes.command>)

## Qualidade e proximos passos

O projeto ja esta mais proximo de um piloto interno real, com:

- separacao clara entre backend e frontend
- autenticacao e autorizacao por papel
- persistencia de importacoes financeiras
- revisao manual antes de finalizacao
- relatorios persistidos

Evolucoes recomendadas depois desta fase:

- testes automatizados de backend e frontend
- exportacao de relatorios em PDF/XLSX
- SSO corporativo
- trilha de auditoria mais detalhada
- filas assincornas para importacoes maiores
