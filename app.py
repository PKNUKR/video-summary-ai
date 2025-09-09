import streamlit as st
from video_utils import transcribe_audio_assemblyai
from summarizer import summarize_text
import shutil

st.set_page_config(page_title="Video Summarizer AI", page_icon="🎥", layout="centered")
st.title("🎥 영상 요약 AI")
st.write("링크를 입력하면 영상을 분석해 요약해주는 AI입니다.\nOpenAI + AssemblyAI API Key를 직접 입력하세요!")

# FFmpeg 자동 감지
def get_ffmpeg_path():
    path = shutil.which("ffmpeg")
    if path:
        return path
    # 일반 설치 경로 예시 (Windows)
    possible_path = "C:\ffmpeg\bin"
    return possible_path if shutil.os.path.exists(possible_path) else None

ffmpeg_path = get_ffmpeg_path()

if not ffmpeg_path:
    st.warning(
        "⚠️ FFmpeg를 찾을 수 없습니다.\n"
        "Windows: https://ffmpeg.org/download.html\n"
        "Mac: brew install ffmpeg\n"
        "Linux: sudo apt install ffmpeg\n\n"
        "설치 후 ffmpeg.exe 경로를 확인하고 app.py에서 직접 지정할 수 있습니다."
    )

# API Key 입력
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")
assemblyai_api_key = st.text_input("🔑 AssemblyAI API Key", type="password")
video_url = st.text_input("🔗 영상 링크를 입력하세요:")

if video_url and openai_api_key and assemblyai_api_key:
    if not ffmpeg_path:
        st.error("FFmpeg 경로를 찾을 수 없어 실행할 수 없습니다.")
    else:
        with st.spinner("⏳ 영상 분석 중..."):
            try:
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
