import os
import re
from typing import List, Optional
import logging

from .config import OPENAI_API_KEY
from .indexer import extract_pdf_text  # Import from indexer to avoid duplication

# Configure logging
logger = logging.getLogger(__name__)

# Path to a local GGML model (llama.cpp / llama-cpp-python). Override via env var.
LOCAL_LLM_MODEL_PATH = os.environ.get("LOCAL_LLM_MODEL_PATH", os.path.join(os.getcwd(), "models", "ggml-alpaca-7b-q4.bin"))

# Maximum query length to prevent abuse
MAX_QUERY_LENGTH = int(os.environ.get("RAG_MAX_QUERY_LENGTH", "500"))


def normalize_query_for_search(query: str) -> str:
    """Create a regex pattern that matches query with optional hyphens/spaces between words.
    
    For example: 'bowtie' matches 'bowtie', 'bow-tie', 'bow tie'
                 'bow-tie' matches 'bowtie', 'bow-tie', 'bow tie'
    """
    # Build a regex that matches the query even if optional hyphens/spaces appear.
    # Example: "bowtie" matches "bowtie", "bow-tie", and "bow tie".
    #
    # IMPORTANT: treat only literal '-' and whitespace as separators.
    original_lower = query.lower()
    pattern_parts: List[str] = []
    for char in original_lower:
        if char == '-' or char.isspace():
            continue
        pattern_parts.append(re.escape(char))
    
    # Join with optional hyphen/space between characters
    # But we need smarter logic - only allow separators where they make sense
    # Simple approach: allow optional [-\s]* between any two letters
    if len(pattern_parts) > 1:
        result_pattern = pattern_parts[0]
        for part in pattern_parts[1:]:
            result_pattern += r'[-\s]?' + part
        return result_pattern
    return re.escape(query)


def simple_synthesizer(query: str, contexts: List[str], doc_ids: Optional[List[str]] = None, top_k: int = 10) -> str:
    """Simple text search function: finds all matching lines (case insensitive) in contexts.
    Returns HTML with file names, line numbers, and clickable links where matches are found.
    
    Args:
        query: Search string
        contexts: List of document texts to search
        doc_ids: Optional list of document IDs/file paths
        top_k: Number of findings shown on one page (results per page)
    """
    import html
    import urllib.parse
    
    if not query.strip():
        return "No search query provided."
    
    query_lower = query.lower()
    # Create flexible pattern to match with/without hyphens (e.g., 'bowtie' matches 'bow-tie')
    search_pattern = normalize_query_for_search(query)
    search_regex = re.compile(search_pattern, re.IGNORECASE)
    results = []
    
    for i, text in enumerate(contexts):
        # Get file name from doc_ids if available, otherwise use index
        file_name = doc_ids[i] if doc_ids and i < len(doc_ids) else f"Document {i+1}"
        
        # Handle PDF files - extract text on-the-fly if needed
        if file_name.lower().endswith('.pdf') and os.path.exists(file_name):
            text = extract_pdf_text(file_name)
        
        lines = text.split('\n')
        for line_no, line in enumerate(lines, start=1):
            # Use regex pattern for flexible matching (handles hyphens)
            if search_regex.search(line):
                # Collect ALL matches, not just top_k
                # Show context: current line + next line (at least 2 lines per result)
                context_lines = []
                
                # Helper function to clean page markers from display
                def clean_page_marker(text):
                    """Remove [Page X] prefix from line for cleaner display"""
                    return re.sub(r'^\[Page \d+\]\s*', '', text)
                
                # Current line (the match) - clean page marker
                current_line = clean_page_marker(line.strip())
                context_lines.append(current_line)
                
                # Add next line if available - clean page marker
                if line_no < len(lines):
                    next_line = clean_page_marker(lines[line_no].strip())  # line_no is already the next index (0-based vs 1-based)
                    if next_line:  # Only add if not empty
                        context_lines.append(next_line)
                
                # Combine lines with line break, truncate if too long
                combined_text = '\n'.join(context_lines)
                if len(combined_text) > 400:
                    combined_text = combined_text[:400] + '...'
                
                # Escape HTML and highlight the query match
                escaped_text = html.escape(combined_text)
                # Case-insensitive highlight - use same flexible pattern
                highlighted_text = search_regex.sub(
                    r'<mark>\g<0></mark>',
                    escaped_text
                )
                
                # Preserve line breaks in HTML
                highlighted_text = highlighted_text.replace('\n', '<br>')
                
                # Create link to view endpoint for browser viewing
                abs_path = os.path.abspath(file_name)
                # URL encode the path and query for the view endpoint
                view_url = f"/view?file={urllib.parse.quote(abs_path)}&line={line_no}&query={urllib.parse.quote(query)}"
                
                # For PDFs, extract page number if present (from original line, not cleaned)
                page_info = ""
                page_num = 1
                para_num = 1
                is_pdf = file_name.lower().endswith('.pdf')
                is_docx = file_name.lower().endswith(('.docx', '.doc'))
                
                if '[Page ' in line:
                    import re as re2
                    page_match = re2.search(r'\[Page (\d+)\]', line)
                    if page_match:
                        page_num = int(page_match.group(1))
                        page_info = f" (Page {page_num})"
                elif '[Para ' in line:
                    import re as re2
                    para_match = re2.search(r'\[Para (\d+)\]', line)
                    if para_match:
                        para_num = int(para_match.group(1))
                        page_info = f" (Para {para_num})"
                elif '[Table ' in line:
                    import re as re2
                    table_match = re2.search(r'\[Table (\d+)\]', line)
                    if table_match:
                        page_info = f" (Table {table_match.group(1)})"
                
                # For PDFs/Word docs, add a link to open the actual document
                doc_link = ""
                if is_pdf:
                    pdf_url = f"/download?file={urllib.parse.quote(abs_path)}&page={page_num}"
                    doc_link = f' <a href="{pdf_url}#page={page_num}" target="_blank" class="pdf-link" title="Open PDF in browser">📖 Open PDF</a>'
                elif is_docx:
                    docx_url = f"/download?file={urllib.parse.quote(abs_path)}"
                    doc_link = f' <a href="{docx_url}" target="_blank" class="pdf-link" title="Download Word document">📝 Open Doc</a>'
                
                results.append(
                    f'<div class="result-item">'
                    f'<div class="result-file">'
                    f'<a href="{view_url}" target="_blank" title="View extracted text at line {line_no}">'
                    f'📄 {html.escape(os.path.basename(file_name))}</a>'
                    f'<span class="result-location"> : Line {line_no}{page_info}</span>'
                    f'{doc_link}'
                    f'</div>'
                    f'<div class="result-text">{highlighted_text}</div>'
                    f'</div>'
                )
    
    if not results:
        return f"No matches found for '{html.escape(query)}'."
    
    total_matches = len(results)
    truncated_msg = f" (showing {min(top_k, total_matches)} per page)" if total_matches > top_k else ""
    header = f'<div class="search-header">Search results for "<strong>{html.escape(query)}</strong>" ({total_matches} total matches{truncated_msg})</div>'
    return header + '\n'.join(results) 

def openai_completion(prompt: str) -> str:
    try:
        from openai import OpenAI
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI call failed: {e}"


def local_llm_completion(prompt: str, model_path: Optional[str] = None) -> str:
    """Attempt to run a local LLM via llama-cpp-python using a GGML model file.
    Falls back to an explanatory error message if the runtime or model is unavailable.
    """
    mp = model_path or LOCAL_LLM_MODEL_PATH
    try:
        from llama_cpp import Llama
    except Exception as e:
        return f"Local LLM unavailable (llama-cpp-python not installed): {e}"

    if not os.path.exists(mp):
        return f"Local model not found at {mp}. Download a GGML model and set LOCAL_LLM_MODEL_PATH."

    try:
        llm = Llama(model_path=mp)
        resp = llm.create_completion(prompt=prompt, max_tokens=256)
        # response shape: {'choices': [{'text': '...'}], ...}
        return resp.get("choices", [{}])[0].get("text", "").strip()
    except Exception as e:
        return f"Local LLM call failed: {e}"


def local_gpt4all_completion(prompt: str, model_name: Optional[str] = None, model_path: Optional[str] = None) -> str:
    """Attempt to run a local LLM via the GPT4All Python package.
    Falls back to an explanatory error message if the runtime or model is unavailable.
    """
    try:
        from gpt4all import GPT4All
    except Exception as e:
        return f"GPT4All unavailable (gpt4all package not installed): {e}"

    try:
        if model_path and os.path.exists(model_path):
            model = GPT4All(model_path=model_path)
        elif model_name:
            model = GPT4All(model_name=model_name)
        else:
            # let GPT4All pick a default model if available
            model = GPT4All()

        # `generate` returns the generated text for common GPT4All builds
        out = model.generate(prompt, max_length=256)
        if isinstance(out, dict):
            # some builds return dicts with a 'text' key
            return out.get("text", "").strip()
        return str(out).strip()
    except Exception as e:
        return f"GPT4All call failed: {e}"

def answer_query(query: str, retrieved_texts: List[str], provider: str = 'openai', doc_ids: Optional[List[str]] = None, top_k: int = 10) -> str:
    contexts_formatted = "\n\n---\n\n".join(retrieved_texts)
    prompt = f"Use the following contexts to answer the query:\n\n{contexts_formatted}\n\nQuery: {query}\nAnswer:"
    if provider == 'gpt4all':
        return local_gpt4all_completion(prompt)
    if provider == 'local':
        return local_llm_completion(prompt)
    if provider == 'simple':
        return simple_synthesizer(query, retrieved_texts, doc_ids, top_k)
    if provider == 'openai' and OPENAI_API_KEY:
        return openai_completion(prompt)
    return simple_synthesizer(query, retrieved_texts, doc_ids, top_k)
