from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        results = (
            self.store.search_with_filter(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
            if metadata_filter is not None
            else self.store.search(question, top_k=top_k)
        )
        if not results:
            return "Không tìm thấy thông tin liên quan trong cơ sở tri thức."

        context = "\n\n".join(
            (
                f"[{index}] source="
                f"{result['metadata'].get('source_url', result['metadata'].get('source', 'not-stated'))}\n"
                f"{result['content']}"
            )
            for index, result in enumerate(results, start=1)
        )
        prompt = (
            "Chỉ trả lời bằng ngữ cảnh được cung cấp và trích dẫn [1], [2], [3] "
            "khi dùng thông tin tương ứng. Nếu ngữ cảnh không đủ, hãy nói rõ.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\nTrả lời:"
        )
        return self.llm_fn(prompt)
