# compliance_agent/api.py

from textwrap import dedent
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

def _compliance_instruction() -> str:
    return dedent(
        """
        You are a compliance reviewer for financial-services advertising.

        You receive:
        - ad_text: the plain text of an advertisement.
        - channel: where it will be shown (e.g. META, SEARCH, LINKEDIN).
        - country: the main jurisdiction (e.g. NG, KE, ZA).

        Your task:
        1. Check for potential issues: misleading promises, implied guarantees,
           "risk-free" language, unclear fees/eligibility, or anything that
           may violate typical financial advertising guidelines.
        2. Suggest a safer rewrite if needed.
        3. Return STRICT JSON only, with the following fields:
           - approved: boolean
           - issues: array of strings (can be empty if approved)
           - suggested_text: string (the best compliant version to use)

        Always respond with valid JSON ONLY, no extra commentary.
        """
    ).strip()


def build_compliance_agent() -> LlmAgent:
    return LlmAgent(
        model="gemini-2.0-flash",
        name="moniepoint_compliance_agent",
        description="Reviews ad copy for compliance and returns JSON with an approval decision.",
        instruction=_compliance_instruction(),
        global_instruction="Only output JSON. No text outside the JSON object.",
    )

class ReviewAdRequest(BaseModel):
    channel: Optional[str] = None
    country: Optional[str] = None
    ad_text: str


class ReviewAdResponse(BaseModel):
    approved: bool
    issues: List[str]
    suggested_text: str


app = FastAPI(title="Moniepoint Compliance Agent")

session_service = InMemorySessionService()
agent = build_compliance_agent()
runner = Runner(
    agent=agent,
    app_name="compliance-service",
    session_service=session_service,
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/reviewAd", response_model=ReviewAdResponse)
async def review_ad(req: ReviewAdRequest) -> ReviewAdResponse:
    session = await session_service.create_session(
        app_name="compliance-service",
        user_id="compliance-user",
        state={},
    )

    prompt_parts = [f"ad_text: {req.ad_text}"]
    if req.channel:
        prompt_parts.append(f"channel: {req.channel}")
    if req.country:
        prompt_parts.append(f"country: {req.country}")
    prompt = "\n".join(prompt_parts)

    content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    final_text = ""

    async for event in runner.run_async(
            user_id="compliance-user",
            session_id=session.id,
            new_message=content,
    ):
        # Debug log
        print("COMPLIANCE EVENT:", event)
        is_final = getattr(event, "is_final_response", None)
        if callable(is_final):
            final = is_final()
        else:
            final = getattr(event, "final_response", False) or getattr(event, "is_final", False)

        if final and getattr(event, "content", None):
            parts = getattr(event.content, "parts", None)
            if parts:
                for part in parts:
                    if getattr(part, "text", None):
                        final_text += part.text

    if not final_text:
        return ReviewAdResponse(
            approved=True,
            issues=["No response from compliance agent; auto-approving."],
            suggested_text=req.ad_text,
        )

    import json

    clean = final_text.strip()

    if clean.startswith("```"):
        lines = clean.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        clean = "\n".join(lines).strip()
    try:
        data = json.loads(clean)
        approved = bool(data.get("approved", True))
        issues = data.get("issues") or []
        suggested_text = data.get("suggested_text") or req.ad_text

    except Exception as exc:
        return ReviewAdResponse(
            approved=True,
            issues=[f"Failed to parse compliance JSON: {exc}", clean],
            suggested_text=req.ad_text,
        )

    return ReviewAdResponse(
        approved=approved,
        issues=issues,
        suggested_text=suggested_text,
    )