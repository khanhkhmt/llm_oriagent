"""
Model-agnostic grounding / output-quality guard for the Public API.

Cheap, deterministic checks that work regardless of how small/weak the model is:
  - numeric grounding: every number in the answer should appear in the grounding
    corpus (the tool observations + user text the model was given). Invented numbers
    (e.g. "15 giường/người", "150.000 dân") are flagged.
  - foreign-script detection: CJK / other non-Latin scripts leaking into a
    Vietnamese/English answer (e.g. "病床數量") indicate a degraded generation.

These are HEURISTIC detectors meant for logging/observability and optional
enforcement (one corrective regeneration). They never hard-block by default.
"""

import re
from typing import Iterable

# A numeric token: a run of digits with optional . , separators (e.g. 1.500, 2,000, 15.5).
_NUMBER_RE = re.compile(r"\d[\d.,]*\d|\d")
# CJK Unified Ideographs / Hiragana / Katakana / Hangul — should not appear in vi/en text.
_FOREIGN_SCRIPT_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯]")


def _digit_core(token: str) -> str:
    """Normalize a numeric token to its bare digits so 1.500 / 1,500 / 1500 match."""
    return re.sub(r"[.,]", "", token)


def extract_numbers(text: str, *, min_digits: int = 2) -> set[str]:
    """Return the set of normalized numeric cores in `text`.

    Single-digit numbers are ignored by default (min_digits=2) — they are usually
    list indices / trivial and create noise.
    """
    if not text:
        return set()
    out = set()
    for m in _NUMBER_RE.finditer(text):
        core = _digit_core(m.group(0))
        if core and len(core) >= min_digits:
            out.add(core)
    return out


def build_corpus(texts: Iterable[str]) -> str:
    """Join grounding texts (tool observations + user content) into one corpus."""
    return "\n".join(t for t in texts if t)


def find_ungrounded_numbers(answer: str, corpus: str) -> list[str]:
    """Numbers present in `answer` whose digit-core does not appear in `corpus`.

    Heuristic: may include legitimately-derived figures, so use for logging /
    optional enforcement, not hard rejection.
    """
    if not answer:
        return []
    corpus_cores = extract_numbers(corpus, min_digits=1)
    ungrounded = []
    for core in extract_numbers(answer):
        if core not in corpus_cores:
            ungrounded.append(core)
    return sorted(ungrounded)


def contains_foreign_script(text: str) -> bool:
    """True if the text contains CJK / Hangul characters (degraded generation)."""
    return bool(text) and bool(_FOREIGN_SCRIPT_RE.search(text))


def grounding_report(answer: str, corpus: str) -> dict:
    """Combined report: {ungrounded_numbers, foreign_script, ok}."""
    ungrounded = find_ungrounded_numbers(answer, corpus)
    foreign = contains_foreign_script(answer)
    return {
        "ungrounded_numbers": ungrounded,
        "foreign_script": foreign,
        "ok": not ungrounded and not foreign,
    }
