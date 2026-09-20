"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation. Nếu thiếu evidence, hãy từ chối xác minh."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context (giảm lost-in-the-middle) mà không mutate list gốc."""
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return list(front) + list(back[::-1])


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label phục vụ citation."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        title = meta.get("title", "Tài liệu")
        source = meta.get("source", "Nguồn")
        parts.append(
            f"[Tài liệu {index} | Title: {title} | Source: {source}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình trong .env."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o") or "gpt-4o"

    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY chưa được thiết lập trong .env")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content or ""

    elif provider == "gemini":
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY chưa được thiết lập trong .env")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name or "gemini-2.5-flash",
            contents=f"{system_prompt}\n\n{user_message}",
        )
        return response.text or ""

    elif provider == "anthropic":
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY chưa được thiết lập trong .env")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name or "claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=TEMPERATURE,
        )
        return response.content[0].text if response.content else ""

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Truy xuất tài liệu và sinh câu trả lời có trích dẫn nguồn."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = (
        f"Dựa vào các đoạn thông tin ngữ cảnh dưới đây để trả lời câu hỏi.\n"
        f"Yêu cầu: Trích dẫn rõ nguồn/tiêu đề tài liệu tham khảo cho từng nội dung trả lời.\n\n"
        f"Ngữ cảnh (Context):\n{context}\n\n"
        f"Câu hỏi: {query}"
    )

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
        if not answer.strip():
            answer = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    except Exception as exc:
        print(f"Lỗi khi gọi mô hình ngôn ngữ: {exc}")
        answer = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    first_method = chunks[0].get("retrieval_method", "hybrid")
    retrieval_source = first_method if first_method in {"hybrid", "pageindex"} else "hybrid"

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    test_question = "Sinh viên cần đáp ứng những điều kiện gì để được làm khóa luận tốt nghiệp?"
    print(f"=== Thử nghiệm Generation có Citation với câu hỏi: '{test_question}' ===\n")
    output = generate_with_citation(test_question, top_k=3)
    print("🤖 CÂU TRẢ LỜI CỦA GPT-4O:\n")
    print(output["answer"])
    print("\n📚 CÁC NGUỒN TRÍCH DẪN ĐÃ SỬ DỤNG:")
    for idx, s in enumerate(output["sources"], 1):
        print(f"  {idx}. [{s['metadata'].get('title')}] ({s['metadata'].get('source')}) - Method: {s['retrieval_method']}")
