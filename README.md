# RAG Search Application

<div align="center">

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A powerful Retrieval-Augmented Generation (RAG) search application for documents, logs, and PDFs**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Usage](#-usage) • [Architecture](#-architecture)

</div>

---

## 📋 Overview

RAG Search Application is a professional document search and retrieval system designed for engineers, analysts, and anyone who needs to efficiently search through large collections of documents, log files, and technical documentation. Built with FastAPI and featuring an ERCOT-styled web interface, it provides fast, context-aware search results with intelligent pagination and multiple LLM provider options.

### 🎯 Key Features

- **🔍 Multi-Format Search**: Index and search across `.txt`, `.pdf`, `.log`, `.err`, `.md`, `.json`, `.xml`, and 30+ file types
- **📄 PDF Intelligence**: Automatic text extraction from PDFs with page number preservation
- **🚀 Real-Time Index Updates**: Rebuild search index on-demand without server restart via UI button or API
- **💡 Multiple LLM Providers**:
  - **Simple Provider**: Fast text-based search (no API keys needed, offline-capable) with hyphen-tolerant matching (e.g., "bowtie" finds "bow-tie")
  - **OpenAI GPT-3.5**: Intelligent answer synthesis using OpenAI API
  - **Local LLM**: Full offline capability with llama.cpp
  - **GPT4All**: Balanced offline solution
- **📊 Smart Pagination**: Browse through thousands of results with configurable results-per-page (client-side for simple provider, server-side for LLM providers)
- **🎨 ERCOT Corporate Styling**: Professional blue gradient interface matching trend.ercot.com
- **🔐 Security-First**: Data files excluded from version control, environment-based API keys
- **⚡ Performance**: TF-IDF vectorization with scikit-learn for fast retrieval
- **📱 Responsive Design**: Works seamlessly on desktop and mobile browsers

### 🏢 Use Cases

- **Log Analysis**: Search through EMS logs, error logs, and system outputs
- **Documentation Search**: Find information across technical manuals and PDFs
- **Code Search**: Index and search through source code repositories
- **Troubleshooting**: Quickly locate error patterns and warnings
- **Compliance**: Search for specific terms across regulatory documents

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- Git
- Web browser (Chrome, Firefox, Edge, or Safari)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/weihuifu777/Repo_wfu.git
   cd Repo_wfu
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add Your Documents**
   ```bash
   # Place your files in the data/ folder
   cp /path/to/your/files/* data/
   ```

4. **Build the Search Index**
   ```bash
   python -m rag_app.cli index --data_dir data --index_path data/index.joblib
   ```

5. **Start the Application**
   
   **Windows**: Double-click `start_rag_app.bat`
   
   **Command Line**:
   ```bash
   python -m uvicorn rag_app.api:app --host 127.0.0.1 --port 8000 --reload
   ```

6. **Open in Browser**
   
   Navigate to: **http://127.0.0.1:8000**

### First Search

1. Enter a search query in the search box
2. Select **Simple** provider (no setup required)
3. Click **Search**
4. Browse results with pagination controls

---

## 📚 Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive user guide with step-by-step instructions, troubleshooting, and tips
- **[DESIGN.md](DESIGN.md)** - Technical architecture, API specification, and design decisions
- **[requirements.txt](requirements.txt)** - Python dependencies and package versions

---

## 💻 Usage

### Web Interface

The primary way to use the application is through the web UI:

1. **Search**: Enter query, select provider, set results per page
2. **Browse**: Use pagination controls to navigate all results
3. **Quick Tests**: Click "I'm Feeling Lucky" sample queries
4. **Rebuild Index**: Click 🔄 button to add new files without restart

### Command Line Interface

**Build Index:**
```bash
python -m rag_app.cli index --data_dir data --index_path data/index.joblib
```

**Query from CLI:**
```bash
python -m rag_app.cli query --index_path data/index.joblib --q "your search query"
```

### API Endpoints

**Health Check:**
```bash
curl http://127.0.0.1:8000/health
```

**Search Query:**
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"q":"error","provider":"simple","per_page":10,"page":1}'
```

**View File:**
```bash
# View a file with line highlighting
curl "http://127.0.0.1:8000/view?file=data/logfile.txt&line=42&query=error"
```

**Rebuild Index:**
```bash
curl -X POST http://127.0.0.1:8000/rebuild-index
```

### OpenAI Integration (Optional)

For AI-powered answers:

```powershell
# Set API key
$env:OPENAI_API_KEY = "your-api-key-here"

# Start server
python -m uvicorn rag_app.api:app --host 127.0.0.1 --port 8000 --reload
```

Then select **openai** provider in the UI.

---

## 🏗️ Architecture

### Components

- **FastAPI Backend**: REST API with lifespan management and async context manager
- **TF-IDF Vectorization**: sklearn-based document indexing with cosine similarity
- **Multiple LLM Providers**: OpenAI, Local, GPT4All, Simple text search with hyphen-tolerant regex
- **PyPDF2**: PDF text extraction with page preservation
- **python-docx**: Word document text extraction with paragraph preservation
- **Static Web UI**: ERCOT-styled HTML/CSS/JavaScript interface
- **File Viewer**: In-browser file viewing with syntax highlighting and line navigation

### Project Structure

```
RAG_Sample/
├── rag_app/
│   ├── __init__.py
│   ├── api.py           # FastAPI endpoints
│   ├── cli.py           # Command-line interface
│   ├── config.py        # Configuration & logging setup
│   ├── embedder.py      # TF-IDF vectorization
│   ├── indexer.py       # Document indexing (PDF, DOCX, text)
│   ├── llm.py           # LLM provider wrappers
│   ├── retriever.py     # Similarity search
│   └── static/
│       ├── index.html   # Main search UI
│       └── demo.html    # Debug interface
├── data/                # Your documents (gitignored)
│   └── index.joblib     # Search index (gitignored)
├── logs/                # Application logs (gitignored)
│   └── rag_app.log      # Auto-rotating log file
├── requirements.txt     # Python dependencies
├── start_rag_app.bat   # Windows startup script
├── README.md           # This file
├── USER_GUIDE.md       # User documentation
├── DESIGN.md           # Technical documentation
└── .gitignore          # Git exclusions
```

### Technology Stack

- **Backend**: FastAPI, Uvicorn
- **Vectorization**: scikit-learn (TF-IDF)
- **PDF Processing**: PyPDF2
- **Word Processing**: python-docx
- **LLM Integration**: OpenAI API, llama-cpp-python, GPT4All
- **Logging**: Python logging with RotatingFileHandler
- **Frontend**: Vanilla JavaScript, HTML5, CSS3

---

## 🔧 Configuration

### Environment Variables

```bash
# Optional: OpenAI API key for GPT-powered answers
OPENAI_API_KEY=your-api-key-here

# Optional: Custom index path
RAG_INDEX_PATH=data/index.joblib

# Optional: Default LLM provider
RAG_LLM_PROVIDER=simple  # or openai, local, gpt4all

# Optional: Local LLM model path
LOCAL_LLM_MODEL_PATH=models/ggml-alpaca-7b-q4.bin

# Optional: Logging configuration
RAG_LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR
RAG_LOG_MAX_BYTES=10485760   # Max log file size (10 MB default)
RAG_LOG_BACKUP_COUNT=5       # Number of backup log files to keep
```

### Supported File Types

Text files: `.txt`, `.log`, `.err`, `.out`
Code files: `.py`, `.js`, `.java`, `.ts`, `.c`, `.cpp`, `.h`
Config files: `.json`, `.xml`, `.yaml`, `.yml`, `.ini`, `.cfg`
Documents: `.md`, `.csv`, `.pdf`, `.docx`, `.doc`
Scripts: `.sh`, `.bat`, `.ps1`, `.sql`

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

```bash
# Clone and install
git clone https://github.com/weihuifu777/Repo_wfu.git
cd Repo_wfu
pip install -r requirements.txt

# Run tests
python -m pytest

# Start development server
python -m uvicorn rag_app.api:app --reload
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ERCOT** - UI design inspiration from trend.ercot.com
- **FastAPI** - High-performance web framework
- **scikit-learn** - Machine learning and vectorization
- **OpenAI** - GPT model integration

---

## 📞 Support

For questions, issues, or feature requests:

- 📖 Check the [User Guide](USER_GUIDE.md)
- 🔍 Review [Technical Documentation](DESIGN.md)
- 🐛 Report issues on GitHub

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Maintained by**: ERCOT Development Team
