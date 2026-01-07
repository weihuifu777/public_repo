from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import html
import logging

from .indexer import load_index, build_index, extract_pdf_text
from .retriever import Retriever
from .llm import answer_query
from .config import MAX_QUERY_LENGTH, MAX_RESULTS_PER_PAGE, DEFAULT_RESULTS_PER_PAGE

# Configure logging
logger = logging.getLogger(__name__)

INDEX_PATH = os.environ.get("RAG_INDEX_PATH", os.path.join(os.getcwd(), "data", "index.joblib"))
DATA_DIR = os.environ.get("RAG_DATA_DIR", os.path.join(os.getcwd(), "data"))

# Application state
app_state = {"index": None, "retriever": None, "rebuilding": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load index
    try:
        logger.info(f"Loading index from {INDEX_PATH}")
        app_state["index"] = load_index(INDEX_PATH)
        app_state["retriever"] = Retriever.from_index(app_state["index"])
        num_docs = len(app_state["index"].get("docs", []))
        logger.info(f"Index loaded successfully: {num_docs} documents")
    except Exception as e:
        logger.warning(f"Failed to load index: {e}. Server will start without index.")
        app_state["index"] = None
        app_state["retriever"] = None
    yield
    # Shutdown: cleanup if needed
    logger.info("Shutting down RAG API server")
    app_state["index"] = None
    app_state["retriever"] = None


app = FastAPI(title="RAG Sample API", lifespan=lifespan)

# Allow all origins for simplicity; adjust in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Set to False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=500, description="Search query")
    per_page: Optional[int] = Field(default=DEFAULT_RESULTS_PER_PAGE, ge=1, le=MAX_RESULTS_PER_PAGE, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    provider: Optional[str] = Field(default="simple", description="LLM provider")
    index_path: Optional[str] = Field(default=None, description="Custom index path")
    
    @field_validator('q')
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be empty')
        if len(v) > MAX_QUERY_LENGTH:
            raise ValueError(f'Query exceeds maximum length of {MAX_QUERY_LENGTH} characters')
        return v
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        valid_providers = {'simple', 'openai', 'local', 'gpt4all'}
        if v.lower() not in valid_providers:
            raise ValueError(f'Invalid provider. Must be one of: {valid_providers}')
        return v.lower()


@app.get("/health")
def health():
    status = {
        "status": "ok", 
        "index_loaded": app_state["index"] is not None,
        "rebuilding": app_state.get("rebuilding", False),
        "num_documents": len(app_state["index"].get("docs", [])) if app_state["index"] else 0
    }
    logger.debug(f"Health check: {status}")
    return status


@app.post("/rebuild-index")
def rebuild_index():
    """Rebuild the index from files in the data directory."""
    if app_state.get("rebuilding", False):
        logger.warning("Rebuild request rejected: already in progress")
        raise HTTPException(status_code=409, detail="Index rebuild already in progress")
    
    try:
        app_state["rebuilding"] = True
        logger.info(f"Starting index rebuild from {DATA_DIR}")
        
        # Build new index
        new_index = build_index(DATA_DIR, INDEX_PATH)
        
        # Update application state with new index
        app_state["index"] = new_index
        app_state["retriever"] = Retriever.from_index(new_index)
        
        num_docs = len(new_index.get('docs', []))
        logger.info(f"Index rebuilt successfully: {num_docs} documents")
        
        return {
            "status": "success",
            "message": f"Index rebuilt successfully with {num_docs} documents",
            "num_documents": num_docs,
            "index_path": INDEX_PATH
        }
    except Exception as e:
        logger.error(f"Failed to rebuild index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild index: {str(e)}")
    finally:
        app_state["rebuilding"] = False


@app.post("/query")
def query(req: QueryRequest):
    logger.info(f"Query request: q='{req.q[:50]}...', provider={req.provider}, page={req.page}")
    index_path = req.index_path or INDEX_PATH
    try:
        if req.index_path:
            index = load_index(index_path)
            retriever = Retriever.from_index(index)
        else:
            if app_state["index"] is None:
                raise HTTPException(status_code=500, detail="Index not loaded on server")
            index = app_state["index"]
            retriever = app_state["retriever"]

        vec = index.get('vectorizer')
        if vec is None:
            raise HTTPException(status_code=500, detail="Index missing vectorizer; re-build index")

        qv = vec.transform([req.q]).toarray()

        # IMPORTANT:
        # - For LLM providers, we intentionally limit context size.
        # - For the 'simple' provider, we must search across ALL documents; client-side
        #   pagination expects the answer HTML to include all matches.
        if req.provider == 'simple':
            num_docs = len(index['docs'])
            idxs, sims = retriever.query(qv, top_k=num_docs)
            all_results = [{"id": index['docs'][i]['id'], "score": s, "text": index['docs'][i]['text']} for i, s in zip(idxs, sims)]

            # Generate the answer from ALL docs (not just the first page), so variants like
            # 'bowtie' vs 'bow-tie' are found even when TF-IDF similarity is low.
            contexts = [r['text'] for r in all_results]
            doc_ids = [r['id'] for r in all_results]
            answer = answer_query(req.q, contexts, provider=req.provider, doc_ids=doc_ids, top_k=req.per_page)
        else:
            idxs, sims = retriever.query(qv, top_k=req.per_page * 3)
            all_results = [{"id": index['docs'][i]['id'], "score": s, "text": index['docs'][i]['text']} for i, s in zip(idxs, sims)]
            contexts = [r['text'] for r in all_results]
            doc_ids = [r['id'] for r in all_results]
            answer = answer_query(req.q, contexts, provider=req.provider, doc_ids=doc_ids, top_k=req.per_page)

        # Calculate pagination (server-side pagination for the `results` field)
        total_results = len(all_results)
        total_pages = (total_results + req.per_page - 1) // req.per_page  # Ceiling division
        page = max(1, min(req.page, total_pages if total_pages > 0 else 1))  # Ensure valid page

        start_idx = (page - 1) * req.per_page
        end_idx = start_idx + req.per_page
        page_results = all_results[start_idx:end_idx]

        return {
            "query": req.q,
            "results": page_results,
            "all_results": all_results,  # Return all results for frontend pagination
            "answer": answer,
            "pagination": {
                "current_page": page,
                "per_page": req.per_page,
                "total_results": total_results,
                "total_pages": total_pages
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static demo files located in rag_app/static
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/download")
def download_file(
    file: str = Query(..., description="Path to file to download/view"),
    page: int = Query(1, description="Page number for PDFs (used for navigation hint)")
):
    """Download or view a file directly (opens PDFs in browser's native viewer)."""
    # Security: only allow files within the data directory
    data_dir = os.path.abspath(os.path.join(os.getcwd(), "data"))
    file_path = os.path.abspath(file)

    try:
        common = os.path.commonpath([data_dir, file_path])
    except Exception:
        common = ""

    if common != data_dir:
        logger.warning(f"Access denied: attempted to access file outside data directory: {file}")
        raise HTTPException(status_code=403, detail="Access denied: file outside data directory")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file}")
    
    file_name = os.path.basename(file_path)
    
    # Determine content type based on file extension
    file_lower = file_path.lower()
    
    if file_lower.endswith('.pdf'):
        media_type = "application/pdf"
        # Return PDF inline so browser displays it (not downloads)
        headers = {"Content-Disposition": f"inline; filename=\"{file_name}\""}
        logger.info(f"Serving PDF file: {file_name}, page hint: {page}")
        return FileResponse(
            file_path, 
            media_type=media_type, 
            filename=file_name,
            headers=headers
        )
    elif file_lower.endswith('.docx'):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        # Word docs typically download rather than display inline
        headers = {"Content-Disposition": f"attachment; filename=\"{file_name}\""}
        logger.info(f"Serving Word document: {file_name}")
        return FileResponse(
            file_path, 
            media_type=media_type, 
            filename=file_name,
            headers=headers
        )
    elif file_lower.endswith('.doc'):
        media_type = "application/msword"
        headers = {"Content-Disposition": f"attachment; filename=\"{file_name}\""}
        logger.info(f"Serving Word document (legacy): {file_name}")
        return FileResponse(
            file_path, 
            media_type=media_type, 
            filename=file_name,
            headers=headers
        )
    else:
        # For other files, redirect to the text view
        import urllib.parse
        return RedirectResponse(url=f"/view?file={urllib.parse.quote(file)}&line=1")


@app.get("/view", response_class=HTMLResponse)
def view_file(
    file: str = Query(..., description="Path to file to view"),
    line: int = Query(1, description="Line number to highlight"),
    query: str = Query("", description="Search term to highlight")
):
    """View a file in the browser with line highlighting."""
    # Security: only allow files within the data directory
    data_dir = os.path.abspath(os.path.join(os.getcwd(), "data"))
    file_path = os.path.abspath(file)

    try:
        common = os.path.commonpath([data_dir, file_path])
    except Exception:
        common = ""

    if common != data_dir:
        raise HTTPException(status_code=403, detail="Access denied: file outside data directory")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file}")
    
    # Read file content
    try:
        if file_path.lower().endswith('.pdf'):
            content = extract_pdf_text(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
    
    # Build HTML with line numbers and highlighting
    lines = content.split('\n')
    file_name = os.path.basename(file_path)
    
    import re
    query_raw = query.strip() if query else ""
    
    lines_html = []
    for i, line_text in enumerate(lines, start=1):
        escaped_line = html.escape(line_text)
        
        # Highlight search term if provided
        if query_raw:
            escaped_line = re.sub(
                f'({re.escape(query_raw)})',
                r'<mark>\1</mark>',
                escaped_line,
                flags=re.IGNORECASE
            )
        
        highlight_class = ' class="highlight"' if i == line else ''
        line_id = f'id="L{i}"' if i == line else ''
        lines_html.append(f'<tr{highlight_class} {line_id}><td class="line-no">{i}</td><td class="line-content">{escaped_line}</td></tr>')
    
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{html.escape(file_name)} - Line {line}</title>
    <style>
        :root {{
            --bg: #1e1e1e;
            --text: #d4d4d4;
            --line-no: #858585;
            --highlight-bg: #264f78;
            --mark-bg: #515c6a;
        }}
        body {{
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
        }}
        .header {{
            position: sticky;
            top: 0;
            background: #252526;
            padding: 10px 20px;
            border-bottom: 1px solid #3c3c3c;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 16px;
            font-weight: normal;
        }}
        .header .info {{
            color: var(--line-no);
            font-size: 13px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        tr:hover {{
            background: #2a2d2e;
        }}
        tr.highlight {{
            background: var(--highlight-bg) !important;
        }}
        .line-no {{
            color: var(--line-no);
            text-align: right;
            padding: 0 15px;
            user-select: none;
            vertical-align: top;
            min-width: 50px;
            border-right: 1px solid #3c3c3c;
        }}
        .line-content {{
            padding: 0 15px;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        mark {{
            background: #515c6a;
            color: #ffffff;
            padding: 1px 3px;
            border-radius: 2px;
        }}
        .back-link {{
            color: #3794ff;
            text-decoration: none;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 {html.escape(file_name)}</h1>
        <div class="info">
            Line {line} of {len(lines)} | 
            <a href="javascript:history.back()" class="back-link">← Back to search</a>
        </div>
    </div>
    <table>
        {''.join(lines_html)}
    </table>
    <script>
        // Scroll to highlighted line
        const target = document.getElementById('L{line}');
        if (target) {{
            target.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
    </script>
</body>
</html>'''
    
    return HTMLResponse(content=html_content)
