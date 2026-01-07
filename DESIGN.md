# RAG Sample — Design Document

## Overview

- **Purpose**: Production-ready Retrieval-Augmented Generation (RAG) web application to index local text files and PDFs, retrieve relevant contexts for queries, and synthesize answers using multiple LLM providers or fast text search fallback.
- **Goals**: 
  - Offline-first capability with simple text search provider
  - Professional REST API with FastAPI and OpenAPI documentation
  - ERCOT-styled static web UI for enterprise use
  - Safe defaults for production with security best practices
  - Multiple LLM provider support (OpenAI, Local, GPT4All, Simple)
  - Real-time index management without downtime
  - Support for 30+ file types including PDFs, logs, and source code

## Components

- Embedder (`rag_app/embedder.py`): wrapper for TF-IDF vectorization with configurable `max_features` and preprocessing. Provides `fit()` and `embed()` methods for building and transforming text into vectors.
- Indexer (`rag_app/indexer.py`): reads multiple file types recursively from a directory, fits `TfidfVectorizer`, and saves `data/index.joblib` with `docs`, `vectors`, `model_name`, and `vectorizer`. The `build_index()` function creates the index, and `load_index()` loads it.
  - **Supported file types**: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.log`, `.py`, `.java`, `.js`, `.ts`, `.html`, `.css`, `.yaml`, `.yml`, `.ini`, `.cfg`, `.conf`, `.err`, `.out`, `.sql`, `.sh`, `.bat`, `.ps1`, `.c`, `.cpp`, `.h`, `.pdf`, `.docx`, `.doc`
  - **PDF support**: extracts text from PDF files using PyPDF2, preserving page numbers with `[Page N]` markers for reference
  - **Word document support**: extracts text from `.docx`/`.doc` files using python-docx, preserving paragraph numbers with `[Para N]` markers
- Retriever (`rag_app/retriever.py`): wraps scikit-learn `NearestNeighbors` (cosine metric) and returns top-k matches with similarity scores. Handles `k > n_docs` gracefully by clamping k to the number of available documents. Provides a `from_index()` class method for convenient initialization.
- LLM wrapper (`rag_app/llm.py`): supports multiple LLM providers:
  - **OpenAI**: uses `gpt-3.5-turbo` model via chat completions API when `OPENAI_API_KEY` is present
  - **Local LLM**: uses `llama-cpp-python` with GGML models (configurable via `LOCAL_LLM_MODEL_PATH`)
  - **GPT4All**: uses the GPT4All Python package for local model inference
  - **Simple (Text Search)**: case-insensitive text search with **hyphen-tolerant matching** - searches "bowtie" will find "bow-tie", "bow tie", and "bowtie". Uses `normalize_query_for_search()` to build flexible regex patterns. Searches ALL indexed documents (not limited by TF-IDF scores), collects all matching results, returns file names, line numbers, and matching text snippets with 2+ lines of context. For PDFs shows page numbers, for Word docs shows paragraph numbers. Results are returned to client for client-side pagination.
  - The `answer_query()` function selects provider based on the `provider` parameter
- Config (`rag_app/config.py`): centralizes configuration values including `DATA_DIR`, `DEFAULT_INDEX_PATH`, `LLM_PROVIDER`, and `OPENAI_API_KEY` from environment variables.
- API (`rag_app/api.py`): FastAPI app exposing `/query` and `/health`, and serving static files from `rag_app/static` (root redirects to `/static/index.html`). The `/query` endpoint accepts optional `provider` and `index_path` parameters for runtime flexibility. Uses lifespan context manager for startup/shutdown events.
- Web UI (`rag_app/static/index.html`, `rag_app/static/demo.html`): Google-style landing and a debug demo that POSTs to `/query`.

## Data Flow

1. Build index: `python -m rag_app.cli index --data_dir data --index_path data/index.joblib`.
2. Client request: POST `/query` with JSON `{ q, per_page?, page?, provider?, index_path? }`.
3. Server validates request via Pydantic model (query length, provider validation).
4. Server loads index from `index_path` (if provided) or uses the globally loaded index.
5. Server transforms query using stored `vectorizer` → query vector.
6. **For simple provider**: Retriever returns ALL documents (not limited by TF-IDF scores), then `simple_synthesizer()` performs hyphen-tolerant regex search across all document text.
7. **For LLM providers**: Retriever returns top `per_page * 3` docs by cosine similarity, then passes to LLM for synthesis.
8. Server calculates pagination metadata (total results, total pages, current page).
9. Server returns `{ query, results, all_results, answer, pagination }` where `results` is current page and `all_results` is complete list.
10. Client displays results with pagination controls; for simple provider, pagination is client-side using `all_results`.

## API Spec

- GET `/health` → `{ status: "ok", index_loaded: bool, rebuilding: bool }`.
  - `index_loaded`: true if index is loaded in memory
  - `rebuilding`: true if index rebuild is currently in progress

- POST `/rebuild-index` → `{ status: "success", message: string, num_documents: int, index_path: string }`.
  - Rebuilds the index from all files in the data directory
  - Automatically reloads the index in memory without server restart
  - Returns 409 if rebuild already in progress
  - Returns 500 on failure with error details
  - **Usage**: Click "🔄 Rebuild Index" button in UI or POST to endpoint

- POST `/query` body `{ q: string, per_page?: int (default: 10), page?: int (default: 1), provider?: string (default: "simple"), index_path?: string }`.
  - **Query validation**: `q` must be 1-500 characters, trimmed of whitespace
  - Supported providers: `"openai"`, `"local"` (llama.cpp), `"gpt4all"`, `"simple"` (text search).
  - If `index_path` is provided, loads index dynamically from that path; otherwise uses globally loaded index.
  - **Simple provider behavior**: searches ALL indexed documents (ignores TF-IDF ranking for text matching), uses hyphen-tolerant regex so "bowtie" matches "bow-tie" and "bow tie", returns all matches with file names, line numbers (or page numbers for PDFs), and 2+ lines of context per result.
  - **LLM provider behavior**: retrieves top `per_page * 3` documents via TF-IDF cosine similarity, then passes contexts to LLM for answer synthesis.
  - **Pagination**: `per_page` controls results shown per page (1-100, default 10), `page` specifies current page number (1-based).

- GET `/view` query params `{ file: string, line?: int (default: 1), query?: string }`.
  - Returns HTML page with file contents, line numbers, syntax highlighting, and scrolls to specified line.
  - Highlights search term if `query` provided.
  - Security: only serves files within the `data/` directory.

- GET `/download` query params `{ file: string, page?: int (default: 1) }`.
  - For PDFs: returns file inline for browser display with page hint.
  - For Word docs: returns as attachment for download.
  - For other files: redirects to `/view` endpoint.
  - Security: only serves files within the `data/` directory.
- 200 response includes:
  - `query`: the original search query string
  - `results`: array of current page results `{id: string, score: float, text: string}`
  - `all_results`: complete array of ALL matching results (used by frontend for client-side pagination with simple provider)
  - `answer`: for simple provider - HTML-formatted search results with file links, line numbers, and highlighted matches; for LLM providers - synthesized answer text
  - `pagination`: metadata object `{ current_page: int, per_page: int, total_results: int, total_pages: int }`

## Index Management

### Building the Index
- **CLI Command**: `python -m rag_app.cli index --data_dir data --index_path data/index.joblib`
- **API Endpoint**: `POST /rebuild-index` (available during runtime)
- **UI Button**: Click **🔄 Rebuild Index** in the application header

### Workflow for Adding New Files
1. **Add Files**: Drop new `.txt`, `.pdf`, `.log`, or other supported files into the `data/` folder
2. **Rebuild Index**: 
   - **Option A (Recommended)**: Click **🔄 Rebuild Index** button in the UI
   - **Option B**: Call `POST /rebuild-index` API endpoint
   - **Option C**: Run CLI command and restart server
3. **Automatic Reload**: Index is automatically reloaded in memory (no server restart needed for Options A & B)
4. **Confirmation**: UI displays success message with document count
5. **Start Searching**: New files are immediately searchable

### Index Rebuild Features
- **On-Demand**: Trigger rebuild anytime without downtime
- **Progress Indication**: Button shows "⏳ Rebuilding..." during process
- **Concurrency Protection**: Prevents multiple simultaneous rebuilds
- **Status Tracking**: Health endpoint reports `rebuilding: true` during rebuild
- **Error Handling**: Clear error messages if rebuild fails
- **No Downtime**: Existing searches continue during rebuild

## Security & Operational Notes

- Development defaults: CORS allows all origins for convenience. Restrict CORS to allowed origins for production.
- Add optional API key (`X-API-Key`) middleware for production use.
- Do not commit secrets or large data; `.gitignore` is present to exclude logs and index files.
- For public exposure, serve the app behind TLS and a reverse proxy; add rate-limiting and authentication.
- **File access security**: `/view` and `/download` endpoints validate that requested files are within the `data/` directory using `os.path.commonpath()` check.
- **Query validation**: Pydantic models enforce max query length (500 chars), valid provider names, and pagination bounds.
- **Note on `index_path` parameter**: The `/query` endpoint accepts an optional `index_path` parameter that loads arbitrary joblib files. For production, consider removing this parameter or restricting to a whitelist of allowed paths, as joblib uses pickle serialization.
- LLM provider security:
  - OpenAI: requires API key via environment variable `OPENAI_API_KEY`
  - Local/GPT4All: ensure model files are from trusted sources and stored securely
  - Simple fallback: no external calls, safe for offline/air-gapped environments

## Repository Hygiene

- Ignore patterns: `data/*.log`, `data/*.dbg`, `data/*.txt`, `data/*.pdf`, `data/expsfcst_logs/`, `data/index.joblib` are ignored by `.gitignore`.
- **Data Privacy**: `.txt` and `.pdf` files in the `data/` folder are excluded from version control to protect IP information and sensitive documentation.
- Sample data files are not committed to the repository - users should add their own data files locally.
- If large files were previously committed, use `git-filter-repo` or BFG to purge them from history (coordinate before force-push).

## Deployment & Running

- Local quick start:
  ```bash
  python -m pip install -r requirements.txt
  python -m uvicorn rag_app.api:app --host 127.0.0.1 --port 8000
  ```
- Environment variables:
  - `RAG_INDEX_PATH`: path to index file (default: `data/index.joblib`)
  - `RAG_LLM_PROVIDER`: default LLM provider (default: `"simple"`)
  - `OPENAI_API_KEY`: OpenAI API key for OpenAI provider
  - `LOCAL_LLM_MODEL_PATH`: path to GGML model file for local LLM (default: `models/ggml-alpaca-7b-q4.bin`)
  - `RAG_LOG_LEVEL`: logging level (default: `INFO`)
  - `RAG_LOG_MAX_BYTES`: max log file size before rotation (default: 10 MB)
  - `RAG_LOG_BACKUP_COUNT`: number of rotated log files to keep (default: 5)
- Log files: `logs/rag_app.log` with automatic rotation when file reaches max size
- Dependencies for full functionality:
  - `PyPDF2`: required for PDF file indexing and search
  - `python-docx`: required for Word document (.docx) indexing and search
  - `openai`: required for OpenAI provider
  - `llama-cpp-python`: required for local LLM provider
  - `gpt4all`: required for GPT4All provider
- Containerization (outline): base python:3.12-slim, copy repo, install deps, expose 8000, run uvicorn.

## Testing

- Unit tests: indexer, retriever, embedder, and llm wrapper behaviors (mock OpenAI where needed).
- Integration: use FastAPI `TestClient` to exercise `/query` end-to-end with various providers (already used in smoke tests).
- Test different LLM providers: ensure fallback behavior works when external services are unavailable.
- Test edge cases: empty queries, k > n_docs, missing index files, invalid provider names.

## Monitoring & Metrics

- **File Logging**: Application logs are written to `logs/rag_app.log` with automatic rotation (10 MB max, 5 backups).
- **Console Logging**: Logs also appear in the terminal for real-time monitoring.
- **Log Levels**: Configure via `RAG_LOG_LEVEL` environment variable (DEBUG, INFO, WARNING, ERROR).
- Add structured logging and basic metrics (request counts, latency, index size). Prometheus exporter is recommended for container deployments.

## Scaling Considerations

- TF-IDF + sklearn is suitable for small prototypes. For larger corpora:
  - Replace TF-IDF embeddings with dense vector-model-based embeddings (e.g., sentence-transformers) and use ANN libraries (FAISS, Annoy) for retrieval performance.
  - Persist vector index and add incremental update paths.
  - Consider distributed/cloud vector databases for production scale (Pinecone, Weaviate, Qdrant).
- LLM provider selection:
  - OpenAI: best quality but requires API costs and network connectivity
  - Local (llama.cpp): full offline capability but requires local compute resources
  - GPT4All: balanced offline solution with reasonable quality
  - Simple (Text Search): fastest, no LLM required, performs case-insensitive text search with file/line references. Ideal for log file analysis, code search, and document lookup.

## UI/UX Features

### ERCOT Corporate Branding
- **Color Scheme**: ERCOT blue (#003087, #0066cc) with professional white/light gray background
- **Header**: Gradient blue header bar with "ERCOT" logo and "Trend Analysis & Search Tool" subtitle
- **Typography**: Segoe UI font family matching ERCOT corporate standards
- **Design**: Clean, professional interface matching trend.ercot.com aesthetic
- **Footer**: ERCOT copyright notice and confidentiality warning

### Search & Results Display
- **Pagination Controls**: Full pagination support with Previous/Next buttons for navigating through all search results
- **Results per Page**: Configurable setting (default: 10, max: 50) renamed from "Top-K" for clarity - controls number of findings shown on one page
- **Multi-line Context**: Each search result displays at least 2 lines (matching line + next line) for better context understanding
- **Clean PDF Display**: Page numbers shown in header `(Page X)` but `[Page X]` markers removed from displayed text for readability
- **Pagination Info**: Display showing "Showing results X-Y of Z (Page N of M)" for clear navigation context
- **Client-side Pagination**: For simple provider, all results are returned once and paginated client-side for optimal performance
- **Status Indicator**: Visible health check status with color-coded indicators (green=ready, red=error)
- **Smart Result Display**: Combined text truncated at 400 characters with ellipsis, highlighted search terms with `<mark>` tags
- **"I'm Feeling Lucky"**: Quick test button with randomized sample queries matching EMS log data (RPC, ERROR, WARN, plugin, HABITAT, client handle, ERCOT, database)
- **Responsive Design**: Professional ERCOT-styled theme optimized for desktop and mobile viewing
- **File Links**: Clickable file names with line/page numbers for direct navigation to source
- **Smooth Scrolling**: Auto-scroll to results when changing pages for better navigation experience
- **Hover Effects**: Enhanced button and result item hover states for better interactivity

## Next Steps / Recommendations

### Production Readiness
1. **Security Hardening**: 
   - Restrict CORS to specific allowed origins (currently allows all for development)
   - Add API key middleware for authentication (`X-API-Key` header)
   - Implement rate limiting to prevent abuse
   - Deploy behind TLS/HTTPS with reverse proxy (nginx, Caddy)
   - Add request validation and sanitization

2. **CI/CD Pipeline**: 
   - Add `.github/workflows` for automated testing
   - Run linting (flake8, black) and tests on pull requests
   - Build and publish Docker images to container registry
   - Automated deployment to staging/production environments

3. **Performance Optimization**:
   - Replace TF-IDF with dense embeddings (sentence-transformers) for better semantic search
   - Implement ANN libraries (FAISS, Annoy) for faster retrieval on large corpora
   - Add caching layer (Redis) for repeated queries to reduce LLM costs/latency
   - Consider distributed vector databases (Pinecone, Weaviate, Qdrant) for production scale

4. **Monitoring & Observability**:
   - Add structured logging with log levels and correlation IDs
   - Implement Prometheus metrics exporter (request counts, latency, index size)
   - Set up alerting for errors and performance degradation
   - Add distributed tracing (OpenTelemetry) for debugging

5. **Enhanced Features**:
   - User authentication and multi-tenant support
   - Query history and saved searches
   - Advanced filters (file type, date range, author)
   - Highlighting search terms in original documents
   - Export results to CSV/JSON
   - Scheduled index rebuilds (cron jobs)

6. **Documentation**:
   - API documentation with Swagger/OpenAPI UI (already available at `/docs`)
   - Deployment guides for cloud providers (AWS, Azure, GCP)
   - Performance benchmarks comparing different LLM providers
   - Video tutorials and screencasts

### Development Improvements
- Add comprehensive unit tests for all modules
- Integration tests with TestClient for end-to-end coverage
- Test different LLM providers with mocked responses
- Test edge cases: empty queries, k > n_docs, missing index files, invalid providers
- Load testing with locust or k6
- Add type hints and run mypy for type checking

## Architecture Diagram

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP POST /query
       │ { q, per_page, page, provider }
       ▼
┌─────────────────────────┐
│   FastAPI Server        │
│  (rag_app/api.py)       │
├─────────────────────────┤
│ • CORS middleware       │
│ • Static file serving   │
│ • Health endpoint       │
│ • Query validation      │
│ • /view file viewer     │
│ • /download endpoint    │
└──────┬──────────────────┘
       │
       ├────────────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│   Indexer    │  │  Retriever   │
│ (indexer.py) │  │(retriever.py)│
├──────────────┤  ├──────────────┤
│ • Load index │  │ • Cosine     │
│ • Vectorizer │  │   similarity │
│ • PDF/DOCX   │  │ • Top-K NN   │
└──────┬───────┘  └──────┬───────┘
       │                 │
       │                 ▼
       │          Retrieved contexts
       │                 │
       └─────────────────┤
                         ▼
                  ┌──────────────┐
                  │  LLM Module  │
                  │   (llm.py)   │
                  ├──────────────┤
                  │ • OpenAI API │
                  │ • Local LLM  │
                  │ • GPT4All    │
                  │ • Simple*    │
                  └──────┬───────┘
                         │
                         ▼
                    { answer }

* Simple provider uses hyphen-tolerant
  regex search across ALL documents
```

---
Generated and committed by the workspace assistant.
