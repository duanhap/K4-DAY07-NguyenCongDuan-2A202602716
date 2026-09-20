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

    def answer(self, question: str, top_k: int = 3) -> str:
        # Guard: empty store — no point calling the LLM.
        if self.store.get_collection_size() == 0:
            return "Không có tài liệu nào trong kho lưu trữ. Vui lòng nạp tài liệu trước khi đặt câu hỏi."

        results = self.store.search(question, top_k=top_k)

        if not results:
            return "Không tìm thấy tài liệu liên quan đến câu hỏi này."

        # Build numbered context with source attribution for traceability.
        context_lines: list[str] = []
        for i, r in enumerate(results, start=1):
            source = (
                r["metadata"].get("source_url")
                or r["metadata"].get("source")
                or r["metadata"].get("doc_id")
                or "unknown"
            )
            context_lines.append(f"[{i}] (Nguồn: {source})\n{r['content']}")

        context = "\n\n".join(context_lines)

        prompt = (
            "Dưới đây là các đoạn tài liệu liên quan được truy xuất từ cơ sở tri thức:\n\n"
            f"{context}\n\n"
            "---\n"
            f"Câu hỏi: {question}\n\n"
            "Hãy trả lời câu hỏi dựa HOÀN TOÀN trên các đoạn tài liệu trên. "
            "Khi sử dụng thông tin từ một đoạn, hãy trích dẫn số thứ tự tương ứng (ví dụ: [1], [2]). "
            "Nếu các đoạn tài liệu không chứa thông tin đủ để trả lời, hãy nói rõ: "
            "\"Không tìm thấy thông tin liên quan trong tài liệu được cung cấp.\""
        )

        return self.llm_fn(prompt)
