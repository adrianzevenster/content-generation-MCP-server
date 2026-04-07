import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RagConfig:
    project: str
    location: str

    gcs_bucket_uri: str
    gcs_prefix: str

    embedding_model: str
    output_dim: int

    index_resource_name: str
    index_endpoint_resource_name: str
    deployed_index_id: str


def _get_env_any(*names: str, default: str | None = None) -> str:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    if default is not None:
        return default
    raise KeyError(f"Missing required environment variable: one of {names}")


def load_rag_config() -> RagConfig:
    project = _get_env_any("RAG_PROJECT", "GOOGLE_CLOUD_PROJECT", "PROJECT_ID")
    location = _get_env_any("RAG_LOCATION", "GOOGLE_CLOUD_LOCATION", default="europe-west1")

    bucket_uri = _get_env_any("RAG_GCS_BUCKET_URI", "RAG_GCS_BUCKET")
    prefix = os.environ.get("RAG_GCS_PREFIX", "rag/monc")

    embedding_model = os.environ.get("RAG_EMBEDDING_MODEL", "gemini-embedding-001")
    output_dim = int(os.environ.get("RAG_OUTPUT_DIM", "768"))

    index_resource_name = os.environ.get("RAG_INDEX_RESOURCE_NAME", "")
    endpoint_resource_name = os.environ.get("RAG_INDEX_ENDPOINT_RESOURCE_NAME", "")
    deployed_index_id = os.environ.get("RAG_DEPLOYED_INDEX_ID", "monc_rag_01")

    return RagConfig(
        project=project,
        location=location,
        gcs_bucket_uri=bucket_uri,
        gcs_prefix=prefix,
        embedding_model=embedding_model,
        output_dim=output_dim,
        index_resource_name=index_resource_name,
        index_endpoint_resource_name=endpoint_resource_name,
        deployed_index_id=deployed_index_id,
    )
