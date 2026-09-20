"""
bench.py — Benchmark retrieval cho Lab 07
Chiến lược cá nhân: RecursiveChunker(chunk_size=500)
Sinh viên: Nguyễn Công Duẩn — 2A202602716
"""

from pathlib import Path
import re

# ── Chiến lược cá nhân của Duẩn ──────────────────────────────────────────────
from src.chunking import RecursiveChunker
# Đổi dòng trên nếu dùng embedder thật:
#   from src.embeddings import GeminiEmbedder
#   EMBEDDER = GeminiEmbedder()
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore

CORPUS_DIR = Path("data/ecommerce")
CHUNKER    = RecursiveChunker(chunk_size=500)
EMBEDDER   = _mock_embed   # đổi thành GeminiEmbedder() nếu có API key

# ── 5 Benchmark Query (nhóm thống nhất) ──────────────────────────────────────
QUERIES = [
    {
        "id": 1,
        "q": "Người mua trên Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng?",
        "filter": {"audience": "buyer"},
        "gold_keyword": "15 ngày",
        "gold_source": "shopee-return-buyer",
    },
    {
        "id": 2,
        "q": "Người bán trên Shopee phải phản hồi yêu cầu trả hàng trong bao lâu?",
        "filter": {"audience": "seller"},
        "gold_keyword": "02 ngày lịch",
        "gold_source": "shopee-return-seller",
    },
    {
        "id": 3,
        "q": "Sendo hoàn tiền cho người mua qua kênh nào và mất bao lâu?",
        "filter": None,
        "gold_keyword": "Senpay",
        "gold_source": "sendo-return-policy",
    },
    {
        "id": 4,
        "q": "Tiki hỗ trợ đổi trả điện thoại bị lỗi trong bao nhiêu ngày?",
        "filter": {"audience": "buyer"},
        "gold_keyword": "7 ngày",
        "gold_source": "tiki-return-policy",
    },
    {
        "id": 5,
        "q": "Người bán có phải chịu phí vận chuyển hoàn trả khi lỗi do đơn vị vận chuyển không?",
        "filter": {"audience": "seller"},
        "gold_keyword": "không chịu",
        "gold_source": "shopee-return-seller",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Tách YAML frontmatter và phần body."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()
    fm_raw = parts[1]
    body   = parts[2].strip()
    fm = {}
    for line in fm_raw.splitlines():
        m = re.match(r'^(\w+):\s*"?([^"]+?)"?\s*$', line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, body


def score_result(rank: int, content: str, gold_keyword: str, gold_source: str,
                 doc_id: str) -> int:
    """
    Chấm điểm theo SCORING.md:
      2đ — chunk trong top-3 chứa gold_keyword VÀ đúng tài liệu nguồn
      1đ — chunk đúng tài liệu nguồn nhưng không chứa gold_keyword
      0đ — không liên quan
    """
    has_kw  = gold_keyword.lower() in content.lower()
    right_doc = (doc_id == gold_source)
    if right_doc and has_kw:
        return 2
    if right_doc:
        return 1
    return 0


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # 1. Đọc corpus → chunk → nạp vào store
    store = EmbeddingStore(collection_name="bench", embedding_fn=EMBEDDER)
    total_chunks = 0

    print("=" * 60)
    print(f"Chunker : {CHUNKER.__class__.__name__}(chunk_size={CHUNKER.chunk_size})")
    print(f"Embedder: {getattr(EMBEDDER, '_backend_name', EMBEDDER.__class__.__name__)}")
    print(f"Corpus  : {CORPUS_DIR}")
    print("=" * 60)

    for md_path in sorted(CORPUS_DIR.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        if not body:
            print(f"  [skip] {md_path.name}: body rỗng")
            continue

        chunks = CHUNKER.chunk(body)
        docs = [
            Document(
                id=f"{md_path.stem}#{i}",
                content=chunk,
                metadata={
                    **fm,
                    "doc_id":      md_path.stem,   # tên file gốc — cho delete & filter
                    "chunk_index": str(i),
                },
            )
            for i, chunk in enumerate(chunks)
        ]
        store.add_documents(docs)
        total_chunks += len(docs)
        print(f"  {md_path.name}: {len(chunks)} chunks")

    print(f"\nTổng: {total_chunks} chunks nạp vào store\n")

    # 2. Chạy 5 query
    lines       = []
    total_score = 0
    sep         = "=" * 60

    lines.append(sep)
    lines.append(f"Chunker : {CHUNKER.__class__.__name__}(chunk_size={CHUNKER.chunk_size})")
    lines.append(f"Embedder: {getattr(EMBEDDER, '_backend_name', EMBEDDER.__class__.__name__)}")
    lines.append(f"Tổng chunks nạp: {total_chunks}")
    lines.append(sep)

    for item in QUERIES:
        header = f"\nCÂU {item['id']}: {item['q']}"
        if item["filter"]:
            header += f"\n         [filter={item['filter']}]"
        print(header)
        lines.append(header)

        # Chạy CÓ filter
        results_with = store.search_with_filter(
            item["q"], top_k=3, metadata_filter=item["filter"]
        )
        # Chạy KHÔNG filter (để A/B compare)
        results_without = store.search_with_filter(
            item["q"], top_k=3, metadata_filter=None
        )

        # ── Kết quả CÓ filter ──
        block = "  --- Có filter ---"
        print(block); lines.append(block)

        query_score = 0
        if not results_with:
            msg = "  >>> Không tìm thấy kết quả <<<"
            print(msg); lines.append(msg)
        else:
            for rank, r in enumerate(results_with, 1):
                doc_id   = r["metadata"].get("doc_id", "?")
                audience = r["metadata"].get("audience", "?")
                pts      = score_result(rank, r["content"],
                                        item["gold_keyword"], item["gold_source"], doc_id)
                query_score = max(query_score, pts)
                flag     = "✓ GOLD" if pts == 2 else ("~ doc đúng" if pts == 1 else "✗")
                s1 = f"  [{rank}] score={r['score']:.4f}  doc={doc_id}  audience={audience}  {flag}"
                s2 = f"      {r['content'][:150].replace(chr(10), ' ')}..."
                print(s1); lines.append(s1)
                print(s2); lines.append(s2)

        # ── Kết quả KHÔNG filter (A/B) ──
        block2 = "  --- Không filter (A/B) ---"
        print(block2); lines.append(block2)
        if not results_without:
            msg = "  >>> Không tìm thấy kết quả <<<"
            print(msg); lines.append(msg)
        else:
            for rank, r in enumerate(results_without, 1):
                doc_id   = r["metadata"].get("doc_id", "?")
                audience = r["metadata"].get("audience", "?")
                s1 = f"  [{rank}] score={r['score']:.4f}  doc={doc_id}  audience={audience}"
                s2 = f"      {r['content'][:120].replace(chr(10), ' ')}..."
                print(s1); lines.append(s1)
                print(s2); lines.append(s2)

        pts_line = f"  → Điểm câu {item['id']}: {query_score}/2"
        print(pts_line); lines.append(pts_line)
        total_score += query_score

    summary = (
        f"\n{sep}\n"
        f"TỔNG ĐIỂM: {total_score}/10\n"
        f"(Thang: 2đ/câu — top-3 có chunk đúng nguồn + chứa gold keyword)\n"
        f"{sep}"
    )
    print(summary)
    lines.append(summary)

    # 3. Ghi ra file
    Path("ket_qua_benchmark.txt").write_text("\n".join(lines), encoding="utf-8")
    print("Đã lưu: ket_qua_benchmark.txt")


if __name__ == "__main__":
    main()
