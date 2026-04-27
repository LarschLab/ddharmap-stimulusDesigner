"""Regenerate coding.md from the appendix block in setupAgents.md."""

from pathlib import Path


START = "<!-- coding.md:start -->"
END = "<!-- coding.md:end -->"


def extract_coding_doc(source: str) -> str:
    start = source.find(START)
    if start == -1:
        raise ValueError(f"Missing marker: {START}")

    body_start = start + len(START)
    end = source.find(END, body_start)
    if end == -1:
        raise ValueError(f"Missing marker: {END}")

    body = source[body_start:end].strip()
    if not body:
        raise ValueError("coding.md source block is empty")

    return body + "\n"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    setup_agents = repo_root / "setupAgents.md"
    coding_md = repo_root / "coding.md"

    source = setup_agents.read_text(encoding="utf-8")
    coding_md.write_text(extract_coding_doc(source), encoding="utf-8")


if __name__ == "__main__":
    main()
