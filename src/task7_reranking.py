"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Dùng Jina hoặc self host hoặc bất cứ công cụ nào bạn quen
"""


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult."""
    if not ranked_lists or top_k <= 0:
        return []

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            if item_id not in items:
                items[item_id] = item

    ranked_ids = sorted(scores, key=scores.get, reverse=True)
    results = []
    for item_id in ranked_ids[:top_k]:
        result = dict(items[item_id])
        result["score"] = scores[item_id]
        result["retrieval_method"] = "hybrid"
        results.append(result)

    return results


if __name__ == "__main__":
    from .task5_semantic_search import semantic_search
    from .task6_lexical_search import lexical_search

    query = "điều kiện làm đồ án tốt nghiệp"
    print(f"=== Thử nghiệm RRF Fusion với câu hỏi: '{query}' ===\n")
    dense_results = semantic_search(query, top_k=5)
    sparse_results = lexical_search(query, top_k=5)
    hybrid_results = rerank_rrf([dense_results, sparse_results], top_k=3)

    for rank, item in enumerate(hybrid_results, 1):
        print(f"Top {rank} [RRF Score: {item['score']:.5f}] - Method: {item['retrieval_method']}")
        print(f"  Tiêu đề: {item['metadata'].get('title')}")
        print(f"  Nội dung: {item['content'][:120]}...\n")
