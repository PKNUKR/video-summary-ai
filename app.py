import streamlit as st
from video_utils import transcribe_audio_assemblyai
from summarizer import summarize_text
import os
import subprocess
import sys

st.set_page_config(page_title="Video Summarizer AI", page_icon="🎥", layout="centered")
st.title("🎥 영상 요약 AI")
st.write(
    "링크를 입력하면 영상을 분석해 요약해주는 AI입니다.\n"
    "OpenAI + AssemblyAI API Key를 직접 입력하세요!"
)

# 1️⃣ 서버 환경용 FFmpeg 설치 체크
def ensure_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "ffmpeg"
    except:
        st.info("⏳ 서버에 FFmpeg가 설치되어 있지 않습니다. 설치 중...")
        if sys.platform.startswith("linux"):
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "ffmpeg"], check=True)
        else:
            st.error("⚠️ 이 서버 환경에서는 자동 설치가 지원되지 않습니다. FFmpeg를 직접 설치해주세요.")
            return None
        return "ffmpeg"

ffmpeg_path = ensure_ffmpeg()
if not ffmpeg_path:
    st.stop()

# 2️⃣ 사용자 입력
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")
assemblyai_api_key = st.text_input("🔑 AssemblyAI API Key", type="password")
video_url = st.text_input("🔗 영상 링크를 입력하세요:")

# 3️⃣ 요약 실행
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
            st.write(summary)
        except Exception as e:
            st.error(f"⚠️ 오류 발생: {e}")

elif video_url:
    st.warning("⚠️ OpenAI와 AssemblyAI API Key를 모두 입력해주세요!")
