![AI Assistant Backend](https://ignaciofigueroa.dev/images/og-assistant.png)

# 🤖 assistant

> My portfolio's AI backend. Completely useless to you. It only talks about me — and honestly, it does a better job of it than I do.

## What is this

A RAG backend built with FastAPI that answers questions about Ignacio Figueroa.

Ask it about my projects → it answers. Ask it about the meaning of life → it tells you to contact me directly. Scope enforced at the prompt level, not by good faith.

## Stack

| Tool                          | Why                                                              |
| ----------------------------- | ---------------------------------------------------------------- |
| **FastAPI**                   | Because Flask is for people who haven't decided yet              |
| **Groq + Llama 3.3 70B**      | Replies faster than I do in a standup                            |
| **pgvector + Neon**           | Vector search without running a database cluster in my apartment |
| **HuggingFace Inference API** | Embeddings without melting the server                            |
| **uv**                        | Dependency management from this century                          |
| **Docker**                    | "Works on my machine" — shipped                                  |

## How it works

```
User asks something about Nacho
          ↓
Question converted to an embedding vector
          ↓
Cosine similarity search against Neon (pgvector)
          ↓
Most relevant context chunks injected into the prompt
          ↓
Groq streams the response token by token
          ↓
You know more about me than my own mother does
```

## Endpoints

| Method | Path    | What it does                              |
| ------ | ------- | ----------------------------------------- |
| `POST` | `/chat` | Ask something about Nacho. Get an answer. |
| `GET`  | `/docs` | Swagger UI — because we're professionals  |

## Run locally

```bash
# Install dependencies
uv sync

# Start the server
uv run uvicorn main:app --reload
```

The server runs at `http://localhost:8000` by default.
Swagger UI at `http://localhost:8000/docs` — use it.

## Environment variables

```env
GROQ_API_KEY=
HUGGINGFACE_API_KEY=
DATABASE_URL=        # Neon connection string with pgvector enabled
```

## License

MIT. Do whatever you want with it.
Just don't ask the assistant for code — it'll redirect you to me, and I'm busy.
