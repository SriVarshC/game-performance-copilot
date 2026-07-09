"""
POST /api/llm/ask
Natural language performance Q&A powered by Ollama (llama3.2).
Fetches live telemetry + diagnostics and injects them as context
so answers are specific to the user's actual hardware state.

Phase 7: Also retrieves relevant knowledge base context via FAISS
semantic search, grounding answers in vetted, hardware-specific
guidance rather than the LLM's general training knowledge alone.

Phase 8: Requires a logged-in user.

Phase 10: Logs every interaction to PostgreSQL. General (non-telemetry)
answers marked helpful by the user become eligible to be folded back
into the FAISS knowledge base via reindex_from_feedback.py.
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.models import User, CopilotInteraction
from src.database.connection import get_db
from src.api.dependencies import get_current_user

router = APIRouter()

MODEL_NAME = "llama3.2"


# ── Request / Response Schemas ────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        example="Why is my GPU at 50% while I'm gaming?",
        description="Natural language question about your game performance.",
    )
    include_telemetry: bool = Field(
        True,
        description=(
            "If True (default), fetches live GPU/CPU/RAM metrics + AI diagnostics "
            "and injects them into the prompt so answers are specific to your "
            "current hardware state. Set False for general questions."
        ),
    )


class AskResponse(BaseModel):
    answer:                 str
    model:                  str
    question:               str
    telemetry_included:     bool
    issues_detected:        int
    knowledge_sources:      list[str]
    response_time_seconds:  float
    interaction_id:         Optional[int] = None


class CopilotFeedbackRequest(BaseModel):
    was_helpful: bool


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.post(
    "/llm/ask",
    response_model=AskResponse,
    summary="Ask the AI Performance Assistant",
    description=(
        "Natural language Q&A about PC gaming performance powered by llama3.2.\n\n"
        "With include_telemetry=true, live GPU/CPU/RAM metrics and detected bottlenecks "
        "are injected into the prompt — so answers reference YOUR actual numbers.\n\n"
        "Phase 7: Also retrieves relevant knowledge base context via FAISS semantic "
        "search, grounding answers in vetted hardware-specific guidance.\n\n"
        "Example questions:\n"
        "- Why is my GPU at 50%?\n"
        "- Why am I getting low FPS in Cyberpunk?\n"
        "- What settings should I change to hit 144 FPS?\n"
        "- Is my CPU bottlenecking my RTX 3050 Ti?\n"
        "- My GPU temperature is 89C — is that dangerous?\n"
        "- Should I enable DLSS or lower resolution for more FPS?"
    ),
)
def ask_llm(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_time = time.time()

    metrics = None
    issues  = []

    # ── Step 1: Fetch live telemetry + diagnostics for context ────────────────
    if request.include_telemetry:
        try:
            # Reuse existing singletons from telemetry route (no double-init)
            from src.api.routes.telemetry import get_collector, get_diagnostics_engine

            collector = get_collector()
            engine    = get_diagnostics_engine()
            metrics   = collector.collect_all()
            issues    = engine.analyze(metrics)

        except Exception as e:
            # Non-fatal: LLM still answers, just without live context
            print(f"[LLM] Warning: Telemetry unavailable — answering without context. {e}")
            metrics = None
            issues  = []

    # ── Step 2: Retrieve relevant knowledge base context (Phase 7) ────────────
    retrieved_docs = []
    try:
        from src.llm.knowledge_base import retrieve
        retrieved_docs = retrieve(request.question, k=3)
    except Exception as e:
        # Non-fatal: LLM still answers using general knowledge + telemetry only
        print(f"[LLM] Warning: Knowledge base retrieval unavailable. {e}")
        retrieved_docs = []

    # ── Step 3: Build prompt ──────────────────────────────────────────────────
    try:
        from src.llm.prompt_builder import build_prompt
        messages = build_prompt(
            question=request.question,
            metrics=metrics,
            issues=issues,
            retrieved_docs=retrieved_docs,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prompt building failed: {str(e)}"
        )

    # ── Step 4: Call Ollama ───────────────────────────────────────────────────
    try:
        import ollama

        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            options={
                "temperature": 0.7,   # slightly creative but still factual
                "num_predict": 300,   # max ~300 tokens = ~200 words, keeps it concise
            },
        )
        answer = response["message"]["content"].strip()

    except Exception as e:
        error_msg = str(e).lower()

        if "connection" in error_msg or "refused" in error_msg or "connect" in error_msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Ollama is not running. "
                    "Open the Ollama desktop app or run 'ollama serve' in a terminal, "
                    "then try again."
                ),
            )

        if "model" in error_msg and "not found" in error_msg:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Model '{MODEL_NAME}' not found in Ollama. "
                    f"Run: ollama pull {MODEL_NAME}"
                ),
            )

        raise HTTPException(
            status_code=500,
            detail=f"LLM call failed: {str(e)}"
        )

    elapsed = round(time.time() - start_time, 2)

    # ── Step 5: Log interaction to PostgreSQL (non-fatal if it fails) ─────────
    interaction_id = None
    try:
        interaction = CopilotInteraction(
            user_id=current_user.user_id,
            question=request.question,
            answer=answer,
            telemetry_included=(metrics is not None),
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        interaction_id = interaction.id
    except Exception as e:
        db.rollback()
        print(f"[LLM] Warning: failed to log interaction. {e}")

    return AskResponse(
        answer=answer,
        model=MODEL_NAME,
        question=request.question,
        telemetry_included=(metrics is not None),
        issues_detected=len(issues),
        knowledge_sources=list({d["source"] for d in retrieved_docs}),
        response_time_seconds=elapsed,
        interaction_id=interaction_id,
    )


@router.post(
    "/llm/feedback/{interaction_id}",
    summary="Submit Copilot Answer Feedback",
)
def submit_copilot_feedback(
    interaction_id: int,
    body: CopilotFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interaction = (
        db.query(CopilotInteraction)
        .filter(CopilotInteraction.id == interaction_id)
        .filter(CopilotInteraction.user_id == current_user.user_id)
        .first()
    )

    if not interaction:
        raise HTTPException(
            status_code=404,
            detail=f"Interaction {interaction_id} not found"
        )

    interaction.was_helpful = body.was_helpful
    db.commit()

    return {
        "status":      "success",
        "message":     "Feedback recorded — thank you!",
        "id":          interaction_id,
        "was_helpful": body.was_helpful,
    }