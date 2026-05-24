from __future__ import annotations

from google.cloud import aiplatform


def update_matching_engine_index(index_resource_name: str, contents_delta_uri: str) -> str:
    index = aiplatform.MatchingEngineIndex(index_resource_name)

    lro = index.update_embeddings(contents_delta_uri=contents_delta_uri)

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

    if hasattr(lro, "result"):
        lro.result()

    return op_name or ""
