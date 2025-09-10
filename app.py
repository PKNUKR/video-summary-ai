# app.py
import streamlit as st
import ffmpeg
from pathlib import Path
import os
from openai import OpenAI
import wave
import contextlib

# --------------------------
# OpenAI API 키
# --------------------------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

st.title("Video Summary AI")

# --------------------------
# 영상 업로드
# --------------------------
uploaded_file = st.file_uploader("영상 파일 업로드", type=["mp4", "mov"])
if uploaded_file:
    video_path = Path("temp_video.mp4")
    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())
    st.success("영상 업로드 완료")

    # --------------------------
    # ffmpeg로 오디오 추출
    # --------------------------
    audio_path = Path("temp_audio.wav")
    try:
        ffmpeg.input(str(video_path)).output(str(audio_path), ac=1, ar=16000).run(overwrite_output=True)
        st.success("오디오 추출 완료")
    except Exception as e:
        st.error(f"오디오 추출 실패: {e}")

    # --------------------------
    # 오디오 분할 (1분 단위)
    # --------------------------
    chunk_paths = []
    with contextlib.closing(wave.open(str(audio_path), 'r')) as wf:
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        duration = nframes / framerate
        chunk_duration = 60  # 초 단위
        num_chunks = int(duration // chunk_duration) + 1

        for i in range(num_chunks):
            start = i * chunk_duration
            end = min((i + 1) * chunk_duration, duration)
            chunk_file = Path(f"chunk_{i}.wav")
            (
                ffmpeg
                .input(str(audio_path), ss=start, t=(end-start))
                .output(str(chunk_file))
                .run(overwrite_output=True)
            )
            chunk_paths.append(chunk_file)

    st.success(f"오디오 분할 완료: {len(chunk_paths)}개")

    # --------------------------
    # Whisper 전사
    # --------------------------
    transcripts = []
    for chunk_file in chunk_paths:
        with open(chunk_file, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
            transcripts.append(response.text)

    st.subheader("영상 전사 결과")
    st.write("\n\n".join(transcripts))

# --------------------------
# 기존 OCR/텍스트 요약 기능은 그대로 유지
# --------------------------
