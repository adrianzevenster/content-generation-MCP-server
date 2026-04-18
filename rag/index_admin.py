from __future__ import annotations

from google.cloud import aiplatform


def update_matching_engine_index(index_resource_name: str, contents_delta_uri: str) -> str:
    """
    Returns the LRO name (if available) so you can `gcloud ai operations describe ...`.
    """
    index = aiplatform.MatchingEngineIndex(index_resource_name)

    lro = index.update_embeddings(contents_delta_uri=contents_delta_uri)

    # Different SDK versions expose different attrs; handle all.
    op_name = None
    if hasattr(lro, "operation") and getattr(lro.operation, "name", None):
        op_name = lro.operation.name
    elif hasattr(lro, "name"):
        op_name = lro.name
    elif hasattr(lro, "operation_name"):
        op_name = lro.operation_name

    if op_name:
        print(f"UpdateIndex operation: {op_name}")
    else:
        print("UpdateIndex operation: <unknown LRO name from SDK>")

    # Wait for completion if supported
    if hasattr(lro, "result"):
        lro.result()

    return op_name or ""
