"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải hoặc kiểm tra ít nhất 3 PDF/DOC/DOCX từ nguồn công khai."""
    existing_files = [
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".pdf", ".doc", ".docx"}
    ]
    if existing_files:
        print(f"Đã tìm thấy {len(existing_files)} tài liệu trong {DATA_DIR}:")
        for f in existing_files:
            print(f"  - {f.name}")
        if len(existing_files) >= 3:
            print("Đạt yêu cầu tối thiểu 3 tài liệu legal.")
        else:
            print(f"Cảnh báo: Hiện chỉ có {len(existing_files)} tài liệu, cần tối thiểu 3 tài liệu.")
        return

    print(f"Chưa có file trong {DATA_DIR}. Vui lòng copy ít nhất 3 file (.pdf, .doc, .docx) vào thư mục này.")


if __name__ == "__main__":
    setup_directory()
    download_documents()
