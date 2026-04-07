from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from google.cloud import aiplatform
from google.protobuf.json_format import MessageToDict

from rag.config import RagConfig
from rag.embeddings import VertexEmbeddingClient


@dataclass
class RagChunk:
    id: str
    score: float
    distance: float
    text: str
    metadata: Dict[str, Any]


# Backwards compat export (your rag/__init__.py expects this name)
RetrievedChunk = RagChunk


def _to_dict(obj: Any) -> Dict[str, Any]:
    """
    Robust conversion for Vertex/Protobuf/SDK objects:
    - dict
    - protobuf message
    - SDK wrapper with _pb
    - SDK wrapper with to_dict()
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj

    # protobuf message (Struct, etc.)
    if hasattr(obj, "DESCRIPTOR"):
        try:
            return MessageToDict(obj, preserving_proto_field_name=True)
        except Exception:
            pass

    # some SDK objects wrap protobuf in _pb
    pb = getattr(obj, "_pb", None)
    if pb is not None and hasattr(pb, "DESCRIPTOR"):
        try:
            return MessageToDict(pb, preserving_proto_field_name=True)
        except Exception:
            pass

    # some SDK objects have to_dict()
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            pass

    # last resort
    try:
        return dict(obj)  # type: ignore[arg-type]
    except Exception:
        return {}


class VertexVectorSearchRetriever:
    def __init__(self, cfg: RagConfig):
        self.cfg = cfg
        aiplatform.init(project=cfg.project, location=cfg.location)

        self.endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=cfg.index_endpoint_resource_name
        )

        self.embedder = VertexEmbeddingClient(
            project=cfg.project,
            location=cfg.location,
            model=cfg.embedding_model,
            output_dim=cfg.output_dim,
        )

    def retrieve(
            self,
            query: str,
            k: int = 5,
            restricts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[RagChunk]:
        qvec = self.embedder.embed_query(query)

        # Your installed SDK returns: list[list[MatchNeighbor]]
        resp = self.endpoint.find_neighbors(
            deployed_index_id=self.cfg.deployed_index_id,
            queries=[qvec],
            num_neighbors=k,
            return_full_datapoint=True,
        )

        chunks = self._parse(resp)

        # Client-side filtering (since “restricts” differs across SDKs)
        if restricts:
            chunks = self._client_filter(chunks, restricts)

        return chunks

    def _parse(self, resp: Any) -> List[RagChunk]:
        # Expected: resp -> [ [MatchNeighbor, MatchNeighbor, ...] ]
        if not isinstance(resp, list) or not resp or not isinstance(resp[0], list):
            return []

        neighbors = resp[0]
        out: List[RagChunk] = []

        for nb in neighbors:
            distance = float(getattr(nb, "distance", 0.0) or 0.0)
            chunk_id = str(getattr(nb, "id", "") or "")

            # datapoint usually here on your SDK
            dp = getattr(nb, "from_index_datapoint", None) or getattr(nb, "datapoint", None)

            emb_md = getattr(dp, "embedding_metadata", None) if dp is not None else None
            md = _to_dict(emb_md)

            text = str(md.get("text", "") or "")
            meta = {k: v for k, v in md.items() if k != "text"}

            out.append(
                RagChunk(
                    id=chunk_id,
                    score=-distance,     # simple monotonic score
                    distance=distance,
                    text=text,
                    metadata=meta,
                )
            )

        return out

    def _client_filter(self, chunks: List[RagChunk], restricts: List[Dict[str, Any]]) -> List[RagChunk]:
        def ok(c: RagChunk) -> bool:
            md = c.metadata or {}
            for r in restricts:
                ns = r.get("namespace")
                allow = r.get("allow") or r.get("allow_list") or []
                if not ns or not allow:
                    continue

                val = md.get(ns)
                if val is None:
                    return False

                allow_set = set(map(str, allow))
                if isinstance(val, list):
                    if not any(str(x) in allow_set for x in val):
                        return False
                else:
                    if str(val) not in allow_set:
                        return False

            return True

        return [c for c in chunks if ok(c)]
