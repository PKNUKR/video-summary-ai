import streamlit as st
from video_utils import transcribe_audio_assemblyai
from summarizer import summarize_text

st.set_page_config(page_title="Video Summarizer AI", page_icon="🎥", layout="centered")
st.title("🎥 영상 요약 AI")
st.write("링크를 입력하면 영상을 분석해 요약해주는 AI입니다.\nOpenAI + AssemblyAI API Key를 직접 입력하세요!")

# 1️⃣ FFmpeg 경로 직접 지정
ffmpeg_path = "C:\\ffmpeg\\bin\\ffmpeg"  # ← ffmpeg.exe 전체 경로

# 2️⃣ 사용자 입력
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")
assemblyai_api_key = st.text_input("🔑 AssemblyAI API Key", type="password")
video_url = st.text_input("🔗 영상 링크를 입력하세요:")

# 3️⃣ 버튼 클릭 시 처리
if video_url and openai_api_key and assemblyai_api_key:
    try:
        with st.spinner("⏳ 영상 분석 중..."):
            # FFmpeg 경로 지정
            text_content = transcribe_audio_assemblyai(
                assemblyai_api_key,
                video_url,
                ffmpeg_location=ffmpeg_path
            )
            summary = summarize_text(openai_api_key, text_content)
            st.subheader("📌 요약 결과")
            st.write(summary)
    except Exception as e:
        st.error(f"⚠️ 오류 발생: {e}")

elif video_url:
    st.warning("⚠️ OpenAI와 AssemblyAI API Key를 모두 입력해주세요!")
