"""Migrate existing local FAISS index to PGVector.

Usage:
    USE_PGVECTOR=true python scripts/faiss_to_pgvector.py \
        --faiss-path indexes/faiss_index \
        --collection docs \
        --connection postgresql+psycopg2://pguser:pgpass@localhost:5432/building_ai

Env var OPENAI_API_KEY must be set for real embeddings; otherwise FakeEmbeddings
will be used and vectors may not match previously stored ones.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Any

from backend.rag.manager import _embedding_cls  # reuse same embedding resolution
from langchain_community.vectorstores import FAISS, PGVector


def migrate(faiss_path: Path, connection: str, collection: str) -> int:
    if not faiss_path.exists():
        raise FileNotFoundError(f"{faiss_path} does not exist")

    embeddings = _embedding_cls()  # same class as DocumentAssistant

    faiss_store = FAISS.load_local(str(faiss_path), embeddings, allow_dangerous_deserialization=True)

    # Extract texts & metadatas
    texts: List[str] = []
    metadatas: List[Any] = []
    for doc_id, doc in faiss_store.docstore._dict.items():  # type: ignore[attr-defined]
        texts.append(doc.page_content)
        metadatas.append(doc.metadata)

    # Insert into PGVector
    pg = PGVector.from_texts(
        texts,
        embeddings,
        metadatas=metadatas,
        connection_string=connection,
        collection_name=collection,
    )

    return len(texts)


def _cli():
    p = argparse.ArgumentParser(description="Migrate FAISS index to PGVector")
    p.add_argument("--faiss-path", default="indexes/faiss_index", help="Directory containing FAISS index")
    p.add_argument("--connection", required=False, default=os.getenv("PG_CONN", "postgresql+psycopg2://pguser:pgpass@localhost:5432/building_ai"))
    p.add_argument("--collection", default="docs", help="Target PGVector collection name")

    args = p.parse_args()
    n = migrate(Path(args.faiss_path), args.connection, args.collection)
    print(f"Migrated {n} documents to PGVector collection '{args.collection}'")


if __name__ == "__main__":
    _cli() 