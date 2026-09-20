"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if not query.strip() or top_k <= 0:
        return []

    query_vectors = embed_texts([query])
    if not query_vectors:
        return []
    query_vector = query_vectors[0]

    collection = get_collection()
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    ids = response.get("ids", [[]])[0] if response.get("ids") else []
    docs = response.get("documents", [[]])[0] if response.get("documents") else []
    metas = response.get("metadatas", [[]])[0] if response.get("metadatas") else []
    dists = response.get("distances", [[]])[0] if response.get("distances") else []

    results = []
    seen_ids = set()
    for item_id, content, meta, dist in zip(ids, docs, metas, dists):
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        score = max(0.0, min(1.0, 1.0 - dist))
        results.append({
            "id": item_id,
            "content": content,
            "score": score,
            "metadata": meta,
            "retrieval_method": "dense",
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)
