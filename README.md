# Generalized RAG Application

A flexible and easy-to-use Retrieval-Augmented Generation (RAG) system that allows you to build a question-answering system over your own documents.

## Features

- 📄 **Multi-format Support**: Process `.txt`, `.md`, `.pdf`, and `.docx` files
- 🔍 **Semantic Search**: Uses state-of-the-art embedding models for accurate retrieval
- 💾 **Persistent Storage**: ChromaDB-based vector store with persistent storage
- 🎯 **Flexible Retrieval**: Configurable top-k retrieval and chunking strategies
- 🤖 **Optional LLM Integration**: Works standalone or with OpenAI GPT models
- 🎨 **Rich CLI**: Beautiful command-line interface with progress indicators

## Installation

1. Clone the repository:
```bash
git clone https://github.com/weihuifu777/public_repo.git
cd public_repo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up OpenAI API key for LLM-powered responses:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### 1. Ingest Documents

Add documents to your knowledge base:

```bash
# Ingest a single file
python main.py ingest /path/to/document.pdf

# Ingest all documents in a directory
python main.py ingest /path/to/documents/

# Clear existing data and ingest fresh
python main.py ingest /path/to/documents/ --clear
```

### 2. Query the System

Ask questions about your documents:

```bash
# Basic query
python main.py query "What is the main topic of the documents?"

# Query with more context (retrieve top 10 documents)
python main.py query "Explain the methodology" --top-k 10

# Show the retrieved context
python main.py query "What are the key findings?" --show-context

# Use OpenAI for enhanced answers (requires API key)
python main.py query "Summarize the main points" --use-llm
```

### 3. Check Status

View system status and configuration:

```bash
python main.py status
```

### 4. Clear Data

Remove all documents from the knowledge base:

```bash
python main.py clear
```

## How It Works

1. **Document Processing**: Documents are loaded, cleaned, and split into manageable chunks
2. **Embedding Generation**: Each chunk is converted to a vector embedding using sentence-transformers
3. **Vector Storage**: Embeddings are stored in ChromaDB for efficient similarity search
4. **Retrieval**: When you query, the system finds the most relevant chunks
5. **Response Generation**: Results are presented either as raw context or processed through an LLM

## Configuration

The system can be configured through environment variables:

```bash
# Embedding model (default: all-MiniLM-L6-v2)
export EMBEDDING_MODEL="all-MiniLM-L6-v2"

# Chunking configuration
export CHUNK_SIZE=1000
export CHUNK_OVERLAP=200

# Retrieval configuration
export TOP_K=5

# LLM configuration (for --use-llm flag)
export LLM_MODEL="gpt-3.5-turbo"
export LLM_TEMPERATURE=0.7
export LLM_MAX_TOKENS=500
export OPENAI_API_KEY="your-key"
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   RAG Application                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐    ┌─────────────────┐          │
│  │   Document   │───▶│   Embedding     │          │
│  │  Processor   │    │    Service      │          │
│  └──────────────┘    └─────────────────┘          │
│         │                     │                     │
│         │                     ▼                     │
│         │            ┌─────────────────┐           │
│         └───────────▶│  Vector Store   │           │
│                      │   (ChromaDB)    │           │
│                      └─────────────────┘           │
│                              │                      │
│                              ▼                      │
│                      ┌─────────────────┐           │
│                      │   RAG Engine    │           │
│                      │  (Orchestrator) │           │
│                      └─────────────────┘           │
│                              │                      │
│                              ▼                      │
│                      ┌─────────────────┐           │
│                      │   CLI / API     │           │
│                      └─────────────────┘           │
└─────────────────────────────────────────────────────┘
```

## Components

### Document Processor (`document_processor.py`)
Handles loading and preprocessing of various document formats, text chunking, and metadata extraction.

### Embedding Service (`embedding_service.py`)
Generates vector embeddings using sentence-transformers models. Default model provides a good balance of speed and accuracy.

### Vector Store (`vector_store.py`)
Manages document storage and similarity search using ChromaDB with persistent storage.

### RAG Engine (`rag_engine.py`)
Orchestrates the retrieval and generation process, coordinating between components.

### Main CLI (`main.py`)
Provides a user-friendly command-line interface for all operations.

## Example Workflow

```bash
# 1. Create a sample document
mkdir -p data/documents
echo "Python is a high-level programming language. It emphasizes code readability." > data/documents/python.txt
echo "Machine learning is a subset of artificial intelligence." > data/documents/ml.txt

# 2. Ingest the documents
python main.py ingest data/documents/

# 3. Query the system
python main.py query "What is Python?"

# 4. Get more detailed results
python main.py query "What is Python?" --show-context --top-k 3
```

## Advanced Usage

### Custom Embedding Model

Use a different sentence-transformers model:

```bash
export EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"
python main.py ingest data/documents/
```

### Batch Processing

Process multiple document sets:

```bash
python main.py ingest ./reports/ --clear
python main.py ingest ./papers/
python main.py ingest ./notes/
```

## Troubleshooting

**Issue**: "No documents in the knowledge base"
- **Solution**: Run `python main.py ingest <path>` first to add documents

**Issue**: PDF processing fails
- **Solution**: Install pypdf: `pip install pypdf`

**Issue**: DOCX processing fails
- **Solution**: Install python-docx: `pip install python-docx`

**Issue**: LLM generation not working
- **Solution**: Set `OPENAI_API_KEY` environment variable and use `--use-llm` flag

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Embeddings by [Sentence Transformers](https://www.sbert.net/)
- Vector storage by [ChromaDB](https://www.trychroma.com/)
- CLI by [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/)
