import os
import requests
import time
import tempfile
from yt_dlp import YoutubeDL, DownloadError
import shutil
import subprocess
import sys

ASSEMBLYAI_URL = "https://api.assemblyai.com/v2"

def get_ffmpeg_path(ffmpeg_location=None):
    """
    FFmpeg/ffprobe 설치 확인 및 경로 반환
    로컬/Cloud 환경 모두 지원
    """
    # 1️⃣ 사용자 지정 경로 확인
    if ffmpeg_location:
        ffmpeg_path = ffmpeg_location
        ffprobe_path = ffmpeg_location.replace("ffmpeg", "ffprobe")
        if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
            return ffmpeg_path
        else:
            raise Exception(f"⚠️ 지정된 FFmpeg/ffprobe 경로를 찾을 수 없습니다.\n{ffmpeg_path}, {ffprobe_path}")

    # 2️⃣ 시스템 PATH에 있는 ffmpeg 확인
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if ffmpeg_path and ffprobe_path:
        return ffmpeg_path

    # 3️⃣ Linux Cloud 환경이면 apt-get으로 설치 시도
    if sys.platform.startswith("linux"):
        try:
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "ffmpeg"], check=True)
            ffmpeg_path = shutil.which("ffmpeg")
            ffprobe_path = shutil.which("ffprobe")
            if ffmpeg_path and ffprobe_path:
                return ffmpeg_path
        except:
            pass

    # 4️⃣ 실패 시 예외
    raise Exception(
        "⚠️ FFmpeg 또는 ffprobe를 찾을 수 없습니다.\n"
        "설치 후 환경 변수에 경로를 추가하거나, ffmpeg_location을 통해 경로를 지정하세요.\n"
        "Windows: https://ffmpeg.org/download.html\n"
        "Mac: brew install ffmpeg\n"
        "Linux: sudo apt install ffmpeg"
    )


def download_audio(url: str, ffmpeg_location=None) -> str:
    """
    영상에서 오디오 추출 후 MP3 변환
    """
    ffmpeg_path = get_ffmpeg_path(ffmpeg_location)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": tmp.name,
            "quiet": True,
            "ffmpeg_location": ffmpeg_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except DownloadError as e:
            raise Exception(f"⚠️ 영상 다운로드 실패: {e}")

        if not os.path.exists(tmp.name) or os.path.getsize(tmp.name) == 0:
            raise Exception("⚠️ 다운로드된 오디오 파일이 없거나 비어있습니다.")
        return tmp.name


def upload_to_assemblyai(api_key: str, audio_path: str) -> str:
    headers_upload = {"authorization": api_key, "content-type": "application/octet-stream"}
    with open(audio_path, "rb") as f:
        response = requests.post(f"{ASSEMBLYAI_URL}/upload", headers=headers_upload, data=f)
    if response.status_code != 200:
        raise Exception(f"⚠️ AssemblyAI 업로드 실패: {response.status_code} - {response.text}")
    return response.json()["upload_url"]


def transcribe_audio_assemblyai(api_key: str, url: str, ffmpeg_location=None) -> str:
    try:
        audio_path = download_audio(url, ffmpeg_location)
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
