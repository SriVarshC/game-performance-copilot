"""
Fold helpful Copilot Q&A pairs back into the FAISS knowledge base.

Pulls CopilotInteraction rows where:
  - telemetry_included = False  (general knowledge, not a one-off hardware snapshot)
  - was_helpful = True          (user explicitly marked it useful)
  - folded_into_kb = False      (not already indexed)

Appends them to the existing FAISS index (incremental — does not
rebuild from the markdown files), then marks each row as folded.

Usage:
    python -m src.llm.reindex_from_feedback
"""

import json
from pathlib import Path

import numpy as np

from src.database.connection import SessionLocal
from src.database.models import CopilotInteraction
from src.llm.knowledge_base import (
    INDEX_PATH,
    CHUNKS_PATH,
    _get_embedder,
    EMBEDDING_MODEL_NAME,
)


def reindex_from_feedback():
    import faiss

    db = SessionLocal()
    try:
        eligible = (
            db.query(CopilotInteraction)
            .filter(CopilotInteraction.telemetry_included == False)
            .filter(CopilotInteraction.was_helpful == True)
            .filter(CopilotInteraction.folded_into_kb == False)
            .all()
        )

        if not eligible:
            print("[reindex] No new helpful Q&A pairs to fold in. Nothing to do.")
            return

        print(f"[reindex] Found {len(eligible)} eligible Q&A pair(s) to fold in.")

        # ── Load existing index + chunks ───────────────────────────────────
        if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
            print(
                f"[reindex] ERROR: base index not found at {INDEX_PATH}. "
                f"Run 'python -m src.llm.knowledge_base' first to build it."
            )
            return

        index = faiss.read_index(str(INDEX_PATH))
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        # ── Build new chunks from Q&A pairs ────────────────────────────────
        new_chunks = []
        for interaction in eligible:
            text = f"Q: {interaction.question}\nA: {interaction.answer}"
            new_chunks.append({
                "text": text,
                "source": f"copilot_feedback:{interaction.id}",
            })

        # ── Embed and append ───────────────────────────────────────────────
        embedder = _get_embedder()
        texts = [c["text"] for c in new_chunks]
        embeddings = embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        faiss.normalize_L2(embeddings)

        index.add(embeddings.astype(np.float32))
        chunks.extend(new_chunks)

        # ── Save updated index + chunks ────────────────────────────────────
        faiss.write_index(index, str(INDEX_PATH))
        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)

        # ── Mark rows as folded ─────────────────────────────────────────────
        for interaction in eligible:
            interaction.folded_into_kb = True
        db.commit()

        print(f"[reindex] Added {len(new_chunks)} new chunk(s). Total chunks now: {len(chunks)}")
        print(f"[reindex] Marked {len(eligible)} interaction(s) as folded_into_kb=True.")

    except Exception as e:
        db.rollback()
        print(f"[reindex] ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reindex_from_feedback()