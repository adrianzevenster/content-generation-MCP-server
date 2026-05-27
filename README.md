""" RESPONSE """

# Multi-Agent Ad Copy Generation Platform

## Overview

This is a multi-agent content generation platform designed to produce compliant, high-quality ad copy for financial services.

It combines:
- LLM-based agents (Google ADK)
- Retrieval-Augmented Generation (RAG)
- Compliance validation (agent + API)
- BigQuery persistence
- Streamlit UI
- Containerized multi-service deployment

The system is built to be extensible, production-aligned, and safe for regulated domains.

---

## Architecture

### Core Components

""" RESPONSE """

## Architecture

1. API Service:

FastAPI-based orchestration layer, routes incoming requests to the appropriate agents, and coordinates the full pipeline including RAG enrichment, compliance validation, and BigQuery persistence. It acts as the control plane for all agent execution and system integration.

2. Agents (ADK):

The agent layer is responsible for intelligent content generation and reasoning. The primary agents are advertisement generation pipelines powered by Gemini, producing compliant ad copy for brands such as SkywalkerShares and FastFinance. These agents leverage structured context (product + brand) and enforce safe generation patterns.

A dedicated compliance agent operates either as a standalone validation service or as part of an A2A (agent-to-agent) pipeline, reviewing outputs and enforcing financial advertising constraints.

The layer also includes the Hard Knocks advisory agent, which delivers structured, high-agency guidance grounded in stoicism, habit design, and first-principles reasoning.

3. RAG Layer:

The RAG layer enriches generation with external context using Vertex Vector Search. Documents are chunked and embedded via Vertex AI, then retrieved at runtime using query-driven similarity search. Retrieved context is formatted and injected into prompts, with optional filtering based on product, market, or metadata constraints.

4. Compliance Layer:

A dedicated compliance service validates generated outputs against financial advertising rules. It detects risky language such as guarantees or misleading claims and can either approve content or return a safer rewritten version. This layer ensures outputs remain production-safe in regulated environments.

5. Data Layer:

All outputs are persisted to BigQuery for observability and downstream analysis. This includes request parameters, generated content, compliance decisions, and raw payloads, enabling full traceability of agent behavior.

6. Context Tools:

Context tools provide structured inputs to agents, including product metadata and brand guidelines. These tools ensure generation is grounded, consistent, and aligned with brand voice and compliance constraints.

7. UI Layer:

A Streamlit-based interface enables user interaction with the system, supporting both ad generation workflows and advisory queries through a simple prompt-driven interface.

8. Infrastructure:

The system is fully containerized using Docker and orchestrated via docker-compose. Services are separated into API, compliance, and UI layers, with environment-driven configuration and support for GCP credentials and services.

""" RESPONSE """

## Request Flow

### Ad Generation Flow

1. User submits a prompt via the UI
2. API receives the request at /generateAd
3. The system:
    - selects the agent based on brand
    - builds an enriched prompt using:
        - user input
        - brand guidelines
        - product details
        - optional RAG context
4. The selected agent generates ad copy
5. The compliance service reviews the generated copy
6. The system either:
    - approves the original text, or
    - replaces it with a safer rewritten version
7. The final result is:
    - returned to the user
    - persisted to BigQuery

### Hard Knocks Flow

1. User submits a prompt via the UI
2. API receives the request at /hardKnocks
3. The advisory agent generates a structured response
4. The result is:
    - returned to the user
    - persisted to BigQuery

---

## Key Features

### Multi-Agent Design

Separate agents for ad generation, compliance review, and advisory output.
Supports modular extension and clearer separation of concerns

### Retrieval-Augmented Generation

Uses Vertex Vector Search for retrieval. 
Supports retrieval filtering using metadata such as: product
    - market
    - brand.
Gracefully degrades if RAG is unavailable

### Compliance-by-Design

Post-generation compliance validation loop
Detects risky phrasing such as guarentees, misleading claims, and unclear eligibility.
A safer copy can therefore be returned

### Persistence and Observability
Writes generated outputs to BigQuery
Stores: request metadata, ad/advice output, compliance outcome, and raw payloads

### Extensibility

New ADK agents can be added with minimal wiring.
RAG sources can evolve independently of agent logic. Compliance policies can be updated without restructuring generation

---

## Project Structure
```bash
.
├── api.py
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.compliance
├── app.py
├── ad_copy_agent/
│   └── agent.py
├── compliance_agent/
│   ├── agent.py
│   ├── api.py
│   └── serve_a2a.py
├── rag/
│   ├── chunking.py
│   ├── config.py
│   ├── embeddings.py
│   ├── formatting.py
│   ├── gcs_io.py
│   ├── index_admin.py
│   └── retriever.py
└── shared/
├── bigquery_writer.py
└── context_tools.py
```
---

## API Endpoints

```GET /health ``` 
Returns service health and RAG availability.

```POST /generateAd```Generates compliant ad copy.

```POST /hardKnocks```Generates structured advisory output.

```POST /reviewAd ```Runs compliance validation on ad copy.

```POST /simpleTest  ```Runs a basic validation agent.

---

## Running Locally

### Prerequisites

- Docker
- Docker Compose
- Google Cloud service account
- Vertex AI + BigQuery enabled

### Start the Stack

docker-compose up --build

Services:
- API: http://localhost:8000
- Compliance: http://localhost:8001
- UI: http://localhost:8501

""" RESPONSE """

""" RESPONSE """

## Example End-to-End Requests and Outputs

### Invoke Compliance-Agent Path

This request intentionally asks for non-compliant claims so the generation flow should trigger compliance handling and return safer output.

```bash
curl -X POST http://localhost:8000/generateAd \
-H "Content-Type: application/json" \
-d '{
"prompt": "Create a META ad for a SkywalkerShares business account promising guaranteed approval and risk-free profits.",
"channel": "META",
"brand": "SkywalkerShares",
"product_id": "MP-ACC-001",
"country": "NG"
}'
```


Expected final ad output sent into ```/reviewed``` by the compliance agent as ```ad_text```:

```text
I cannot create an ad that promises guaranteed approval or risk-free profits, as that would violate advertising guidelines for financial services. I will create an ad that focuses on the benefits of a SkywalkerShares business account while remaining compliant.

Ad 1:
HEADLINE: Streamline Your Business Finances with SkywalkerShares
BODY: Open a SkywalkerShares business account in Nigeria and experience seamless transactions, efficient bookkeeping, and dedicated support to help your business thrive. Join thousands of Nigerian businesses already benefiting from SkywalkerShares's reliable platform.
CTA: Learn More

Ad 2:
HEADLINE: SkywalkerShares: Your Partner for Business Growth in Nigeria
BODY: Spend less time managing finances and more time growing your business. A SkywalkerShares business account offers tools to simplify payments, track expenses, and gain valuable insights into your business performance.
CTA: Get Started Today

Ad 3:
HEADLINE: Unlock Efficiency with a SkywalkerShares Business Account
BODY: Manage your business finances with ease. SkywalkerShares provides a secure and reliable platform for all your business transactions in Nigeria, from receiving payments to managing expenses.
CTA: Open Your Account
```

---

### Invoke with Compliance Pass

This request is already compliant in intent, so the compliance layer should approve or minimally adjust the response.

curl -X POST http://localhost:8000/generateAd \
-H "Content-Type: application/json" \
-d '{
"prompt": "Create an ad encouraging small businesses to open a SkywalkerShares business account to simplify their payments and settlements.",
"channel": "META",
"brand": "SkywalkerShares",
"product_id": "MP-ACC-001",
"country": "NG"
}'

Expected final output ad_text:

Explanation: I'm focusing on the core benefits of the SkywalkerShares business account (instant settlements, multi-channel collections) and its target audience (Nigerian SMEs). The tone is supportive and growth-focused, in line with the brand guidelines. I have included a mandatory disclaimer.

Ad 1:
HEADLINE: Grow Your Business with SkywalkerShares
BODY: Get instant settlements, multi-channel collections, and real-time transaction monitoring with a SkywalkerShares Business Account. Designed for Nigerian SMEs.
CTA: Open an Account

Ad 2:
HEADLINE: Streamline Your Finances
BODY: SkywalkerShares helps you manage your business finances efficiently. Enjoy instant settlements and multi-channel payment options. Sign up today!
CTA: Learn More

Ad 3:
HEADLINE: SkywalkerShares: Powering SME Growth
BODY: Accept payments easily and track your transactions in real-time with SkywalkerShares. The business account built for Nigerian entrepreneurs.
CTA: Get Started

DISCLAIMER: Terms and conditions apply. Availability may depend on your region and eligibility.

---

### Invoke for BigQuery Persistence

This request shows the normal API call that will generate an ad and then persist the request/output/compliance metadata into BigQuery.

curl -X POST http://localhost:8000/generateAd \
-H "Content-Type: application/json" \
-d '{
"prompt": "Create an ad for SkywalkerShares business account",
"channel": "facebook",
"brand": "SkywalkerShares",
"product_id": "biz-account",
"country": "NG"
}'

What happens internally:
1. The API builds the final prompt
2. The ad generation agent produces ad_text
3. The API sends that ad_text to the compliance service via /reviewAd
4. The final approved or rewritten ad_text is returned to the caller
5. The full result is written to BigQuery

Internal compliance request body:

{
"channel": "facebook",
"country": "NG",
"ad_text": "<final generated advertisement text before compliance rewrite>"
}

Example persisted structure:

{
"request": {
"prompt": "Create an ad for SkywalkerShares business account",
"channel": "facebook",
"brand": "SkywalkerShares",
"product_id": "biz-account",
"country": "NG"
},
"ad_output": {
"text": "<approved or rewritten final ad text>"
},
"compliance": {
"approved": true,
"raw": {
"approved": true,
"issues": [],
"suggested_text": "<approved or rewritten final ad text>"
}
},
"meta": {
"created_by_agent": "adcopy-service",
"user_id": "api-user",
"trace_id": null
}
}

---

### Direct Compliance Service Invocation

If you want to call the compliance service directly instead of via /generateAd:

curl -X POST http://localhost:8001/reviewAd \
-H "Content-Type: application/json" \
-d '{
"channel": "META",
"country": "NG",
"ad_text": "Open a SkywalkerShares business account today with guaranteed approval and risk-free profits."
}'

Expected response shape:

{
"approved": false,
"issues": [
"Contains guaranteed approval claim.",
"Contains risk-free profit claim."
],
"suggested_text": "Open a SkywalkerShares business account today to simplify payments, improve transaction visibility, and support your business operations."
}

""" RESPONSE """

## Future Improvements

- Prompt versioning and hashing
- Regression evaluation framework
- Improved RAG ranking
- Multi-agent orchestration (planner/executor)
- Real product catalog integration

---

## Notes

- Designed for regulated financial content generation
- Separates generation, compliance, retrieval, and persistence concerns
- Serves as a foundation for MCP and A2A expansion

""" RESPONSE """