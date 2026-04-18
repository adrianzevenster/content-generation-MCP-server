from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VertexEmbeddingClient:
    project: str
    location: str
    model: str = "gemini-embedding-001"
    output_dim: int = 768

    def __post_init__(self) -> None:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel

        vertexai.init(project=self.project, location=self.location)
        self._model = TextEmbeddingModel.from_pretrained(self.model)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vecs: list[list[float]] = []
        for t in texts:
            t = t or ""
            emb = self._model.get_embeddings([t], output_dimensionality=self.output_dim)[0].values
            vecs.append(list(emb))
        return vecs
