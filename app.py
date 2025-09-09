import streamlit as st
import os
import imageio_ffmpeg as ffmpeg
from video_utils import transcribe_audio_assemblyai
from summarizer import summarize_text

st.set_page_config(page_title="Video Summarizer AI", page_icon="🎥", layout="centered")
st.title("🎥 영상 요약 AI")
st.write(
    "링크를 입력하면 영상을 분석해 요약해주는 AI입니다.\n"
    "OpenAI + AssemblyAI API Key를 직접 입력하세요!"
)

# ✅ ffmpeg 경로 자동 설정 (Streamlit Cloud에서도 동작)
ffmpeg_path = ffmpeg.get_ffmpeg_exe()

# 1️⃣ 사용자 입력
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")
assemblyai_api_key = st.text_input("🔑 AssemblyAI API Key", type="password")
video_url = st.text_input("🔗 영상 링크를 입력하세요:")

# 2️⃣ 요약 실행
if video_url and openai_api_key and assemblyai_api_key:
    with st.spinner("⏳ 영상 분석 중..."):
        try:
            text_content = transcribe_audio_assemblyai(
                assemblyai_api_key,
                video_url,
                ffmpeg_location=ffmpeg_path
            )
            summary = summarize_text(openai_api_key, text_content)
            st.subheader("📌 요약 결과")
            st.markdown(summary)  # 더 깔끔하게 표시
        except Exception as e:
            import traceback
            st.error(f"⚠️ 오류 발생: {e}")
            st.text(traceback.format_exc())

elif video_url:
    st.warning("⚠️ OpenAI와 AssemblyAI API Key를 모두 입력해주세요!")
