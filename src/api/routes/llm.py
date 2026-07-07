"""
POST /api/llm/ask
Natural language performance Q&A powered by Ollama (llama3.2).
Fetches live telemetry + diagnostics and injects them as context
so answers are specific to the user's actual hardware state.

Phase 7: Also retrieves relevant knowledge base context via FAISS
semantic search, grounding answers in vetted, hardware-specific
guidance rather than the LLM's general training knowledge alone.
"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
def ask_llm(request: AskRequest):
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

    return AskResponse(
        answer=answer,
        model=MODEL_NAME,
        question=request.question,
        telemetry_included=(metrics is not None),
        issues_detected=len(issues),
        knowledge_sources=list({d["source"] for d in retrieved_docs}),
        response_time_seconds=elapsed,
    )