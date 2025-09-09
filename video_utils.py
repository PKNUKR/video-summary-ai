import requests
import time

def transcribe_audio_assemblyai(api_key, video_url):
    """
    AssemblyAI를 사용해 영상 URL에서 오디오 전사
    ffmpeg를 사용하지 않음 → Streamlit Cloud 호환
    """
    headers = {
        "authorization": api_key,
        "content-type": "application/json"
    }

    # 전사 요청
    transcript_request = {"audio_url": video_url}
    transcript_response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json=transcript_request
    )
    transcript_response.raise_for_status()
    transcript_id = transcript_response.json()["id"]

    # 전사 완료 대기
    while True:
        polling_response = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers
        )
        polling_response.raise_for_status()
        status = polling_response.json()["status"]

        if status == "completed":
            return polling_response.json()["text"]
        elif status == "failed":
            raise RuntimeError("AssemblyAI transcription failed")
        time.sleep(3)
