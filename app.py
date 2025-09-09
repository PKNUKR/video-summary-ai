import os
import streamlit as st
from dotenv import load_dotenv

from video_utils import is_youtube_url, download_subtitles_text_youtube
from transcriber import transcribe
from summarizer import summarize_text_long as summarize_text

load_dotenv()

st.set_page_config(page_title="Video Summarizer AI (Fast)", page_icon="🎥", layout="centered")
st.title("🎥 영상 요약 AI — 초고속 버전 (AssemblyAI)")

st.caption("링크를 넣으면 자막/음성을 자동 분석해 요약합니다. 유튜브/일반 영상 지원 • 긴 영상도 OK")

with st.sidebar:
    st.header("⚙️ 설정")
    provider = st.selectbox("STT 엔진", ["assemblyai", "whisper"], index=0)
    target_lang = os.getenv("SUMMARY_LANGUAGE", "ko")
    st.write(f"요약 언어: **{target_lang}** (summarizer.py에서 변경 가능)")

video_url = st.text_input("🔗 영상(또는 강의) 링크를 입력하세요:")

btn = st.button("요약 시작", type="primary", disabled=not video_url)

if btn:
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OPENAI_API_KEY가 설정되지 않았습니다. .env를 확인하세요.")
        st.stop()
    if provider == "assemblyai" and not os.getenv("ASSEMBLYAI_API_KEY"):
        st.error("❌ ASSEMBLYAI_API_KEY가 설정되지 않았습니다. .env를 확인하세요.")
        st.stop()

    with st.spinner("🔍 콘텐츠 분석 중..."):
        transcript_text = ""

        # 1) 유튜브면 자막 우선 시도
        if is_youtube_url(video_url):
            st.write("✅ 유튜브 링크 감지: 자막 우선 확인")
            srt_text = download_subtitles_text_youtube(video_url)
            if srt_text:
                st.success("자막을 찾았어요! (STT 없이 바로 요약)")
                transcript_text = srt_text
            else:
                st.warning("자막 미탐지 → STT(음성 인식)로 전사 중...")
                transcript_text = transcribe(video_url, provider=provider)
        else:
            # 2) 일반 링크: 바로 STT
            st.write("🌐 일반 영상 링크 감지 → STT 전사 중...")
            transcript_text = transcribe(video_url, provider=provider)

        if not transcript_text or len(transcript_text) < 20:
            st.error("전사 결과가 비어있거나 너무 짧습니다. 접근 권한/링크 상태를 확인해주세요.")
            st.stop()

        st.write("🧠 요약 생성 중...")
        summary = summarize_text(transcript_text)

    st.subheader("📌 최종 요약")
    st.write(summary)

    with st.expander("🧾 원문 전사 보기 (길 수 있어요)"):
        st.text_area("Transcript", transcript_text, height=300)
