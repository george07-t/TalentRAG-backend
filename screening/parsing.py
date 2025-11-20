import re
from io import BytesIO
from typing import Tuple, List
from pdfminer.high_level import extract_text

SECTION_HEADINGS = [
    'summary', 'experience', 'work experience', 'professional experience', 'education', 'skills', 'technical skills', 'projects'
]

SKILL_PATTERN = re.compile(r"(?i)\b([A-Za-z][A-Za-z0-9+.#-]{1,})\b")
STOP_WORDS = set(['and','or','the','in','on','at','for','with','to','of','a','an'])

def extract_text_from_pdf(data: bytes) -> str:
    try:
        bio = BytesIO(data)
        text = extract_text(bio)
        return text
    except Exception:
        return ''

def read_file_content(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.read()
    if name.endswith('.pdf'):
        return extract_text_from_pdf(data)
    return data.decode(errors='ignore')

def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def split_sections(text: str) -> List[Tuple[str,str]]:
    lowered = text.lower()
    positions = []
    for heading in SECTION_HEADINGS:
        for match in re.finditer(rf"(?i)\b{re.escape(heading)}\b", lowered):
            positions.append((match.start(), heading))
    positions.sort()
    sections = []
    for i,(pos, heading) in enumerate(positions):
        end = positions[i+1][0] if i+1 < len(positions) else len(text)
        section_text = text[pos:end].strip()
        sections.append((heading, section_text))
    if not sections:
        sections.append(('full', text))
    return sections

def extract_skills(text: str) -> List[str]:
    candidates = SKILL_PATTERN.findall(text)
    skills = []
    for c in candidates:
        token = c.strip('.').lower()
        if token in STOP_WORDS:
            continue
        if len(token) < 2:
            continue
        if token.isdigit():
            continue
        skills.append(token)
    uniq = []
    for s in skills:
        if s not in uniq:
            uniq.append(s)
    return uniq[:300]

def chunk_text(sections: List[Tuple[str,str]], max_chars: int = 1200) -> List[str]:
    chunks = []
    for heading, sec in sections:
        # break by sentences
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', sec)
        current = ''
        for sent in sentences:
            if len(current) + len(sent) + 1 > max_chars and current:
                chunks.append(current.strip())
                current = sent
            else:
                current += ' ' + sent
        if current.strip():
            chunks.append(current.strip())
    # ensure not too small: merge tiny chunks
    merged = []
    buf = ''
    for c in chunks:
        if len(c) < 300 and buf:
            buf += ' ' + c
        else:
            if buf:
                merged.append(buf.strip())
            buf = c
    if buf:
        merged.append(buf.strip())
    return merged
