"""Remove caminhos absolutos tipo </C:\\...> dos links Markdown (portavel no GitHub)."""
from __future__ import annotations

from pathlib import Path

TOKEN = "</C:\\Projects\\Python aplicação teste\\"
ROOT = Path(__file__).resolve().parents[1]


def fix_text(text: str) -> str:
    while True:
        try:
            i = text.index(TOKEN)
        except ValueError:
            break
        j = text.index(">)", i)
        inner = text[i + len(TOKEN) : j].replace("\\", "/")
        if inner == ".env":
            inner = ".env.example"
        text = text[:i] + inner + ")" + text[j + 2 :]
    return text


def main() -> None:
    for rel in ("README.md", "docs/GUIA_DO_COLEGA.md"):
        path = ROOT / rel
        raw = path.read_text(encoding="utf-8")
        path.write_text(fix_text(raw), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
