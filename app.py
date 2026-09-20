import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation

load_dotenv()

ROOT = Path(__file__).parent
EVAL_RESULTS_JSON = ROOT / "group_project" / "evaluation" / "eval_results.json"
RESULT_MD_PATH = ROOT / "group_project" / "evaluation" / "RESULT.md"
GOLDEN_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"

st.set_page_config(
    page_title="PTIT RAG System — Chatbot & Đánh giá A/B",
    page_icon="🎓",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🎓 PTIT RAG System")
    st.caption("Tra cứu Kế hoạch Đào tạo, Thực tập & Tốt nghiệp PTIT")
    st.markdown("---")
    top_k = st.slider("Số lượng Chunks truy xuất (top_k)", min_value=1, max_value=10, value=4)
    st.markdown("---")
    st.markdown("**Cấu hình hệ thống:**")
    st.markdown("- **Mô hình LLM:** OpenAI GPT-4o")
    st.markdown("- **Embedding:** text-embedding-3-small")
    st.markdown("- **Retrieval:** Hybrid (ChromaDB Cosine + BM25 Okapi + RRF)")
    st.markdown("---")
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

tab_chat, tab_eval = st.tabs(["💬 Chatbot Tra cứu & Citation", "📊 Báo cáo Đánh giá & Benchmark A/B"])

# ==================== TAB 1: CHATBOT ====================
with tab_chat:
    st.subheader("🎓 Trợ lý Tra cứu Thông tin Tốt nghiệp & Đào tạo PTIT")
    st.caption("Chatbot RAG sử dụng Hybrid Search (Semantic + BM25 + RRF) và trích dẫn nguồn có kiểm chứng")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander(f"📚 Nguồn tham khảo ({len(message['sources'])} chunks - Phương thức: {message.get('retrieval_source', 'hybrid')})"):
                    for idx, src in enumerate(message["sources"], 1):
                        meta = src.get("metadata", {})
                        st.markdown(
                            f"**{idx}. {meta.get('title', 'Tài liệu')}** "
                            f"`[{src.get('retrieval_method', 'hybrid')}]` — "
                            f"Điểm: `{src.get('score', 0.0):.4f}` | "
                            f"Nguồn: `{meta.get('source', '')}`"
                        )
                        st.caption(src.get("content", ""))

    query = st.chat_input("Nhập câu hỏi (ví dụ: điều kiện làm đồ án tốt nghiệp, kế hoạch thực tập, mã học phần...)...")

    if query:
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
                result = generate_with_citation(query, top_k=top_k)
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                retrieval_source = result.get("retrieval_source", "hybrid")

                st.markdown(answer)

                if sources:
                    with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks - Phương thức: {retrieval_source})"):
                        for idx, src in enumerate(sources, 1):
                            meta = src.get("metadata", {})
                            st.markdown(
                                f"**{idx}. {meta.get('title', 'Tài liệu')}** "
                                f"`[{src.get('retrieval_method', 'hybrid')}]` — "
                                f"Điểm: `{src.get('score', 0.0):.4f}` | "
                                f"Nguồn: `{meta.get('source', '')}`"
                            )
                            st.caption(src.get("content", ""))

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "retrieval_source": retrieval_source,
        })

# ==================== TAB 2: BENCHMARK & EVALUATION ====================
with tab_eval:
    st.subheader("📊 Báo cáo Đánh giá Hiệu năng & So sánh A/B Testing")
    st.caption("Đánh giá hệ thống trên bộ 15 câu hỏi Golden Dataset theo 4 chỉ số Ragas tiêu chuẩn")

    if EVAL_RESULTS_JSON.exists():
        eval_data = json.loads(EVAL_RESULTS_JSON.read_text(encoding="utf-8"))
        sa = eval_data["scores_a"]
        sb = eval_data["scores_b"]
        delta = eval_data["delta"]

        st.info(f"🕒 **Thời điểm đánh giá:** {eval_data.get('date')} | **Tập câu hỏi:** {eval_data.get('num_cases')} câu | **Mô hình LLM:** {eval_data.get('generator')}")

        st.markdown("### 🏆 Bảng so sánh 4 Metrics cốt lõi (A/B Test)")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Faithfulness", f"{sb['faithfulness']:.3f}", f"{delta['faithfulness']:+.3f} vs Dense")
        col2.metric("Answer Relevance", f"{sb['relevance']:.3f}", f"{delta['relevance']:+.3f} vs Dense")
        col3.metric("Context Recall", f"{sb['recall']:.3f}", f"{delta['recall']:+.3f} vs Dense")
        col4.metric("Context Precision", f"{sb['precision']:.3f}", f"{delta['precision']:+.3f} vs Dense")
        col5.metric("Điểm Trung Bình", f"{sb['average']:.3f}", f"{delta['average']:+.3f} vs Dense")

        st.markdown("---")

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### 🔵 Config A (Dense-only)")
            st.markdown("- **Chiến lược:** Chỉ dùng ChromaDB Cosine Vector Search")
            st.markdown(f"- Faithfulness: `{sa['faithfulness']}`")
            st.markdown(f"- Answer Relevance: `{sa['relevance']}`")
            st.markdown(f"- Context Recall: `{sa['recall']}`")
            st.markdown(f"- Context Precision: `{sa['precision']}`")
            st.markdown(f"👉 **Điểm trung bình:** `{sa['average']}`")

        with col_right:
            st.markdown("#### 🟢 Config B (Hybrid + RRF)")
            st.markdown("- **Chiến lược:** Kết hợp ChromaDB + BM25 Okapi + RRF Fusion ($k=60$)")
            st.markdown(f"- Faithfulness: `{sb['faithfulness']}`")
            st.markdown(f"- Answer Relevance: `{sb['relevance']}`")
            st.markdown(f"- Context Recall: `{sb['recall']}`")
            st.markdown(f"- Context Precision: `{sb['precision']}`")
            st.markdown(f"👉 **Điểm trung bình:** `{sb['average']}`")

        if sb["average"] > sa["average"]:
            st.success(
                "💡 **Kết luận thực nghiệm:** Hybrid + RRF có điểm trung bình cao hơn Dense-only "
                f"({sb['average']:.3f} so với {sa['average']:.3f})."
            )
        else:
            st.warning(
                "💡 **Kết luận thực nghiệm:** Dense-only có điểm trung bình cao hơn Hybrid + RRF "
                f"({sa['average']:.3f} so với {sb['average']:.3f}). Hybrid cần tiếp tục hiệu chỉnh "
                "RRF/top-k trước khi dùng làm cấu hình mặc định."
            )

        st.markdown("---")
        with st.expander("📄 Xem toàn văn Báo cáo nhóm (RESULT.md)"):
            if RESULT_MD_PATH.exists():
                st.markdown(RESULT_MD_PATH.read_text(encoding="utf-8"))
            else:
                st.warning("Chưa tìm thấy file RESULT.md")

    else:
        st.warning("⚠️ Chưa có dữ liệu benchmark. Bạn hãy chạy script `python -m src.evaluate` để tiến hành đánh giá hệ thống!")

    if st.button("🚀 Chạy lại Benchmark Đánh giá (Live Evaluation)"):
        with st.spinner("Đang chạy kiểm thử 15 câu hỏi qua cả 2 cấu hình A và B..."):
            from src.evaluate import run_benchmark
            run_benchmark()
            st.success("Hoàn tất đánh giá! Đã cập nhật số liệu mới nhất.")
            st.rerun()
