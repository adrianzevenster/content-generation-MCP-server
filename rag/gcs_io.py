from __future__ import annotations

import json
from typing import Iterable, Dict, Any, Tuple, Optional
from google.cloud import storage


def _split_gs_uri(gs_uri: str) -> Tuple[str, str]:
    if not gs_uri.startswith("gs://"):
        raise ValueError(f"Expected gs:// URI, got: {gs_uri}")
    parts = gs_uri[5:].split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    return bucket, prefix


def ensure_bucket_exists(bucket_uri: str, location: Optional[str] = None) -> None:
    bucket_name, _ = _split_gs_uri(bucket_uri)
    client = storage.Client()
    try:
        client.get_bucket(bucket_name)
        return
    except Exception:
        bucket = client.bucket(bucket_name)
        if location:
            bucket.location = location
        client.create_bucket(bucket)


def upload_json_lines_as_json(
        *,
        bucket_uri: str,
        object_path: str,
        rows: Iterable[Dict[str, Any]],
) -> str:
    """
    Writes newline-delimited JSON to GCS and returns gs://... URI.
    (We keep the name you’re calling from scripts.)
    """
    bucket_name, bucket_prefix = _split_gs_uri(bucket_uri)
    full_path = f"{bucket_prefix.rstrip('/')}/{object_path.lstrip('/')}".strip("/")

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(full_path)

    data = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    blob.upload_from_string(data, content_type="application/json")

    return f"gs://{bucket_name}/{full_path}"
