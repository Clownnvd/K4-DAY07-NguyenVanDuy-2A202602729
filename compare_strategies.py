"""CP6: compare the four group chunking configurations fairly."""

from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from bench import DEFAULT_MODEL, QUERY_FILE, build_records, clean_preview, ranked_results
from src.chunking import FixedSizeChunker, MarkdownHeadingChunker, RecursiveChunker, SentenceChunker


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "ket_qua_so_sanh_nhom.txt"


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


def content_evidence_rank(results: list[dict], markers: list[str]) -> int | None:
    expected = [normalize(marker) for marker in markers]
    for rank, result in enumerate(results, start=1):
        content = normalize(result["content"])
        if all(marker in content for marker in expected):
            return rank
    return None


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    queries = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
    model = SentenceTransformer(DEFAULT_MODEL, local_files_only=True)
    query_embeddings = model.encode(
        [item["query"] for item in queries],
        batch_size=5,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    strategies = [
        (
            "Lục Tiến Đạt",
            'RecursiveChunker(size=500)',
            RecursiveChunker(chunk_size=500, separators=["\n\n", "\n", ". ", " ", ""]),
        ),
        (
            "Dương Thị Ngân",
            "FixedSizeChunker(size=500, overlap=50)",
            FixedSizeChunker(chunk_size=500, overlap=50),
        ),
        (
            "Nguyễn Thanh Bình",
            "SentenceChunker(max_sentences=3)",
            SentenceChunker(max_sentences_per_chunk=3),
        ),
        (
            "Nguyễn Văn Duy",
            "MarkdownHeadingChunker(size=650)",
            MarkdownHeadingChunker(chunk_size=650),
        ),
    ]

    lines = [
        "DAY07 CP6 — GROUP STRATEGY COMPARISON",
        f"Embedding: {DEFAULT_MODEL}",
        "Same corpus, queries, filters and top_k=3; only chunker changes.",
        "Content scoring: evidence markers must occur in the retrieved chunk.",
        "",
    ]
    summary: list[dict] = []

    for member, name, chunker in strategies:
        records = build_records(chunker)
        chunk_embeddings = model.encode(
            [record["content"] for record in records],
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        hits = 0
        points = 0
        ranks: list[str] = []
        lines.extend([f"## {member}", f"Strategy: {name}", f"Chunks: {len(records)}"])

        for item, query_embedding in zip(queries, query_embeddings):
            results = ranked_results(
                records,
                chunk_embeddings,
                query_embedding,
                item.get("metadata_filter"),
            )
            rank = content_evidence_rank(results, item["evidence_markers"])
            score = 2 if rank == 1 else 1 if rank in (2, 3) else 0
            hits += int(rank is not None)
            points += score
            ranks.append(str(rank) if rank is not None else "miss")
            lines.append(
                f"Q{item['id']}: evidence_rank={ranks[-1]}, points={score}/2, "
                f"top1={results[0]['doc_id']} ({results[0]['score']:.6f}) | "
                f"{clean_preview(results[0]['content'], 130)}"
            )

        lines.extend([f"evidence@3: {hits}/5", f"retrieval_points: {points}/10", ""])
        summary.append(
            {
                "member": member,
                "strategy": name,
                "chunks": len(records),
                "hits": hits,
                "points": points,
                "ranks": ranks,
            }
        )

    lines.append("SUMMARY")
    for item in sorted(summary, key=lambda row: (row["points"], row["hits"]), reverse=True):
        lines.append(
            f"{item['member']} | {item['strategy']} | chunks={item['chunks']} | "
            f"ranks={','.join(item['ranks'])} | evidence@3={item['hits']}/5 | "
            f"points={item['points']}/10"
        )

    output = "\n".join(lines) + "\n"
    OUTPUT.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
