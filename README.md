🤖 assistant

> My portfolio's AI backend. Completely useless to you. It only talks about me (I hope not too much).

## What is this

A RAG backend built with FastAPI that answers questions about me (Ignacio Figueroa).
If you ask it about the meaning of life, it will tell you to contact me directly.

## Stack

- **FastAPI** — because Flask is for people who don't know what they want
- **Groq + Llama 3.3 70B** — replies faster than me in a standup
- **pgvector + Neon** — searches vectors like it knows what it's doing
- **HuggingFace Inference API** — embeddings without melting the server
- **uv** — dependency management from this century
- **Docker** — "works on my machine" solved forever

## How it works

```
User asks something
       ↓
Embedding generated from the question
       ↓
Most relevant chunks retrieved from Neon by cosine similarity
       ↓
Context injected into the prompt
       ↓
Groq streams the response token by token
       ↓
You learn more about me than his own mother knows
```

## Endpoints

| Method | Path    | Description                             |
| ------ | ------- | --------------------------------------- |
| POST   | `/chat` | Ask something about Nacho               |
| GET    | `/docs` | Swagger UI, because we're professionals |

## Run locally

```bash
uv sync
uv run uvicorn main:app --reload
```

## License

Do whatever you want. Just don't ask the assistant for code.
