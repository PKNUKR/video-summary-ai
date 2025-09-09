import os
import requests
import time
import tempfile
from yt_dlp import YoutubeDL

ASSEMBLYAI_URL = "https://api.assemblyai.com/v2"

def download_audio(url: str) -> str:
    """
    영상에서 오디오 추출 후 MP3로 변환
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": tmp.name,
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if not os.path.exists(tmp.name) or os.path.getsize(tmp.name) == 0:
            raise Exception("⚠️ 다운로드된 오디오 파일이 없거나 비어있습니다.")
        return tmp.name

def upload_to_assemblyai(api_key: str, audio_path: str) -> str:
    """
    AssemblyAI에 오디오 파일 업로드 후 URL 반환
    """
    headers_upload = {"authorization": api_key, "content-type": "application/octet-stream"}
    with open(audio_path, "rb") as f:
        response = requests.post(f"{ASSEMBLYAI_URL}/upload", headers=headers_upload, data=f)
    if response.status_code != 200:
        raise Exception(f"⚠️ AssemblyAI 업로드 실패: {response.status_code} - {response.text}")
    return response.json()["upload_url"]

def transcribe_audio_assemblyai(api_key: str, url: str) -> str:
    """
    AssemblyAI를 사용한 음성 인식 → 텍스트 변환
    """
    try:
        audio_path = download_audio(url)
        upload_url = upload_to_assemblyai(api_key, audio_path)

        headers = {"authorization": api_key, "content-type": "application/json"}
        json_data = {
            "audio_url": upload_url,
            "language_code": "ko",
            "auto_highlights": True
        }
        response = requests.post(f"{ASSEMBLYAI_URL}/transcript", headers=headers, json=json_data)
        if response.status_code != 200:
            raise Exception(f"⚠️ 전사 요청 실패: {response.status_code} - {response.text}")
        transcript_id = response.json()["id"]

        # 처리 완료까지 대기
        while True:
            status_response = requests.get(f"{ASSEMBLYAI_URL}/transcript/{transcript_id}", headers=headers)
            if status_response.status_code != 200:
                raise Exception(f"⚠️ 상태 조회 실패: {status_response.status_code} - {status_response.text}")
            status = status_response.json()

            if status["status"] == "completed":
                return status["text"]
            elif status["status"] == "error":
                raise Exception(f"⚠️ AssemblyAI 오류: {status['error']}")
            time.sleep(5)

    except Exception as e:
        return str(e)
