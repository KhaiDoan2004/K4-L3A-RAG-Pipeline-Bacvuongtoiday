# Individual contribution report

## Thông tin

- Họ và tên: Trần Ngọc Khuyến
- Mã học viên: 2A202602682
- Nhóm: Bacvuongtoiday
- Repository/branch: `K4-L3A-RAG-Pipeline-Bacvuongtoiday` / `main`
- Phần việc trọng tâm: Task 7 — Reciprocal Rank Fusion và Task 8 — PageIndex vectorless fallback

## Phần việc đã thực hiện

| Module/deliverable | Việc trực tiếp thực hiện | File liên quan | Trạng thái |
|---|---|---|---|
| Task 7 — RRF | Xây dựng hàm `rerank_rrf()` để hợp nhất nhiều danh sách kết quả Dense/BM25 theo thứ hạng; dùng công thức `sum(1 / (k + rank))`, rank bắt đầu từ 1; loại kết quả trùng ID; sắp xếp giảm dần và gắn `retrieval_method="hybrid"`. | `src/task7_reranking.py` | Hoàn thành |
| Contract cho RRF | Bảo đảm kết quả không vượt quá `top_k`, giữ nguyên nội dung và metadata của tài liệu, không cộng trực tiếp cosine score với BM25 score. | `src/task7_reranking.py`, `tests/test_contracts.py` | Hoàn thành |
| Task 8 — PageIndex fallback | Thiết lập interface `upload_documents()` và `pageindex_search(query, top_k)`; đọc `PAGEINDEX_API_KEY` từ `.env`; trả kết quả rỗng an toàn khi dịch vụ chưa cấu hình hoặc khi provider phát sinh lỗi. | `src/task8_pageindex_vectorless.py` | Hoàn thành phần fallback an toàn; chưa tích hợp API thật |
| Tích hợp fallback | Phối hợp pipeline dùng cosine score gốc của Dense Search để quyết định fallback; không dùng RRF score làm threshold; nếu PageIndex không khả dụng thì giữ kết quả Hybrid thay vì làm ứng dụng crash. | `src/task9_retrieval_pipeline.py` | Hoàn thành |
| Kiểm thử | Kiểm tra công thức RRF, khử trùng lặp, method `hybrid`, nhánh fallback theo dense score và khả năng chịu lỗi provider. | `tests/test_contracts.py` | 20/20 test toàn repo đạt |

## Quyết định kỹ thuật quan trọng

### 1. Hợp nhất theo thứ hạng bằng RRF

Dense Search và BM25 sử dụng hai thang điểm khác nhau, nên không thể cộng trực tiếp cosine similarity với điểm BM25. Task 7 sử dụng Reciprocal Rank Fusion:

```text
RRF(d) = Σ 1 / (k + rank(d))
```

Với `k=60`, kết quả xuất hiện ở cả hai danh sách được ưu tiên, nhưng một kết quả đứng đầu ở riêng một retriever vẫn giữ được đóng góp hợp lý. ID tài liệu được dùng làm khóa hợp nhất để không trả chunk trùng lặp.

Trade-off: RRF chỉ phản ánh sự đồng thuận về thứ hạng, không còn giữ ý nghĩa xác suất hay cosine similarity. Vì vậy RRF score không được dùng để quyết định fallback.

### 2. Fallback dựa trên Dense cosine score và chịu lỗi provider

Pipeline lấy `dense[0]["score"]` làm tín hiệu confidence. Khi score thấp hơn `SCORE_THRESHOLD`, hệ thống thử gọi `pageindex_search()`. Lời gọi được bảo vệ để lỗi cấu hình, lỗi mạng hoặc lỗi provider không làm UI dừng; pipeline quay lại kết quả Hybrid nếu PageIndex không trả kết quả.

Trade-off: cơ chế chịu lỗi đã hoàn chỉnh, nhưng adapter PageIndex hiện chưa thực hiện upload, cache document ID và parse response thật. Khi chưa có `PAGEINDEX_API_KEY`, Task 8 hoạt động như fallback tùy chọn và trả danh sách rỗng.

## Kiểm thử và kết quả

Lệnh kiểm thử trong môi trường `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Kết quả ngày 20/09/2026:

```text
20 passed in 26.14s
```

Các ca kiểm thử liên quan trực tiếp:

- `test_rrf_uses_rank_deduplicates_and_marks_hybrid`: xác minh công thức RRF, thứ hạng, khử trùng lặp và method `hybrid`.
- `test_retrieve_uses_dense_score_for_fallback`: xác minh fallback dựa trên cosine score gốc của Dense Search.
- `test_retrieve_fuses_once_when_dense_is_confident`: xác minh RRF chỉ chạy một lần khi Dense đủ confidence.
- `test_retrieve_survives_fallback_provider_error`: xác minh lỗi PageIndex không làm pipeline crash.

## Điều còn hạn chế

- `src/task8_pageindex_vectorless.py` chưa gọi PageIndex API thật, chưa upload tài liệu, cache document ID hoặc chuyển response thành `SearchResult`.
- `SCORE_THRESHOLD = 0.30` cần được hiệu chỉnh thêm bằng một tập query in-domain và out-of-domain riêng trước khi triển khai thực tế.
- Khi hai kết quả có cùng RRF score, thứ tự hiện phụ thuộc vào thứ tự xuất hiện trong các ranked list; có thể bổ sung tie-break bằng dense score gốc.

## Hướng phát triển tiếp theo

1. Hoàn thiện PageIndex client với timeout và retry hữu hạn.
2. Lưu mapping document ID vào file cache để không upload lại khi chạy lần sau.
3. Parse kết quả PageIndex về đúng schema `SearchResult` với `retrieval_method="pageindex"`.
4. Bổ sung integration test dùng fake PageIndex client, không gọi network thật.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh phần việc tập trung vào Task 7 và Task 8, đồng thời ghi rõ giới hạn hiện tại của tích hợp PageIndex.

- Ngày: 20/09/2026
- Thành viên: Trần Ngọc Khuyến
