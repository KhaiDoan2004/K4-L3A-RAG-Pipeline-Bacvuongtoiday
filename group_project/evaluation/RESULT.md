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

- Cấu hình tốt hơn trên benchmark hiện tại: **Config A — Dense-only**, với điểm trung bình `0.826`, cao hơn Config B (`0.739`) là `0.087` điểm.
- Evidence: Config A cao hơn ở Faithfulness (`+0.207`), Answer relevance (`+0.006`) và Context recall (`+0.134`); Context precision của hai cấu hình bằng nhau (`0.783`). BM25 vẫn hữu ích với mã học phần và tên riêng, nhưng cách RRF/top-k hiện tại làm giảm recall và đưa thêm context không đủ căn cứ vào một số câu hỏi.
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
|        1 | Dùng Dense-only làm cấu hình mặc định hiện tại; giữ Hybrid + RRF ở chế độ thử nghiệm | Benchmark cho thấy Dense cao hơn Hybrid `0.087` điểm trung bình | Tránh suy giảm Faithfulness và Context Recall | Chạy lại cùng 15 câu sau mỗi lần chỉnh RRF/top-k |
|        2 | Nâng cấp Document Layout Splitter cho bảng biểu | Các bảng biểu phân công đồ án có nhiều cột số liệu dễ bị đứt dòng | Tăng độ bao phủ thông tin bảng biểu | So sánh Context Recall trên các câu hỏi bảng biểu |
|        3 | Calibrate ngưỡng `SCORE_THRESHOLD` theo domain thực tế | Ngưỡng 0.30 phân biệt tốt câu hỏi trong ngành và ngoài lề | Giảm tỷ lệ hallucination câu hỏi ngoài lề về 0% | Kiểm thử với 10 câu hỏi ngoài ngành |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Document Reordering (Lost-in-the-middle) | No Reorder | +0.032 Faithfulness | +0 ms / 0$ | Đưa chunk quan trọng về đầu và cuối context giúp LLM chú ý trích dẫn chính xác hơn |
