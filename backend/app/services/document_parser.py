"""文档解析服务 - PDF/Word/HTML"""
from pathlib import Path

class DocumentParser:
    async def parse(self, filepath: str | Path) -> str:
        """解析文档，返回纯文本"""
        filepath = Path(filepath)
        ext = filepath.suffix.lower()

        if ext == ".pdf":
            return self._parse_pdf(filepath)
        elif ext in (".docx", ".doc"):
            return self._parse_docx(filepath)
        elif ext == ".html" or ext == ".htm":
            return self._parse_html(filepath)
        else:
            # 尝试作为纯文本读取
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                return f"[无法解析文件格式: {ext}]"

    def _parse_pdf(self, filepath: Path) -> str:
        """解析 PDF 文件"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(filepath))
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            return "\n\n".join(text_parts)
        except ImportError:
            return "[PDF 解析器未安装]"
        except Exception as e:
            return f"[PDF 解析失败: {e}]"

    def _parse_docx(self, filepath: Path) -> str:
        """解析 Word 文件"""
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(str(filepath))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            return "[Word 解析器未安装]"
        except Exception as e:
            return f"[Word 解析失败: {e}]"

    def _parse_html(self, filepath: Path) -> str:
        """解析 HTML 文件"""
        try:
            from bs4 import BeautifulSoup
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                soup = BeautifulSoup(f.read(), "lxml")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except ImportError:
            return "[HTML 解析器未安装]"
        except Exception as e:
            return f"[HTML 解析失败: {e}]"
