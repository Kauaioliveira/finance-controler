# Assistente Contabil API

Assistente contábil com `FastAPI`, `LangChain`, `OpenAI` e `PostgreSQL + pgvector`.

Guia detalhado para onboarding e contribuicao:

- [docs/GUIA_DO_COLEGA.md](</C:\Projects\Python aplicação teste\docs\GUIA_DO_COLEGA.md>)

## O que esta fase entrega

- API HTTP em FastAPI
- upload de documentos via API
- ingestão de `PDF`, `DOCX`, `TXT` e `MD`
- indexação vetorial com embeddings da OpenAI
- busca RAG com citação de fontes
- histórico conversacional persistido em PostgreSQL

## Requisitos

- Python 3.14+
- Docker Desktop com backend WSL 2
- PostgreSQL com extensão `pgvector` via container

## Configuração

### Windows

1. Crie o ambiente virtual e instale as dependências:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

2. Ajuste o arquivo `.env`:

- `OPENAI_API_KEY`
- `DATABASE_URL`
- `OPENAI_EMBEDDINGS_MODEL`
- `ALLOWED_ORIGINS`
- `MAX_UPLOAD_SIZE_MB`

Exemplo de `DATABASE_URL`:

```text
postgresql://postgres:postgres@localhost:5432/assistente_contabil
```

### macOS

Depois de clonar o projeto no Mac, rode uma vez:

```bash
cd "/caminho/do/projeto"
chmod +x ./*.command ./scripts/*.sh
./setup-mac.command
```

Atalhos executaveis no Mac:

- [setup-mac.command](</C:\Projects\Python aplicação teste\setup-mac.command>)
- [validar-ambiente.command](</C:\Projects\Python aplicação teste\validar-ambiente.command>)
- [abrir-tudo.command](</C:\Projects\Python aplicação teste\abrir-tudo.command>)
- [abrir-api.command](</C:\Projects\Python aplicação teste\abrir-api.command>)
- [parar-tudo.command](</C:\Projects\Python aplicação teste\parar-tudo.command>)

## Subindo o banco com Docker

Depois que o Docker Desktop estiver instalado e aberto:

```powershell
docker compose up -d postgres
docker compose ps
```

Ou use o script do projeto:

```powershell
.\scripts\start-dev.ps1
```

Para derrubar:

```powershell
.\scripts\stop-dev.ps1
```

## Atalhos práticos

Se quiser usar com duplo clique ou um comando curto:

### Windows

- [abrir-tudo.bat](</C:\Projects\Python aplicação teste\abrir-tudo.bat>): sobe o PostgreSQL no Docker, abre `/docs` e inicia a API
- [abrir-api.bat](</C:\Projects\Python aplicação teste\abrir-api.bat>): sobe só a API e abre `/docs`
- [parar-tudo.bat](</C:\Projects\Python aplicação teste\parar-tudo.bat>): derruba os containers do projeto
- [instalar-docker-admin.bat](</C:\Projects\Python aplicação teste\instalar-docker-admin.bat>): abre o bootstrap do Docker/WSL com elevação de administrador
- [validar-ambiente.bat](</C:\Projects\Python aplicação teste\validar-ambiente.bat>): confere Docker, daemon e ambiente virtual

### macOS

- [setup-mac.command](</C:\Projects\Python aplicação teste\setup-mac.command>): prepara `.venv`, instala dependencias e cria `.env`
- [validar-ambiente.command](</C:\Projects\Python aplicação teste\validar-ambiente.command>): confere Docker e ambiente virtual
- [abrir-tudo.command](</C:\Projects\Python aplicação teste\abrir-tudo.command>): sobe PostgreSQL, abre `/docs` e inicia a API
- [abrir-api.command](</C:\Projects\Python aplicação teste\abrir-api.command>): sobe so a API
- [parar-tudo.command](</C:\Projects\Python aplicação teste\parar-tudo.command>): derruba os containers do projeto
- `make setup`, `make validate`, `make dev`, `make stop`

Fluxo mais simples para o dia a dia:

1. Rode `instalar-docker-admin.bat` uma vez, se Docker/WSL ainda nao estiverem instalados.
2. Depois use `abrir-tudo.bat`.
3. Quando terminar, use `parar-tudo.bat`.

Fluxo mais simples no Mac:

1. Rode `chmod +x ./*.command ./scripts/*.sh` uma vez.
2. Rode `./setup-mac.command`.
3. Depois use `./abrir-tudo.command`.
4. Quando terminar, use `./parar-tudo.command`.

## Execução

```cmd
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

## Endpoints principais

- `GET /health`
- `GET /config`
- `POST /chat`
- `GET /sessions/{session_id}/history`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `DELETE /documents/{document_id}`
- `POST /documents/{document_id}/reindex`

## Melhorias para frontend

- `POST /chat` agora retorna `sources` estruturado com `filename`, `document_id`, `chunk_index`, `excerpt`, `score` e `source_label`
- `GET /sessions/{session_id}/history` retorna tambem `sources` e `confidence_hint` por mensagem
- `CORS` pode ser controlado por `ALLOWED_ORIGINS`
- uploads respeitam o limite configuravel `MAX_UPLOAD_SIZE_MB`

## Exemplos

### Enviar pergunta

```cmd
curl -X POST http://127.0.0.1:8010/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Explique o que e DRE.\",\"session_id\":\"sessao-1\"}"
```

### Upload de documento

```cmd
curl -X POST http://127.0.0.1:8010/documents/upload ^
  -F "file=@C:\caminho\seu-documento.pdf"
```

### Exemplo de `sources` no `/chat`

```json
{
  "answer": "Resumo da resposta...",
  "session_id": "sessao-1",
  "used_demo_mode": false,
  "confidence_hint": "medium",
  "sources": [
    {
      "filename": "politica-contabil.txt",
      "source_label": "politica-contabil.txt#chunk-0",
      "document_id": "uuid-do-documento",
      "chunk_index": 0,
      "excerpt": "Trecho resumido do documento usado como base...",
      "score": 0.91
    }
  ]
}
```

## Bootstrap de máquina Windows

Se você abrir um PowerShell **como Administrador**, pode usar o script abaixo para preparar WSL + Docker Desktop:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\scripts\windows-admin-bootstrap.ps1
```

O script:

- habilita `WSL` e `VirtualMachinePlatform`
- executa `wsl --install`
- baixa o instalador oficial do Docker Desktop
- instala o Docker Desktop usando backend `WSL 2`

Depois disso, reinicie o Windows.

## Observações

- Sem `OPENAI_API_KEY`, o `/chat` entra em modo demo e os endpoints de indexação dependem de chave real.
- Sem PostgreSQL acessível, a API responde com erro controlado de infraestrutura nos endpoints dependentes do banco.
- Esta fase não inclui autenticação nem interface web dedicada.
- Docker Desktop pode exigir licença paga em empresas maiores, conforme a política oficial da Docker.
