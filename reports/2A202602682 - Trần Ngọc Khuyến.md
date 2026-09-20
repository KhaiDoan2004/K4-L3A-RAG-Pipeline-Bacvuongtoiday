# Individual contribution report

## Thông tin

- Họ và tên: Trần Ngọc Khuyến
- Mã học viên: 2A202602682
- Nhóm: Bacvuongtoiday
- Repository/branch: `K4-L3A-RAG-Pipeline-Bacvuongtoiday` / `main`
- Phần việc trọng tâm: Task 7 — Reciprocal Rank Fusion và Task 8 — PageIndex vectorless fallback

## Phần việc đã thực hiện

| Module | Nội dung | File | Trạng thái |
|---|---|---|---|
| Task 7 — RRF | Hợp nhất kết quả Dense/BM25 theo `sum(1/(k+rank))`, rank bắt đầu từ 1; khử trùng ID; sắp xếp giảm dần; gắn method `hybrid`. | `src/task7_reranking.py` | Hoàn thành |
| Task 7 — Contract | Giữ content/metadata, giới hạn `top_k`, không cộng trực tiếp cosine score với BM25 score. | `tests/test_contracts.py` | Hoàn thành |
| Task 8 — Fallback | Đọc `PAGEINDEX_API_KEY`; cung cấp interface upload/search; trả rỗng an toàn khi dịch vụ chưa cấu hình hoặc provider lỗi. | `src/task8_pageindex_vectorless.py` | Hoàn thành fallback an toàn; adapter API thật còn hạn chế |
| Tích hợp retrieval | Dùng dense cosine score gốc để quyết định fallback; không dùng RRF score; giữ kết quả Hybrid nếu PageIndex lỗi. | `src/task9_retrieval_pipeline.py` | Hoàn thành |

## Quyết định kỹ thuật

### RRF thay vì cộng điểm trực tiếp

Dense cosine similarity và BM25 score không cùng thang đo. Vì vậy Task 7 hợp nhất theo thứ hạng:

```text
RRF(d) = Σ 1 / (k + rank(d))
```

Với `k=60`, tài liệu xuất hiện ở cả hai retriever được ưu tiên mà không phải chuẩn hóa hai thang điểm. ID chunk là khóa hợp nhất để không tạo kết quả trùng.

### Fallback dựa trên Dense score

RRF score chỉ thể hiện sự đồng thuận thứ hạng nên không phù hợp để đo confidence. Pipeline dùng `dense[0]["score"]` so với `SCORE_THRESHOLD`; nếu thấp thì thử PageIndex. Lỗi provider được bắt để giao diện không crash và pipeline vẫn trả kết quả Hybrid nếu có.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_contracts.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_acceptance.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Kết quả kiểm tra ngày 20/09/2026:

- Contract tests: `15 passed`.
- Acceptance tests: `5 passed`.
- Toàn bộ: `20 passed`.

Các ca liên quan trực tiếp gồm kiểm tra công thức RRF/khử trùng lặp, RRF chỉ chạy một lần, fallback dùng dense score và pipeline chịu được lỗi PageIndex.

## Hạn chế và hướng phát triển

- Adapter PageIndex hiện chưa upload/cache/parse kết quả API đầy đủ; khi không có API key, fallback trả danh sách rỗng an toàn.
- `SCORE_THRESHOLD=0.30` cần tiếp tục hiệu chỉnh bằng nhiều query in-domain và out-of-domain.
- Có thể bổ sung tie-break bằng dense score khi nhiều tài liệu có cùng RRF score.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh phần việc tập trung vào Task 7 và Task 8 và có thể giải thích, chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Thành viên: Trần Ngọc Khuyến
