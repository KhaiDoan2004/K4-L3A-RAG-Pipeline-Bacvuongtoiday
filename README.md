# PTIT RAG — Tra cứu thực tập và tốt nghiệp

Chatbot RAG của nhóm **Bacvuongtoiday** trả lời câu hỏi về kế hoạch thực tập, điều kiện làm đồ án/khóa luận và các thông báo tốt nghiệp của Học viện Công nghệ Bưu chính Viễn thông (PTIT). Hệ thống truy xuất từ tài liệu nhóm tự thu thập, sinh câu trả lời có trích dẫn và hiển thị nguồn, phương thức retrieval cùng điểm số trên Streamlit.

## Dữ liệu

- 3 tài liệu PDF chính sách/thông báo PTIT trong `data/landing/legal/`.
- 5 bài viết công khai trong `data/landing/news/`, lưu JSON với `url`, `title`, `date_crawled`, `content_markdown`.
- 8 tài liệu Markdown chuẩn hóa trong `data/standardized/`; đây là đầu vào duy nhất của bước chunk và index.
- Metadata `source`, `title`, `doc_type` (`legal` hoặc `news`) và `url` được giữ xuyên suốt pipeline.

## Kiến trúc

```text
PDF/DOCX + bài viết web
        ↓
Markdown chuẩn hóa
        ↓
Recursive chunking (500 ký tự, overlap 50)
        ↓
Embedding → ChromaDB (cosine) → Dense Search ─┐
                                               ├→ RRF → threshold/fallback → LLM → citation
Markdown chunks → BM25 Lexical Search ─────────┘
```

| Task | Chức năng |
|---:|---|
| 1–3 | Thu thập PDF, crawl bài viết và chuẩn hóa Markdown |
| 4 | Chunk, embedding và index vào ChromaDB |
| 5 | Dense semantic search |
| 6 | BM25 lexical search |
| 7 | Reciprocal Rank Fusion (RRF) |
| 8 | PageIndex vectorless fallback an toàn |
| 9 | Retrieval pipeline, threshold theo dense cosine score |
| 10 | Sinh câu trả lời có citation và safe refusal |

## Cài đặt

Yêu cầu Python 3.10–3.13.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m playwright install chromium
Copy-Item .env.example .env
```

Cấu hình `.env` và không commit file này:

```dotenv
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=your_key
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
SCORE_THRESHOLD=0.30
PAGEINDEX_API_KEY=
```

Generation cũng hỗ trợ Gemini và Anthropic theo `.env.example`.

## Chạy pipeline

```powershell
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown
python -m src.task4_chunking_indexing
streamlit run app.py
```

Task 1 kiểm tra các PDF tải thủ công. Task 2 chỉ crawl URL công khai; nếu gặp WAF/captcha, chọn nguồn khác thay vì vượt cơ chế bảo vệ.

Ứng dụng `app.py` có tab chatbot hiển thị answer/source/method/score và tab evaluation trình bày benchmark A/B.

## Đánh giá

Golden dataset tại `group_project/evaluation/golden_dataset.json` gồm 15 câu. Hai cấu hình dùng cùng dataset, generator, evaluator và `top_k=3`:

| Metric | Dense-only | Hybrid + RRF | Delta B−A |
|---|---:|---:|---:|
| Faithfulness | 0.860 | 0.653 | -0.207 |
| Answer relevance | 0.993 | 0.987 | -0.006 |
| Context recall | 0.667 | 0.533 | -0.134 |
| Context precision | 0.783 | 0.783 | 0.000 |
| **Average** | **0.826** | **0.739** | **-0.087** |

Trên benchmark hiện tại, **Dense-only tốt hơn Hybrid + RRF**. Hybrid vẫn hữu ích với mã học phần và tên riêng nhưng cần hiệu chỉnh RRF/top-k trước khi chọn làm mặc định. Xem chi tiết tại `group_project/evaluation/RESULT.md`.

Chạy lại benchmark (cần API key):

```powershell
python -m src.evaluate
```

## Kiểm thử

```powershell
pytest tests/test_contracts.py -q
pytest tests/test_acceptance.py -q
pytest -q
```

Kết quả gần nhất: **20 tests passed** (15 contract, 5 acceptance).

## Thành phần nộp bài

```text
data/landing/                 dữ liệu gốc
data/standardized/            Markdown chuẩn hóa
group_project/evaluation/     golden dataset và báo cáo A/B
reports/                      báo cáo cá nhân từng thành viên
src/                          pipeline Task 1–10
app.py                        chatbot Streamlit
```

Không commit `.env`, API key, `.venv/`, cache hoặc dữ liệu ChromaDB sinh cục bộ.
