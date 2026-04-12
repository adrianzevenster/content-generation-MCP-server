from __future__ import annotations

from rag.config import load_rag_config
from rag.retriever import VertexVectorSearchRetriever


def main() -> None:
    cfg = load_rag_config()
    r = VertexVectorSearchRetriever(cfg)

    q = "SkywalkerShares business account product sheet"
    hits = r.retrieve(
        q,
        k=10,
        restricts=[{"namespace": "product", "allow": ["skywalkershares_business_account"]}],
    )

    print("hits:", len(hits))
    for h in hits[:10]:
        print(h.id, h.score, list(h.metadata.keys())[:10])


if __name__ == "__main__":
    main()
