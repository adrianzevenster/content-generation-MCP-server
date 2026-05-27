from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DOCSTORE_PATH = Path("rag/docstore.jsonl")


def write_docstore(rows: list[dict[str, Any]], path: Path = DOCSTORE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_docstore(path: Path = DOCSTORE_PATH) -> Dict[str, dict[str, Any]]:
    if not path.exists():
        return {}

    out: Dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                out[row["id"]] = row
    return out