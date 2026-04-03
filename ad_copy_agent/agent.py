from textwrap import dedent

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.function_tool import FunctionTool

from shared.context_tools import get_product_details, get_brand_guidelines


def _adcopy_instruction() -> str:
    return dedent(
        """
        You are a senior performance marketing copywriter for Moniepoint and similar financial services.

        You have access to tools:
        - get_product_details(product_id: str) -> returns structured product info
        - get_brand_guidelines(brand: str) -> returns brand voice and guardrails

        Your job:
        - Take the user's description of the campaign, channel, brand, product and market.
        - If a product_id or product name is mentioned, CALL get_product_details to understand the product.
        - If a brand is mentioned (e.g. Moniepoint), CALL get_brand_guidelines to understand tone and guardrails.
        - Infer the key value proposition and emotional angle.
        - Write 1–3 high-quality ad variants for the requested channel (META, SEARCH, LINKEDIN, etc.).
        - Keep language compliant and conservative for financial services (no guarantees, no "risk-free" claims).

        Output format:
        - Start with a 1–2 sentence explanation of the angle you chose.
        - Then provide 1–3 ad variants clearly labeled, for example:

          Explanation: ...
          
          Ad 1:
          HEADLINE: ...
          BODY: ...
          CTA: ...

          Ad 2:
          HEADLINE: ...
          BODY: ...
          CTA: ...

        If the user mentions a country (e.g. NG, KE, ZA), adapt wording slightly for that market.
        If product or brand info is missing from the tools, say so briefly and produce a generic but safe ad.
        """
    ).strip()


def build_ad_copy_agent(
        compliance_base_url: str | None = None,
) -> LlmAgent:
    """
    AdCopyAgent with function tools for product + brand context.
    No A2A / compliance yet
    """
    product_tool = FunctionTool(get_product_details)
    brand_tool = FunctionTool(get_brand_guidelines)

    return LlmAgent(
        model="gemini-2.0-flash",
        name="moniepoint_adcopy_agent",
        description="Generates channel-specific ad copy for Moniepoint products.",
        instruction=_adcopy_instruction(),
        tools=[product_tool, brand_tool],
    )

def build_simple_echo_agent() -> LlmAgent:
    return LlmAgent(
        model="gemini-2.0-flash",
        name="simple_echo_agent",
        description="Just repeats and lightly rewrites the user prompt.",
        instruction=(
            "You are a simple helper. When the user sends a message, "
            "restate their request and propose one short ad variant. "
            "Keep it under 3 sentences."
        ),
    )
