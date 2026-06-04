# Finance Controler

Produto interno para operacao financeira, com backend em `FastAPI + LangChain + PostgreSQL/pgvector` e frontend em `React + TypeScript + Vite`.

O projeto hoje cobre dois fluxos principais:

- assistente contabil com RAG para documentos internos
- cockpit financeiro para importar `CSV`, categorizar transacoes, revisar resultados e gerar relatorios persistidos

Guia tecnico detalhado:

- [docs/GUIA_DO_COLEGA.md](docs/GUIA_DO_COLEGA.md)

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

Variaveis mais importantes no [`.env`](.env.example):

- `OPENAI_API_KEY`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ALLOWED_ORIGINS`
- `SEED_ADMIN_EMAIL`
- `SEED_ADMIN_PASSWORD`

Observacoes:

- o backend aceita `.env` tanto na raiz quanto em `backend/.env`
- o frontend usa [frontend/.env.example](frontend/.env.example) para apontar a API
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

Se preferir copiar exatamente a partir da raiz do repositorio:

```powershell
cd backend
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

Em ambiente local, a aplicacao cria a empresa default e o primeiro admin a
partir das variaveis de seed definidas no `.env`.

Recomendacoes:

- configure `SEED_ADMIN_EMAIL` e `SEED_ADMIN_PASSWORD` com valores locais antes do primeiro boot
- nunca publique nem reutilize credenciais de seed em ambiente compartilhado
- altere a senha bootstrap logo depois do primeiro acesso

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

Suite atual de testes no backend:

- contratos principais da API
- auth, seguranca JWT e regras de acesso
- parser financeiro
- fluxo de imports, review e relatorio com mocks estaveis
- regras centrais de `AuthService` e `UserService`
- unidade do fluxo do assistente (`AssistantService`), com dependencias simuladas

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

Numeros atuais (rodar localmente com o comando acima para reproduzir):

- `38` testes passando
- cobertura de instrucoes do pacote `backend/app` em torno de `60%` (varia conforme ambiente)

Observacao:

- a cobertura ainda e desigual: rotas e servicos centrais tendem a ficar mais altos, enquanto repositorios com SQL direto e fluxos RAG/documentos costumam ficar mais baixos ate ganharem testes de integracao
- proximos passos naturais: mais testes de integracao com banco, fluxo completo de documentos/RAG e testes automatizados no frontend

## Arquivo de exemplo

Para testes rapidos:

- [docs/examples/transactions-sample.csv](docs/examples/transactions-sample.csv)

## Atalhos

### Windows

- [validar-ambiente.bat](validar-ambiente.bat)
- [abrir-api.bat](abrir-api.bat)
- [abrir-frontend.bat](abrir-frontend.bat)
- [abrir-tudo.bat](abrir-tudo.bat)
- [rodar-testes.bat](rodar-testes.bat)
- [parar-tudo.bat](parar-tudo.bat)

### macOS

- [setup-mac.command](setup-mac.command)
- [validar-ambiente.command](validar-ambiente.command)
- [abrir-api.command](abrir-api.command)
- [abrir-frontend.command](abrir-frontend.command)
- [abrir-tudo.command](abrir-tudo.command)
- [rodar-testes.command](rodar-testes.command)

## Qualidade e proximos passos

O projeto ja esta mais proximo de um piloto interno real, com:

- separacao clara entre backend e frontend
- autenticacao e autorizacao por papel
- persistencia de importacoes financeiras
- revisao manual antes de finalizacao
- relatorios persistidos

Evolucoes recomendadas depois desta fase:

- mais testes de integracao no backend (banco, RAG) e suite no frontend
- exportacao de relatorios em PDF/XLSX
- SSO corporativo
- trilha de auditoria mais detalhada
- filas assincornas para importacoes maiores
