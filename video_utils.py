import subprocess
import imageio_ffmpeg as ffmpeg
import requests
import time
import os

def download_video(video_url, filename="video.mp4"):
    """URL에서 비디오 다운로드"""
    response = requests.get(video_url, stream=True)
    response.raise_for_status()
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return filename

def transcribe_audio_assemblyai(api_key, video_url):
    """AssemblyAI를 사용해 영상 오디오 전사"""
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()  # 자동 ffmpeg 경로

    # 1️⃣ 영상 다운로드
    video_file = download_video(video_url)

    # 2️⃣ 오디오 추출
    audio_file = "audio.mp3"
    subprocess.run([
        ffmpeg_path,
        "-i", video_file,
        "-q:a", "0",
        "-map", "a",
        audio_file
    ], check=True)

    # 3️⃣ AssemblyAI API 호출
    headers = {
        "authorization": api_key,
        "content-type": "application/json"
    }
    upload_url = "https://api.assemblyai.com/v2/upload"
    with open(audio_file, "rb") as f:
        response = requests.post(upload_url, headers=headers, files={"file": f})
    response.raise_for_status()
    audio_url = response.json()["upload_url"]

    # 4️⃣ 전사 요청
    transcript_request = {
        "audio_url": audio_url
    }
    transcript_response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json=transcript_request
    )
    transcript_response.raise_for_status()
    transcript_id = transcript_response.json()["id"]

    # 5️⃣ 전사 완료 대기
    while True:
        polling_response = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
        polling_response.raise_for_status()
        status = polling_response.json()["status"]
        if status == "completed":
            return polling_response.json()["text"]
        elif status == "failed":
            raise RuntimeError("AssemblyAI transcription failed")
        time.sleep(3)
