from __future__ import annotations

from typing import Any, Dict, List

FILTER_KEYS = ("market", "product", "brand", "type", "doc_id")


def format_rag_context(chunks: List[Dict[str, Any]]) -> str:
    # Convenience helper (your __init__.py was importing this earlier)
    parts: List[str] = []
    for c in chunks:
        meta = c.get("metadata") or {}
        doc_id = meta.get("doc_id", "")
        parts.append(f"[{doc_id}] {c.get('text','')}".strip())
    return "\n\n".join([p for p in parts if p])


def build_datapoint_row(
        *,
        datapoint_id: str,
        embedding: List[float],
        text: str,
        metadata: Dict[str, Any],
) -> Dict[str, Any]:
    md = dict(metadata or {})
    md.setdefault("doc_id", md.get("doc_id") or _doc_id_from_chunk_id(datapoint_id))

    # IMPORTANT: Matching Engine returns embedding_metadata only if you stored it
    embedding_metadata: Dict[str, Any] = {"text": text}
    for k in FILTER_KEYS:
        if k in md and md[k] is not None:
            embedding_metadata[k] = md[k]

    restricts: List[Dict[str, Any]] = []
    for k in FILTER_KEYS:
        v = md.get(k)
        if v is None:
            continue
        allow_list = _as_str_list(v)
        if not allow_list:
            continue
        restricts.append({"namespace": k, "allow_list": allow_list})

    return {
        "id": datapoint_id,
        "embedding": embedding,
        "embedding_metadata": embedding_metadata,
        "restricts": restricts,
        "numeric_restricts": [],
    }


def _as_str_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x is not None and str(x) != ""]
    return [str(v)]


def _doc_id_from_chunk_id(chunk_id: str) -> str:
    return chunk_id.split("::", 1)[0] if "::" in chunk_id else chunk_id
