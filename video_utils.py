import os
import requests
import time
import tempfile
from yt_dlp import YoutubeDL

ASSEMBLYAI_URL = "https://api.assemblyai.com/v2"

def is_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url

def download_audio(url: str) -> str:
    """
    영상에서 오디오 추출 후 임시 mp3 파일 경로 반환.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": tmp.name,
            "quiet": True
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return tmp.name

def upload_to_assemblyai(api_key: str, audio_path: str) -> str:
    """
    AssemblyAI에 오디오 파일 업로드 후 URL 반환.
    """
    headers_upload = {"authorization": api_key}
    with open(audio_path, "rb") as f:
        response = requests.post(
            f"{ASSEMBLYAI_URL}/upload",
            headers=headers_upload,
            data=f
        )
    response.raise_for_status()
    return response.json()["upload_url"]

def transcribe_audio_assemblyai(api_key: str, url: str) -> str:
    """
    AssemblyAI를 사용한 음성 인식 → 텍스트 변환.
    """
    try:
        headers = {"authorization": api_key, "content-type": "application/json"}
        audio_path = download_audio(url)
        upload_url = upload_to_assemblyai(api_key, audio_path)

        # AssemblyAI 전사 요청
        json_data = {
            "audio_url": upload_url,
            "language_code": "ko",
            "auto_highlights": True
        }
        response = requests.post(
            f"{ASSEMBLYAI_URL}/transcript",
            headers=headers,
            json=json_data
        )
        response.raise_for_status()
        transcript_id = response.json()["id"]

        # 처리 완료까지 대기
        while True:
            status_response = requests.get(
                f"{ASSEMBLYAI_URL}/transcript/{transcript_id}",
                headers=headers
            )
            status_response.raise_for_status()
            status = status_response.json()

            if status["status"] == "completed":
                return status["text"]
            elif status["status"] == "error":
                raise Exception(f"AssemblyAI 오류: {status['error']}")
            time.sleep(5)

    except Exception as e:
        return f"⚠️ 음성 인식 중 오류 발생: {e}"
