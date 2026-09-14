"""
Resume Tool
-----------
Extracts raw text from an uploaded resume PDF using PyMuPDF, then does a
lightweight local keyword scan for common technical skills. The resume is
processed entirely in-memory / on local disk for this session and is never
uploaded to any external service.
"""
from __future__ import annotations
from typing import BinaryIO
from dataclasses import dataclass, field

import fitz  # PyMuPDF

# A reasonably broad skill keyword list for local (non-LLM) evidence scanning.
SKILL_KEYWORDS = [
    "python", "java", "c++", "javascript", "typescript", "sql",
    "machine learning", "deep learning", "pytorch", "tensorflow", "keras",
    "scikit-learn", "pandas", "numpy", "nlp", "computer vision", "opencv",
    "llm", "langchain", "transformers", "huggingface", "generative ai",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux",
    "rest api", "fastapi", "flask", "django", "react", "node.js",
    "data structures", "algorithms", "statistics", "mlops", "airflow",
    "spark", "hadoop", "tableau", "power bi", "excel", "streamlit",
]


@dataclass
class ResumeResult:
    success: bool
    raw_text: str = ""
    char_count: int = 0
    detected_skills: list = field(default_factory=list)
    error: str = ""


def parse_resume(file_obj: BinaryIO) -> ResumeResult:
    """
    Extract text from an in-memory PDF file object (e.g. Streamlit UploadedFile).
    Returns a ResumeResult; never raises — failures are captured in .error so
    the agent can adapt gracefully.
    """
    try:
        file_bytes = file_obj.read()
        if not file_bytes:
            return ResumeResult(success=False, error="Uploaded file was empty.")

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            return ResumeResult(
                success=False,
                error="No extractable text found (resume may be a scanned image).",
            )

        detected = _detect_skills(full_text)

        return ResumeResult(
            success=True,
            raw_text=full_text,
            char_count=len(full_text),
            detected_skills=detected,
        )
    except Exception as e:
        return ResumeResult(success=False, error=f"Resume parsing failed: {e}")


def _detect_skills(text: str) -> list:
    lowered = text.lower()
    found = []
    for kw in SKILL_KEYWORDS:
        if kw.strip() in lowered:
            found.append(kw.strip().title())
    # de-duplicate while preserving order
    seen = set()
    unique = []
    for s in found:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique.append(s)
    return unique
