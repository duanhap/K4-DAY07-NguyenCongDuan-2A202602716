# KẾ HOẠCH THỰC HIỆN — Lab 07: Data Foundations, Embedding & Vector Store
**Sinh viên:** Nguyễn Công Duẩn — MSSV: 2A202602716
**Lớp:** K4-L3B | **Chủ đề:** Chính sách đổi trả thương mại điện tử

---

## TỔNG QUAN DELIVERABLE & ĐIỂM SỐ

| # | Nộp gì | Điểm |
|---|--------|------|
| 1 | `src/` hoàn thiện — `pytest tests/ -v` → 42 passed | 30 |
| 2 | `data/ecommerce/` — 5–10 tài liệu `.md` + `sources.csv` | 10 (nhóm) |
| 3 | `bench.py` + `ket_qua_benchmark.txt` | nền cho #4, #5 |
| 4 | `report/REPORT_CANHAN.md` | 60 (cá nhân) |
| 5 | `report/REPORT_NHOM.md` | 40 (nhóm) |
| 6 | Repo GitHub `K4-DAY07-NguyenCongDuan-2A202602716` | điều kiện chấm |

---

## GIAI ĐOẠN 1 — CÀI ĐẶT & KIỂM TRA MÔI TRƯỜNG

```powershell
cd d:\AITC\DAY7.2\K4-DAY07-NguyenCongDuan-2A202602716
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests/ -v
```

✅ **CHECKPOINT 1:** phải thấy **31 failed, 11 passed** — nếu thấy ModuleNotFoundError thì venv chưa activate.

---

## GIAI ĐOẠN 2 — THU THẬP DỮ LIỆU CHỦ ĐỀ "CHÍNH SÁCH ĐỔI TRẢ"

> **Mục tiêu:** có thư mục `data/ecommerce/` với 5–10 file `.md` sạch + `sources.csv` khớp 1-1.
> Thư mục đã có 2 file mẫu (`return-refund-policy.md`, `seller-warranty-policy.md`) nhưng đó là **template rỗng**, không dùng được làm benchmark — phải thay bằng nội dung thật.

---

### BƯỚC 2.1 — Lên danh sách URL (làm trước khi crawl bất kỳ gì)

Nhóm cần **5–10 trang chính sách thật** về đổi trả. Mỗi thành viên tìm 2–3 URL, tổng hợp lại tránh trùng.

**Nguồn đề xuất (chính sách đổi trả công khai, thường cho phép crawl):**

| Nền tảng | Trang gợi ý | audience |
|----------|-------------|---------|
| Shopee | `https://help.shopee.vn/portal/article/77241` (đổi trả người mua) | buyer |
| Shopee | `https://help.shopee.vn/portal/article/77244` (quy định người bán xử lý đổi trả) | seller |
| Tiki | `https://tiki.vn/chinh-sach-doi-tra-hang` | buyer |
| Lazada | `https://www.lazada.vn/helpcenter/...` | buyer |
| Sendo | trang chính sách công khai | buyer |
| Thegioididong | `https://www.thegioididong.com/tin-tuc/chinh-sach-doi-tra` | buyer |
| FPT Shop | trang chính sách đổi trả | buyer |
| Người bán Tiki | trang chính sách dành cho seller | seller |

> **Quan trọng:** Cần có **ít nhất 2 tài liệu** `audience: buyer` và **ít nhất 1 tài liệu** `audience: seller` để phần filter benchmark có nghĩa.

---

### BƯỚC 2.2 — Kiểm tra robots.txt TRƯỚC khi crawl

Với mỗi URL bạn định dùng, mở terminal và kiểm tra thủ công:

```powershell
# Ví dụ kiểm tra Shopee
python -c "
from urllib.robotparser import RobotFileParser
rp = RobotFileParser()
rp.set_url('https://help.shopee.vn/robots.txt')
rp.read()
url = 'https://help.shopee.vn/portal/article/77241'
print('Allowed:', rp.can_fetch('*', url))
"
```

- **Kết quả `True`** → được phép crawl tự động → dùng script
- **Kết quả `False`** → **bắt buộc copy thủ công** (xem Bước 2.4) → không được dùng script
- Nếu không đọc được robots.txt (lỗi network) → coi như không được phép, xử lý thủ công

---

### BƯỚC 2.3 — Crawl tự động bằng script (chỉ với URL được phép)

**Bước 2.3a — Tạo file `data/urls.csv`**

Copy file mẫu rồi điền URL vào:
```powershell
copy scripts\urls.example.csv data\urls.csv
```

Mở `data/urls.csv` và điền theo format sau (mỗi URL 1 dòng):
```csv
url,doc_id,title,audience,category,language,document_version,license_or_permission
https://help.shopee.vn/portal/article/77241,shopee-return-buyer,Chính sách đổi trả Shopee - Người mua,buyer,return-policy,vi,not-stated,public-source
https://help.shopee.vn/portal/article/77244,shopee-return-seller,Quy định xử lý đổi trả dành cho người bán Shopee,seller,return-policy,vi,not-stated,public-source
https://tiki.vn/chinh-sach-doi-tra-hang,tiki-return-policy,Chính sách đổi trả Tiki,buyer,return-policy,vi,not-stated,public-source
```

Giải thích các cột:
- `url` — URL trang cần crawl **(bắt buộc)**
- `doc_id` — tên file sẽ tạo ra (không dấu, không cách, dùng dấu `-`), phải unique
- `title` — tiêu đề tài liệu
- `audience` — `buyer` / `seller` / `both`
- `category` — loại chính sách: `return-policy`, `warranty-policy`, `refund-policy`...
- `language` — `vi` hoặc `en`
- `document_version` — điền nếu trang có ghi ngày hiệu lực, không thì để `not-stated`
- `license_or_permission` — ghi `public-source`

**Bước 2.3b — Chạy script crawl**

```powershell
python scripts\fetch_public_pages.py data\urls.csv --output-dir data\ecommerce
```

Script sẽ tự:
- Kiểm tra robots.txt từng URL
- Tải trang HTML, trích xuất text
- Tạo file `.md` với frontmatter trong `data/ecommerce/`
- Tạo/cập nhật `data/ecommerce/sources.csv`

**Xử lý lỗi thường gặp khi chạy script:**

| Thông báo lỗi | Nghĩa là gì | Cách xử lý |
|---------------|-------------|------------|
| `disallowed by robots.txt` | Trang cấm crawl tự động | Xoá URL khỏi csv, copy thủ công (Bước 2.4) |
| `extracted content is too short` | Trang render bằng JS, script không đọc được | Xoá URL, chọn trang khác hoặc copy thủ công |
| `LookupError: unknown encoding` | Server trả charset lạ, script crash | Xoá URL đó khỏi csv, chạy lại, xử lý riêng |
| `HTTP Error 403` | Server chặn | Xoá URL, chọn trang khác |
| File `.md` tạo ra nhưng chỉ có menu/footer | Output thô, chưa sạch | Tiếp tục Bước 2.5 (làm sạch) |

---

### BƯỚC 2.4 — Copy thủ công (cho URL bị chặn hoặc render bằng JS)

Với các trang script không crawl được, làm thủ công:

1. Mở trang trong trình duyệt
2. **Chọn toàn bộ nội dung chính** (chỉ phần điều khoản, không lấy menu/footer)
3. Copy và paste vào file `.md` mới trong `data/ecommerce/`
4. Thêm frontmatter đúng format ở đầu file

**Mẫu file `.md` cần tạo:**
```markdown
---
doc_id: shopee-return-buyer
title: "Chính sách đổi trả Shopee - Người mua"
source_url: "https://help.shopee.vn/portal/article/77241"
retrieved_at: "2026-09-20"
document_version: "not-stated"
audience: buyer
category: return-policy
language: vi
---

# Chính sách đổi trả Shopee - Người mua

[Dán nội dung đã copy vào đây, đã bỏ menu/header/footer]
```

> **Lưu ý `doc_id`:** phải trùng với tên file (không có `.md`). Ví dụ file `shopee-return-buyer.md` thì `doc_id: shopee-return-buyer`.

---

### BƯỚC 2.5 — Làm sạch nội dung (QUAN TRỌNG — không bỏ qua)

File `.md` vừa tạo ra (dù bằng script hay thủ công) thường còn rất bẩn. Phải đọc và xoá thủ công:

**Xoá những phần này:**
- Menu điều hướng (Trang chủ / Danh mục / Giỏ hàng...)
- Banner khuyến mãi, quảng cáo sản phẩm
- Footer (thông tin công ty, mạng xã hội, copyright)
- Sidebar (bài viết liên quan, sản phẩm gợi ý)
- Các dòng lặp lại không có nội dung (dòng trắng liên tiếp)

**Giữ lại những phần này:**
- Tiêu đề và tiêu đề mục (##, ###)
- Các điều khoản, điều kiện cụ thể
- **Số liệu quan trọng:** số ngày đổi trả, % hoàn tiền, mức phạt...
- Mốc thời gian, deadline
- Ngoại lệ và trường hợp đặc biệt

**Kiểm tra nhanh sau khi làm sạch:**
- File còn khoảng 500–3000 ký tự là vừa (quá ngắn = thiếu nội dung, quá dài = còn rác)
- Đọc lại 1 lần xem có câu nào bị cắt giữa chừng không

---

### BƯỚC 2.6 — Xử lý tài liệu có audience: both

Nếu một trang có cả quy định cho người mua lẫn người bán (ví dụ: "Người mua được đổi trong 7 ngày" và "Người bán phải xử lý trong 3 ngày"), **đừng để `audience: both`** vì filter sẽ không hoạt động được.

**Cách xử lý:**
1. Tạo 2 file riêng từ cùng 1 trang nguồn
2. File 1: chỉ lấy phần nội dung dành cho người mua, đặt `audience: buyer`
3. File 2: chỉ lấy phần nội dung dành cho người bán, đặt `audience: seller`
4. Cả 2 file cùng `source_url`, khác `doc_id`

Ví dụ:
```
shopee-return-buyer.md   (audience: buyer)  — "7 ngày đổi trả, hàng phải còn nguyên tem"
shopee-return-seller.md  (audience: seller) — "Người bán phải phản hồi trong 3 ngày làm việc"
```

---

### BƯỚC 2.7 — Cập nhật sources.csv thủ công (nếu có file tạo thủ công)

Nếu bạn tạo file `.md` thủ công (Bước 2.4), script không tự thêm vào `sources.csv`. Phải thêm tay:

Mở `data/ecommerce/sources.csv` và thêm dòng:
```csv
doc_id,file_path,title,source_url,retrieved_at,document_version,license_or_permission
shopee-return-buyer,data/ecommerce/shopee-return-buyer.md,Chính sách đổi trả Shopee - Người mua,https://help.shopee.vn/portal/article/77241,2026-09-20,not-stated,public-source
```

**Quy tắc sources.csv:**
- Mỗi file `.md` phải có đúng 1 dòng trong csv
- `doc_id` trong csv phải trùng khớp với `doc_id` trong frontmatter file `.md` và tên file

---

### BƯỚC 2.8 — Kiểm tra toàn bộ (CHECKPOINT 2)

Chạy lệnh kiểm tra sau, mọi dòng phải ra `OK`:

```powershell
python -c "
import csv, re
from pathlib import Path
D = Path('data/ecommerce')
REQ = ['doc_id','title','source_url','retrieved_at','document_version','audience']
mds = sorted(D.glob('*.md'))
rows = list(csv.DictReader(open(D/'sources.csv', encoding='utf-8')))
ids, auds = [], {}
for p in mds:
    text = p.read_text(encoding='utf-8')
    parts = text.split('---')
    fm_text = parts[1] if len(parts) >= 3 else ''
    fm = dict(re.findall(r'^(\w+):\s*(.+)$', fm_text, re.M))
    ids.append(fm.get('doc_id'))
    aud = fm.get('audience','').strip().strip('\"')
    auds[aud] = auds.get(aud, 0) + 1
    ok = all(k in fm for k in REQ) and fm.get('doc_id','').strip('\"') == p.stem
    print(f'{p.name:50} {\"OK\" if ok else \">>> THIEU METADATA <<<\"}')
print()
print('So file   :', len(mds), '(can 5-10)')
csv_ids = sorted(r['doc_id'] for r in rows)
print('CSV khop  :', 'OK' if csv_ids == sorted(ids) else '>>> LECH <<<')
print('Audience  :', auds)
print('Filter OK :', 'OK' if len(auds) >= 2 else '>>> CHI CO 1 GIA TRI, FILTER SE KHONG HOAT DONG <<<')
"
```

**Kết quả cần đạt:**
- Tất cả file đều in `OK`
- `So file: 5-10`
- `CSV khop: OK`
- `Audience` có **ít nhất 2 giá trị** khác nhau (ví dụ `{'buyer': 4, 'seller': 2}`)

**Nếu có file báo `THIEU METADATA`:** mở file đó, kiểm tra frontmatter, đảm bảo `doc_id` trùng tên file và đủ 6 trường bắt buộc.

**Nếu `CSV khop: LECH`:** so sánh tên file trong thư mục với `doc_id` trong sources.csv, tìm dòng thừa/thiếu.

**Nếu `Audience` chỉ có 1 giá trị:** bổ sung thêm tài liệu `seller` hoặc tách file `both` thành 2 file riêng.

---

### Tóm tắt trạng thái thư mục sau Giai đoạn 2

```
data/ecommerce/
├── shopee-return-buyer.md       (audience: buyer)
├── shopee-return-seller.md      (audience: seller)
├── tiki-return-policy.md        (audience: buyer)
├── lazada-refund-policy.md      (audience: buyer)
├── thegioididong-return.md      (audience: buyer)
├── sendo-return-policy.md       (audience: buyer)
└── sources.csv                  (6 dòng khớp 6 file trên)
```

> 2 file mẫu `return-refund-policy.md` và `seller-warranty-policy.md` đã có sẵn trong repo là **template rỗng** — có thể xoá hoặc thay bằng nội dung thật (giữ nguyên `doc_id` nếu muốn giữ file, sửa nội dung và `source_url`).

✅ **CHECKPOINT 2 đạt khi:** script kiểm tra in toàn `OK`, ≥5 file, CSV khớp, audience có ≥2 giá trị.

---

## GIAI ĐOẠN 3 — VIẾT CODE (src/)

### Thứ tự ưu tiên
```
compute_similarity
    ↓
SentenceChunker.chunk
    ↓
RecursiveChunker.chunk + _split
    ↓
ChunkingStrategyComparator.compare
    ↓
EmbeddingStore: _make_record → _search_records → add_documents → search → get_collection_size → search_with_filter → delete_document
    ↓
KnowledgeBaseAgent.answer
```

---

### 3.1 — `src/chunking.py`

#### A. `compute_similarity`
```python
def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (mag_a * mag_b)
```

#### B. `SentenceChunker.chunk`
**Thuật toán:**
1. Dùng `re.split(r'(?<=[.!?])\s+', text)` — lookbehind giữ dấu câu, không bị nuốt mất
2. Lọc bỏ chuỗi rỗng
3. Group theo `max_sentences_per_chunk` câu
4. Join mỗi nhóm bằng `" "`, strip khoảng trắng
5. Text rỗng → `[]`

**Edge case ghi vào báo cáo (không cần fix, nêu ra là được điểm):**
- Chữ viết tắt `TS.`, `v.v.`, `P.GS.` bị cắt sai
- Số thập phân `3.14` bị cắt sau dấu chấm

#### C. `RecursiveChunker.chunk` và `_split`
**Thuật toán `_split(text, separators)`:**
1. **Base case 1:** `len(text) <= chunk_size` → return `[text]`
2. **Base case 2:** `separators == []` → cắt cứng theo `chunk_size`, return list các mảnh
3. Thử `sep = separators[0]`, split text
4. Nếu split được ≥2 mảnh:
   - Mỗi mảnh dài hơn `chunk_size` → đệ quy với `separators[1:]`
   - **Bước gom (merge):** duyệt các mảnh nhỏ, cộng dồn vào buffer cho đến khi gần `chunk_size`, mới flush
5. Nếu không split được → thử tiếp `separators[1:]`

**`chunk(text)`:** gọi `_split(text, self.separators)`, lọc bỏ string rỗng

**Bẫy thường gặp:**
- Thiếu merge step → hàng trăm chunk 5–10 ký tự
- Thiếu base case `separators == []` → fail `test_empty_separators_falls_back_gracefully`

#### D. `ChunkingStrategyComparator.compare`
Trả về dict với 3 key chính xác: `fixed_size`, `by_sentences`, `recursive`.
Mỗi key là dict có `count`, `avg_length`, `chunks`.
Chặn chia cho 0 khi `count == 0`.

✅ **CHECKPOINT 3:**
```powershell
pytest tests/ -k "Chunker or Similarity or Compare" -v
# Kỳ vọng: 23 passed
```

---

### 3.2 — `src/store.py`

**Nguyên tắc thiết kế:** Bỏ hoàn toàn ChromaDB, chỉ dùng `self._store: list[dict]` in-memory. Sửa ngay dòng `self._use_chroma = True` thành `False`.

#### A. `_make_record(doc)`
```python
{
    "id": doc.id,
    "content": doc.content,
    "embedding": self._embedding_fn(doc.content),
    "metadata": {**doc.metadata, "doc_id": doc.id},  # luôn có doc_id
}
```
- Copy metadata, không dùng trực tiếp object người gọi
- Luôn set `metadata["doc_id"]` → `delete_document` phụ thuộc đây

#### B. `_search_records(query, records, top_k)`
- Tính `_dot(query_vec, record["embedding"])` cho mọi record
- Sort giảm dần theo score
- Trả về top_k, **bỏ key `embedding`** khỏi output, thêm key `score`

#### C. `add_documents` → `self._store.append(self._make_record(doc))` cho mỗi doc

#### D. `search` → `return self._search_records(query, self._store, top_k)`

#### E. `get_collection_size` → `return len(self._store)`

#### F. `search_with_filter` — **LỌC TRƯỚC, search SAU**
```python
if metadata_filter:
    candidates = [r for r in self._store
                  if all(r["metadata"].get(k) == v for k, v in metadata_filter.items())]
else:
    candidates = self._store
return self._search_records(query, candidates, top_k)
```

#### G. `delete_document`
```python
before = len(self._store)
self._store = [r for r in self._store if r["metadata"].get("doc_id") != doc_id]
return len(self._store) < before
```

---

### 3.3 — `src/agent.py`

#### `__init__`
```python
self.store = store
self.llm_fn = llm_fn
```

#### `answer(question, top_k=3)`
1. Kiểm tra store rỗng (`get_collection_size() == 0`) → trả `"Không có tài liệu nào trong kho lưu trữ."` ngay
2. `results = self.store.search(question, top_k=top_k)`
3. Dựng context đánh số `[1]`, `[2]`, `[3]` kèm nguồn (`metadata.get("source_url")` hoặc `doc_id`)
4. Tạo prompt yêu cầu: chỉ dùng context đã cho, trích dẫn số khi dùng, nói rõ nếu không tìm thấy
5. `return self.llm_fn(prompt)`

✅ **CHECKPOINT 4:**
```powershell
pytest tests/ -v
# Kỳ vọng: 42 passed

python main.py "Chinh sach doi tra la gi?"
# Không crash, in ra kết quả
```

---

## GIAI ĐOẠN 4 — VIẾT bench.py

### Luồng hoạt động
```
Đọc file .md → parse frontmatter → chunk phần body → tạo Document → nạp vào store → chạy 5 query → ghi ket_qua_benchmark.txt
```

### 4 điều KHÔNG được làm sai
1. **Không nạp cả file làm 1 Document** — phải chunk body trước, mỗi chunk 1 Document
2. **`Document.id` = `"file#0"`, `"file#1"`...** còn `metadata["doc_id"]` = tên file gốc
3. **Metadata frontmatter phải trải vào MỌI chunk** — nếu không, `search_with_filter` không lọc được
4. **Bỏ frontmatter trước khi chunk** — không chunk cả khối YAML

### Cấu trúc bench.py

```python
from pathlib import Path
import re

# ← ĐỔI CHUNKER NÀY THEO CHIẾN LƯỢC CÁ NHÂN CỦA BẠN
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed   # ← đổi sang GeminiEmbedder nếu có API key
from src.models import Document
from src.store import EmbeddingStore

CORPUS_DIR = Path("data/ecommerce")
CHUNKER = RecursiveChunker(chunk_size=500)

# ← NHÓM THỐNG NHẤT 5 CÂU NÀY
QUERIES = [
    {
        "id": 1,
        "q": "Người mua có thể đổi hàng trong bao nhiêu ngày?",
        "filter": {"audience": "buyer"},
        "gold_keyword": "7 ngày",
    },
    {
        "id": 2,
        "q": "Người bán phải xử lý yêu cầu đổi trả trong bao nhiêu ngày?",
        "filter": {"audience": "seller"},
        "gold_keyword": "3 ngày",
    },
    {
        "id": 3,
        "q": "Điều kiện để sản phẩm được chấp nhận đổi trả?",
        "filter": None,
        "gold_keyword": "nguyên tem",
    },
    {
        "id": 4,
        "q": "Hàng giảm giá có được đổi trả không?",
        "filter": {"audience": "buyer"},
        "gold_keyword": "không áp dụng",
    },
    {
        "id": 5,
        "q": "Quy trình hoàn tiền sau khi đổi trả thành công?",
        "filter": None,
        "gold_keyword": "hoàn tiền",
    },
]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Tách YAML frontmatter và phần body."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()
    fm_raw = parts[1]
    body = parts[2].strip()
    # Parse từng dòng key: value, bỏ dấu ngoặc kép nếu có
    fm = {}
    for line in fm_raw.splitlines():
        m = re.match(r'^(\w+):\s*"?([^"]+)"?\s*$', line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, body


def main():
    # 1. Đọc corpus, chunk, nạp vào store
    store = EmbeddingStore(collection_name="bench", embedding_fn=_mock_embed)
    total_chunks = 0

    for md_path in sorted(CORPUS_DIR.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        if not body:
            print(f"Bỏ qua {md_path.name}: không có nội dung sau frontmatter")
            continue

        chunks = CHUNKER.chunk(body)
        docs = [
            Document(
                id=f"{md_path.stem}#{i}",          # id của chunk
                content=chunk,
                metadata={
                    **fm,                            # trải toàn bộ frontmatter vào metadata
                    "doc_id": md_path.stem,          # doc_id = tên file gốc (cho delete)
                    "chunk_index": str(i),
                },
            )
            for i, chunk in enumerate(chunks)
        ]
        store.add_documents(docs)
        total_chunks += len(docs)
        print(f"  {md_path.name}: {len(chunks)} chunks")

    print(f"\nTong: {total_chunks} chunks tu {CORPUS_DIR}\n")
    print("=" * 60)

    # 2. Chạy 5 queries và ghi kết quả
    lines = [f"Tong chunks: {total_chunks}", "=" * 60]

    for item in QUERIES:
        header = f"\nCAU {item['id']}: {item['q']}"
        if item.get("filter"):
            header += f"  [filter={item['filter']}]"
        print(header)
        lines.append(header)

        results = store.search_with_filter(
            item["q"], top_k=3, metadata_filter=item.get("filter")
        )

        if not results:
            msg = "  >>> Khong tim thay ket qua <<<"
            print(msg)
            lines.append(msg)
            continue

        for rank, r in enumerate(results, 1):
            gold_kw = item.get("gold_keyword", "")
            has_gold = gold_kw.lower() in r["content"].lower() if gold_kw else False
            flag = "✓ CO GOLD" if has_gold else "✗"
            doc_id = r["metadata"].get("doc_id", "?")
            audience = r["metadata"].get("audience", "?")
            score_line = f"  [{rank}] score={r['score']:.4f}  doc={doc_id}  audience={audience}  {flag}"
            content_preview = r["content"][:150].replace("\n", " ")
            content_line = f"      {content_preview}..."

            print(score_line)
            print(content_line)
            lines.append(score_line)
            lines.append(content_line)

    # 3. Lưu kết quả
    output = "\n".join(lines)
    Path("ket_qua_benchmark.txt").write_text(output, encoding="utf-8")
    print("\n" + "=" * 60)
    print("Da luu: ket_qua_benchmark.txt")


if __name__ == "__main__":
    main()
```

✅ **CHECKPOINT 5:**
```powershell
python bench.py
# In ra số chunk + top-3 cho 5 câu, không crash
```

---

## GIAI ĐOẠN 5 — SO SÁNH & PHÂN TÍCH LỖI

### A/B test bắt buộc với câu hỏi cần filter
Chạy câu 1 hai lần, ghi lại kết quả vào REPORT:

```python
# Trong bench.py hoặc chạy riêng trong Python shell
q = "Người mua có thể đổi hàng trong bao nhiêu ngày?"

# Lần 1: có filter
r_with = store.search_with_filter(q, top_k=3, metadata_filter={"audience": "buyer"})

# Lần 2: không filter
r_without = store.search_with_filter(q, top_k=3, metadata_filter=None)

# So sánh: top-3 có khác nhau không? audience của kết quả có đúng không?
```

### Thang điểm tự chấm mỗi câu
- **2 điểm:** top-1 là chunk liên quan + content chứa `gold_keyword`
- **1 điểm:** chunk liên quan ở top-2 hoặc top-3
- **0 điểm:** không có chunk liên quan trong top-3

### Phân tích failure case (phải có ≥1 trong báo cáo)
Mẫu viết:
```
Câu hỏi: "..."
Top-3 trả về: [mô tả ngắn doc nào, score bao nhiêu]
Vấn đề: chunk đúng chủ đề nhưng không chứa số liệu cụ thể / MockEmbedder không mã hóa ngữ nghĩa...
Đề xuất: dùng overlap lớn hơn / dùng embedder thật / tách câu hỏi rõ hơn...
```

✅ **CHECKPOINT 6:** Có `ket_qua_benchmark.txt` và đã điền bảng top-3 vào REPORT_CANHAN mục 5.

---

## GIAI ĐOẠN 6 — HOÀN THIỆN BÁO CÁO

### REPORT_CANHAN.md — 5 mục, 60 điểm

| Mục | Nội dung cần điền | Điểm |
|-----|-------------------|------|
| 1. Khởi động | Cosine similarity + bài toán chunking | 5 |
| 2. Hướng tiếp cận | Giải thích từng phần code | 10 |
| 3. Hoàn thiện code | Dán output `pytest tests/ -v` (42 passed) | 30 |
| 4. Dự đoán similarity | 5 cặp câu về chính sách đổi trả + nhận xét | 5 |
| 5. Kết quả truy xuất | Bảng top-3, 5 câu benchmark | 10 |

### Gợi ý trả lời warm-up (mục 1)

**Cosine similarity cao nghĩa là gì:**
Hai văn bản có cosine similarity cao khi embedding của chúng hướng về cùng một vùng trong không gian vector — tức chúng chia sẻ ý nghĩa/chủ đề dù từ ngữ có thể khác nhau.

**Cặp câu về chính sách đổi trả:**
- **Cao:** *"Khách hàng được đổi hàng trong 7 ngày kể từ ngày nhận"* vs *"Thời hạn trả sản phẩm là một tuần tính từ lúc giao thành công"*
- **Thấp:** *"Chính sách hoàn tiền khi hàng lỗi"* vs *"Hướng dẫn đăng ký tài khoản người bán"*

**Tại sao cosine tốt hơn Euclidean:**
Cosine đo góc giữa 2 vector nên không bị ảnh hưởng bởi độ dài — văn bản ngắn và văn bản dài cùng chủ đề vẫn cho cosine cao. Euclidean đo khoảng cách tuyệt đối nên văn bản dài có vector lớn hơn sẽ luôn "xa hơn" văn bản ngắn dù nói cùng nội dung.

**Bài toán chunking:**
- `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunks`
- Overlap 100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25 chunks`
- Overlap lớn hơn → nhiều chunk hơn, nhưng mỗi ranh giới giữa 2 chunk được phủ bởi nhiều chunk → giảm nguy cơ mất thông tin tại biên (ví dụ: một điều khoản nằm vắt qua 2 chunk).

---

## GIAI ĐOẠN 7 — NỘP BÀI

### Checklist trước khi push
```powershell
pytest tests/ -v           # phải 42 passed, không còn NotImplementedError
git status                 # không được thấy .venv/ hay .env
```

### Lệnh push
```powershell
git add src/ data/ecommerce/ bench.py ket_qua_benchmark.txt report/
git commit -m "Nop bai Lab 07"
git branch -M main
git remote add origin https://github.com/<tai-khoan>/K4-DAY07-NguyenCongDuan-2A202602716.git
git push -u origin main
```

### Cấu trúc repo khi nộp
```
K4-DAY07-NguyenCongDuan-2A202602716/
├── src/                      ← chunking.py, store.py, agent.py đã hoàn thiện
├── data/ecommerce/           ← 5-10 .md thật + sources.csv
├── report/
│   ├── REPORT_CANHAN.md      ← điền đủ 5 mục
│   └── REPORT_NHOM.md        ← nhóm điền chung
├── bench.py
├── ket_qua_benchmark.txt
└── tests/, main.py, ...
```

✅ **CHECKPOINT 7 — hoàn tất:**
- [ ] 42/42 tests passed
- [ ] `data/ecommerce/` có 5–10 tài liệu thật + sources.csv khớp 1-1
- [ ] audience có ≥2 giá trị (buyer + seller)
- [ ] ≥1 query dùng `metadata_filter={"audience": "buyer"}` hoặc `"seller"`
- [ ] REPORT_CANHAN.md + REPORT_NHOM.md điền đủ
- [ ] bench.py + ket_qua_benchmark.txt đã commit
- [ ] Repo đúng tên `K4-DAY07-NguyenCongDuan-2A202602716`, không chứa `.venv`/`.env`

---

## BẢNG LỖI THƯỜNG GẶP → CÁCH TRÁNH

| Lỗi | Nguyên nhân | Cách phòng |
|-----|-------------|-----------|
| `_use_chroma = True` sập 14 test | ChromaDB nhánh chưa implement | Set `False` trong `__init__`, xoá `try/import chromadb` |
| `delete_document` luôn `False` | Thiếu `doc_id` trong metadata | Luôn set `metadata["doc_id"] = doc.id` trong `_make_record` |
| `test_no_filter_returns_all_candidates` fail | `search` và `search_with_filter` dùng 2 code path riêng | Cho cả 2 gọi chung `_search_records` |
| `test_empty_separators_falls_back_gracefully` fail | Thiếu base case `separators == []` | Thêm nhánh cắt cứng theo `chunk_size` |
| SentenceChunker nuốt dấu câu | `re.split(r'[.!?]\s+')` | Dùng lookbehind `r'(?<=[.!?])\s+'` |
| RecursiveChunker ra chunk 5-10 ký tự | Thiếu merge step | Gom các mảnh nhỏ liền kề vào buffer |
| `search_with_filter` luôn rỗng | Metadata không trải vào từng chunk | Gộp frontmatter vào metadata khi tạo Document trong bench.py |
| Filter không đổi kết quả | Corpus chỉ có 1 giá trị audience | Tách file `both` thành 2 file riêng |
| Score âm cho chunk đúng | MockEmbedder không mã hóa ngữ nghĩa | Ghi rõ trong báo cáo; dùng GeminiEmbedder nếu có key |
| File `.md` rỗng sau crawl | Trang render bằng JS | Đổi nguồn hoặc copy thủ công |
| `sources.csv` không khớp file | Tạo file thủ công mà quên thêm vào csv | Sau mỗi file thủ công → thêm dòng vào csv ngay |
