import os
import numpy as np
from typing import List, Dict
from openai import OpenAI
from .models import ResumeChunk, Session, ChatMessage

EMBED_MODEL = os.environ.get('OPENAI_EMBED_MODEL', 'text-embedding-3-small')
CHAT_MODEL = os.environ.get('OPENAI_CHAT_MODEL', 'gpt-4.1-mini')

def get_client() -> OpenAI:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set. Set it or create backend/.env and restart.")
    return OpenAI(api_key=api_key)

def embed_text(texts: List[str]) -> List[List[float]]:
    client = get_client()
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

def store_chunks(session: Session, chunks: List[str], doc_type: str = 'resume'):
    if not chunks:
        return
    embeddings = embed_text(chunks)
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        ResumeChunk.objects.create(session=session, doc_type=doc_type, index=i, text=chunk, embedding=emb)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if not np.any(a) or not np.any(b):
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def retrieve(session: Session, question: str, top_k: int = 6, per_doc_k: int = 3) -> List[Dict]:
    """Retrieve relevant chunks from BOTH resume and job description.

    per_doc_k ensures we don't accidentally return only resume chunks when the question
    is about job requirements (or vice versa).
    """
    q_emb = embed_text([question])[0]
    chunks = list(session.chunks.all())
    q_vec = np.array(q_emb)

    scored_by_doc: Dict[str, List] = {}
    for c in chunks:
        c_vec = np.array(c.embedding)
        sim = cosine_similarity(q_vec, c_vec)
        scored_by_doc.setdefault(getattr(c, 'doc_type', 'resume') or 'resume', []).append((sim, c))

    # Sort each doc bucket
    for doc_type in scored_by_doc:
        scored_by_doc[doc_type].sort(key=lambda x: x[0], reverse=True)

    picked = []
    leftovers = []
    for doc_type, scored in scored_by_doc.items():
        picked.extend(scored[:per_doc_k])
        leftovers.extend(scored[per_doc_k:])

    # If we still need more, fill by best remaining irrespective of doc_type
    picked.sort(key=lambda x: x[0], reverse=True)
    if len(picked) < top_k and leftovers:
        leftovers.sort(key=lambda x: x[0], reverse=True)
        picked.extend(leftovers[: max(0, top_k - len(picked))])
    picked = picked[:top_k]

    results = []
    for sim, c in picked:
        snippet = c.text[:400]
        results.append({
            'chunk_index': c.index,
            'doc_type': getattr(c, 'doc_type', 'resume') or 'resume',
            'text': snippet,
            'score': sim,
        })
    return results

def generate_answer(session: Session, question: str, retrieved: List[Dict]) -> str:
    history = list(session.messages.order_by('-created_at')[:6])
    history_messages = []
    for m in reversed(history):
        if m.role == 'user':
            history_messages.append({'role': 'user', 'content': m.question})
        else:
            history_messages.append({'role': 'assistant', 'content': m.answer})

    resume_ctx = [r for r in retrieved if r.get('doc_type') == 'resume']
    jd_ctx = [r for r in retrieved if r.get('doc_type') == 'job_description']
    other_ctx = [r for r in retrieved if r.get('doc_type') not in ('resume', 'job_description')]

    def _block(title: str, items: List[Dict]) -> str:
        if not items:
            return f"{title}:\n(none)"
        return title + ":\n" + "\n\n".join(
            [f"[Chunk {i+1} | score={r['score']:.3f}]\n{r['text'][:1500]}" for i, r in enumerate(items)]
        )

    match_block = (
        f"Match Score: {session.match_score if session.match_score is not None else 'N/A'}\n"
        f"Strengths: {session.strengths or []}\n"
        f"Gaps: {session.gaps or []}\n"
        f"Insights: {session.insights or ''}"
    )

    system_prompt = (
        "You are an expert recruiter assistant. You must answer using BOTH: (1) the candidate's resume and "
        "(2) the job description.\n\n"
        "Use the retrieved context below. If a claim is not supported by the retrieved context, say you don't have enough evidence.\n\n"
        "MATCH ANALYSIS (precomputed):\n"
        f"{match_block}\n\n"
        f"{_block('RELEVANT JOB DESCRIPTION CONTEXT', jd_ctx)}\n\n"
        f"{_block('RELEVANT RESUME CONTEXT', resume_ctx)}\n\n"
        f"{_block('OTHER CONTEXT', other_ctx)}\n\n"
        "Instructions:\n"
        "- Compare resume vs job requirements when asked about fit\n"
        "- Be concrete (skills/years/projects/tools)\n"
        "- If the question is about 'gaps', name gaps relative to the job description\n"
        "- Keep answers concise but useful (3-6 sentences)\n"
    )
    messages = [{'role': 'system', 'content': system_prompt}] + history_messages + [
        {'role': 'user', 'content': question}
    ]
    client = get_client()
    resp = client.chat.completions.create(model=CHAT_MODEL, messages=messages, temperature=0.2)
    return resp.choices[0].message.content.strip()

def answer_question(session: Session, question: str) -> Dict:
    ChatMessage.objects.create(session=session, role='user', question=question, answer='')
    retrieved = retrieve(session, question)
    answer = generate_answer(session, question, retrieved)
    msg = ChatMessage.objects.create(session=session, role='assistant', question=question, answer=answer, retrieved_chunks=retrieved)
    sources = [
        {
            'chunk_index': r['chunk_index'],
            'doc_type': r.get('doc_type', 'resume'),
            'score': round(r['score'], 4),
            'preview': r['text']
        } for r in retrieved
    ]
    return {
        'answer': answer,
        'sources': sources,
        'message_id': msg.id
    }
