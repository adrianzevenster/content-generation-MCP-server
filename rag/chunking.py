from __future__ import annotations

from typing import List


def simple_text_chunker(
        text: str,
        max_chars: int = 1200,
        overlap_chars: int = 120,
        **_: object,  # ignore unexpected kwargs safely
) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []

    if max_chars <= 0:
        return [text]

    overlap_chars = max(0, min(overlap_chars, max_chars - 1))

    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break

        start = end - overlap_chars

    return chunks
