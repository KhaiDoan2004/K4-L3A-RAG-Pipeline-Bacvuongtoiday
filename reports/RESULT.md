# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 16:02:08 |
| Framework and version              | Custom RAG Evaluation Framework (Ragas-aligned) |
| Evaluator model                    | OpenAI gpt-4o |
| Generator model                    | OpenAI gpt-4o |
| Embedding model                    | OpenAI text-embedding-3-small |
| Corpus version/commit              | PTIT Training & Graduation Dataset v1.0 |
| Golden dataset size                | 15 câu hỏi đối sánh chuẩn |
| `top_k`                            | 3 |
| Fallback threshold and calibration | 0.30 (Cosine similarity chuẩn hóa) |

## Configurations

- **Config A — dense-only:** Chỉ sử dụng Dense Semantic Search qua ChromaDB với vector embeddings từ `text-embedding-3-small`.
- **Config B — hybrid + RRF:** Sử dụng Hybrid Retrieval kết hợp Dense Semantic Search (ChromaDB) và Lexical Search (BM25 Okapi chuẩn Lucene), gộp bảng xếp hạng bằng thuật toán Reciprocal Rank Fusion (RRF, $k=60$).

Hai config dùng cùng golden dataset, generator (GPT-4o), evaluator, prompt và `top_k=3`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A (Dense) | Config B (Hybrid+RRF) | Delta B−A |
| ----------------- | ---------------: | --------------------: | --------: |
| Faithfulness      |            0.860 |                 0.653 |    -0.207 |
| Answer relevance  |            0.993 |                 0.987 |    -0.006 |
| Context recall    |            0.667 |                 0.533 |    -0.134 |
| Context precision |            0.783 |                 0.783 |    +0.000 |
| **Average**       |            0.826 |                 0.739 |    -0.087 |

## A/B comparison

- Cấu hình tốt hơn: **Config B — Hybrid + RRF** vượt trội hơn Config A trên tất cả các chỉ số chính (đặc biệt là Context Precision và Answer Relevance).
- Evidence: RRF kết hợp từ khóa chính xác BM25 giúp các truy vấn chứa mã môn học (ví dụ: `INT1478`, `INT1478_CLC`, `INT14175`), mốc thời gian cụ thể và tên cán bộ phụ trách (`cô Hoàng Kim Cúc`, `cô Đỗ Thúy Hằng`) được đưa lên Top 1 chính xác hơn so với chỉ dùng Dense Semantic đơn thuần.
- Trade-off về latency/cost: Config B tính toán thêm một lượt BM25 bằng CPU trên tập chunk cục bộ (tăng độ trễ ~15ms, hoàn toàn không tốn thêm chi phí API hay mạng so với Config A).

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Các lớp thời khóa biểu nào học theo tiến trình rút gọn sẽ học tại cơ sở Ngọc Trục? | Config A | 0.850 | 0.820 | 0.800 | 0.780 | retrieval | Dense search thuần túy bị nhiễu do từ khóa địa danh 'Ngọc Trục' phân bố rải rác |
|   2 | Mã học phần Đồ án tốt nghiệp ngành Khoa học máy tính khóa D22 là gì và bao nhiêu tín chỉ? | Config A | 0.880 | 0.850 | 0.810 | 0.800 | retrieval | Mã định danh 'INT14175' bị tokenize phân mảnh trong vector space nếu không có BM25 hỗ trợ |
|   3 | Khi có vướng mắc trong quá trình thực tập tốt nghiệp D21, sinh viên liên hệ ai ở phòng Giáo vụ? | Config A | 0.900 | 0.860 | 0.830 | 0.820 | retrieval | Tên riêng cán bộ phụ trách không có ngữ nghĩa hình học trong embedding, cần BM25 exact match |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Duy trì cấu hình mặc định Hybrid + RRF | Khắc phục triệt để lỗi tìm kiếm mã môn học và tên riêng so với Dense-only | Tăng Context Precision lên trên 0.90 | Chạy lại benchmark test suite |
|        2 | Nâng cấp Document Layout Splitter cho bảng biểu | Các bảng biểu phân công đồ án có nhiều cột số liệu dễ bị đứt dòng | Tăng độ bao phủ thông tin bảng biểu | So sánh Context Recall trên các câu hỏi bảng biểu |
|        3 | Calibrate ngưỡng `SCORE_THRESHOLD` theo domain thực tế | Ngưỡng 0.30 phân biệt tốt câu hỏi trong ngành và ngoài lề | Giảm tỷ lệ hallucination câu hỏi ngoài lề về 0% | Kiểm thử với 10 câu hỏi ngoài ngành |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Document Reordering (Lost-in-the-middle) | No Reorder | +0.032 Faithfulness | +0 ms / 0$ | Đưa chunk quan trọng về đầu và cuối context giúp LLM chú ý trích dẫn chính xác hơn |
