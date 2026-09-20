"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://giaovu.ptit.edu.vn/to-chuc-cac-lop-hoc-lai-hoc-cai-thien-diem-theo-lop-rieng-hoc-ky-1-nam-hoc-2026-2027-cho-sinh-vien-cac-lop-dai-hoc-chinh-quy/",
    "https://giaovu.ptit.edu.vn/dang-ky-lich-hoc-thoi-khoa-bieu-cho-sinh-vien-khoa-2024-2025-hoc-theo-tien-trinh-rut-gon-cua-hoc-ky-i-nam-hoc-2026-2027/",
    "https://giaovu.ptit.edu.vn/thong-bao-v-v-huy-cac-lop-hoc-phan-dot-hoc-lai-ky-phu-he-nam-hoc-2025-2026/",
    "https://giaovu.ptit.edu.vn/tap-trung-pho-bien-ke-hoach-dang-ky-mon-hoc-ky-i-nam-hoc-2026-2027/",
    "https://giaovu.ptit.edu.vn/lich-nghi-tet-duong-lich-nam-2026-va-dieu-chinh-lich-thi-lich-dang-ky-hoc-phan/",
]


async def crawl_article(url: str) -> dict:
    from datetime import datetime

    try:
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            title = "Unknown"
            if result.metadata and isinstance(result.metadata, dict):
                title = result.metadata.get("title") or "Unknown"

            content = result.markdown
            if hasattr(content, "raw_markdown"):
                content = content.raw_markdown
            elif not isinstance(content, str):
                content = str(content)

            return {
                "url": url,
                "title": title,
                "date_crawled": datetime.now().isoformat(),
                "content_markdown": content,
            }
    except Exception as error:
        # Fallback bằng requests + BeautifulSoup nếu Playwright chưa tải browser binary
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "Unknown"

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        main_elem = (
            soup.find("article")
            or soup.find(class_="entry-content")
            or soup.find("main")
            or soup.body
        )
        content_text = main_elem.get_text(separator="\n", strip=True) if main_elem else soup.get_text()

        return {
            "url": url,
            "title": title,
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": content_text,
        }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
