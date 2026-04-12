import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://api:8000")

st.set_page_config(page_title="MONC Prompt UI", layout="centered")
st.title("MONC Ad Copy Generator")

BRAND_VOICES = {
    "Moniepoint (SME, supportive)": "Moniepoint",
    "FastFinance (direct, modern)": "FastFinance",
}

with st.form("prompt_form"):
    prompt = st.text_area("Prompt", height=140, placeholder="Describe the campaign, channel, product, market…")
    col1, col2 = st.columns(2)
    with col1:
        channel = st.text_input("Channel (optional)", value="META")

    brand_label = st.selectbox(
        "Brand voice",
        options=list(BRAND_VOICES.keys()),
        index=0,
    )

    brand = BRAND_VOICES[brand_label]

    with col2:
        product_id = st.text_input("Product ID (optional)", value="")
        country = st.text_input("Country (optional)", value="NG")

    submitted = st.form_submit_button("Generate")

if submitted:
    if not prompt.strip():
        st.warning("Please enter a prompt.")
        st.stop()

    payload = {
        "prompt": prompt,
        "channel": channel or None,
        "brand": brand or None,
        "product_id": product_id or None,
        "country": country or None,
    }

    try:
        r = requests.post(f"{API_BASE}/generateAd", json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        st.subheader("Result")
        ad_copy = (data.get("ad_copy") or "").strip()

        # Make single newlines behave like readable paragraphs in markdown
        ad_copy_md = (
            ad_copy.replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\n", "\n\n")
        )

        st.markdown(ad_copy_md)

    except Exception as e:
        st.error(f"Request failed: {e}")
        if "r" in locals():
            st.text(r.text)

# =========================
# School of Hard Knocks UI
# =========================

st.divider()
st.title("School of Hard Knocks")

st.markdown(
    """
<style>
/* Remove Streamlit's scrolling behavior for pre/code blocks */
div[data-testid="stMarkdownContainer"] pre {
  white-space: pre-wrap !important;
  word-break: break-word !important;
  overflow: visible !important;
  overflow-x: visible !important;
  overflow-y: visible !important;
}

/* Sometimes Streamlit wraps markdown in another div that scrolls */
div[data-testid="stMarkdownContainer"] {
  overflow: visible !important;
}
</style>
""",
    unsafe_allow_html=True,
)

st.caption(
    "Blunt, practical advice inspired by Stoicism, habit science, deep work, "
    "first-principles reasoning, and hard-earned experience."
)

hard_knocks_prompt = st.text_area(
    "What are you struggling with?",
    height=160,
    placeholder="e.g. I'm stuck in my career, distracted, and unsure what to focus on.",
)

if st.button("Get Hard Truth"):
    if not hard_knocks_prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        try:
            r = requests.post(
                f"{API_BASE}/hardKnocks",
                json={"prompt": hard_knocks_prompt},
                timeout=90,
            )
            r.raise_for_status()

            st.subheader("Response")
            advice = (r.json().get("advice") or "").strip()
            advice_md = (
                advice.replace("\r\n", "\n")
                .replace("\r", "\n")
                .replace("\n", "\n\n")
            )
            st.markdown(advice_md)

        except Exception as e:
            st.error(f"Request failed: {e}")
            if "r" in locals():
                st.text(r.text)
