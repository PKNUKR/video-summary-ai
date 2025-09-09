import openai

def chunk_text(text: str, max_tokens=2000):
    words = text.split()
    chunks, chunk = [], []
    token_count = 0

    for word in words:
        chunk.append(word)
        token_count += len(word.split())
        if token_count > max_tokens:
            chunks.append(" ".join(chunk))
            chunk = []
            token_count = 0

    if chunk:
        chunks.append(" ".join(chunk))
    return chunks

def summarize_text(api_key: str, text: str, language="ko") -> str:
    """
    OpenAI API를 사용한 텍스트 요약 (사용자 입력 API Key 사용)
    """
    openai.api_key = api_key
    try:
        chunks = chunk_text(text)
        summaries = []

        for idx, chunk in enumerate(chunks, 1):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # 필요 시 gpt-4o-mini로 변경 가능
                messages=[
                    {"role": "system", "content": "당신은 영상을 간결하게 요약하는 전문가입니다."},
                    {"role": "user", "content": f"다음 영상 내용 일부를 요약해줘:\n{chunk}"}
                ]
            )
            summaries.append(response.choices[0].message["content"])

        # 부분 요약들을 종합하여 최종 요약 생성
        final_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 영상 요약 전문가입니다."},
                {"role": "user", "content": f"다음 요약들을 종합하여 간결한 최종 요약을 작성해줘:\n{''.join(summaries)}"}
            ]
        )
        return final_response.choices[0].message["content"]

    except Exception as e:
        return f"⚠️ 요약 중 오류 발생: {e}"
