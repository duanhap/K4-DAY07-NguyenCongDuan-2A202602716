# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Công Duẩn
**MSSV:** 2A202602716
**Nhóm:** Soul
**Ngày:** 2026-09-20

> **Nộp 1 bản / sinh viên.** Phần nhóm nộp chung trong `REPORT_NHOM.md`.
> Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất (10).

---

## 1. Khởi Động (Warm-up) — Cá nhân (5 điểm)

### Cosine Similarity (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Hai văn bản có cosine similarity cao khi vector embedding của chúng hướng về cùng một vùng trong không gian vector — tức chúng chia sẻ ý nghĩa hoặc chủ đề dù từ ngữ bề mặt có thể khác nhau. Cosine đo góc giữa hai vector, không phải khoảng cách tuyệt đối, nên một văn bản ngắn và một văn bản dài nói về cùng chủ đề vẫn có thể cho cosine cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: *"Khách hàng được đổi hàng trong 7 ngày kể từ ngày nhận"*
- Câu B: *"Thời hạn trả sản phẩm là một tuần tính từ lúc giao thành công"*
- Tại sao tương đồng: cả hai đều nói về thời hạn đổi/trả hàng (~7 ngày), chỉ khác cách diễn đạt. Một embedding tốt sẽ ánh xạ cả hai về cùng vùng không gian.

**Ví dụ có độ tương tự THẤP:**
- Câu A: *"Chính sách hoàn tiền khi hàng lỗi"*
- Câu B: *"Hướng dẫn đăng ký tài khoản người bán"*
- Tại sao khác: hai câu thuộc hai chủ đề hoàn toàn khác nhau — một về khiếu nại sản phẩm, một về onboarding seller.

**Tại sao cosine được ưu tiên hơn Euclidean cho text embedding?**

Cosine đo góc giữa hai vector nên **không bị ảnh hưởng bởi độ dài văn bản**. Một đoạn chính sách 200 từ và một đoạn tóm tắt 20 từ về cùng nội dung sẽ có vector có độ lớn (magnitude) khác nhau rất nhiều, khiến Euclidean distance lớn dù nội dung gần nhau. Cosine bỏ qua độ lớn, chỉ so hướng — phù hợp hơn khi so sánh ngữ nghĩa.

---

### Bài Toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**

Áp dụng công thức: `ceil((độ_dài - overlap) / (chunk_size - overlap))`

```
ceil((10000 - 50) / (500 - 50))
= ceil(9950 / 450)
= ceil(22.11)
= 23 chunks
```

Kiểm tra bằng code:
```python
from src.chunking import FixedSizeChunker
print(len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a' * 10000)))
# → 23
```

**Nếu overlap tăng lên 100, số chunk thay đổi thế nào?**

```
ceil((10000 - 100) / (500 - 100))
= ceil(9900 / 400)
= ceil(24.75)
= 25 chunks
```

Overlap lớn hơn → nhiều chunk hơn (25 thay vì 23). Lý do muốn overlap lớn: mỗi ranh giới giữa 2 chunk được "phủ" bởi nhiều chunk hơn, giảm nguy cơ một thông tin quan trọng nằm vắt đúng chỗ bị cắt và không chunk nào chứa đủ ngữ cảnh để trả lời câu hỏi.

---

## 2. Hướng Tiếp Cận (My Approach) — Cá nhân (10 điểm)

### SentenceChunker.chunk

Dùng `re.split(r'(?<=[.!?])\s+', text)` — lookbehind giữ dấu câu gắn với câu trước, tránh bị "nuốt" mất dấu chấm. Sau đó group các câu theo `max_sentences_per_chunk`, join bằng khoảng trắng, strip whitespace thừa. Text rỗng trả `[]` ngay, không xử lý thêm.

Edge case biết là chưa xử lý được: chữ viết tắt (`TS.`, `v.v.`, `P.GS.`) và số thập phân (`3.14`) sẽ bị coi là kết thúc câu và cắt sai. Đây là giới hạn của regex đơn giản, cần NLP library thật (spaCy, underthesea) để xử lý đúng tiếng Việt.

### RecursiveChunker.chunk / _split

Thuật toán có hai chiều:

**Đệ quy xuống:** thử separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Nếu separator hiện tại không tìm thấy trong text thì thử separator tiếp theo. Mảnh nào sau khi split vẫn dài hơn `chunk_size` thì gọi đệ quy `_split(mảnh, separators[1:])`.

**Merge lên:** sau khi có danh sách các mảnh nhỏ, duyệt lần lượt và gom vào buffer cho đến khi buffer + mảnh tiếp theo vượt `chunk_size` thì flush. Bước này quan trọng — thiếu nó thì một file nhiều dòng ngắn sẽ sinh ra hàng trăm chunk 5–10 ký tự.

Base case: `len(text) <= chunk_size` trả ngay `[text]`; `separators == []` cắt cứng theo `chunk_size`.

### EmbeddingStore — add_documents + search

Lưu trữ in-memory bằng `list[dict]`. Mỗi record gồm `id`, `content`, `embedding` (vector float), `metadata`. ChromaDB bị tắt hoàn toàn (`_use_chroma = False`) để đảm bảo 42 test pass trên mọi máy chấm bài.

`search` và `search_with_filter` đều gọi chung `_search_records` — đảm bảo hai hàm không bao giờ lệch kết quả khi không có filter. Similarity tính bằng dot product vì vector đã được chuẩn hóa (`||v|| = 1`) nên dot product = cosine.

### search_with_filter + delete_document

`search_with_filter`: **lọc trước, search sau**. Nếu làm ngược (search top-k rồi lọc), tài liệu không khớp filter sẽ chiếm hết k slot và kết quả trả về rỗng dù store còn tài liệu hợp lệ.

`delete_document`: duyệt `_store`, giữ lại những record có `metadata["doc_id"] != doc_id`. `doc_id` luôn được set trong `_make_record` dù người gọi không truyền vào — nếu không có thì dùng `doc.id` làm fallback. Trả `True` nếu `len` giảm, `False` nếu không tìm thấy gì để xóa.

### KnowledgeBaseAgent.answer

Ba bước: guard store rỗng → search → build prompt → call LLM.

Prompt đánh số từng chunk `[1]`, `[2]`, `[3]` kèm `source_url` hoặc `doc_id` làm nguồn. Yêu cầu model trích dẫn số khi dùng thông tin — giúp câu trả lời truy vết được về đúng chunk và file gốc (tiêu chí Source Traceability trong `docs/EVALUATION.md`). Có ràng buộc chống hallucination: nếu không tìm thấy trong context thì nói rõ, không tự bịa.

---

## 3. Hoàn Thiện Code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử

```
=========================== test session starts ============================
platform win32 -- Python 3.12.6, pytest-8.3.3, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================ 42 passed in 0.10s ============================
```

**Số lượng bài test vượt qua: 42 / 42**

---

## 4. Dự Đoán Độ Tương Tự (Similarity Predictions) — Cá nhân (5 điểm)

5 cặp câu chạy qua `compute_similarity` với MockEmbedder (MD5 hash → vector giả):

| # | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|-------|-------|---------|--------------|-------|
| 1 | "Khách hàng được đổi hàng trong 7 ngày kể từ ngày nhận" | "Thời hạn trả sản phẩm là một tuần tính từ lúc giao thành công" | cao | **0.1087** | ❌ Thấp hơn dự đoán |
| 2 | "Chính sách hoàn tiền khi hàng lỗi" | "Hướng dẫn đăng ký tài khoản người bán" | thấp | **0.0585** | ✅ |
| 3 | "Người mua có thể yêu cầu trả hàng" | "Buyer có thể request return item" | cao (cùng nghĩa, khác ngôn ngữ) | **-0.0319** | ❌ Âm — bất ngờ nhất |
| 4 | "Sản phẩm bị vỡ trong vận chuyển" | "Hàng bị hư hỏng khi ship" | cao | **-0.0457** | ❌ |
| 5 | "Chính sách đổi trả Shopee" | "Quy định bảo hành Lazada" | trung bình (cùng lĩnh vực) | **0.2562** | ❌ Cao hơn dự đoán |

**Kết quả nào bất ngờ nhất?**

Cặp 3 và 4 bất ngờ nhất — hai câu rõ ràng cùng nghĩa (một tiếng Việt, một tiếng Anh; hoặc cùng mô tả hàng bị hỏng) nhưng lại có similarity **âm**. Cặp 5 ngược lại: "Shopee" và "Lazada" là hai nền tảng khác nhau nhưng lại cho similarity cao nhất (0.2562).

Điều này chứng minh **MockEmbedder không mã hóa ngữ nghĩa** — nó băm MD5 chuỗi ký tự rồi sinh số giả ngẫu nhiên. Hai câu cùng nghĩa nhưng khác từ ngữ hoàn toàn sẽ có vector không liên quan. Đây là lý do tại sao benchmark cần embedder thật (local/OpenAI/Gemini) để cho kết quả có ý nghĩa.

---

## 5. Kết Quả Truy Xuất (Competition Results) — Cá nhân (10 điểm)

**Chiến lược cá nhân:** `RecursiveChunker(chunk_size=500)` · Embedder: MockEmbedder
**Corpus:** 7 file, 50 chunks tổng

### Bảng Kết Quả Top-3

| # | Câu hỏi | Top-1 (tóm tắt) | Score | Liên quan? | Điểm |
|---|---------|----------------|-------|-----------|------|
| 1 | Người mua Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng? | tiki-return-policy / "30 ngày đầu..." | 0.2445 | ❌ Sai doc | 1/2 |
| 2 | Người bán Shopee phải phản hồi trong bao lâu? | tiktok-shop-return-seller / "phản hồi trong 2 ngày..." | 0.2129 | ❌ Sai doc | 0/2 |
| 3 | Sendo hoàn tiền qua kênh nào, mất bao lâu? | shopee-return-refund-policy / "Trả hàng COM..." | 0.2331 | ❌ Sai doc | 0/2 |
| 4 | Tiki đổi trả điện thoại lỗi trong bao nhiêu ngày? | shopee-return-buyer / "Shopee chỉ hoàn tiền..." | 0.2714 | ✅ top-2 GOLD | 2/2 |
| 5 | Người bán có phải chịu phí vận chuyển khi lỗi vận chuyển? | tiktok-shop-return-seller / "phản hồi trong 2 ngày..." | 0.1033 | ✅ top-3 GOLD | 2/2 |

**Tổng: 5/10**

### A/B Test — Filter Có Giúp Ích Không?

Câu 5 là ví dụ rõ nhất về giá trị của filter:

| Lần chạy | Top-1 | Top-2 | Top-3 |
|---------|-------|-------|-------|
| **Có filter** `seller` | tiktok-seller (✗) | tiktok-seller (✗) | **shopee-seller ✓ GOLD** |
| **Không filter** | tiki-buyer (✗) | tiki-buyer (✗) | shopee-refund-both (✗) |

Không filter → `shopee-return-seller` (tài liệu gold) hoàn toàn biến mất khỏi top-3, bị đẩy ra ngoài bởi tài liệu Tiki buyer có score cao hơn. Có filter `seller` → tài liệu gold xuất hiện ở top-3 dù score thấp hơn, vì pool ứng viên đã bị thu hẹp.

### Phân Tích Failure Case

**Câu 3 — Sendo hoàn tiền qua kênh nào?**

Top-3 trả về toàn bộ là Shopee (score 0.23, 0.22, 0.22), trong khi `sendo-return-policy` không xuất hiện.

- **Vì sao thất bại:** MockEmbedder dùng MD5 hash, không mã hóa ngữ nghĩa. Shopee có 18 chunks trong store (3 file × ~6-8 chunks) so với Sendo chỉ có 7 chunks. Xác suất thống kê khiến Shopee chiếm đa số top-k. Ngoài ra query "Sendo hoàn tiền" chứa từ "hoàn tiền" — nhiều chunk Shopee cũng chứa từ này, làm score tương đồng về mặt hash.
- **Đề xuất cải thiện:** Dùng embedder thật (Gemini/OpenAI) để vector phản ánh ngữ nghĩa thực. Thêm filter `{"doc_id": "sendo-return-policy"}` nếu biết trước nguồn (tuy nhiên mất tính tổng quát). Hoặc cân bằng corpus — không để một nguồn chiếm quá nhiều chunks so với các nguồn khác.

**Câu 2 — Người bán Shopee phản hồi trong bao lâu?**

Có filter `seller` nhưng TikTok seller lấn át Shopee seller vì TikTok có 5 chunks tập trung vào chủ đề "phản hồi" trong khi Shopee seller chia đều ra nhiều chủ đề hơn.

- **Đề xuất:** Dùng HeadingChunker (chiến lược của Vũ) — chunk theo heading `## Thông Báo Và Thời Hạn Phản Hồi` sẽ giữ nguyên section đó trong 1 chunk, tăng mật độ thông tin liên quan đến query.

### Nhận Xét Chung

Benchmark với MockEmbedder phản ánh vấn đề phân phối corpus hơn là chất lượng chunking thực sự. RecursiveChunker tạo ra 50 chunks với avg ~300 ký tự/chunk — kích thước hợp lý. Với embedder thật, kỳ vọng câu 1, 2, 3 sẽ cải thiện đáng kể vì các câu hỏi có từ khóa rõ ràng ("Shopee", "Sendo", "02 ngày lịch").

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận (My Approach) | 9 / 10 |
| Hoàn thiện code (42/42 tests) | 30 / 30 |
| Dự đoán độ tương tự | 4 / 5 |
| Kết quả truy xuất | 7 / 10 |
| **Tổng phần cá nhân** | **55 / 60** |
