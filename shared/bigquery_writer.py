import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

import json

# -------------------------------------------------------------------
# CONFIG (override these with env vars in Docker / Cloud Run / local)
# -------------------------------------------------------------------

BQ_PROJECT_ID = (
        os.getenv("MONC_BQ_PROJECT_ID")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or "adg-delivery-moniepoint"
)
BQ_DATASET_ID = os.getenv("MONC_BQ_DATASET_ID", "monc_content")
BQ_TABLE_ID = os.getenv("MONC_BQ_TABLE_ID", "generated_ads_v2")


_client: Optional[bigquery.Client] = None
_bq_initialized = False


def _get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=BQ_PROJECT_ID)
    return _client


# ------------------------------------
# Dataset & table creation (code-first)
# ------------------------------------

def ensure_bigquery_dataset_and_table() -> None:
    """
    Ensure that the dataset and table exist in BigQuery.
    Safe to call multiple times (idempotent).
    """
    global _bq_initialized
    if _bq_initialized:
        return

    client = _get_client()

    # Dataset
    dataset_ref = bigquery.Dataset(f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}")
    try:
        client.get_dataset(dataset_ref)
    except NotFound:
        # Set region to match your project (e.g. "EU", "US", "europe-west1")
        dataset_ref.location = "EU"
        client.create_dataset(dataset_ref)

    # Table schema: 1 row per /generateAd call
    table_id = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"

    schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),

        bigquery.SchemaField("request_prompt", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("request_channel", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("request_brand", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("request_product_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("request_country", "STRING", mode="NULLABLE"),

        bigquery.SchemaField("ad_text", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("compliance_approved", "BOOL", mode="NULLABLE"),

        bigquery.SchemaField("created_by_agent", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("trace_id", "STRING", mode="NULLABLE"),

        bigquery.SchemaField("raw_agent_payload", "STRING", mode="NULLABLE"),

        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]

    table = bigquery.Table(table_id, schema=schema)

    try:
        client.get_table(table)
    except NotFound:
        client.create_table(table)

    _bq_initialized = True


# -----------------------------------
# Map your agent/API result to a row
# -----------------------------------

def _build_rows_from_agent_result(agent_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Expected structure (built in api.py):

    {
      "request": {...},
      "ad_output": {...},
      "compliance": {...},
      "meta": {...}
    }
    """
    request = agent_result.get("request", {})
    ad_output = agent_result.get("ad_output", {})
    compliance = agent_result.get("compliance", {})
    meta = agent_result.get("meta", {})

    now = datetime.now(timezone.utc).isoformat()

    row = {
        "id": str(uuid.uuid4()),

        "request_prompt": request.get("prompt"),
        "request_channel": request.get("channel"),
        "request_brand": request.get("brand"),
        "request_product_id": request.get("product_id"),
        "request_country": request.get("country"),

        "ad_text": ad_output.get("text"),
        "compliance_approved": compliance.get("approved"),

        "created_by_agent": meta.get("created_by_agent"),
        "user_id": meta.get("user_id"),
        "trace_id": meta.get("trace_id"),

        "raw_agent_payload": json.dumps(agent_result, ensure_ascii=False),

        "created_at": now,
    }

    return [row]


# -----------------------
# Public write function
# -----------------------

def write_agent_result_to_bigquery(agent_result: Dict[str, Any]) -> None:
    """
    Ensures dataset & table exist, then writes one row
    representing this call to /generateAd.
    """
    ensure_bigquery_dataset_and_table()

    client = _get_client()
    table_id = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
    rows_to_insert = _build_rows_from_agent_result(agent_result)

    if not rows_to_insert:
        return

    errors = client.insert_rows_json(table_id, rows_to_insert)

    if errors:
        raise RuntimeError(f"Failed to insert rows into BigQuery: {errors}")
