"""文本处理工具函数"""
import re

def split_into_chunks(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> list[dict]:
    """将长文本按段落切割成块，返回 [{index, content, page}]"""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunks.append({"index": chunk_index, "content": current_chunk.strip()})
            chunk_index += 1
            # overlap: 保留上一块末尾部分
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else current_chunk
            current_chunk = overlap_text + "\n\n" + para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

    if current_chunk.strip():
        chunks.append({"index": chunk_index, "content": current_chunk.strip()})

    return chunks

def extract_text_from_url_html(html: str) -> str:
    """从 HTML 中提取可读文本（简易版）"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)
