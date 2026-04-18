from __future__ import annotations

import glob
import json
import os
import time
from typing import Any, Dict, List

from google.cloud import aiplatform

from rag.config import load_rag_config
from rag.embeddings import VertexEmbeddingClient
from rag.gcs_io import ensure_bucket_exists, upload_json_lines_as_json
from rag.chunking import simple_text_chunker
from rag.index_admin import update_matching_engine_index


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_resource_docs() -> List[Dict[str, Any]]:
    root = _repo_root()
    candidates = [
        os.path.join(root, "rag", "sources"),
        os.path.join(root, "rag", "resources"),
    ]

    folder = next((p for p in candidates if os.path.isdir(p)), None)
    if not folder:
        raise RuntimeError(
            f"Missing sources folder. Create one of:\n- {candidates[0]}\n- {candidates[1]}"
        )

    files = sorted(glob.glob(os.path.join(folder, "*.json")))
    if not files:
        raise RuntimeError(f"No *.json docs found in {folder}")

    docs: List[Dict[str, Any]] = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)

        text = d.get("text") or d.get("content") or ""
        if not text.strip():
            raise RuntimeError(f"{os.path.basename(fp)} missing non-empty 'text' (or 'content') field")

        doc_id = d.get("doc_id") or os.path.splitext(os.path.basename(fp))[0]
        docs.append(
            {
                "doc_id": doc_id,
                "title": d.get("title") or doc_id,
                "source": d.get("source") or "internal",
                "type": d.get("type") or "unknown",
                "market": d.get("market") or "NG",
                "product": d.get("product") or "moniepoint",
                "text": text,
            }
        )

    return docs


def build_datapoint(
        *,
        chunk_id: str,
        embedding: List[float],
        text: str,
        doc_id: str,
        meta: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "id": chunk_id,
        "embedding": embedding,
        "embedding_metadata": {
            "text": text[:1800],
            "doc_id": doc_id,
            "title": meta.get("title", ""),
            "type": meta.get("type", ""),
            "market": meta.get("market", ""),
            "product": meta.get("product", ""),
            "source": meta.get("source", ""),
        },
        "restricts": [
            {"namespace": "doc_id", "allow_list": [doc_id]},
            {"namespace": "type", "allow_list": [str(meta.get("type", "unknown"))]},
            {"namespace": "market", "allow_list": [str(meta.get("market", "unknown"))]},
            {"namespace": "product", "allow_list": [str(meta.get("product", "unknown"))]},
        ],
        "numeric_restricts": [],
    }


def main() -> None:
    cfg = load_rag_config()
    if not cfg.index_resource_name:
        raise ValueError("RAG_INDEX_RESOURCE_NAME is not set.")

    docs = load_resource_docs()
    print(f"Loaded source docs: {len(docs)}")

    ensure_bucket_exists(cfg.gcs_bucket_uri, location=cfg.location)

    aiplatform.init(project=cfg.project, location=cfg.location)
    embedder = VertexEmbeddingClient(cfg.project, cfg.location, cfg.embedding_model, cfg.output_dim)

    rows: List[Dict[str, Any]] = []

    for d in docs:
        chunks = simple_text_chunker(
            d["doc_id"],
            d["text"],
            max_chars=2200,
            overlap_chars=200,
            base_metadata={
                "title": d["title"],
                "source": d["source"],
                "type": d["type"],
                "market": d["market"],
                "product": d["product"],
            },
        )

        if not chunks:
            continue

        vectors = embedder.embed_texts([c.text for c in chunks], task_type="RETRIEVAL_DOCUMENT").vectors

        for c, v in zip(chunks, vectors):
            rows.append(
                build_datapoint(
                    chunk_id=c.chunk_id,
                    embedding=v,
                    text=c.text,
                    doc_id=d["doc_id"],
                    meta={**c.metadata, "title": d["title"], "source": d["source"]},
                )
            )

    print(f"Total chunks: {len(rows)}")

    ts = int(time.time())
    object_path = f"{cfg.gcs_prefix}/deltas/{ts}/embeddings.json"

    gs_uri = upload_json_lines_as_json(
        bucket_uri=cfg.gcs_bucket_uri,
        object_path=object_path,
        rows=rows,
    )
    print(f"Uploaded JSONL(.json): {gs_uri}")

    contents_delta_uri = f"{cfg.gcs_bucket_uri.rstrip('/')}/{cfg.gcs_prefix}/deltas/{ts}/"
    op_name = update_matching_engine_index(cfg.index_resource_name, contents_delta_uri=contents_delta_uri)
    print("Index updated successfully.")
    if op_name:
        print(f"LRO: {op_name}")


if __name__ == "__main__":
    main()
