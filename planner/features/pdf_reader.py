# planner/features/pdf_reader.py
import PyPDF2
from typing import List

def extract_text_from_pdf(file_path: str) -> str:
    """
    Return extracted text from PDF file_path.
    Safe: returns empty string if no text found.
    """
    text = []
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
    except Exception:
        return ""
    return "\n".join(text).strip()
