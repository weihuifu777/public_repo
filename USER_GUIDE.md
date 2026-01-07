# RAG Search Application - User Guide

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Using the Search Interface](#using-the-search-interface)
4. [Understanding Search Results](#understanding-search-results)
5. [Advanced Features](#advanced-features)
6. [Tips & Best Practices](#tips--best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is this application?
The RAG (Retrieval-Augmented Generation) Search Application is a powerful document search tool designed to help you quickly find information across your text documents, PDFs, and log files. It uses advanced text search capabilities to locate relevant passages and provide context-rich results.

### Key Features
- 🔍 **Fast Text Search**: Search across all your documents instantly with hyphen-tolerant matching
- 📄 **Multi-Format Support**: Works with `.txt`, `.pdf`, `.docx`, `.log`, and other text files
- 🎯 **Context-Aware Results**: See surrounding context (2+ lines) for better understanding
- 📊 **Pagination**: Browse through all matching results efficiently
- 🎨 **ERCOT-Styled Interface**: Professional, easy-to-use web interface
- 🔄 **Live Index Updates**: Add new documents without restarting
- 💡 **Smart Search**: "bowtie" automatically finds "bow-tie" and "bow tie"
- 📂 **File Viewer**: Click results to view files with line highlighting

### Who is it for?
- **Engineers** searching through log files, error logs, and technical documentation
- **System Administrators** troubleshooting production issues across multiple log files
- **Analysts** looking for specific patterns or errors in large datasets
- **Developers** searching through source code repositories and documentation
- **Compliance Officers** finding specific terms across regulatory documents
- **Support Teams** quickly locating solutions in knowledge bases
- **Anyone** who needs to search across multiple documents efficiently without manual file browsing

---

## Getting Started

### Prerequisites
- **Python 3.12 or higher** installed on your computer
  - Download from [python.org](https://www.python.org/downloads/)
  - Verify installation: `python --version`
- **Web browser** (Chrome, Firefox, Edge, or Safari)
- **Git** (optional, for cloning the repository)
- **Text editor** (optional, for viewing/editing configuration)

### Installation

1. **Get the Application**
   
   **Option A: Clone from GitHub**
   ```bash
   git clone https://github.com/weihuifu777/Repo_wfu.git
   cd Repo_wfu
   ```
   
   **Option B: Download ZIP**
   - Visit the repository and download as ZIP
   - Extract to a folder like `C:\Python_PlayGround\RAG_Sample`

2. **Install Dependencies**
   ```bash
   # Navigate to the project folder
   cd C:\Python_PlayGround\RAG_Sample
   
   # Install required Python packages
   pip install -r requirements.txt
   ```
   
   This installs: FastAPI, Uvicorn, scikit-learn, PyPDF2, and other required packages.

2. **Prepare Your Documents**
   - Place all files you want to search in the `data/` folder
   - **Supported formats**: 
     - Text files: `.txt`, `.log`, `.err`, `.out`
     - Documents: `.pdf`, `.docx`, `.doc`, `.md`, `.csv`
     - Code files: `.py`, `.js`, `.java`, `.ts`, `.c`, `.cpp`, `.h`
     - Config files: `.json`, `.xml`, `.yaml`, `.yml`, `.ini`, `.cfg`, `.conf`
     - Scripts: `.sh`, `.bat`, `.ps1`, `.sql`
   - Organize files in subfolders for better management (optional)
   
   **Example structure:**
   ```
   data/
   ├── logs/
   │   ├── ems_errors.log
   │   └── system.log
   ├── manuals/
   │   ├── user_manual.pdf
   │   └── technical_guide.pdf
   └── code/
       └── source_files.py
   ```

3. **Build the Search Index**
   ```bash
   python -m rag_app.cli index --data_dir data --index_path data/index.joblib
   ```
   This creates a searchable index from all files in the `data/` folder.

4. **Start the Application**
   - **Windows**: Double-click `start_rag_app.bat`
   - **Command Line**: 
     ```bash
     python -m uvicorn rag_app.api:app --host 127.0.0.1 --port 8000 --reload
     ```

5. **Open in Browser**
   - Navigate to: `http://127.0.0.1:8000`
   - You should see the ERCOT-styled search interface

---

## Using the Search Interface

### Basic Search

1. **Enter Your Search Query**
   - Type your search term in the main search box
   - Example: `RPC error`, `plugin initialization`, `HABITAT`

2. **Choose Search Provider**
   - **Simple (Recommended)**: Fast text-based search, no API keys needed, works offline
   - **OpenAI**: Uses GPT-3.5-turbo for intelligent answers (requires API key setup)
   - **Local**: Offline LLM using llama.cpp (requires model download)
   - **GPT4All**: Balanced offline solution (requires model download)

3. **Set Results Per Page**
   - Default: 10 results per page
   - Options: 10, 25, 50, or 100
   - Shows total count (e.g., "Showing 1-10 of 1623 results")

4. **Click Search**
   - Results appear below with file names, locations, and matching text
   - Multi-line context shows at least 2 lines per result for better understanding

### "I'm Feeling Lucky" Quick Searches

Click any sample query button to instantly search for common patterns:
- **RPC**: Remote Procedure Call references
- **ERROR**: Error messages and exceptions
- **WARN**: Warning messages
- **plugin**: Plugin-related information
- **HABITAT**: HABITAT system references
- **client handle**: Client connection handling
- **ERCOT**: ERCOT-specific information
- **database**: Database operations and queries

### Navigation

- **Pagination Controls**: Use `◄ Previous` and `Next ►` buttons to browse results
- **Page Numbers**: Click specific page numbers for direct access
- **Results Counter**: Always shows current position (e.g., "1-10 of 1623")

---

## Understanding Search Results

### Result Format

Each search result displays:

```
📄 logfile.txt : Line 42
────────────────────────────────────────
[ERROR] RPC call failed: Connection timeout
Attempting reconnection to remote server...
```

**Components:**
- **File Name**: Clickable link to open file in browser viewer
- **Location**: Line number (for text files), Page number (for PDFs), or Paragraph number (for Word docs)
- **Context**: 2+ lines showing the matching text and next line for context
- **Highlighted Terms**: Search terms are highlighted with `<mark>` tags
- **Document Links**: For PDFs, an "📖 Open PDF" link opens the original document; for Word docs, "📝 Open Doc" downloads the file

**File Viewer Features:**
- Click any file name to open in the built-in viewer
- Viewer shows line numbers and highlights the matching line
- Dark theme for comfortable reading
- Search term highlighting throughout the file

### PDF Results

PDF files are processed differently:
- Text is extracted from PDF pages
- Results show **Page X** instead of line numbers
- Context includes surrounding text from the same page
- Original PDF formatting is not preserved (text-only search)

### Result Sorting

Results are ordered by:
1. **Relevance**: Best matches appear first
2. **Location**: Within same file, earlier occurrences come first
3. **File Name**: Alphabetical when relevance is equal

---

## Advanced Features

### 🔄 Rebuilding the Index

When you add new files to the `data/` folder, you need to update the search index.

**Method 1: UI Button (Easiest)**
1. Click **🔄 Rebuild Index** in the top-right corner
2. Wait for confirmation message: "✅ Index rebuilt successfully!"
3. New files are immediately searchable

**Method 2: API Call**
```bash
curl -X POST http://127.0.0.1:8000/rebuild-index
```

**Method 3: Command Line**
```bash
python -m rag_app.cli index --data_dir data --index_path data/index.joblib
# Then restart the server
```

**What happens during rebuild:**
- Server scans all files in `data/` folder
- Extracts text from PDFs and other documents
- Creates searchable index with TF-IDF vectorization
- Automatically reloads index (no restart needed with Method 1 or 2)
- Typically takes 5-30 seconds depending on file count

### 🔑 OpenAI Integration (Optional)

For AI-powered answers instead of simple text search:

1. **Get API Key**
   - Sign up at [OpenAI Platform](https://platform.openai.com)
   - Create an API key in your account settings

2. **Set Environment Variable**
   - **Windows PowerShell**:
     ```powershell
     $env:OPENAI_API_KEY = "your-api-key-here"
     python -m uvicorn rag_app.api:app --host 127.0.0.1 --port 8000 --reload
     ```
   - **Windows Command Prompt**:
     ```cmd
     set OPENAI_API_KEY=your-api-key-here
     python -m uvicorn rag_app.api:app --host 127.0.0.1 --port 8000 --reload
     ```
   - **Linux/Mac**:
     ```bash
     export OPENAI_API_KEY="your-api-key-here"
     python -m uvicorn rag_app.api:app --host 127.0.0.1 --port 8000 --reload
     ```

3. **Select OpenAI Provider**
   - In the search interface, choose "openai" from the Provider dropdown
   - Searches will now generate intelligent summaries using GPT-3.5-turbo

### 📊 Pagination Deep Dive

**Simple Provider (Client-Side Pagination):**
- Server searches ALL indexed documents using hyphen-tolerant regex
- All matching results returned in `all_results` array
- Browser handles page navigation instantly
- Fast switching between pages with no server round-trips
- Best for: log analysis, code search, document lookup

**LLM Providers (Server-Side Pagination):**
- Server retrieves top `per_page × 3` documents via TF-IDF similarity
- LLM synthesizes answer from retrieved contexts
- Results paginated server-side
- Best for: semantic questions requiring AI synthesis

**Customization:**
- Change "Results per page" to control density (10, 25, 50, or 100)
- Use page numbers for direct access
- Total count and page info always visible (e.g., "Showing 1-10 of 1623 results")

---

## Tips & Best Practices

### Search Query Tips

✅ **DO:**
- Use specific terms: `"connection timeout"` instead of `"error"`
- Try multiple keywords: `RPC failed initialization`
- Use technical terms from your domain: `HABITAT plugin LFLOG`
- Check sample queries for ideas
- **Hyphen variations work automatically**: searching "bowtie" will find "bow-tie" and "bow tie" too!

❌ **DON'T:**
- Use overly generic terms: `"the"`, `"a"`, `"is"`
- Include special characters unless searching for them: `@#$%`
- Make queries too long (keep under 500 characters)

### Performance Optimization

- **Index Size**: Keep `data/` folder under 10,000 files for best performance
- **File Size**: Large PDFs (>50MB) may slow down indexing
- **Results Per Page**: Start with 10-25 for faster loading
- **Rebuild Frequency**: Only rebuild when adding new files

### File Organization

```
data/
├── logs/              # Log files organized by date or system
│   ├── ems/
│   ├── habitat/
│   └── network/
├── manuals/           # PDF documentation
└── reports/           # Text reports
```

Keep files organized in subfolders for easier management.

### Security Best Practices

⚠️ **Important:**
- Never commit sensitive logs or documents to version control
- The `.gitignore` file excludes `data/*.txt`, `data/*.pdf` by default
- Review files before adding to `data/` folder
- Use environment variables for API keys (never hardcode)

---

## Troubleshooting

### Server Won't Start

**Error: "Address already in use"**
- Another instance is already running on port 8000
- **Solution**: 
  ```powershell
  # Find the process using port 8000
  netstat -ano | findstr :8000
  # Kill the process (replace PID with actual number)
  taskkill /PID <PID> /F
  ```

**Error: "Module not found"**
- Dependencies not installed
- **Solution**: `pip install -r requirements.txt`

### Search Not Working

**"Index not loaded" Error**
- Index file missing or corrupted
- **Solution**: Click **🔄 Rebuild Index** or run CLI command

**No Results Found**
- Files not indexed yet
- **Solution**: Rebuild index after adding files
- Check spelling and try broader terms

**Slow Search Performance**
- Too many files in index (>10,000)
- **Solution**: Split into multiple instances or clean up old files

### Index Rebuild Issues

**"Rebuilding in progress" Message**
- Another rebuild is already running
- **Solution**: Wait 30-60 seconds and try again

**Rebuild Fails Silently**
- Check terminal/console for error messages
- Verify `data/` folder exists and contains files
- Ensure write permissions for `data/index.joblib`

### OpenAI Provider Issues

**"API key not found"**
- Environment variable not set
- **Solution**: Set `OPENAI_API_KEY` before starting server

**"Rate limit exceeded"**
- Too many requests to OpenAI API
- **Solution**: Switch to "Simple" provider or wait a few minutes

### Browser/UI Issues

**Page Not Loading**
- Server not running or wrong URL
- **Solution**: Check server is running, use `http://127.0.0.1:8000`

**Styling Looks Wrong**
- Browser cache issue
- **Solution**: Hard refresh (Ctrl+Shift+R on Windows/Linux, Cmd+Shift+R on Mac)

---

## Getting Help

### Resources

- **User Guide**: This document - comprehensive usage instructions
- **Technical Documentation**: [DESIGN.md](DESIGN.md) - architecture and API details
- **README**: [README.md](README.md) - quick start and overview
- **API Documentation**: Visit `http://127.0.0.1:8000/docs` when server is running for interactive API docs

### Log Files

**File Logging** (automatically created):
- **Location**: `logs/rag_app.log`
- **Rotation**: Automatically rotates when file reaches 10 MB
- **Backups**: Keeps 5 backup files (`rag_app.log.1`, `.2`, etc.)

**Console Logging**:
Server logs also appear in the terminal where you started the application.

**Log Levels** (set via `RAG_LOG_LEVEL` environment variable):
- `DEBUG`: Detailed debugging information
- `INFO`: Normal operation messages (default)
- `WARNING`: Potential issues
- `ERROR`: Problems requiring attention

**View Recent Logs:**
```powershell
# Windows PowerShell
Get-Content logs/rag_app.log -Tail 50

# Or open in VS Code
code logs/rag_app.log
```

### Useful Commands

**Check Server Status:**
```bash
curl http://127.0.0.1:8000/health
```
Response: `{"status":"ok","index_loaded":true,"rebuilding":false}`

**View Indexed Files:**
- The index stores all file paths and content
- Check `data/index.joblib` size to verify index was built
- Typical size: 1-10 MB depending on document count

**Manual Index Inspection:**
```bash
python -c "import joblib; idx = joblib.load('data/index.joblib'); print(f'Documents: {len(idx[\"docs\"])}')"
```

**Test Search from Command Line:**
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"q":"error","provider":"simple","per_page":10}'
```

---

## Additional Resources

- **Technical Documentation**: See [DESIGN.md](DESIGN.md) for architecture details, API specifications, and design decisions
- **Code Repository**: Check [README.md](README.md) for development information, quick start guide, and project overview
- **Configuration**: Edit `rag_app/config.py` for advanced settings like default provider, index path, and data directory
- **API Documentation**: Interactive Swagger UI at `http://127.0.0.1:8000/docs` when server is running
- **GitHub Repository**: [weihuifu777/Repo_wfu](https://github.com/weihuifu777/Repo_wfu) - source code, issues, and updates

### Related Documentation

- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com) - Web framework documentation
- **scikit-learn**: [scikit-learn.org](https://scikit-learn.org) - Machine learning library used for vectorization
- **OpenAI API**: [platform.openai.com/docs](https://platform.openai.com/docs) - If using OpenAI provider
- **PyPDF2**: PDF text extraction library documentation

### Community & Support

- **Report Issues**: Create an issue on the GitHub repository for bugs or feature requests
- **Feature Requests**: Suggest improvements via GitHub issues
- **Contributions**: Pull requests welcome! See README.md for development setup

---

**Version**: 1.0  
**Last Updated**: January 2026  
**Repository**: [github.com/weihuifu777/Repo_wfu](https://github.com/weihuifu777/Repo_wfu)  
**Maintained by**: ERCOT Development Team
