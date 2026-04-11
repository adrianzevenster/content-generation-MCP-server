from __future__ import annotations

from rag.config import load_rag_config
from rag.index_admin import ensure_index_and_endpoint


def main() -> None:
    cfg = load_rag_config()
    ensure_index_and_endpoint(
        project=cfg.project,
        location=cfg.location,
        embedding_dim=cfg.output_dim,
        index_display_name="monc-rag-index",
        endpoint_display_name="monc-rag-endpoint",
    )


if __name__ == "__main__":
    main()
