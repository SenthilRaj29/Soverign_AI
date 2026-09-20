import os
import uuid
import pandas as pd
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

try:
    import fitz
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

class DocumentChunk(BaseModel):
    chunk_id: str
    filename: str
    file_type: str
    page_number: int
    section: Optional[str] = "General"
    content: str
    department: str = "ENGINEERING"
    allowed_roles: List[str] = ["ENGINEER", "MANAGER", "AUDITOR"]
    classification: str = "CONFIDENTIAL"

class DocumentIngestionService:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def ingest_file(
        self,
        filepath: str,
        department: str = "ENGINEERING",
        allowed_roles: List[str] = ["ENGINEER", "MANAGER"],
        classification: str = "CONFIDENTIAL"
    ) -> List[DocumentChunk]:
        filename = os.path.basename(filepath)
        ext = filename.split(".")[-1].lower()

        if ext == "pdf":
            return self._parse_pdf(filepath, filename, department, allowed_roles, classification)
        elif ext in ["docx", "doc"]:
            return self._parse_docx(filepath, filename, department, allowed_roles, classification)
        elif ext in ["csv", "xlsx"]:
            return self._parse_tabular(filepath, filename, ext, department, allowed_roles, classification)
        else:
            return self._parse_txt(filepath, filename, department, allowed_roles, classification)

    def _parse_pdf(self, filepath: str, filename: str, dept: str, roles: List[str], classif: str) -> List[DocumentChunk]:
        chunks = []
        if fitz is None:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self._chunk_text(content, filename, "pdf", 1, "PDF Document", dept, roles, classif)

        doc = fitz.open(filepath)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                page_chunks = self._chunk_text(text, filename, "pdf", page_num + 1, f"Page {page_num + 1}", dept, roles, classif)
                chunks.extend(page_chunks)
        return chunks

    def _parse_docx(self, filepath: str, filename: str, dept: str, roles: List[str], classif: str) -> List[DocumentChunk]:
        if docx is None:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self._chunk_text(content, filename, "docx", 1, "DOCX Document", dept, roles, classif)

        doc = docx.Document(filepath)
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return self._chunk_text(full_text, filename, "docx", 1, "Document Body", dept, roles, classif)

    def _parse_tabular(self, filepath: str, filename: str, ext: str, dept: str, roles: List[str], classif: str) -> List[DocumentChunk]:
        df = pd.read_csv(filepath) if ext == "csv" else pd.read_excel(filepath)
        summary = f"Dataset Columns: {', '.join(df.columns)}. Total Records: {len(df)}. Sample Data:\n" + df.head(5).to_string()
        return [
            DocumentChunk(
                chunk_id=f"chk_{uuid.uuid4().hex[:8]}",
                filename=filename,
                file_type=ext,
                page_number=1,
                section="Tabular Sensor Summary",
                content=summary,
                department=dept,
                allowed_roles=roles,
                classification=classif
            )
        ]

    def _parse_txt(self, filepath: str, filename: str, dept: str, roles: List[str], classif: str) -> List[DocumentChunk]:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return self._chunk_text(text, filename, "txt", 1, "Text Document", dept, roles, classif)

    def _chunk_text(self, text: str, filename: str, file_type: str, page_num: int, section: str, dept: str, roles: List[str], classif: str) -> List[DocumentChunk]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_content = text[start:end]
            chunks.append(
                DocumentChunk(
                    chunk_id=f"chk_{uuid.uuid4().hex[:8]}",
                    filename=filename,
                    file_type=file_type,
                    page_number=page_num,
                    section=section,
                    content=chunk_content,
                    department=dept,
                    allowed_roles=roles,
                    classification=classif
                )
            )
            start += self.chunk_size - self.chunk_overlap
        return chunks
