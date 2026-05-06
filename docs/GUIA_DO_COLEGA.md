# Guia do Colega

Guia rapido para rodar, entender e evoluir o `Finance Controler`.

## Visao geral

O projeto esta dividido em duas camadas:

- `backend/`: API em `FastAPI + LangChain + PostgreSQL/pgvector`
- `frontend/`: app em `React + TypeScript + Vite`

Capacidades atuais:

- auth com `JWT + RBAC`
- empresa e usuarios em modelo single-tenant preparado para crescer
- RAG para documentos contabeis
- historico de conversa com fontes estruturadas
- upload e indexacao de `PDF`, `DOCX`, `TXT` e `MD`
- importacao financeira por `CSV`
- categorizacao automatica de transacoes
- revisao manual de categoria e notas
- finalizacao da analise
- relatorio persistido por importacao

## Como rodar

### 1. Preparar ambiente

Na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
cd frontend
npm.cmd install
cd ..
copy backend\.env.example .env
docker compose up -d postgres
```

### 2. Rodar migracao

```powershell
Set-Location "C:\Projects\Python aplicação teste\backend"
..\.venv\Scripts\alembic.exe upgrade head
```

Se seu terminal reclamar do formato, rode pelo caminho ajustado para sua shell. O ponto principal e executar o `alembic upgrade head` dentro de `backend/`.

### 3. Subir backend

```powershell
Set-Location "C:\Projects\Python aplicação teste"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010 --reload
```

Links uteis:

- [Swagger](http://127.0.0.1:8010/docs)
- [Health](http://127.0.0.1:8010/health)

### 4. Subir frontend

Em outro terminal:

```powershell
Set-Location "C:\Projects\Python aplicação teste\frontend"
npm.cmd run dev
```

App React:

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

## Credenciais iniciais

No ambiente local, a app cria automaticamente:

- empresa: `Finance Controler`
- admin:
  - email: `admin@finance-controler.local`
  - senha: `Admin123!`

Esses valores sao controlados pelo `.env` e devem ser trocados fora de ambiente local.

## Variaveis importantes

Arquivo local principal:

- [`.env`](</C:\Projects\Python aplicação teste\.env>)

Campos mais importantes:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_EMBEDDINGS_MODEL`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ACCESS_TOKEN_MINUTES`
- `REFRESH_TOKEN_DAYS`
- `ALLOWED_ORIGINS`
- `DEFAULT_PAGE_SIZE`
- `MAX_PAGE_SIZE`
- `SEED_COMPANY_NAME`
- `SEED_ADMIN_EMAIL`
- `SEED_ADMIN_PASSWORD`

Observacoes:

- o backend aceita `.env` na raiz ou em `backend/.env`
- o frontend usa [frontend/.env.example](</C:\Projects\Python aplicação teste\frontend\.env.example>) para a URL da API

## Endpoints principais

Arquivo das rotas:

- [backend/app/api/routes.py](</C:\Projects\Python aplicação teste\backend\app\api\routes.py>)

### Auth

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

### Usuarios

- `GET /users`
- `POST /users`
- `PATCH /users/{user_id}`
- `PATCH /users/{user_id}/password`
- `PATCH /users/{user_id}/status`

### Documentos e chat

- `POST /chat`
- `GET /sessions/{session_id}/history`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `DELETE /documents/{document_id}`
- `POST /documents/{document_id}/reindex`

### Financas

- `GET /finance/categories`
- `POST /finance/imports`
- `GET /finance/imports`
- `GET /finance/imports/{import_id}`
- `GET /finance/imports/{import_id}/transactions`
- `PATCH /finance/imports/{import_id}/transactions/{transaction_id}`
- `POST /finance/imports/{import_id}/finalize`
- `GET /finance/imports/{import_id}/report`
- `POST /finance/analyze`
  - legado para preview/dev helper

## Fluxo de backend

### Auth e autorizacao

Arquivos principais:

- [backend/app/core/security.py](</C:\Projects\Python aplicação teste\backend\app\core\security.py>)
- [backend/app/services/auth_service.py](</C:\Projects\Python aplicação teste\backend\app\services\auth_service.py>)
- [backend/app/api/dependencies.py](</C:\Projects\Python aplicação teste\backend\app\api\dependencies.py>)

Fluxo:

1. usuario faz login com email e senha
2. backend gera `access_token` e `refresh_token`
3. frontend guarda sessao local e renova token quando necessario
4. dependencias protegem rotas por papel

### Chat e documentos

Arquivos principais:

- [backend/app/services/assistant.py](</C:\Projects\Python aplicação teste\backend\app\services\assistant.py>)
- [backend/app/services/document_service.py](</C:\Projects\Python aplicação teste\backend\app\services\document_service.py>)
- [backend/app/services/retrieval.py](</C:\Projects\Python aplicação teste\backend\app\services\retrieval.py>)
- [backend/app/repositories/document_repository.py](</C:\Projects\Python aplicação teste\backend\app\repositories\document_repository.py>)

Fluxo:

1. documento e recebido e parseado
2. texto e quebrado em chunks
3. embeddings sao gerados
4. chunks vao para o PostgreSQL com `pgvector`
5. o chat busca contexto, monta prompt e responde com `sources`

### Operacao financeira persistida

Arquivos principais:

- [backend/app/services/finance_parser.py](</C:\Projects\Python aplicação teste\backend\app\services\finance_parser.py>)
- [backend/app/services/finance_service.py](</C:\Projects\Python aplicação teste\backend\app\services\finance_service.py>)
- [backend/app/repositories/finance_repository.py](</C:\Projects\Python aplicação teste\backend\app\repositories\finance_repository.py>)
- [backend/app/schemas/finance.py](</C:\Projects\Python aplicação teste\backend\app\schemas\finance.py>)

Fluxo:

1. o frontend envia um `CSV`
2. a API normaliza colunas como data, descricao e valor
3. a importacao e persistida em `finance_imports`
4. as transacoes vao para `finance_transactions`
5. a API gera e salva um snapshot de relatorio
6. o analista revisa categorias e notas
7. a importacao pode ser finalizada

## Fluxo do frontend

Arquivos principais:

- [frontend/src/App.tsx](</C:\Projects\Python aplicação teste\frontend\src\App.tsx>)
- [frontend/src/auth/AuthContext.tsx](</C:\Projects\Python aplicação teste\frontend\src\auth\AuthContext.tsx>)
- [frontend/src/lib/api.ts](</C:\Projects\Python aplicação teste\frontend\src\lib\api.ts>)
- [frontend/src/styles.css](</C:\Projects\Python aplicação teste\frontend\src\styles.css>)

Telas:

- `/login`
- `/app/overview`
- `/app/imports`
- `/app/imports/:importId/review`
- `/app/imports/:importId/report`
- `/app/settings/users`

Pontos importantes:

- sessao centralizada em context
- rotas protegidas por papel
- cliente HTTP com refresh automatico
- visual pensado como cockpit financeiro operacional

## Testes

Primeira bateria de testes incluida:

- [backend/tests/test_api_auth_contracts.py](</C:\Projects\Python aplicação teste\backend\tests\test_api_auth_contracts.py>)
- [backend/tests/test_finance_api.py](</C:\Projects\Python aplicação teste\backend\tests\test_finance_api.py>)
- [backend/tests/test_finance_parser.py](</C:\Projects\Python aplicação teste\backend\tests\test_finance_parser.py>)
- [backend/tests/test_finance_service_unit.py](</C:\Projects\Python aplicação teste\backend\tests\test_finance_service_unit.py>)
- [backend/tests/test_auth_service_and_security.py](</C:\Projects\Python aplicação teste\backend\tests\test_auth_service_and_security.py>)
- [backend/tests/test_user_service_unit.py](</C:\Projects\Python aplicação teste\backend\tests\test_user_service_unit.py>)

Como rodar:

Windows:

```powershell
.\rodar-testes.bat
```

Ou:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests --cov=backend\app --cov-report=term-missing
```

macOS / Linux:

```bash
./scripts/test-backend.sh
```

Baseline atual:

- `33` testes passando
- cobertura inicial do backend em `58%`

Escopo coberto agora:

- contratos de auth e erros padronizados
- seguranca JWT e hash de senha
- RBAC e regras de usuario
- parser CSV financeiro
- endpoints principais de importacao, review e relatorio via mocks

## Onde mexer

### Backend

- `backend/app/api`: endpoints HTTP
- `backend/app/core`: config, seguranca e excecoes
- `backend/app/repositories`: acesso a banco
- `backend/app/schemas`: contratos da API
- `backend/app/services`: regra de negocio
- `backend/alembic`: migracoes

### Frontend

- `frontend/src/pages`: telas de negocio
- `frontend/src/components`: blocos visuais reutilizaveis
- `frontend/src/auth`: sessao e auth
- `frontend/src/lib`: cliente HTTP, formatacao e utilitarios
- `frontend/src/styles.css`: design system

## Atalhos

Windows:

- [validar-ambiente.bat](</C:\Projects\Python aplicação teste\validar-ambiente.bat>)
- [abrir-api.bat](</C:\Projects\Python aplicação teste\abrir-api.bat>)
- [abrir-frontend.bat](</C:\Projects\Python aplicação teste\abrir-frontend.bat>)
- [abrir-tudo.bat](</C:\Projects\Python aplicação teste\abrir-tudo.bat>)
- [rodar-testes.bat](</C:\Projects\Python aplicação teste\rodar-testes.bat>)

macOS:

- [setup-mac.command](</C:\Projects\Python aplicação teste\setup-mac.command>)
- [validar-ambiente.command](</C:\Projects\Python aplicação teste\validar-ambiente.command>)
- [abrir-api.command](</C:\Projects\Python aplicação teste\abrir-api.command>)
- [abrir-frontend.command](</C:\Projects\Python aplicação teste\abrir-frontend.command>)
- [abrir-tudo.command](</C:\Projects\Python aplicação teste\abrir-tudo.command>)
- [rodar-testes.command](</C:\Projects\Python aplicação teste\rodar-testes.command>)

## Proximos passos recomendados

1. adicionar testes automatizados de backend
2. adicionar testes de interface para o frontend
3. exportar relatorios em PDF ou XLSX
4. introduzir fila assincorna para uploads grandes
5. integrar SSO corporativo
