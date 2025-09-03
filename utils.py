import io, re, hashlib
from typing import List, Tuple
from pypdf import PdfReader
from docx import Document
from PIL import Image

def file_signature(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]

def extract_text_from_file(file_name: str, file_bytes: bytes) -> Tuple[str, str]:
    name = file_name.lower()
    if name.endswith(".pdf"):
        return _pdf_text(file_bytes), "pdf"
    if name.endswith(".docx"):
        return _docx_text(file_bytes), "docx"
    if name.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8", errors="ignore"), "txt"
        except Exception:
            pass
    # Try naive image open just to detect; skip OCR to avoid dependency
    try:
        Image.open(io.BytesIO(file_bytes))
        # no OCR installed -> return hint
        return "", "image-unsupported"
    except Exception:
        pass
    # fallback: best-effort decode
    return file_bytes.decode("utf-8", errors="ignore"), "raw"

def _pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(texts)

def _docx_text(file_bytes: bytes) -> str:
    bio = io.BytesIO(file_bytes)
    doc = Document(bio)
    return "\n".join(p.text for p in doc.paragraphs)

def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    paras = re.split(r"\n\s*\n", text.strip())
    chunks = []
    cur = ""
    for p in paras:
        if len(cur) + len(p) + 2 <= max_chars:
            cur += ("\n\n" if cur else "") + p
        else:
            if cur: 
                chunks.append(cur)
            cur = p
    if cur: 
        chunks.append(cur)
    if not chunks:
        for i in range(0, len(text), max_chars):
            chunks.append(text[i:i+max_chars])
    return chunks

def compute_risk_axes(flags: list) -> dict:
    axes = {"payment":0, "termination":0, "liability":0, "dispute":0, "other":0}
    weights = {"low":1, "medium":2, "high":3}
    for f in flags:
        where = (f.get("where","") or "").lower()
        sev   = (f.get("severity","low") or "low").lower()
        w = weights.get(sev, 1)
        if "payment" in where:
            axes["payment"] += w
        elif "termination" in where:
            axes["termination"] += w
        elif "liability" in where or "indemn" in where:
            axes["liability"] += w
        elif "dispute" in where:
            axes["dispute"] += w
        else:
            axes["other"] += w
    return axes

def highlight_terms(text: str, query: str) -> str:
    if not query.strip():
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<span class='highlight'>{m.group(0)}</span>", text)
