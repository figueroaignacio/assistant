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
| **Gemini 2.5 Flash**          | Replies faster than I do in a standup                            |
| **LangChain**                 | Tool calling and streaming without hand-rolling the loop         |
| **pgvector + Neon**           | Vector search without running a database cluster in my apartment |
| **HuggingFace Inference API** | Embeddings without melting the server                            |
| **Payload CMS**               | Where the projects and experience actually live                  |
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
Gemini answers — calling tools (projects, experience,
contact, job-match) against Payload CMS when it needs
live data
          ↓
Response streams back token by token
          ↓
You know more about me than my own mother does
```

## Endpoints

| Method | Path                    | What it does                                      | Rate limit |
| ------ | ----------------------- | ------------------------------------------------- | ---------- |
| `GET`  | `/`                     | ASCII banner and uptime. Peak engineering.        | —          |
| `POST` | `/chat`                 | Ask something about Nacho. Get a streamed answer. | 10/min     |
| `GET`  | `/portfolio/projects`   | Published projects, `?locale=en\|es`               | —          |
| `GET`  | `/portfolio/experience` | Work experience, `?locale=en\|es`                  | —          |
| `POST` | `/portfolio/summarize`  | Summarize a Payload Lexical body                  | 5/min      |
| `GET`  | `/docs`                 | Swagger UI — because we're professionals          | —          |

`POST /chat` returns a raw `text/plain` token stream (not SSE frames), so read it
with `fetch` + `response.body.getReader()`.

## Run locally

```bash
# Install dependencies
uv sync

# Build the knowledge base from Payload CMS (full rebuild, safe to re-run)
uv run python scripts/ingest.py

# Start the server
uv run uvicorn main:app --reload
```

The server runs at `http://localhost:8000` by default.
Swagger UI at `http://localhost:8000/docs` — use it.

## Environment variables

```env
DATABASE_URL=        # Neon connection string with pgvector enabled
GEMINI_API_KEY=      # or GOOGLE_API_KEY, which takes precedence
HF_TOKEN=            # HuggingFace Inference API token
PAYLOAD_CMS_URL=     # Payload CMS API base, e.g. https://site.com/api
FRONTEND_URL=        # Allowed CORS origins, comma-separated
```

## License

MIT. Do whatever you want with it.
Just don't ask the assistant for code — it'll redirect you to me, and I'm busy.
