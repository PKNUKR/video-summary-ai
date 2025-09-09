import os
import requests
import time
import tempfile
from yt_dlp import YoutubeDL, DownloadError

ASSEMBLYAI_URL = "https://api.assemblyai.com/v2"

def check_ffmpeg(ffmpeg_location=None):
    """
    FFmpeg와 ffprobe 설치 확인
    """
    import shutil
    ffmpeg_path = ffmpeg_location or shutil.which("ffmpeg")
    ffprobe_path = ffmpeg_location or shutil.which("ffprobe")
    if not ffmpeg_path or not ffprobe_path:
        raise Exception(
            "⚠️ FFmpeg 또는 ffprobe를 찾을 수 없습니다.\n"
            "설치 후 환경 변수에 경로를 추가하거나, "
            "--ffmpeg-location 옵션으로 경로를 지정하세요.\n"
            "Windows: https://ffmpeg.org/download.html\n"
            "Mac: brew install ffmpeg\n"
            "Linux: sudo apt install ffmpeg"
        )
    return ffmpeg_path

def download_audio(url: str, ffmpeg_location=None) -> str:
    """
    영상에서 오디오 추출 후 MP3로 변환
    ffmpeg 자동 확인 포함
    """
    ffmpeg_path = check_ffmpeg(ffmpeg_location)

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
