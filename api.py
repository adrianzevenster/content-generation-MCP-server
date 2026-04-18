import os
import json
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from shared.context_tools import get_brand_guidelines, get_product_details

from ad_copy_agent.agent import (
    build_ad_copy_agent,
    build_fastfinance_ad_copy_agent,
    build_simple_echo_agent,
    build_school_of_hard_knocks_agent,
)

from shared.bigquery_writer import (
    ensure_bigquery_dataset_and_table,
    write_agent_result_to_bigquery,
    write_hardknocks_result_to_bigquery,
)

try:
    from rag.config import load_rag_config
    from rag.retriever import VertexVectorSearchRetriever
    from rag.formatting import format_rag_context
except Exception:
    load_rag_config = None
    VertexVectorSearchRetriever = None
    format_rag_context = None


load_dotenv()

APP_NAME = "adcopy-service"
FASTFINANCE_APP_NAME = "fastfinance-adcopy-service"
HARD_KNOCKS_APP_NAME = "hard-knocks-service"
USER_ID = "api-user"

COMPLIANCE_URL = os.getenv("COMPLIANCE_API_URL", "http://localhost:8001/reviewAd")

session_service = InMemorySessionService()

moniepoint_adcopy_agent = build_ad_copy_agent(compliance_base_url=None)
moniepoint_adcopy_runner = Runner(
    agent=moniepoint_adcopy_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

fastfinance_adcopy_agent = build_fastfinance_ad_copy_agent(compliance_base_url=None)
fastfinance_adcopy_runner = Runner(
    agent=fastfinance_adcopy_agent,
    app_name=FASTFINANCE_APP_NAME,
    session_service=session_service,
)

simple_agent = build_simple_echo_agent()
simple_runner = Runner(
    agent=simple_agent,
    app_name="simple-echo-service",
    session_service=session_service,
)

hard_knocks_agent = build_school_of_hard_knocks_agent()
hard_knocks_runner = Runner(
    agent=hard_knocks_agent,
    app_name=HARD_KNOCKS_APP_NAME,
    session_service=session_service,
)

app = FastAPI(title="Skywalker Shares Ad Copy Service (ADK + Compliance)")

rag_retriever = None
rag_enabled = False


@app.on_event("startup")
async def startup_event() -> None:
    ensure_bigquery_dataset_and_table()

    global rag_retriever, rag_enabled

    if load_rag_config is None or VertexVectorSearchRetriever is None:
        rag_enabled = False
        rag_retriever = None
        print("[RAG] rag module not available; continuing without RAG.")
        return

    cfg = load_rag_config()

    if not cfg.index_endpoint_resource_name or not cfg.deployed_index_id:
        rag_enabled = False
        rag_retriever = None
        print("[RAG] Missing RAG_INDEX_ENDPOINT_RESOURCE_NAME or RAG_DEPLOYED_INDEX_ID; continuing without RAG.")
        return

    try:
        rag_retriever = VertexVectorSearchRetriever(cfg)
        rag_enabled = True
        print("[RAG] Vertex Vector Search retriever initialized.")
    except Exception as exc:
        rag_enabled = False
        rag_retriever = None
        print(f"[RAG] Failed to initialize retriever; continuing without RAG. Error: {exc}")


class GenerateAdRequest(BaseModel):
    prompt: str
    channel: Optional[str] = None
    brand: Optional[str] = "SkywalkerShares"
    product_id: Optional[str] = None
    country: Optional[str] = None


class GenerateAdResponse(BaseModel):
    ad_copy: str
    raw_events_truncated: Optional[bool] = None


class SimpleRequest(BaseModel):
    prompt: str


class SimpleResponse(BaseModel):
    text: str


class HardKnocksRequest(BaseModel):
    prompt: str


class HardKnocksResponse(BaseModel):
    advice: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "rag_enabled": rag_enabled}


@app.post("/simpleTest", response_model=SimpleResponse)
async def simple_test(req: SimpleRequest) -> SimpleResponse:
    session = await session_service.create_session(
        app_name="simple-echo-service",
        user_id="test-user",
        state={},
    )

    content = types.Content(role="user", parts=[types.Part(text=req.prompt)])
    text_chunks: List[str] = []

    async for event in simple_runner.run_async(
            user_id="test-user",
            session_id=session.id,
            new_message=content,
    ):
        is_final = getattr(event, "is_final_response", None)
        final = is_final() if callable(is_final) else (
                getattr(event, "final_response", False) or getattr(event, "is_final", False)
        )

        if final and getattr(event, "content", None):
            parts = getattr(event.content, "parts", None) or []
            for part in parts:
                if getattr(part, "text", None):
                    text_chunks.append(part.text)

    return SimpleResponse(text="".join(text_chunks) if text_chunks else "[no text from simple agent]")


def _build_retrieval_query(req: GenerateAdRequest) -> str:
    bits = [req.prompt]
    if req.brand:
        bits.append(f"brand={req.brand}")
    if req.product_id:
        bits.append(f"product_id={req.product_id}")
    if req.country:
        bits.append(f"market={req.country}")
    if req.channel:
        bits.append(f"channel={req.channel}")
    return " | ".join(bits)

def _fallback_product_details(product_id: Optional[str], brand: str, country: Optional[str]) -> Optional[Dict[str, Any]]:
    if not product_id:
        return None

    base = {
        "product_id": product_id,
        "brand": brand,
        "market": country,
        "positioning": "Business account for SMEs",
        "safe_benefits": [
            "separate business and personal finances",
            "track incoming and outgoing transactions",
            "support day-to-day business payments",
            "help with basic cash flow management",
        ],
        "disallowed_claims": [
            "guaranteed approvals",
            "risk-free profits",
            "instant account opening time guarantees",
            "lowest fees claims",
        ],
        "cta_options": ["Learn More", "Get Started", "Open an Account"],
    }

    if product_id == "skywalkershares_business_account":
        base["name"] = "SkywalkerShares Business Account"
        base["audience"] = "Nigerian SMEs"
        base["notes"] = "Keep claims generic unless specific details are provided elsewhere."

    return base


def _build_restricts(req: GenerateAdRequest) -> Optional[List[Dict[str, Any]]]:
    restricts: List[Dict[str, Any]] = []
    if req.country:
        restricts.append({"namespace": "market", "allow": [req.country]})
    if req.product_id:
        restricts.append({"namespace": "product", "allow": [req.product_id]})
    return restricts or None


@app.post("/generateAd", response_model=GenerateAdResponse)
async def generate_ad(req: GenerateAdRequest) -> GenerateAdResponse:
    brand_name = req.brand or "SkywalkerShares"
    brand_lower = brand_name.lower()

    if brand_lower in {"fastfinance", "fast finance", "fastfinance ltd"}:
        runner = fastfinance_adcopy_runner
        app_name = FASTFINANCE_APP_NAME
    else:
        runner = moniepoint_adcopy_runner
        app_name = APP_NAME

    session = await session_service.create_session(
        app_name=app_name,
        user_id=USER_ID,
        state={},
    )
    session_id = session.id

    rag_block: str = ""
    rag_debug: List[Dict[str, Any]] = []
    retrieval_query: Optional[str] = None
    restricts: Optional[List[Dict[str, Any]]] = None

    if rag_enabled and rag_retriever is not None and format_rag_context is not None:
        try:
            retrieval_query = _build_retrieval_query(req)
            restricts = _build_restricts(req)

            chunks = rag_retriever.retrieve(
                retrieval_query,
                k=6,
                restricts=restricts,
            )

            rag_block = format_rag_context(chunks)
            rag_debug = [{"id": c.id, "score": c.score, "meta": c.metadata} for c in chunks]
        except Exception as exc:
            print(f"[RAG] Retrieval failed (continuing without RAG context): {exc}")
            rag_block = ""
            rag_debug = []

            query_parts: List[str] = [req.prompt]

    query_parts.append(
        "Instruction: Use only claims supported by [RAG_CONTEXT], [PRODUCT_DETAILS], and [BRAND_GUIDELINES]. "
        "If details are provided there, do NOT say you lack details; instead, write compliant copy using those details."
    )
    query_parts.append("Output format: Provide 3 variants. Each variant must include HEADLINE, BODY, CTA.")


    if rag_block:
        query_parts.append("\n[RAG_CONTEXT]\n" + rag_block)

    if req.channel:
        query_parts.append(f"Channel: {req.channel}")
    if req.brand:
        query_parts.append(f"Brand: {req.brand}")
    if req.product_id:
        query_parts.append(f"Product ID: {req.product_id}")
    if req.country:
        query_parts.append(f"Country: {req.country}")

    brand_guidelines = get_brand_guidelines(brand_name)
    product_details = get_product_details(req.product_id) if req.product_id else None
    if (not product_details) or (isinstance(product_details, dict) and product_details.get("status") != "ok"):
        product_details = _fallback_product_details(req.product_id, brand_name, req.country)


    print(f"[PRODUCT] product_id={req.product_id} has_details={bool(product_details)}")


    query_parts.append("\n[BRAND_GUIDELINES]\n" + json.dumps(brand_guidelines, indent=2))
    if product_details:
        query_parts.append("\n[PRODUCT_DETAILS]\n" + json.dumps(product_details, indent=2))

    full_query = "\n".join(query_parts)
    content = types.Content(role="user", parts=[types.Part(text=full_query)])

    final_text_chunks: List[str] = []
    any_events = False

    try:
        async for event in runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=content,
        ):
            any_events = True

            is_final = getattr(event, "is_final_response", None)
            final = is_final() if callable(is_final) else (
                    getattr(event, "final_response", False) or getattr(event, "is_final", False)
            )

            if final and getattr(event, "content", None):
                parts = getattr(event.content, "parts", None) or []
                for part in parts:
                    if getattr(part, "text", None):
                        final_text_chunks.append(part.text)

    except Exception as exc:
        print(f"[ERROR] ADK runner failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}")

    if not any_events:
        ad_text = "[no events from adcopy agent]"
        approved = True
        compliance: Dict[str, Any] = {}
    else:
        ad_text = "".join(final_text_chunks) if final_text_chunks else "[events received but no text in final response]"
        compliance = {}
        approved = True

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    COMPLIANCE_URL,
                    json={
                        "channel": req.channel,
                        "country": req.country,
                        "ad_text": ad_text,
                    },
                    timeout=30.0,
                )
                resp.raise_for_status()
                compliance = resp.json()
                approved = compliance.get("approved", True)
                suggested_text = compliance.get("suggested_text") or ad_text
                if not approved:
                    print("[INFO] Compliance requested rewrite.")
                    ad_text = suggested_text
        except Exception as exc:
            print(f"[WARN] Compliance service error: {exc}")

    agent_result: Dict[str, Any] = {
        "request": {
            "prompt": req.prompt,
            "channel": req.channel,
            "brand": req.brand,
            "product_id": req.product_id,
            "country": req.country,
        },
        "ad_output": {"text": ad_text},
        "compliance": {"approved": approved, "raw": compliance},
        "rag": {
            "enabled": bool(rag_block),
            "retrieval_query": retrieval_query,
            "restricts": restricts,
            "results_count": len(rag_debug),
            "top_k": rag_debug,
        },
        "meta": {
            "created_by_agent": app_name,
            "user_id": USER_ID,
            "trace_id": None,
        },
    }

    try:
        write_agent_result_to_bigquery(agent_result)
    except Exception as exc:
        print(f"[WARN] Failed to persist to BigQuery: {exc}")

    return GenerateAdResponse(ad_copy=ad_text)


@app.post("/hardKnocks", response_model=HardKnocksResponse)
async def hard_knocks(req: HardKnocksRequest) -> HardKnocksResponse:
    session = await session_service.create_session(
        app_name=HARD_KNOCKS_APP_NAME,
        user_id=USER_ID,
        state={},
    )

    content = types.Content(role="user", parts=[types.Part(text=req.prompt)])

    chunks: List[str] = []
    any_events = False

    try:
        async for event in hard_knocks_runner.run_async(
                user_id=USER_ID,
                session_id=session.id,
                new_message=content,
        ):
            any_events = True

            is_final = getattr(event, "is_final_response", None)
            final = is_final() if callable(is_final) else (
                    getattr(event, "final_response", False) or getattr(event, "is_final", False)
            )

            if final and getattr(event, "content", None):
                parts = getattr(event.content, "parts", None) or []
                for part in parts:
                    if getattr(part, "text", None):
                        chunks.append(part.text)

    except Exception as exc:
        print(f"[ERROR] HardKnocks runner failed: {exc}")
        raise HTTPException(status_code=500, detail=f"HardKnocks agent failed: {exc}")

    advice_text = (
        "[no events from hard-knocks agent]" if not any_events
        else ("".join(chunks) if chunks else "[events received but no text in final response]")
    )

    hk_result: Dict[str, Any] = {
        "request": {"prompt": req.prompt},
        "advice_output": {"text": advice_text},
        "meta": {
            "created_by_agent": HARD_KNOCKS_APP_NAME,
            "user_id": USER_ID,
            "trace_id": None,
        },
    }

    try:
        write_hardknocks_result_to_bigquery(hk_result)
    except Exception as exc:
        print(f"[WARN] Failed to persist HardKnocks to BigQuery: {exc}")

    return HardKnocksResponse(advice=advice_text)
