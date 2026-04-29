# Contributing

Obrigado por contribuir com este projeto.

## Objetivo

O projeto implementa um assistente contábil com:

- `FastAPI` para a API
- `LangChain` para o fluxo de chat
- `OpenAI` para chat e embeddings
- `PostgreSQL + pgvector` para persistência e busca vetorial

Antes de alterar o código, leia também:

- [README.md](./README.md)
- [docs/GUIA_DO_COLEGA.md](./docs/GUIA_DO_COLEGA.md)

## Setup local

### Windows

```powershell
Set-Location "C:\Projects\Python aplicação teste"
.\validar-ambiente.bat
.\abrir-tudo.bat
```

### macOS

```bash
cd "/caminho/do/projeto"
chmod +x ./*.command ./scripts/*.sh
./setup-mac.command
./validar-ambiente.command
./abrir-tudo.command
```

## Estrutura principal

- `app/api`: endpoints HTTP
- `app/core`: configuração e exceções
- `app/repositories`: acesso ao PostgreSQL
- `app/schemas`: contratos da API
- `app/services`: regras de negócio, parser, embeddings, retrieval e chat
- `docker/`: bootstrap do PostgreSQL com pgvector
- `scripts/`: automações para Windows e macOS
- `docs/`: documentação de onboarding

## Fluxo de contribuição

1. Entenda primeiro qual camada será alterada.
2. Faça mudanças pequenas e focadas.
3. Atualize a documentação se o fluxo de uso ou setup mudar.
4. Se adicionar variável nova de ambiente, atualize `.env.example`.
5. Se alterar contrato da API, atualize os schemas e o README.

## Regras práticas

- Não commitar `.env`, banco local, logs ou `.venv`.
- Não commitar chaves reais da OpenAI.
- Não commitar documentos internos sensíveis por engano.
- Prefira mudanças pequenas e fáceis de revisar.
- Preserve `FastAPI + LangChain` como base da aplicação.

## Quando mexer em cada arquivo

### Mudar comportamento do assistente

- `app/services/assistant.py`

### Mudar parsing de documentos

- `app/services/document_parser.py`

### Mudar chunking ou indexação

- `app/services/document_service.py`

### Mudar busca vetorial ou confiança

- `app/services/retrieval.py`

### Mudar banco ou schema

- `app/repositories/database.py`
- `app/repositories/document_repository.py`
- `app/repositories/chat_repository.py`

### Mudar endpoints

- `app/api/routes.py`
- `app/schemas/*.py`

## Checklist antes de abrir PR

- O projeto sobe localmente
- O Docker/PostgreSQL está funcional
- A API responde em `/health`
- O fluxo principal não foi quebrado
- A documentação relevante foi atualizada
- Nenhum arquivo sensível entrou no commit

## Validação mínima recomendada

1. Validar ambiente

```bash
# Windows
.\validar-ambiente.bat

# macOS
./validar-ambiente.command
```

2. Subir a aplicação

```bash
# Windows
.\abrir-tudo.bat

# macOS
./abrir-tudo.command
```

3. Testar endpoints principais

- `GET /health`
- `GET /config`
- `POST /documents/upload`
- `GET /documents`
- `POST /chat`
- `GET /sessions/{session_id}/history`

## Licença

Este repositório está atualmente sob a licença MIT. Se a equipe decidir mudar a política de uso, atualize também o arquivo `LICENSE`.
