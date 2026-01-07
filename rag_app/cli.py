import argparse
from . import indexer, retriever, llm
from .config import DEFAULT_INDEX_PATH, DATA_DIR

def cmd_index(args):
    index = indexer.build_index(args.data_dir, args.index_path, model_name=args.model)
    print(f"Index built: {len(index['docs'])} docs, saved to {args.index_path}")

def cmd_query(args):
    index = indexer.load_index(args.index_path)
    vec = index.get('vectorizer')
    if vec is None:
        raise RuntimeError("Index missing vectorizer; re-build index")
    qv = vec.transform([args.q]).toarray()
    ret = retriever.Retriever.from_index(index)
    idxs, sims = ret.query(qv, top_k=args.k)
    contexts = [index['docs'][i]['text'] for i in idxs]
    print("Top matches:")
    for i, s in zip(idxs, sims):
        print(f"- {index['docs'][i]['id']} (score={s:.3f})")
    doc_ids = [index['docs'][i]['id'] for i in idxs]
    ans = llm.answer_query(args.q, contexts, provider=args.provider, doc_ids=doc_ids, top_k=args.k)
    print('\n==== ANSWER ===\n')
    print(ans)

def main():
    p = argparse.ArgumentParser(prog='rag_app', description='RAG Search Application CLI')
    sp = p.add_subparsers(dest='cmd')

    p_index = sp.add_parser('index', help='Build search index from files')
    p_index.add_argument('--data_dir', default=DATA_DIR, help='Directory containing files to index')
    p_index.add_argument('--index_path', default=DEFAULT_INDEX_PATH, help='Path to save the index')
    p_index.add_argument('--model', default='tfidf', help='Embedding model (default: tfidf)')
    p_index.set_defaults(func=cmd_index)

    p_q = sp.add_parser('query', help='Query the search index')
    p_q.add_argument('--index_path', default=DEFAULT_INDEX_PATH, help='Path to the index file')
    p_q.add_argument('--q', required=True, help='Search query')
    p_q.add_argument('-k', type=int, default=5, help='Number of results to return')
    p_q.add_argument('--provider', default='simple', help='LLM provider (simple, openai, local, gpt4all)')
    p_q.set_defaults(func=cmd_query)

    args = p.parse_args()
    if not hasattr(args, 'func'):
        p.print_help()
        return
    args.func(args)

if __name__ == '__main__':
    main()
