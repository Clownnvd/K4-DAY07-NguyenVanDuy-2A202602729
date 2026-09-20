"""Run Nguyễn Văn Duy's heading-aware CP5 benchmark with real embeddings."""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from src.chunking import MarkdownHeadingChunker


ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "data" / "shopee-return-refund"
QUERY_FILE = ROOT / "benchmark_queries.json"
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


SIMILARITY_PAIRS = [
    (
        "Người mua nhận tiền hoàn trong bao lâu?",
        "Thời gian hoàn tiền cho khách hàng là mấy ngày?",
        "cao nhất",
    ),
    (
        "Điều kiện để yêu cầu trả hàng là gì?",
        "Trường hợp nào người mua được hoàn trả sản phẩm?",
        "cao",
    ),
    (
        "Người bán khiếu nại quyết định hoàn tiền thế nào?",
        "Nhà bán hàng phản hồi tranh chấp bằng cách nào?",
        "cao",
    ),
    (
        "Phí gửi hàng hoàn trả do ai chịu?",
        "Người bán cần nộp bằng chứng hình ảnh nào?",
        "trung bình/thấp",
    ),
    (
        "Chính sách hoàn tiền Shopee",
        "Cách tạo môi trường ảo Python",
        "thấp nhất",
    ),
]


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {"doc_id": path.stem}, text.strip()
    _, raw_metadata, body = text.split("---", 2)
    metadata: dict[str, str] = {}
    for line in raw_metadata.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    metadata.setdefault("doc_id", path.stem)
    return metadata, body.strip()


def build_records(chunker=None) -> list[dict]:
    if chunker is None:
        chunker = MarkdownHeadingChunker(chunk_size=650)
    records: list[dict] = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        if path.name == "README.md":
            continue
        metadata, body = parse_frontmatter(path)
        for index, chunk in enumerate(chunker.chunk(body)):
            records.append(
                {
                    "id": f"{metadata['doc_id']}#{index}",
                    "doc_id": metadata["doc_id"],
                    "content": chunk,
                    "metadata": metadata,
                }
            )
    return records


def ranked_results(
    records: list[dict],
    chunk_embeddings: np.ndarray,
    query_embedding: np.ndarray,
    metadata_filter: dict | None,
    top_k: int = 3,
) -> list[dict]:
    candidate_indices = [
        index
        for index, record in enumerate(records)
        if metadata_filter is None
        or all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
    ]
    scored = [
        (float(np.dot(query_embedding, chunk_embeddings[index])), records[index])
        for index in candidate_indices
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [{**record, "score": score} for score, record in scored[:top_k]]


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


def evidence_rank(results: list[dict], evidence_markers: list[str]) -> int | None:
    expected = [normalize(marker) for marker in evidence_markers]
    for rank, result in enumerate(results, start=1):
        content = normalize(result["content"])
        if all(marker in content for marker in expected):
            return rank
    return None


def clean_preview(text: str, limit: int = 210) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def run(model_name: str, output_path: Path, offline: bool = False) -> str:
    records = build_records()
    queries = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
    model = SentenceTransformer(model_name, local_files_only=offline)

    chunk_embeddings = model.encode(
        [record["content"] for record in records],
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    query_embeddings = model.encode(
        [item["query"] for item in queries],
        batch_size=5,
        normalize_embeddings=True,
    )

    lines = [
        "DAY07 CP5 — NGUYỄN VĂN DUY",
        f"Embedding: {model_name}",
        "Chunker: MarkdownHeadingChunker(chunk_size=650)",
        f"Corpus: {len(list(CORPUS_DIR.glob('*.md'))) - 1} documents",
        f"Chunks indexed: {len(records)}",
        "top_k: 3",
        "",
    ]
    evidence_hits = 0
    retrieval_points = 0

    for item, query_embedding in zip(queries, query_embeddings):
        results = ranked_results(
            records,
            chunk_embeddings,
            query_embedding,
            item.get("metadata_filter"),
        )
        rank = evidence_rank(results, item["evidence_markers"])
        evidence_hits += int(rank is not None)
        points = 2 if rank == 1 else 1 if rank in (2, 3) else 0
        retrieval_points += points

        lines.extend(
            [
                f"Q{item['id']}: {item['query']}",
                f"Filter: {json.dumps(item.get('metadata_filter'), ensure_ascii=False)}",
                f"Gold: {item['gold_answer']}",
                f"Expected evidence: {item['evidence_doc_id']} — {item['evidence_section']}",
            ]
        )
        for result_rank, result in enumerate(results, start=1):
            lines.append(
                f"  Top-{result_rank}: score={result['score']:.6f} "
                f"doc_id={result['doc_id']} chunk={result['id']} | "
                f"{clean_preview(result['content'])}"
            )
        lines.extend(
            [
                f"Evidence rank: {rank if rank is not None else 'not in top-3'}",
                f"Retrieval points: {points}/2",
                "",
            ]
        )

        if item.get("metadata_filter"):
            unfiltered = ranked_results(records, chunk_embeddings, query_embedding, None)
            unfiltered_rank = evidence_rank(unfiltered, item["evidence_markers"])
            lines.extend(
                [
                    "  Filter A/B:",
                    f"  without_filter evidence_rank={unfiltered_rank if unfiltered_rank is not None else 'not in top-3'}",
                    f"  with_filter evidence_rank={rank if rank is not None else 'not in top-3'}",
                    "",
                ]
            )

    pair_texts = [text for pair in SIMILARITY_PAIRS for text in pair[:2]]
    pair_embeddings = model.encode(pair_texts, normalize_embeddings=True)
    lines.append("SIMILARITY PREDICTIONS")
    for index, (_, _, prediction) in enumerate(SIMILARITY_PAIRS):
        score = float(np.dot(pair_embeddings[index * 2], pair_embeddings[index * 2 + 1]))
        lines.append(f"Pair {index + 1}: prediction={prediction}; cosine={score:.6f}")

    lines.extend(
        [
            "",
            "SUMMARY",
            f"evidence@3: {evidence_hits}/5",
            f"retrieval_points: {retrieval_points}/10",
            "Scoring: answer-bearing chunk at rank 1 = 2; rank 2–3 = 1; absent = 0.",
            "This score measures retrieval only; final agent-answer grading remains a separate check.",
        ]
    )
    output = "\n".join(lines) + "\n"
    output_path.write_text(output, encoding="utf-8")
    return output


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=ROOT / "ket_qua_benchmark.txt")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    print(run(args.model, args.output, args.offline))


if __name__ == "__main__":
    main()
