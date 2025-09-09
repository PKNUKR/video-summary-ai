import os
import tempfile
from typing import Optional
from yt_dlp import YoutubeDL

def is_youtube_url(url: str) -> bool:
    return ("youtube.com" in url) or ("youtu.be" in url)

def download_subtitles_text_youtube(url: str) -> Optional[str]:
    """
    유튜브 자막(SRT/JSON3 등)을 로컬에 내려받아 텍스트로 변환해 반환.
    자막이 없으면 None.
    """
    # SRT가 가장 간편. 없으면 best effort로 자동 선택
    ydl_opts = {
        "writesubtitles": True,
        "writeautomaticsub": True,  # 자동 생성 자막 허용
        "subtitleslangs": ["ko", "en"],
        "skip_download": True,
        "quiet": True,
        "subtitlesformat": "srt/best",
        "outtmpl": "%(id)s.%(ext)s",
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            vid = info.get("id")
            # 실제로 자막 파일을 다운받자
            ydl.download([url])

        # yt-dlp가 현재 작업 디렉토리에 저장함. srt 또는 vtt를 탐색
        for ext in ("ko.srt", "en.srt", "srt", "ko.vtt", "en.vtt", "vtt"):
            candidate = f"{vid}.{ext}"
            if os.path.exists(candidate):
                with open(candidate, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                try:
                    os.remove(candidate)
                except Exception:
                    pass
                return _strip_subtitle_format(text)
        return None
    except Exception:
        return None

def _strip_subtitle_format(raw: str) -> str:
    """
    매우 단순한 SRT/VTT 타임라인 제거. (번호/시간라인/스타일 태그 제거)
    """
    import re
    # 시간 라인 제거
    raw = re.sub(r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}.*", "", raw)
    # 인덱스 번호 라인 제거
    raw = re.sub(r"^\s*\d+\s*$", "", raw, flags=re.MULTILINE)
    # 웹브이티티 헤더 제거
    raw = raw.replace("WEBVTT", "")
    # 스타일/태그 제거
    raw = re.sub(r"<[^>]+>", "", raw)
    # 공백 정리
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    return "\n".join(lines)

def extract_best_audio(url: str) -> str:
    """
    어떤 사이트든 오디오만 추출하여 로컬 파일 경로 반환 (m4a/mp3 등).
    AssemblyAI 업로드/로컬 처리에 사용.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".m4a")
    tmp.close()
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": tmp.name,
        "quiet": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return tmp.name
