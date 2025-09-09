import streamlit as st
from video_utils import transcribe_audio_assemblyai
from summarizer import summarize_text
import os

st.set_page_config(page_title="Video Summarizer AI", page_icon="🎥", layout="centered")
st.title("🎥 영상 요약 AI")
st.write(
    "링크를 입력하면 영상을 분석해 요약해주는 AI입니다.\n"
    "OpenAI + AssemblyAI API Key를 직접 입력하세요!"
)

# 1️⃣ FFmpeg/ffprobe 경로 직접 지정
ffmpeg_path = "C:\\ffmpeg\\bin\\ffmpeg.exe"   # ← ffmpeg.exe 전체 경로
ffprobe_path = "C:\\ffmpeg\\bin\\ffprobe.exe" # ← ffprobe.exe 전체 경로

# 2️⃣ 설치 여부 확인
if not (os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path)):
    st.warning(
        "⚠️ FFmpeg 또는 ffprobe를 찾을 수 없습니다.\n"
        "Windows: https://ffmpeg.org/download.html\n"
        "Mac: brew install ffmpeg\n"
        "Linux: sudo apt install ffmpeg\n\n"
        "설치 후 ffmpeg.exe와 ffprobe.exe 경로를 app.py에 정확히 지정해주세요."
    )

# 3️⃣ 사용자 입력
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")
assemblyai_api_key = st.text_input("🔑 AssemblyAI API Key", type="password")
video_url = st.text_input("🔗 영상 링크를 입력하세요:")

# 4️⃣ 요약 실행
if video_url and openai_api_key and assemblyai_api_key:
    if not (os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path)):
        st.error("FFmpeg/ffprobe 경로를 찾을 수 없어 실행할 수 없습니다.")
    else:
        with st.spinner("⏳ 영상 분석 중..."):
            try:
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
