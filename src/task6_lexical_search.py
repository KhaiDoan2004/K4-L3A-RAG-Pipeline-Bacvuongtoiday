import math
import numpy as np

CORPUS: list[dict] = []


def get_corpus() -> list[dict]:
    """Lấy hoặc load corpus chunks từ Task 4."""
    global CORPUS
    if not CORPUS:
        from .task4_chunking_indexing import chunk_documents, load_documents

        CORPUS = chunk_documents(load_documents())
    return CORPUS


class BM25Index:
    """Bộ chỉ mục BM25 chuẩn Lucene/BM25+ hỗ trợ cả corpus thực tế và tập test nhỏ."""

    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = (
            sum(len(doc) for doc in corpus) / self.corpus_size
            if self.corpus_size > 0
            else 1.0
        )
        self.doc_freqs: list[dict[str, int]] = []
        self.doc_lens = [len(doc) for doc in corpus]
        self.nd: dict[str, int] = {}

        for doc in corpus:
            frequencies: dict[str, int] = {}
            for word in doc:
                frequencies[word] = frequencies.get(word, 0) + 1
            self.doc_freqs.append(frequencies)
            for word in frequencies:
                self.nd[word] = self.nd.get(word, 0) + 1

        self.idf: dict[str, float] = {}
        for word, freq in self.nd.items():
            # Chuẩn Lucene/BM25+ log(1 + (N - n + 0.5) / (n + 0.5)) để IDF luôn dương
            self.idf[word] = math.log(
                1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5)
            )

    def get_scores(self, query: list[str]) -> list[float]:
        scores = [0.0] * self.corpus_size
        for word in query:
            if word not in self.idf:
                continue
            idf_val = self.idf[word]
            for idx, doc_freq in enumerate(self.doc_freqs):
                freq = doc_freq.get(word, 0)
                if freq > 0:
                    denom = freq + self.k1 * (
                        1.0 - self.b + self.b * (self.doc_lens[idx] / self.avgdl)
                    )
                    scores[idx] += idf_val * (freq * (self.k1 + 1.0)) / denom
        return scores


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ corpus chunks."""
    tokenized = [item["content"].lower().split() for item in corpus]
    return BM25Index(tokenized)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    corpus = CORPUS if CORPUS else get_corpus()
    if not corpus or not query.strip() or top_k <= 0:
        return []

    tokens = query.lower().split()
    if not tokens:
        return []

    bm25 = build_bm25_index(corpus)
    scores = np.array(bm25.get_scores(tokens))
    indices = np.argsort(scores)[::-1]

    results = []
    seen_ids = set()
    for index in indices:
        item = corpus[index]
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
        if len(results) >= top_k:
            break

    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
