# Guia do Colega

Guia rapido para rodar, entender e evoluir o projeto `Assistente Contabil API`.

## 1. Visao geral

Este projeto implementa um assistente contabil com:

- `FastAPI` para a API HTTP
- `LangChain` para orquestrar o fluxo de chat
- `OpenAI` para modelo de resposta e embeddings
- `PostgreSQL + pgvector` para guardar documentos, chunks e historico
- `Docker` para subir o banco localmente

Hoje o sistema faz:

- upload de documentos `PDF`, `DOCX`, `TXT` e `MD`
- extracao de texto
- chunking para RAG
- geracao de embeddings
- busca vetorial por similaridade
- resposta com fontes e `confidence_hint`
- historico de conversa por `session_id`

## 2. Como rodar

### Windows

### Opcao mais pratica

Abrir um PowerShell na pasta do projeto e rodar:

```powershell
Set-Location "C:\Projects\Python aplicação teste"
.\validar-ambiente.bat
.\abrir-tudo.bat
```

O que acontece:

- valida Docker e `.venv`
- sobe o PostgreSQL com `pgvector`
- sobe a API em `http://127.0.0.1:8010`
- abre a documentacao Swagger em `/docs`

### Opcao manual

```powershell
Set-Location "C:\Projects\Python aplicação teste"
docker compose up -d postgres
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

### Para parar

```powershell
.\parar-tudo.bat
```

### macOS

Na primeira vez:

```bash
cd "/caminho/do/projeto"
chmod +x ./*.command ./scripts/*.sh
./setup-mac.command
```

Opcao mais pratica:

```bash
./validar-ambiente.command
./abrir-tudo.command
```

Opcao manual:

```bash
docker compose up -d postgres
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

Para parar:

```bash
./parar-tudo.command
```

Se preferir terminal puro:

```bash
make setup
make validate
make dev
make stop
```

## 3. Requisitos locais

- Python 3.14+
- Docker Desktop funcionando
- virtualizacao habilitada na BIOS/UEFI quando for Windows
- `OPENAI_API_KEY` configurada no arquivo `.env`

Sem chave real da OpenAI:

- o `/chat` entra em `modo demo`
- upload pode falhar ao indexar embeddings
- a busca vetorial real nao fica completa

## 4. Variaveis importantes do `.env`

Arquivo atual: [`.env`](</C:\Projects\Python aplicação teste\.env>)

Principais campos:

- `OPENAI_API_KEY`: chave real da OpenAI
- `OPENAI_MODEL`: modelo de chat
- `OPENAI_EMBEDDINGS_MODEL`: modelo de embeddings
- `OPENAI_EMBEDDINGS_DIMENSIONS`: dimensao do vetor
- `DATABASE_URL`: conexao do PostgreSQL
- `DATABASE_CONNECT_TIMEOUT`: timeout de conexao
- `RAG_TOP_K`: quantidade maxima de chunks recuperados
- `RAG_MAX_DISTANCE`: limite de distancia para considerar chunk relevante
- `DOCUMENT_CHUNK_SIZE`: tamanho do chunk
- `DOCUMENT_CHUNK_OVERLAP`: sobreposicao entre chunks
- `SOURCE_EXCERPT_LENGTH`: tamanho maximo do trecho retornado em `sources`
- `MAX_UPLOAD_SIZE_MB`: limite de upload por arquivo
- `ALLOWED_ORIGINS`: origens liberadas para frontend via CORS

## 5. Endpoints principais

Arquivo das rotas: [routes.py](</C:\Projects\Python aplicação teste\app\api\routes.py>)

- `GET /health`
- `GET /config`
- `POST /chat`
- `GET /sessions/{session_id}/history`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `DELETE /documents/{document_id}`
- `POST /documents/{document_id}/reindex`

Contratos uteis para frontend:

- `POST /chat` retorna `sources` estruturado com `filename`, `source_label`, `document_id`, `chunk_index`, `excerpt` e `score`
- `GET /sessions/{session_id}/history` retorna `sources` e `confidence_hint` por mensagem
- `GET /config` expone `allowed_origins`, `supported_extensions` e `max_upload_size_mb`

## 6. Fluxo da aplicacao

### Inicializacao

Entrada da API: [main.py](</C:\Projects\Python aplicação teste\app\main.py>)

No startup:

- a API cria a aplicacao FastAPI
- registra as rotas
- instala o handler de erro da aplicacao
- chama `assistant_service.initialize()`
- o `database.initialize()` tenta criar extensao `vector` e tabelas

### Upload de documento

Servico principal: [document_service.py](</C:\Projects\Python aplicação teste\app\services\document_service.py>)

Fluxo:

1. recebe o arquivo em `POST /documents/upload`
2. usa [document_parser.py](</C:\Projects\Python aplicação teste\app\services\document_parser.py>) para extrair texto
3. divide o texto em chunks com `RecursiveCharacterTextSplitter`
4. gera embeddings com [embeddings.py](</C:\Projects\Python aplicação teste\app\services\embeddings.py>)
5. salva documento e chunks em [document_repository.py](</C:\Projects\Python aplicação teste\app\repositories\document_repository.py>)

### Chat

Servico principal: [assistant.py](</C:\Projects\Python aplicação teste\app\services\assistant.py>)

Fluxo:

1. recebe `message` e `session_id`
2. busca historico no [chat_repository.py](</C:\Projects\Python aplicação teste\app\repositories\chat_repository.py>)
3. consulta chunks relevantes em [retrieval.py](</C:\Projects\Python aplicação teste\app\services\retrieval.py>)
4. monta contexto documental
5. chama `ChatOpenAI`
6. salva pergunta e resposta no banco

## 7. Estrutura da aplicacao

### `app/api`

- define os endpoints HTTP

### `app/core`

- configuracoes do projeto
- excecoes de dominio e infraestrutura

### `app/repositories`

- acesso ao PostgreSQL
- criacao de schema
- consultas e persistencia

### `app/schemas`

- contratos de entrada e saida da API

### `app/services`

- regra de negocio
- parser de arquivos
- embeddings
- retrieval vetorial
- orquestracao do chat

## 8. Como mexer no codigo

### Se quiser mudar o prompt do assistente

Editar: [assistant.py](</C:\Projects\Python aplicação teste\app\services\assistant.py>)

Ponto principal:

- constante `SYSTEM_PROMPT`

### Se quiser mudar como os documentos sao quebrados em chunks

Editar: [document_service.py](</C:\Projects\Python aplicação teste\app\services\document_service.py>)

Ponto principal:

- metodo `_build_chunks`

### Se quiser aceitar outro tipo de arquivo

Editar: [document_parser.py](</C:\Projects\Python aplicação teste\app\services\document_parser.py>)

Pontos principais:

- `SUPPORTED_DOCUMENT_EXTENSIONS`
- metodo `parse`
- criar parser novo se necessario

### Se quiser mudar a regra de relevancia

Editar: [retrieval.py](</C:\Projects\Python aplicação teste\app\services\retrieval.py>)

Pontos principais:

- filtro por `rag_max_distance`
- calculo de `confidence_hint`

### Se quiser adicionar campo novo na API

Arquivos tipicos:

- [schemas/chat.py](</C:\Projects\Python aplicação teste\app\schemas\chat.py>)
- [schemas/document.py](</C:\Projects\Python aplicação teste\app\schemas\document.py>)
- [routes.py](</C:\Projects\Python aplicação teste\app\api\routes.py>)
- repositorio/servico correspondente

## 9. Banco de dados

Bootstrap do banco:

- [compose.yaml](</C:\Projects\Python aplicação teste\compose.yaml>)
- [01-enable-vector.sql](</C:\Projects\Python aplicação teste\docker\postgres\init\01-enable-vector.sql>)
- [database.py](</C:\Projects\Python aplicação teste\app\repositories\database.py>)

Tabelas principais:

- `documents`
- `document_chunks`
- `chat_sessions`
- `chat_messages`

## 10. Como testar rapido

### Health

Abrir:

- [http://127.0.0.1:8010/health](http://127.0.0.1:8010/health)

### Swagger

Abrir:

- [http://127.0.0.1:8010/docs](http://127.0.0.1:8010/docs)

### Upload de documento

No Swagger:

1. abrir `POST /documents/upload`
2. clicar em `Try it out`
3. enviar um arquivo
4. executar

### Chat

Payload de exemplo:

```json
{
  "message": "Explique o conteudo principal do documento enviado.",
  "session_id": "teste-1"
}
```

## 11. Problemas comuns

### Docker nao sobe

Verifique:

- Docker Desktop aberto
- virtualizacao habilitada
- `validar-ambiente.bat`

### PostgreSQL nao conecta

Verifique:

- `docker compose ps`
- porta `5432`
- valor de `DATABASE_URL`

### API sobe mas fica em modo demo

Verifique:

- `OPENAI_API_KEY` ainda esta como `coloque_sua_chave_aqui`

### Upload funciona mas a resposta nao usa contexto

Verifique:

- se o documento foi indexado
- se a chave OpenAI esta correta
- se o `/documents` lista o arquivo
- se `RAG_MAX_DISTANCE` nao esta muito restritivo

## 12. Proximos passos recomendados

Para evoluir com seguranca:

1. adicionar autenticacao
2. adicionar testes automatizados
3. adicionar observabilidade e logs melhores
4. criar ambiente de homologacao
5. separar configuracoes de desenvolvimento e producao

## 13. Arquivos mais importantes para onboarding

- [README.md](</C:\Projects\Python aplicação teste\README.md>)
- [Makefile](</C:\Projects\Python aplicação teste\Makefile>)
- [main.py](</C:\Projects\Python aplicação teste\app\main.py>)
- [routes.py](</C:\Projects\Python aplicação teste\app\api\routes.py>)
- [assistant.py](</C:\Projects\Python aplicação teste\app\services\assistant.py>)
- [document_service.py](</C:\Projects\Python aplicação teste\app\services\document_service.py>)
- [retrieval.py](</C:\Projects\Python aplicação teste\app\services\retrieval.py>)
- [database.py](</C:\Projects\Python aplicação teste\app\repositories\database.py>)
- [scripts/setup-mac.sh](</C:\Projects\Python aplicação teste\scripts\setup-mac.sh>)
- [scripts/start-dev.sh](</C:\Projects\Python aplicação teste\scripts\start-dev.sh>)
