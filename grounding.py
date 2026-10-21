"""Plain-code accuracy checks (no LLM). Every step should point at the exact
words in the source that support it. We verify that in code."""
import re

_STOP = {"the", "a", "an", "team", "of", "and", "or", "to"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _check_item(label: str, quote: str | None, owner: str | None, src: str) -> list[str]:
    q = _norm(quote or "")
    if not q:
        return [f"{label}: no supporting quote (inferred, not stated?)"]
    if q not in src:
        return [f"{label}: quote not found in the source text (possible invention)"]
    if owner:
        words = [w for w in _norm(owner).split() if w not in _STOP]
        if words and not any(w in q.split() for w in words):
            return [f"{label}: owner '{owner}' is not named in its quote (inferred?)"]
    return []


def check_grounding(sop, source: str) -> list[str]:
    """Return a list of warnings. Empty list = every item is backed by the source."""
    src = _norm(source)
    warnings: list[str] = []
    for s in sop.steps:
        warnings += _check_item(f"Step {s.number}", s.source_quote, s.owner, src)
    for i, e in enumerate(sop.exceptions, 1):
        warnings += _check_item(f"Exception {i}", e.source_quote, e.owner, src)
    return warnings


