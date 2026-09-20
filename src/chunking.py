from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Lookbehind keeps the punctuation attached to the sentence before the split.
        # e.g. "Hello. World" → ["Hello.", "World"]
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(group))

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\\n\\n", "\\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        result = self._split(text, self.separators)
        return [c for c in result if c.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1: text fits within chunk_size — no need to split further
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case 2: no separators left — hard-cut by chunk_size
        if not remaining_separators:
            pieces = []
            for start in range(0, len(current_text), self.chunk_size):
                pieces.append(current_text[start : start + self.chunk_size])
            return pieces

        sep = remaining_separators[0]
        rest = remaining_separators[1:]

        # Try splitting with current separator
        if sep == "":
            # Empty string separator: split every character — just hard-cut
            pieces = []
            for start in range(0, len(current_text), self.chunk_size):
                pieces.append(current_text[start : start + self.chunk_size])
            return pieces

        parts = current_text.split(sep)

        if len(parts) == 1:
            # Separator not found — try the next one
            return self._split(current_text, rest)

        # Recursively process each part that is still too large,
        # then merge small adjacent parts back up to chunk_size.
        all_small: list[str] = []
        for part in parts:
            if not part:
                continue
            if len(part) <= self.chunk_size:
                all_small.append(part)
            else:
                all_small.extend(self._split(part, rest))

        # Merge step: combine small pieces into chunks up to chunk_size
        merged: list[str] = []
        buffer = ""
        for piece in all_small:
            candidate = (buffer + sep + piece) if buffer else piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    merged.append(buffer)
                # If a single piece is already bigger than chunk_size, split it further
                if len(piece) > self.chunk_size:
                    merged.extend(self._split(piece, rest))
                    buffer = ""
                else:
                    buffer = piece
        if buffer:
            merged.append(buffer)

        return merged if merged else [current_text]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size":   FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive":    RecursiveChunker(chunk_size=chunk_size),
        }
        result = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            result[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return result
