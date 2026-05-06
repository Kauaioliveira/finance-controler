# Backend

Camada de API da aplicação.

Stack:

- `FastAPI`
- `LangChain`
- `PostgreSQL + pgvector`
- `OpenAI`

Rodar localmente:

```powershell
pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010 --reload
```
