"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

COLLECTION_NAME = "rag_documents"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Tạo embedding vector cho danh sách texts theo provider được cấu hình."""
    if not texts:
        return []

    provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY chưa được thiết lập trong .env")
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(input=texts, model=model_name)
        return [item.embedding for item in response.data]

    elif provider == "gemini":
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY chưa được thiết lập trong .env")
        client = genai.Client(api_key=api_key)
        results = []
        for text in texts:
            resp = client.models.embed_content(
                model=model_name or "text-embedding-004",
                contents=text,
            )
            results.append(resp.embedding.values)
        return results

    elif provider == "sentence_transformers":
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(model_name or "BAAI/bge-m3")
        embeddings = model.encode(texts)
        return embeddings.tolist()

    else:
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if path.name == ".gitkeep":
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        doc_type = "legal" if "legal" in path.parts else "news"
        title = path.stem
        url = None

        lines = content.splitlines()
        for line in lines[:10]:
            if line.startswith("# ") and title == path.stem:
                title = line[2:].strip()
            elif line.startswith("**Source:**"):
                extracted_url = line.replace("**Source:**", "").strip()
                if extracted_url:
                    url = extracted_url

        documents.append({
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": {
                "source": path.name,
                "title": title,
                "doc_type": doc_type,
                "url": url,
            },
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        splits = splitter.split_text(document["content"])
        for index, text in enumerate(splits):
            chunk_content = text.strip()
            if not chunk_content:
                continue
            chunks.append({
                "id": f"{document['id']}::chunk-{index}",
                "content": chunk_content,
                "metadata": {**document["metadata"], "chunk_index": index},
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []

    texts = [chunk["content"] for chunk in chunks]
    batch_size = 50
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_vectors = embed_texts(batch_texts)
        if len(batch_vectors) != len(batch_texts):
            raise ValueError(
                f"embed_texts trả về {len(batch_vectors)} vector cho "
                f"{len(batch_texts)} chunk (batch bắt đầu tại index {i})"
            )
        all_vectors.extend(batch_vectors)

    dims = {len(vector) for vector in all_vectors}
    if len(dims) > 1:
        raise ValueError(
            f"Embedding không đồng nhất chiều: {sorted(dims)}. "
            "Task 4 và Task 5 phải dùng chung embedding model/dimension."
        )

    for chunk, vector in zip(chunks, all_vectors):
        chunk["embedding"] = vector
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return

    collection = get_collection()
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[chunk["metadata"] for chunk in batch],
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    print(f"Đã đọc {len(documents)} tài liệu từ {STANDARDIZED_DIR}")
    chunks = chunk_documents(documents)
    print(f"Đã cắt thành {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"Bắt đầu embed qua {EMBEDDING_PROVIDER} ({EMBEDDING_MODEL})...")
    embedded_chunks = embed_chunks(chunks)
    print("Đang index vào ChromaDB...")
    index_to_vectorstore(embedded_chunks)
    print(f"Thành công! Đã index {len(embedded_chunks)} chunks vào ChromaDB.")


if __name__ == "__main__":
    run_pipeline()
