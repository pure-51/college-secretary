"""网页链接内容抓取服务"""
import httpx
from bs4 import BeautifulSoup

class WebScraper:
    async def fetch_text(self, url: str) -> str:
        """抓取网页中的可读文本"""
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                if response.status_code != 200:
                    return f"[无法访问: HTTP {response.status_code}]"

                soup = BeautifulSoup(response.text, "lxml")
                # 移除无用标签
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()

                # 尝试查找正文
                article = soup.find("article") or soup.find("main") or soup.find("body")
                if article:
                    text = article.get_text(separator="\n", strip=True)
                else:
                    text = soup.get_text(separator="\n", strip=True)

                lines = [line.strip() for line in text.splitlines() if line.strip()]
                return "\n".join(lines[:200])  # 限制输出长度
        except Exception as e:
            return f"[抓取失败: {e}]"

web_scraper = WebScraper()
