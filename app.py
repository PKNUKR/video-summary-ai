# app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
from pytube import YouTube
import subprocess
import os
import tempfile
from pydub import AudioSegment
import cv2
import pytesseract
import openai
from pathlib import Path
import math
import time

# ---------- 설정 ----------
st.set_page_config(page_title="영상(음성+화면) 자동 요약기", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ---------- 유틸: 사이트에서 YouTube 링크 추출 ----------
def extract_video_links_from_page(url):
    try:
        res = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
    except Exception as e:
        st.error(f"페이지 요청 실패: {e}")
        return []
    soup = BeautifulSoup(res.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "youtube.com/watch" in href or "youtu.be/" in href:
            # 절대 URL이 아닌 경우 도메인 붙일 필요는 있지만 대부분 절대 URL
            if href.startswith("//"):
                href = "https:" + href
            if href.startswith("/"):
                href = requests.compat.urljoin(url, href)
            links.append(href)
    # 중복 제거
    return list(dict.fromkeys(links))

# ---------- 유틸: YouTube 영상 다운로드 (mp4) ----------
def download_youtube_video(video_url, target_dir):
    yt = YouTube(video_url)
    # 최적의 progressive (audio+video) 스트림
    stream = yt.streams.filter(file_extension="mp4", progressive=True, res="720p").first()
    if not stream:
        stream = yt.streams.filter(file_extension="mp4", progressive=True).order_by('resolution').desc().first()
    out_path = stream.download(output_path=target_dir)
    return out_path

# ---------- 오디오 추출 using ffmpeg ----------
def extract_audio_with_ffmpeg(video_path, out_audio_path):
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "mp3", "-ar", "16000", "-ac", "1",
        str(out_audio_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_audio_path

# ---------- 오디오 분할 (pydub) ----------
def split_audio_to_chunks(audio_path, chunk_minutes=3):
    audio = AudioSegment.from_file(audio_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    total_ms = len(audio)
    for i in range(0, total_ms, chunk_ms):
        chunk = audio[i: i + chunk_ms]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        chunk.export(tmp.name, format="mp3")
        chunks.append(tmp.name)
    return chunks

# ---------- Whisper로 전사 (OpenAI) ----------
def transcribe_audio_file(path):
    # openai 라이브러리의 audio transcription 호출
    with open(path, "rb") as f:
        # 모델 이름은 "whisper-1"
        res = openai.Audio.transcribe(model="whisper-1", file=f)
    # res는 dict 형태로 'text' 포함
    return res.get("text", "")

def transcribe_audio_chunks(chunk_paths, progress_callback=None):
    texts = []
    for i, p in enumerate(chunk_paths):
        if progress_callback:
            progress_callback(i, len(chunk_paths), f"Transcribing chunk {i+1}/{len(chunk_paths)}")
        try:
            txt = transcribe_audio_file(p)
        except Exception as e:
            txt = f"[Transcription failed chunk {i+1}: {e}]"
        texts.append(txt)
    return "\n".join(texts)

# ---------- OCR: 프레임 추출 + pytesseract ----------
def ocr_extract_text_from_video(video_path, frame_interval_seconds=2, lang="kor+eng", max_frames=200):
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_interval = int(fps * frame_interval_seconds)
    texts = []
    frame_idx = 0
    saved_frames = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            # 전처리: 그레이스케일 -> 임계치(선택적)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # pytesseract로 텍스트 추출
            try:
                txt = pytesseract.image_to_string(gray, lang=lang)
                if txt and txt.strip():
                    texts.append(txt.strip())
            except Exception:
                # pytesseract 설정 문제 등
                pass
            saved_frames += 1
            if saved_frames >= max_frames:
                break
        frame_idx += 1
    cap.release()
    return "\n".join(texts)

# ---------- GPT 요약 (오디오 전사 + OCR 합쳐서) ----------
def summarize_combined_text(transcript_text, ocr_text, model="gpt-4o-mini", max_tokens=400):
    system = "당신은 영상 내용(음성 전사 + 화면 OCR 텍스트)을 전문적으로 요약하는 도우미입니다."
    user_in = (
        "아래 두 종류의 텍스트를 종합해 다음 항목을 포함하는 요약을 만들어 주세요:\n"
        "1) 한 문장 요약(핵심) 2) 핵심 포인트(불릿 5개 이내) 3) 영상 시간순 요약(가능하면 타임라인) "
        "4) 중요 키워드(태그 형식)\n\n"
        "==== 오디오 전사 ====\n"
        f"{transcript_text[:30000]}\n"  # 길이 제한: 잘라서 보냄
        "\n==== 화면 OCR 텍스트 ====\n"
        f"{ocr_text[:10000]}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_in}
    ]
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.2
    )
    return resp.choices[0].message["content"]

# ---------- Streamlit UI ----------
st.title("🎬 영상(음성+화면) 자동 요약기 — 확장형")

with st.sidebar:
    st.header("설정")
    frame_interval_seconds = st.number_input("OCR 프레임 간격(초)", min_value=1, max_value=10, value=2)
    ocr_max_frames = st.number_input("OCR 최대 프레임 수", min_value=10, max_value=1000, value=200)
    audio_chunk_minutes = st.number_input("오디오 분할 길이(분)", min_value=1, max_value=10, value=3)
    model_choice = st.selectbox("요약에 사용할 모델", options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)

st.markdown("### 1) 분석할 웹페이지 URL 입력")
url = st.text_input("웹페이지 URL (YouTube 영상 링크가 포함된 페이지)")

if st.button("분석 시작") and url:
    tmpdir = Path(tempfile.mkdtemp(prefix="video_summarize_"))
    st.info("🔎 페이지에서 영상 링크 추출 중...")
    links = extract_video_links_from_page(url)
    if not links:
        st.error("해당 페이지에서 유튜브 영상 링크를 찾지 못했습니다.")
    else:
        st.success(f"🔗 찾은 영상: {len(links)}개 (첫 번째 영상 처리)")
        video_link = links[0]
        st.write(video_link)

        try:
            status_text = st.empty()
            status_text.info("📥 영상 다운로드 중...")
            video_path = download_youtube_video(video_link, tmpdir)
            status_text.success("✅ 다운로드 완료")

            status_text.info("🔊 오디오 추출 중 (ffmpeg)...")
            audio_path = tmpdir / "extracted_audio.mp3"
            extract_audio_with_ffmpeg(video_path, audio_path)
            status_text.success("✅ 오디오 추출 완료")

            status_text.info("✂️ 오디오 분할 중...")
            chunk_paths = split_audio_to_chunks(audio_path, chunk_minutes=int(audio_chunk_minutes))
            status_text.success(f"✅ 오디오 분할 완료 ({len(chunk_paths)}개 청크)")

            # 오디오 전사 (Whisper)
            progress_bar = st.progress(0)
            progress_msg = st.empty()
            def progress_cb(i, n, msg):
                progress_bar.progress(int((i+1)/n*100))
                progress_msg.text(msg)

            status_text.info("🎤 음성 전사(Whisper) 중...")
            transcript_text = transcribe_audio_chunks(chunk_paths, progress_callback=progress_cb)
            status_text.success("✅ 음성 전사 완료")
            progress_bar.empty()
            progress_msg.empty()

            # OCR
            status_text.info("🔎 화면 OCR 처리 중...")
            ocr_text = ocr_extract_text_from_video(video_path, frame_interval_seconds=int(frame_interval_seconds),
                                                   lang="kor+eng", max_frames=int(ocr_max_frames))
            status_text.success("✅ 화면 OCR 완료")

            # 요약
            status_text.info("🧠 GPT로 요약 생성 중...")
            combined_summary = summarize_combined_text(transcript_text, ocr_text, model=model_choice)
            status_text.success("✅ 요약 완료")

            st.markdown("## 결과")
            with st.expander("원문 (오디오 전사)"):
                st.write(transcript_text[:20000] + ("..." if len(transcript_text) > 20000 else ""))
            with st.expander("원문 (OCR)"):
                st.write(ocr_text[:10000] + ("..." if len(ocr_text) > 10000 else ""))
            with st.expander("요약"):
                st.markdown(combined_summary)

            # 파일 다운로드 제공
            out_txt = tmpdir / "summary.txt"
            out_txt.write_text("SUMMARY\n\n" + combined_summary + "\n\n---\nAUDIO_TRANSCRIPT\n\n" + transcript_text + "\n\nOCR\n\n" + ocr_text, encoding="utf-8")
            with open(out_txt, "rb") as f:
                st.download_button("요약 + 원문 다운로드 (.txt)", f, file_name="video_summary.txt")
        except subprocess.CalledProcessError as e:
            st.error(f"ffmpeg 실행 오류: {e}")
        except Exception as e:
            st.error(f"오류 발생: {e}")
