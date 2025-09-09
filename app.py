import streamlit as st
import shutil
from video_utils import transcribe_audio_assemblyai

st.set_page_config(page_title="영상 요약 AI", layout="wide")
st.title("🎬 영상 요약 AI")

# 1️⃣ 사용자 입력
api_key = st.text_input("AssemblyAI / OpenAI API Key", type="password")
video_url = st.text_input("영상 URL 또는 MP3 파일 URL")

# 2️⃣ FFmpeg 설치 확인
def get_default_ffmpeg_path():
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    # 일반 설치 경로 예시
    possible_path = "C:\\ffmpeg\\bin\\ffmpeg"  # Windows 예시
    if shutil.os.path.exists(possible_path):
        return possible_path
    return None

ffmpeg_path = get_default_ffmpeg_path()

if not ffmpeg_path:
    st.warning(
        "⚠️ FFmpeg를 찾을 수 없습니다.\n"
        "Windows: https://ffmpeg.org/download.html\n"
        "Mac: brew install ffmpeg\n"
        "Linux: sudo apt install ffmpeg\n\n"
        "설치 후 ffmpeg.exe 경로를 확인하고 app.py에서 직접 지정할 수 있습니다."
    )

# 3️⃣ 요약 버튼
if st.button("요약 시작") and api_key and video_url:
    if not ffmpeg_path:
        st.error("FFmpeg 경로를 찾을 수 없어서 실행할 수 없습니다.")
    else:
        st.info("🔄 영상 처리 및 음성 인식 중...")
        try:
            summary_text = transcribe_audio_assemblyai(
                api_key,
                video_url,
                ffmpeg_location=ffmpeg_path
            )
            st.success("✅ 처리 완료!")
            st.subheader("요약 결과")
            st.write(summary_text)
        except Exception as e:
            st.error(f"⚠️ 오류 발생: {e}")
