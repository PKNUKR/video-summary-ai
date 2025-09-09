import os
from typing import Optional
from dotenv import load_dotenv

from video_utils import extract_best_audio

load_dotenv()

# ---------------- AssemblyAI ----------------
def transcribe_with_assemblyai(url: str) -> str:
    """
    링크(URL)를 받아 오디오를 로컬로 추출한 뒤 AssemblyAI에 업로드-전사.
    (직접 URL 업로드도 가능하지만, 일반 사이트의 경우 접근 이슈가 있어 로컬 업로드가 안정적)
    """
    import assemblyai as aai
    aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
    audio_path = extract_best_audio(url)

    # 한국어/영어 자동 감지
    config = aai.TranscriptionConfig(
        speaker_labels=False,
        language_detection=True,
        punctuate=True,
        format_text=True,
        disfluency_removal=True,
        dual_channel=False,
        # 필요 시 glossary/filters 추가 가능
    )

    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)

    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"AssemblyAI 실패: {transcript.error}")

    text = transcript.text or ""
    # 파일 정리
    try:
        os.remove(audio_path)
    except Exception:
        pass
    return text.strip()

# ---------------- Whisper (선택) ----------------
def transcribe_with_whisper(url: str, language_hint: Optional[str] = "ko") -> str:
    """
    로컬 Whisper 백업 경로 (속도 느림, GPU 권장)
    """
    import whisper
    audio_path = extract_best_audio(url)
    model = whisper.load_model("base")  # "small" 이상이면 더 정확
    result = model.transcribe(audio_path, language=language_hint)
    try:
        os.remove(audio_path)
    except Exception:
        pass
    return (result.get("text") or "").strip()

def transcribe(url: str, provider: Optional[str] = None) -> str:
    """
    provider = "assemblyai" | "whisper"
    .env의 DEFAULT_STT_PROVIDER 우선
    """
    prov = (provider or os.getenv("DEFAULT_STT_PROVIDER", "assemblyai")).lower()
    if prov == "whisper":
        return transcribe_with_whisper(url)
    # 기본값: assemblyai
    return transcribe_with_assemblyai(url)
