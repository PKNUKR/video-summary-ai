import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")
TARGET_LANG = os.getenv("SUMMARY_LANGUAGE", "ko")

def _chunk_by_chars(text: str, max_chars: int = 8000, overlap: int = 400) -> List[str]:
    """
    문자 기준 청크. 모델 토큰 초과 방지용. (대략 3~4문자 = 1토큰 가정)
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        # 문장 경계 근처에서 자르기(간단히 마침표 탐색)
        cut = text.rfind("\n", start, end)
        if cut == -1:
            cut = text.rfind(". ", start, end)
        if cut == -1 or cut <= start + 200:
            cut = end
        chunks.append(text[start:cut].strip())
        start = max(cut - overlap, cut)
    return [c for c in chunks if c]

def _summarize_chunk(chunk: str) -> str:
    msg = [
        {"role": "system", "content": f"너는 고품질 영상 요약가야. 한국어({TARGET_LANG})로 핵심만 간결하게 요약해."},
        {"role": "user", "content": f"다음 일부 내용을 요약해줘:\n\n{chunk}"}
    ]
    resp = client.chat.completions.create(model=MODEL, messages=msg, temperature=0.2)
    return resp.choices[0].message.content.strip()

def summarize_text_long(text: str) -> str:
    """
    긴 텍스트도 안정적으로 요약:
    1) 청크별 1차 요약
    2) 1차 요약들을 통합해 최종 요약
    """
    chunks = _chunk_by_chars(text)
    partials = []
    for c in chunks:
        partials.append(_summarize_chunk(c))

    joined = "\n\n".join(f"- {p}" for p in partials)
    final_prompt = [
        {"role": "system", "content": f"너는 전문 요약가야. 한국어({TARGET_LANG})로 명확하고 짧게 핵심을 정리해."},
        {"role": "user", "content": f"아래 파트별 요약을 하나의 간결한 최종 요약으로 통합해줘.\n\n{joined}\n\n형식: 개요 → 핵심 논점(불릿) → 결론"}
    ]
    final = client.chat.completions.create(model=MODEL, messages=final_prompt, temperature=0.2)
    return final.choices[0].message.content.strip()
