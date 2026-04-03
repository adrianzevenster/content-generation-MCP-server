from typing import Dict, Any


def get_product_details(product_id: str) -> Dict[str, Any]:
    demo_catalog = {
        # keep the old alias if you want
        "MP-ACC-001": {
            "name": "Moniepoint Business Account",
            "category": "financial_product",
            "features": [
                "Instant settlements",
                "Multi-channel collections",
                "Realtime transaction monitoring",
            ],
            "target_segment": "SMEs in Nigeria and Kenya",
            "tone": "trustworthy, growth-focused, supportive",
        },

        # ✅ NEW: match what your API sends
        "moniepoint_business_account": {
            "name": "Moniepoint Business Account",
            "category": "financial_product",
            "features": [
                "Business account for SMEs",
                "Helps separate business and personal finances",
                "Supports day-to-day business transactions",
            ],
            "target_segment": "SMEs in Nigeria",
            "tone": "trustworthy, growth-focused, supportive",
            "note": "Generic fallback; real product facts should live in RAG sources.",
        },
    }

    product = demo_catalog.get(product_id)
    if not product:
        return {
            "status": "not_found",
            "product_id": product_id,
            "message": "Unknown product_id; use generic copy.",
        }

    return {
        "status": "ok",
        "product_id": product_id,
        "product": product,
    }



def get_brand_guidelines(brand: str) -> Dict[str, Any]:
    brand_lower = (brand or "").lower()

    # -----------------------
    # Moniepoint Brand Voice
    # -----------------------
    if brand_lower in {"moniepoint", "moniepoint bank", "moniepoint inc"}:
        return {
            "status": "ok",
            "brand": "Moniepoint",
            "voice": {
                "tone": "conversational, clear, financially responsible",
                "avoid": [
                    "guaranteeing returns",
                    "overpromising approvals",
                    "complex financial jargon",
                ],
                "do": [
                    "speak plainly",
                    "emphasize safety and compliance",
                    "focus on small-business empowerment",
                ],
            },
            "channel_style": {
                "meta": "short, punchy one-liners; emoji allowed if appropriate",
                "search": "benefit-led headlines, concrete proof, strong CTA",
                "linkedin": "professional but warm, include detail and proof points",
            },
            "mandatory_disclaimers": [
                "Terms and conditions apply.",
                "Availability may depend on your region and eligibility.",
            ],
        }

    # -----------------------
    # FastFinance Brand Voice
    # -----------------------
    if brand_lower in {"fastfinance", "fast finance", "fastfinance ltd"}:
        return {
            "status": "ok",
            "brand": "FastFinance",

            # NEW: high-level context so the model can write “targeted” copy even when prompt is vague
            "positioning": (
                "FastFinance is a digital-first finance platform for modern businesses and professionals. "
                "It helps customers manage money with speed, clarity, and control."
            ),
            "target_audience": [
                "time-poor founders",
                "growing SMEs",
                "independent professionals",
                "ops and finance managers",
            ],
            "value_props": [
                "fast setup",
                "clear pricing",
                "simple onboarding",
                "digital-first account management",
                "visibility and control over transactions",
            ],

            "voice": {
                "tone": "confident, direct, modern, no-nonsense",
                "avoid": [
                    "hype or exaggerated claims",
                    "guaranteed outcomes",
                    "fear-based messaging",
                    "casual slang or emojis",
                    "income/wealth promises",
                ],
                "do": [
                    "emphasize speed, clarity, and control",
                    "use active voice and concrete outcomes",
                    "keep claims verifiable and conservative",
                    "offer a clear next step",
                ],
            },

            # NEW: when the prompt is garbage/vague, the model should still have a safe lane
            "safe_offer_defaults": {
                "default_product": "FastFinance Business Account",
                "default_goal": "open an account and manage business finances efficiently",
                "default_cta": "Get started",
                "default_proof_points": [
                    "fast setup",
                    "clear pricing",
                    "simple onboarding",
                ],
            },

            # NEW: explicitly block the “make money fast” angle
            "prohibited_angles": [
                "fast money / get rich quick",
                "income claims (earn X, increase your income)",
                "guaranteed approvals",
                "risk-free claims",
                "free money / bonuses unless verified",
            ],

            "channel_style": {
                "meta": "short, clear statements focused on efficiency and outcomes",
                "search": "direct value props, clarity over cleverness",
                "linkedin": "confident, professional, execution-oriented",
            },

            "mandatory_disclaimers": [
                "Terms and conditions apply.",
                "Eligibility and availability may vary.",
            ],

            # NEW: give the model examples in the right voice
            "example_messages": {
                "meta": [
                    "Move faster with a business account built for modern teams. Clear pricing. Simple setup.",
                    "Your money, under control—track transactions and manage cash flow with confidence.",
                ],
                "search": [
                    "FastFinance Business Account — Fast setup, clear pricing. Get started.",
                    "Business banking made simple — Open your FastFinance account today.",
                ],
                "linkedin": [
                    "FastFinance helps growing teams manage business finances with speed, clarity, and control. Apply in minutes.",
                ],
            },
        }


    # -----------------------
    # Default / Unknown Brand
    # -----------------------
    return {
        "status": "ok",
        "brand": brand,
        "voice": {
            "tone": "neutral, informative, customer-centric",
            "avoid": [],
            "do": [
                "be clear",
                "avoid making legal or financial guarantees",
            ],
        },
        "channel_style": {},
        "mandatory_disclaimers": [],
    }
