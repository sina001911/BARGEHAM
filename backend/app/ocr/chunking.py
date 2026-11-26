"""Text chunking with paragraph-aware splitting and overlap."""
from __future__ import annotations

import re
from dataclasses import dataclass

_ARABIC_RANGE = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?؟۔])\s+")


@dataclass
class TextPiece:
    """A chunk of text tied to a source page."""

    chunk_index: int
    page_number: int
    text: str
    direction: str


def detect_direction(text: str) -> str:
    """Return 'rtl' when the text is majority Arabic-script, else 'ltr'."""
    if not text:
        return "ltr"
    rtl = len(_ARABIC_RANGE.findall(text))
    latin = sum(1 for ch in text if "a" <= ch.lower() <= "z")
    return "rtl" if rtl > latin else "ltr"


def _split_long(paragraph: str, chunk_size: int) -> list[str]:
    """Break an over-long paragraph on sentence boundaries, then hard-wrap."""
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_SPLIT.split(paragraph):
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
            continue
        if current:
            pieces.append(current)
        if len(sentence) <= chunk_size:
            current = sentence
        else:
            for i in range(0, len(sentence), chunk_size):
                pieces.append(sentence[i : i + chunk_size])
            current = ""
    if current:
        pieces.append(current)
    return pieces


def chunk_pages(
    pages: list[tuple[int, str]],
    chunk_size: int = 900,
    overlap: int = 150,
) -> list[TextPiece]:
    """Chunk ``(page_number, text)`` pairs into overlapping pieces.

    Paragraphs are kept intact when they fit; long paragraphs are split on
    sentence boundaries. ``overlap`` characters of the previous chunk are
    prepended to each new chunk to preserve context across boundaries.
    """
    pieces: list[TextPiece] = []
    index = 0
    carry = ""

    for page_number, text in pages:
        text = (text or "").strip()
        if not text:
            continue
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        buffer = carry
        for paragraph in paragraphs:
            segments = (
                [paragraph]
                if len(paragraph) <= chunk_size
                else _split_long(paragraph, chunk_size)
            )
            for segment in segments:
                if len(buffer) + len(segment) + 2 <= chunk_size:
                    buffer = f"{buffer}\n\n{segment}".strip() if buffer else segment
                else:
                    if buffer:
                        pieces.append(
                            TextPiece(
                                chunk_index=index,
                                page_number=page_number,
                                text=buffer,
                                direction=detect_direction(buffer),
                            )
                        )
                        index += 1
                        carry = buffer[-overlap:] if overlap > 0 else ""
                    buffer = f"{carry}\n\n{segment}".strip() if carry else segment
        carry = buffer[-overlap:] if overlap > 0 and buffer else ""
        if buffer:
            pieces.append(
                TextPiece(
                    chunk_index=index,
                    page_number=page_number,
                    text=buffer,
                    direction=detect_direction(buffer),
                )
            )
            index += 1

    return pieces
