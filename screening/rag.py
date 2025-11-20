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

def store_chunks(session: Session, chunks: List[str]):
    embeddings = embed_text(chunks)
    for i,(chunk, emb) in enumerate(zip(chunks, embeddings)):
        ResumeChunk.objects.create(session=session, index=i, text=chunk, embedding=emb)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if not np.any(a) or not np.any(b):
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def retrieve(session: Session, question: str, top_k: int = 4) -> List[Dict]:
    q_emb = embed_text([question])[0]
    chunks = list(session.chunks.all())
    scored = []
    q_vec = np.array(q_emb)
    for c in chunks:
        c_vec = np.array(c.embedding)
        sim = cosine_similarity(q_vec, c_vec)
        scored.append((sim, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for sim, c in scored[:top_k]:
        snippet = c.text[:400]
        results.append({'chunk_index': c.index, 'text': snippet, 'score': sim})
    return results

def generate_answer(session: Session, question: str, retrieved: List[Dict]) -> str:
    history = list(session.messages.order_by('-created_at')[:6])
    history_messages = []
    for m in reversed(history):
        if m.role == 'user':
            history_messages.append({'role': 'user', 'content': m.question})
        else:
            history_messages.append({'role': 'assistant', 'content': m.answer})
    context_block = '\n\n'.join([f"[Context {i+1}]\n{r['text'][:1500]}" for i, r in enumerate(retrieved)])
    system_prompt = (
        "You are an expert recruiter assistant helping evaluate a candidate. "
        "Answer questions about the candidate based on the resume context provided below.\n\n"
        "RELEVANT RESUME SECTIONS:\n"
        f"{context_block}\n\n"
        "Instructions:\n"
        "- Be specific and cite actual information from the resume\n"
        "- Provide detailed, complete answers (2-4 sentences)\n"
        "- If information is not in the context, say so honestly\n"
        "- Focus on facts, not assumptions\n"
        "- Maintain a professional, objective tone"
    )
    messages = [{'role': 'system', 'content': system_prompt}] + history_messages + [
        {'role': 'user', 'content': question}
    ]
    client = get_client()
    resp = client.chat.completions.create(model=CHAT_MODEL, messages=messages, temperature=0.2)
    return resp.choices[0].message.content.strip()

def answer_question(session: Session, question: str) -> Dict:
    retrieved = retrieve(session, question)
    answer = generate_answer(session, question, retrieved)
    msg = ChatMessage.objects.create(session=session, role='assistant', question=question, answer=answer, retrieved_chunks=retrieved)
    sources = [
        {
            'chunk_index': r['chunk_index'],
            'score': round(r['score'], 4),
            'preview': r['text']
        } for r in retrieved
    ]
    return {
        'answer': answer,
        'sources': sources,
        'message_id': msg.id
    }
