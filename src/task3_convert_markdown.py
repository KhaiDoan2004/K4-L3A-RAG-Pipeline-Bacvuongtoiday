"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert PDF/DOC/DOCX từ data/landing/legal vào data/standardized/legal."""
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()
    legal_files = [
        p for p in legal_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".pdf", ".doc", ".docx"}
    ]

    if not legal_files:
        print(f"Cảnh báo: Không tìm thấy file PDF/DOC/DOCX nào trong {legal_dir}")
        return

    for path in legal_files:
        try:
            result = converter.convert(str(path))
            content = result.text_content
        except Exception as error:
            print(f"MarkItDown không đọc được trực tiếp {path.name} ({error}), thử đọc dưới dạng văn bản/HTML...")
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
                # Nếu file là dạng HTML được lưu đuôi .doc
                if "<html" in raw.lower() or "<body" in raw.lower():
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(raw, "html.parser")
                    content = soup.get_text(separator="\n", strip=True)
                else:
                    content = raw
            except Exception as read_err:
                print(f"Không thể convert {path.name}: {read_err}")
                continue

        out_path = output_dir / f"{path.stem}.md"
        out_path.write_text(content, encoding="utf-8")
        print(f"Đã chuyển đổi legal: {path.name} -> {out_path.name}")


def clean_web_markdown(raw_text: str) -> str:
    """Loại bỏ menu điều hướng đầu trang và footer chân trang khỏi nội dung cào web."""
    lines = raw_text.splitlines()
    start_idx = 0

    # 1. Tìm điểm bắt đầu nội dung chính (bỏ qua menu điều hướng, logo header)
    for idx, line in enumerate(lines):
        line_stripped = line.strip()
        if "Chi tiết bài viết" in line_stripped or (line_stripped.startswith("# ") and idx > 5):
            start_idx = idx
            break

    # 2. Tìm điểm kết thúc nội dung chính (cắt bỏ footer, bản quyền, bài viết liên quan)
    stop_markers = [
        "#### Bài viết liên quan",
        "##  [ Thông báo:",
        "## Đường dẫn liên kết",
        "Số điện thoại liên hệ",
        "Trụ sở chính",
        "logo-gv-footer",
        "© Copyright",
        "Go to top",
    ]
    end_idx = len(lines)
    for idx in range(start_idx, len(lines)):
        line_stripped = lines[idx]
        if any(marker in line_stripped for marker in stop_markers):
            end_idx = idx
            break

    cleaned = "\n".join(lines[start_idx:end_idx]).strip()
    return cleaned if len(cleaned) > 50 else raw_text


def convert_news_articles() -> None:
    """Convert JSON từ data/landing/news vào data/standardized/news có kèm metadata header và lọc rác."""
    import json

    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(news_dir.glob("*.json"))
    if not json_files:
        print(f"Cảnh báo: Không tìm thấy file JSON nào trong {news_dir}")
        return

    for path in json_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        header = (
            f"# {data.get('title', 'Unknown')}\n\n"
            f"**Source:** {data.get('url', '')}\n\n"
            f"**Crawled:** {data.get('date_crawled', '')}\n\n---\n\n"
        )
        raw_content = data.get("content_markdown", "")
        cleaned_content = clean_web_markdown(raw_content)

        out_path = output_dir / f"{path.stem}.md"
        out_path.write_text(header + cleaned_content, encoding="utf-8")
        print(f"Đã chuyển đổi & làm sạch news: {path.name} -> {out_path.name}")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
