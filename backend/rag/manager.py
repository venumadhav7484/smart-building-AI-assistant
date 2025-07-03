"""Simple RAG manager for ingesting PDFs and querying chunks.
This is MVP: FAISS local store; later swap to PGVector via env flag.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Any, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS, PGVector
from langchain_community.document_loaders.csv_loader import CSVLoader

# Embeddings with graceful fallback when no OpenAI key
try:
    from langchain_openai import OpenAIEmbeddings
    _embedding_cls = OpenAIEmbeddings  # type: ignore
except Exception:  # pragma: no cover
    from langchain_community.embeddings import FakeEmbeddings  # type: ignore

    class _embedding_cls(FakeEmbeddings):
        def __init__(self):
            super().__init__(size=1536)

DATA_DIR = Path("indexes")
DATA_DIR.mkdir(exist_ok=True)

INDEX_PATH = DATA_DIR / "faiss_index"


class DocumentAssistant:
    """Manage ingestion and similarity search."""

    def __init__(self) -> None:
        try:
            self.embeddings = _embedding_cls()
        except Exception:  # pragma: no cover
            from langchain_community.embeddings import FakeEmbeddings  # type: ignore

            self.embeddings = FakeEmbeddings(size=1536)
        self.vector_store: FAISS | None = None
        self.use_pg = os.getenv("USE_PGVECTOR", "false").lower() == "true"

        if self.use_pg:
            # Lazy import psycopg2 only when actually using Postgres
            try:
                import psycopg2  # noqa: F401
            except ImportError as e:  # pragma: no cover
                raise RuntimeError("USE_PGVECTOR is true but psycopg2 is not installed") from e

            self.pg_conn_str = os.getenv("PG_CONN", "postgresql+psycopg2://pguser:pgpass@localhost:5432/building_ai")
            try:
                self.vector_store = PGVector(connection_string=self.pg_conn_str, embedding_function=self.embeddings, collection_name="docs", use_jsonb=True)
            except Exception:
                self.vector_store = None  # will create on first ingest
            return

        # FAISS path
        if INDEX_PATH.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(INDEX_PATH), self.embeddings, allow_dangerous_deserialization=True
                )
            except Exception:  # corrupted index
                INDEX_PATH.unlink(missing_ok=True)

    def ingest_pdf(self, file_path: str) -> int:
        """Load PDF, chunk, embed, and persist.
        Returns number of chunks added.
        """
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(docs)
        if self.use_pg:
            if self.vector_store is None:
                self.vector_store = PGVector.from_documents(
                    chunks,
                    self.embeddings,
                    connection_string=self.pg_conn_str,
                    collection_name="docs",
                    use_jsonb=True,
                )
            else:
                self.vector_store.add_documents(chunks)
        else:
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                self.vector_store.add_documents(chunks)
        if not self.use_pg:
            self.vector_store.save_local(str(INDEX_PATH))
        return len(chunks)

    def ingest_csv(self, file_path: str) -> int:
        """Load CSV, convert rows to Documents and persist."""
        loader = CSVLoader(file_path)
        docs = loader.load()
        if self.use_pg:
            if self.vector_store is None:
                self.vector_store = PGVector.from_documents(
                    docs,
                    self.embeddings,
                    connection_string=self.pg_conn_str,
                    collection_name="docs",
                    use_jsonb=True,
                )
            else:
                self.vector_store.add_documents(docs)
        else:
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(docs, self.embeddings)
            else:
                self.vector_store.add_documents(docs)
        if not self.use_pg:
            self.vector_store.save_local(str(INDEX_PATH))
        return len(docs)

    def similarity_search(self, query: str, k: int = 4) -> List[str]:
        if self.vector_store is None:
            return []
        docs = self.vector_store.similarity_search(query, k)
        return [d.page_content for d in docs]

    # New helper returning Document objects
    def similarity_search_docs(self, query: str, k: int = 4):
        if self.vector_store is None:
            return []
        return self.vector_store.similarity_search(query, k)


# ----------------------- CLI helper -----------------------


def _cli():  # pragma: no cover – utility script
    """Minimal command-line interface.

    Usage examples:
        python -m backend.rag.manager ingest docs/*.pdf
        python -m backend.rag.manager query "How to reset AHU?" -k 3
    """

    import argparse, glob, textwrap

    parser = argparse.ArgumentParser(
        prog="python -m backend.rag.manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(_cli.__doc__ or ""),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    ing = sub.add_parser("ingest", help="Ingest one or more PDF files (supports glob patterns)")
    ing.add_argument("paths", nargs="+", help="PDF file paths or glob patterns")

    qry = sub.add_parser("query", help="Run an ad-hoc similarity search from the terminal")
    qry.add_argument("question", help="Natural-language query")
    qry.add_argument("-k", type=int, default=4, help="Top-k chunks to return")

    args = parser.parse_args()

    assistant = DocumentAssistant()

    if args.command == "ingest":
        total_chunks = 0
        for pattern in args.paths:
            for path in glob.glob(pattern):
                if not path.lower().endswith(".pdf"):
                    print(f"[skip] {path} is not a PDF")
                    continue
                num = assistant.ingest_pdf(path)
                total_chunks += num
                print(f"[ok] {path}: {num} chunks")
        print("---")
        print(f"Total chunks ingested: {total_chunks}")

    elif args.command == "query":
        chunks = assistant.similarity_search(args.question, k=args.k)
        for i, ch in enumerate(chunks, 1):
            snippet = ch[:200].replace("\n", " ")
            print(f"[{i}] {snippet}…")


if __name__ == "__main__":  # pragma: no cover
    _cli() 