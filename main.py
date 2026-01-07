"""Main CLI application for the RAG system."""
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import print as rprint

from document_processor import DocumentProcessor
from embedding_service import EmbeddingService
from vector_store import VectorStore
from rag_engine import RAGEngine
import config

console = Console()


def initialize_rag_system():
    """Initialize the RAG system components."""
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    rag_engine = RAGEngine(embedding_service, vector_store)
    return rag_engine, vector_store


@click.group()
def cli():
    """Generalized RAG (Retrieval-Augmented Generation) Application.
    
    This tool allows you to:
    - Ingest documents into a knowledge base
    - Query the knowledge base using natural language
    - Get answers based on retrieved context
    """
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--clear', is_flag=True, help='Clear existing documents before ingestion')
def ingest(path: str, clear: bool):
    """Ingest documents from a file or directory.
    
    PATH: Path to a file or directory containing documents to ingest.
    
    Supported formats: .txt, .md, .pdf, .docx
    """
    console.print("\n[bold blue]Starting document ingestion...[/bold blue]\n")
    
    path_obj = Path(path)
    
    # Initialize components
    doc_processor = DocumentProcessor()
    rag_engine, vector_store = initialize_rag_system()
    
    # Clear if requested
    if clear:
        console.print("[yellow]Clearing existing documents...[/yellow]")
        vector_store.clear()
    
    # Process documents
    console.print(f"Processing documents from: [cyan]{path}[/cyan]\n")
    
    if path_obj.is_file():
        documents = doc_processor.process_file(path_obj)
    else:
        documents = doc_processor.process_directory(path_obj)
    
    if not documents:
        console.print("[red]No documents were processed![/red]")
        return
    
    # Index documents
    rag_engine.index_documents(documents)
    
    # Show summary
    console.print(f"\n[green]✓[/green] Successfully ingested [bold]{len(documents)}[/bold] document chunks")
    console.print(f"[green]✓[/green] Total documents in store: [bold]{vector_store.count()}[/bold]")


@cli.command()
@click.argument('question')
@click.option('--top-k', default=config.TOP_K, help='Number of documents to retrieve')
@click.option('--show-context', is_flag=True, help='Show retrieved context')
@click.option('--use-llm', is_flag=True, help='Use LLM for answer generation (requires API key)')
def query(question: str, top_k: int, show_context: bool, use_llm: bool):
    """Query the RAG system with a question.
    
    QUESTION: The question to ask the RAG system.
    """
    console.print(f"\n[bold blue]Processing query...[/bold blue]\n")
    
    # Initialize RAG system
    rag_engine, vector_store = initialize_rag_system()
    
    # Check if there are documents
    if vector_store.count() == 0:
        console.print("[red]No documents in the knowledge base![/red]")
        console.print("Please ingest documents first using the 'ingest' command.")
        return
    
    # Set up LLM client if requested
    llm_client = None
    if use_llm:
        if config.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                llm_client = OpenAI(api_key=config.OPENAI_API_KEY)
                console.print("[green]Using OpenAI for answer generation[/green]\n")
            except ImportError:
                console.print("[yellow]Warning: OpenAI library not installed. Falling back to context-only mode.[/yellow]")
                console.print("Install with: pip install openai\n")
                use_llm = False
        else:
            console.print("[yellow]Warning: OPENAI_API_KEY not set. Falling back to context-only mode.[/yellow]\n")
            use_llm = False
    
    # Query the system
    result = rag_engine.query(question, top_k=top_k, use_llm=use_llm, llm_client=llm_client)
    
    # Display results
    console.print(Panel(f"[bold]{question}[/bold]", title="Question", border_style="blue"))
    console.print()
    
    console.print(Panel(result['answer'], title="Answer", border_style="green"))
    console.print()
    
    if result['sources']:
        console.print("[bold]Sources:[/bold]")
        for source in result['sources']:
            console.print(f"  • {source}")
        console.print()
    
    if show_context:
        console.print(Panel(result['context'], title="Retrieved Context", border_style="yellow"))


@cli.command()
def status():
    """Show the current status of the RAG system."""
    console.print("\n[bold blue]RAG System Status[/bold blue]\n")
    
    # Initialize components
    _, vector_store = initialize_rag_system()
    
    # Create status table
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Embedding Model", config.EMBEDDING_MODEL)
    table.add_row("Chunk Size", str(config.CHUNK_SIZE))
    table.add_row("Chunk Overlap", str(config.CHUNK_OVERLAP))
    table.add_row("Top-K Retrieval", str(config.TOP_K))
    table.add_row("Documents in Store", str(vector_store.count()))
    table.add_row("Vector Store Path", str(config.VECTOR_STORE_DIR))
    
    console.print(table)
    console.print()


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear all documents?')
def clear():
    """Clear all documents from the vector store."""
    console.print("\n[bold blue]Clearing vector store...[/bold blue]\n")
    
    _, vector_store = initialize_rag_system()
    vector_store.clear()
    
    console.print("[green]✓[/green] Vector store cleared successfully")


if __name__ == '__main__':
    cli()
