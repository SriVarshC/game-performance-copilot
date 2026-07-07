"""
FAISS-based knowledge retrieval for the AI Copilot (Phase 7 — RAG upgrade).

Chunks markdown knowledge files, embeds them locally with
sentence-transformers' all-MiniLM-L6-v2 model (no API calls, runs on CPU),
and builds a FAISS index for fast semantic similarity search.

Usage:
    Build/rebuild the index (run once, or whenever knowledge files change):
        python -m src.llm.knowledge_base

    Retrieve relevant context at query time (used by llm.py route):
        from src.llm.knowledge_base import retrieve
        chunks = retrieve("why is my FPS dropping", k=3)
"""

import json
import re
from pathlib import Path
from typing import List, Optional

import numpy as np

# ─── Paths ────────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_DIR  = PROJECT_ROOT / "data" / "knowledge"
INDEX_DIR      = PROJECT_ROOT / "models" / "knowledge_index"
INDEX_PATH     = INDEX_DIR / "faiss.index"
CHUNKS_PATH    = INDEX_DIR / "chunks.json"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# ─── Lazy singletons ──────────────────────────────────────────────────────
_embedder = None
_index    = None
_chunks   = None   # list of {"text": ..., "source": ...}


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        print(f"[knowledge_base] Loading embedding model '{EMBEDDING_MODEL_NAME}'...")
        _embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedder


def _chunk_markdown(text: str, source: str, target_chars: int = 700) -> List[dict]:
    """
    Split a markdown document into chunks along paragraph boundaries,
    merging small paragraphs together up to ~target_chars per chunk so
    each embedding covers a coherent, complete idea rather than a
    fragment. Keeps track of the originating filename for citation.
    """
    # Split on blank lines (paragraphs / list items / headers)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) <= target_chars or not current:
            current = f"{current}\n\n{para}".strip()
        else:
            chunks.append(current)
            current = para
    if current:
        chunks.append(current)

    return [{"text": c, "source": source} for c in chunks]


def build_index():
    """
    Read all .md files under data/knowledge/, chunk them, embed each
    chunk, and save a FAISS index + chunk metadata to models/knowledge_index/.
    Run this once initially, and again any time knowledge files change.
    """
    import faiss

    if not KNOWLEDGE_DIR.exists():
        print(f"[knowledge_base] ERROR: {KNOWLEDGE_DIR} does not exist. "
              f"Create it and add .md files first.")
        return

    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not md_files:
        print(f"[knowledge_base] ERROR: no .md files found in {KNOWLEDGE_DIR}")
        return

    all_chunks: List[dict] = []
    for path in md_files:
        text = path.read_text(encoding="utf-8")
        all_chunks.extend(_chunk_markdown(text, source=path.name))

    print(f"[knowledge_base] {len(md_files)} file(s) -> {len(all_chunks)} chunk(s)")

    embedder = _get_embedder()
    texts = [c["text"] for c in all_chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # Normalize embeddings so inner-product search behaves like cosine similarity
    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype(np.float32))

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"[knowledge_base] Index built: {len(all_chunks)} chunks, dim={dim}")
    print(f"[knowledge_base] Saved to: {INDEX_PATH}")


def _load_index():
    """Load the FAISS index + chunk metadata from disk (cached after first call)."""
    global _index, _chunks
    if _index is not None:
        return

    import faiss

    if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
        print(
            f"[knowledge_base] WARNING: index not found at {INDEX_PATH}. "
            f"Run 'python -m src.llm.knowledge_base' to build it first."
        )
        _index = False   # sentinel: "tried and failed", don't retry every call
        _chunks = []
        return

    _index = faiss.read_index(str(INDEX_PATH))
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        _chunks = json.load(f)


def retrieve(query: str, k: int = 3) -> List[dict]:
    """
    Return the top-k most semantically relevant knowledge chunks for a
    given query. Returns [] if the index hasn't been built yet or the
    query is empty — non-fatal, callers should treat this as "no extra
    context available" rather than an error.

    Returns:
        [{"text": "...", "source": "filename.md", "score": 0.83}, ...]
    """
    _load_index()
    if not _index or not _chunks or not query.strip():
        return []

    embedder = _get_embedder()
    query_vec = embedder.encode([query], convert_to_numpy=True)

    import faiss
    faiss.normalize_L2(query_vec)

    scores, indices = _index.search(query_vec.astype(np.float32), k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_chunks):
            continue
        results.append({
            "text":   _chunks[idx]["text"],
            "source": _chunks[idx]["source"],
            "score":  float(score),
        })
    return results


if __name__ == "__main__":
    build_index()