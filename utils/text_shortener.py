"""Utility helpers for trimming long responses naturally."""

from __future__ import annotations

import re
from typing import Tuple


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def condense_text(text: str, *, min_length: int = 200, max_length: int = 600) -> str:
    """Return text condensed between min_length and max_length characters.

    The algorithm keeps whole sentences where possible and appends an ellipsis
    if content had to be shortened. It never returns more than max_length
    characters and attempts to include at least min_length characters when
    the input provides enough content.
    """
    text = (text or '').strip()
    if not text:
        return text

    min_length = max(0, min(min_length, max_length))
    sentences = _SENTENCE_SPLIT_RE.split(text)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    if not sentences:
        return _truncate_text(text, max_length)

    selected, total = [], 0
    for sentence in sentences:
        sentence_len = len(sentence) + 1  # account for space when joining
        if total + sentence_len > max_length and total >= min_length:
            break
        selected.append(sentence)
        total += sentence_len
        if total >= max_length:
            break

    if not selected:
        selected.append(sentences[0])

    condensed = ' '.join(selected).strip()

    if len(condensed) < min_length:
        for sentence in sentences[len(selected):]:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(condensed) + len(sentence) + 1 > max_length:
                break
            condensed = f"{condensed} {sentence}".strip()
            if len(condensed) >= min_length:
                break

    needs_truncation = len(condensed) > max_length
    if needs_truncation:
        condensed = _truncate_text(condensed, max_length)

    if len(condensed) < min(len(text), min_length) and len(text) > len(condensed):
        condensed = _truncate_text(text, min(max_length, len(text)))

    return condensed


def _truncate_text(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rstrip()
    if ' ' in truncated:
        truncated = truncated.rsplit(' ', 1)[0]
    return f"{truncated} ?"
