# BARGEHAM

**Intelligent Document Processing Platform with Knowledge Graph**

BARGEHAM is a production-grade, open-source platform for managing, processing,
understanding, and extracting knowledge from documents — with first-class support
for Persian (Farsi), English, and RTL layouts.

> "اسناد را بگیر، بگرد، بپرس و بدان."

| Feature | Status |
|---|---|
| Document Management | ✅ Core |
| Persian + English OCR | ✅ PaddleOCR + Tesseract |
| Hybrid Search (FTS + Vector + Metadata) | ✅ PostgreSQL + pgvector |
| AI Document Assistant with citations | ✅ RAG pipeline |
| Structured data extraction | ✅ Configurable pipeline |
| Persian RTL web UI | ✅ Tailwind `rtl:` variant |
| Single-command deployment | ✅ Docker Compose |
| Type-safe full-stack | ✅ SQLModel + Pydantic + TypeScript |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/<your-username>/BARGEHAM.git
cd BARGEHAM

# 2. Start everything (PostgreSQL, Redis, MinIO, backend, frontend, OCR workers)
docker compose up -d

# 3. Create admin user
docker compose exec backend bash
python -m scripts.init_db

# 4. Open
http://localhost:3000
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend   │     │   Backend    │     │  Worker Nodes   │
│  Next.js     │────▶│  FastAPI     │────▶│  (Celery)       │
│  +TS+Tailwind│     │  +SQLModel   │     │  PaddleOCR      │
│  RTL support │     │  +Pydantic   │     │  Tesseract      │
└──────┬───────┘     └──────┬───────┘     │  Embedding      │
       │                    │              │  LLM            │
       │     ┌───────────────┘              └─────────────────┘
       │     │
┌──────┴─────┴─────────────────────┐
│  PostgreSQL 16 + pgvector        │
│  (metadata + FTS + vector)       │
└──────────────────────────────────┘
         │
┌────────┴───────────────┐
│  Redis (cache + queue) │
└────────────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for the full design.

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI + SQLModel + Pydantic v2 | Async-native, type-safe, auto OpenAPI docs |
| Database | PostgreSQL 16 + pgvector | FTS + vector + metadata in ONE database |
| Storage | MinIO (S3-compatible) | Self-hosted, high performance |
| Queue | Celery + Redis | Background OCR/embedding/indexing |
| OCR | PaddleOCR PP-OCRv5 + Tesseract fas | Multilingual + dedicated Persian model |
| AI | OpenRouter + local models + sentence-transformers | Multi-provider abstraction |
| Frontend | Next.js 15 + TypeScript + Tailwind v4 | SSR, RTL variant, type-safe |
| Testing | Pytest + Playwright | Unit, integration, E2E |
| CI/CD | GitHub Actions + Docker | Automated on every PR |

## License

[Apache-2.0](LICENSE)