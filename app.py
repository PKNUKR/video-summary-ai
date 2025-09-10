# app.py
import streamlit as st
from pathlib import Path
import os
from openai import OpenAI
import ffmpeg
import wave
import contextlib

# yt-dlp
import yt_dlp

# --------------------------
# OpenAI API 키
# --------------------------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

st.title("Video Summary AI (자동 다운로드 + 요약)")

# --------------------------
# YouTube URL 입력
# --------------------------
url = st.text_input("YouTube 영상 URL 입력")
if url:
    st.info("영상 다운로드 중...")
    video_path = Path("temp_video.mp4")
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(video_path),
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        st.success(f"영상 다운로드 완료: {video_path.name}")
    except Exception as e:
        st.error(f"영상 다운로드 실패: {e}")
        st.stop()

    # --------------------------
    # ffmpeg로 오디오 추출
    # --------------------------
    audio_path = Path("temp_audio.wav")
    try:
        ffmpeg.input(str(video_path)).output(str(audio_path), ac=1, ar=16000).run(overwrite_output=True)
        st.success("오디오 추출 완료")
    except Exception as e:
        st.error(f"오디오 추출 실패: {e}")
        st.stop()

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
# 기존 OCR/텍스트 요약 기능 유지 가능
# --------------------------
