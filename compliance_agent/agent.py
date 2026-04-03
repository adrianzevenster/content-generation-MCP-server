import json
from typing import Dict, Any

from google.adk.agents.llm_agent import LlmAgent
from google.genai import types


def _make_instruction() -> str:
    return """
You are a compliance reviewer for financial-services advertising.

You receive:
- 'ad_copy': the plain text of an advertisement.
- 'channel': where it will be shown (e.g. META, SEARCH, LINKEDIN).
- 'country': the main jurisdiction (e.g. NG, KE, ZA).

Your task:
1. Check for potential issues: misleading claims, implied guarantees, unclear fees,
   or language that could violate financial advertising guidelines.
2. Suggest safer rewrites if needed.
3. Return a STRICT JSON object with fields:
   - approved: boolean (true if it can be published as-is)
   - issues: array of strings describing problems
   - suggested_text: string (the best compliant version of the ad)
Always return valid JSON ONLY. No surrounding text.
""".strip()


def build_compliance_agent() -> LlmAgent:
    """
    Build the ComplianceAgent as an A2A-compatible ADK LlmAgent.
    """
    return LlmAgent(
        model="gemini-2.0-flash",
        name="moniepoint_compliance_agent",
        description="Reviews ad copy for compliance and returns JSON with an approval decision.",
        instruction=_make_instruction(),
        global_instruction=(
            "Only output JSON. Do not include any commentary outside of the JSON object."
        ),
    )
