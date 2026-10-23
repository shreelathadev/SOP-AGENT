"""Plain-code accuracy checks (no LLM). Every step should point at the exact
words in the source that support it. We verify that in code."""
import re

_STOP = {"the", "a", "an", "team", "of", "and", "or", "to"}
# "Sales Executive (SE)" -> remember that "se" is another name for "sales executive"
_ABBR = re.compile(r"((?:[A-Z][A-Za-z&]+\s+){1,4}[A-Z][A-Za-z&]+)\s*\(([A-Z]{2,6})\)")


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _aliases(source: str) -> dict[str, set[str]]:
    amap: dict[str, set[str]] = {}
    for full, abbr in _ABBR.findall(source):
        for w in _norm(full).split():
            amap.setdefault(w, set()).add(abbr.lower())
    return amap


def _check_item(label, quote, owner, src, answer_words, aliases) -> list[str]:
    q = _norm(quote or "")
    if not q:
        return [f"{label}: no supporting quote (inferred, not stated?)"]
    if q not in src:
        return [f"{label}: quote not found in the source text (possible invention)"]
    if owner:
        words = [w for w in _norm(owner).split() if w not in _STOP]
        accepted = set(words)
        for w in words:
            accepted |= aliases.get(w, set())
        named_in_quote = any(a in q.split() for a in accepted)
        named_in_answer = any(w in answer_words for w in words)  # a human typed it
        if words and not (named_in_quote or named_in_answer):
            return [f"{label}: owner '{owner}' is not named in its quote or in your answers (inferred?)"]
    return []


def check_grounding(sop, source: str, answers=()) -> list[str]:
    """Return warnings. Empty list = every item is backed by the source.
    `answers` = the human's accepted answers; an owner they typed is grounded."""
    src = _norm(source)
    aliases = _aliases(source)
    answer_words = set()
    for a in answers:
        answer_words.update(_norm(a).split())
    warnings: list[str] = []
    for s in sop.steps:
        warnings += _check_item(f"Step {s.number}", s.source_quote, s.owner, src, answer_words, aliases)
    for i, e in enumerate(sop.exceptions, 1):
        warnings += _check_item(f"Exception {i}", e.source_quote, e.owner, src, answer_words, aliases)
    return warnings