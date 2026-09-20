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

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split after sentence-ending punctuation so the punctuation remains
        # attached to the sentence it closes.
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:\s+|\n+)", text.strip())
            if sentence.strip()
        ]
        return [
            " ".join(sentences[index : index + self.max_sentences_per_chunk])
            for index in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return FixedSizeChunker(self.chunk_size, overlap=0).chunk(current_text)

        separator = remaining_separators[0]
        remaining = remaining_separators[1:]
        if not separator or separator not in current_text:
            return self._split(current_text, remaining)

        raw_parts = current_text.split(separator)
        # Keep the separator with the preceding part so sentence and paragraph
        # boundaries are not silently discarded.
        parts = [part + separator for part in raw_parts[:-1]] + [raw_parts[-1]]
        chunks: list[str] = []
        buffer = ""

        for part in parts:
            if not part:
                continue
            if len(part) > self.chunk_size:
                if buffer.strip():
                    chunks.append(buffer.strip())
                    buffer = ""
                chunks.extend(self._split(part, remaining))
                continue
            if buffer and len(buffer) + len(part) > self.chunk_size:
                chunks.append(buffer.strip())
                buffer = part
            else:
                buffer += part

        if buffer.strip():
            chunks.append(buffer.strip())
        return chunks


class MarkdownHeadingChunker:
    """Split Markdown policies by semantic heading/section boundaries.

    Sections longer than ``chunk_size`` fall back to ``RecursiveChunker``.
    The original heading is repeated on every child chunk so a retrieved
    fragment still carries the policy section that gives it meaning.
    """

    HEADING_PATTERN = re.compile(r"(?m)^(#{2,3}\s+.+)$")

    def __init__(self, chunk_size: int = 650) -> None:
        self.chunk_size = max(80, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        matches = list(self.HEADING_PATTERN.finditer(text))
        if not matches:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text)

        chunks: list[str] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            chunks.extend(
                RecursiveChunker(chunk_size=self.chunk_size).chunk(preamble)
            )

        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = text[match.start() : end].strip()
            heading = match.group(1).strip()
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            body = section[len(match.group(1)) :].strip()
            body_size = max(40, self.chunk_size - len(heading) - 1)
            for piece in RecursiveChunker(chunk_size=body_size).chunk(body):
                chunks.append(f"{heading}\n{piece}".strip())

        return [chunk for chunk in chunks if chunk.strip()]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            comparison[name] = {
                "count": count,
                "avg_length": (
                    sum(len(chunk) for chunk in chunks) / count if count else 0.0
                ),
                "chunks": chunks,
            }
        return comparison
