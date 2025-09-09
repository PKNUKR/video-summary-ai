import streamlit as st
from video_utils import is_youtube_url, transcribe_audio_assemblyai
from summarizer import summarize_text

st.set_page_config(page_title="Video Summarizer AI", page_icon="🎥", layout="centered")
st.title("🎥 영상 요약 AI")
st.write("링크를 입력하면 영상을 분석해 요약해주는 AI입니다.\nOpenAI + AssemblyAI API Key를 직접 입력하세요!")

# API Key 입력
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")
assemblyai_api_key = st.text_input("🔑 AssemblyAI API Key", type="password")

video_url = st.text_input("🔗 영상 링크를 입력하세요:")

if video_url and openai_api_key and assemblyai_api_key:
    with st.spinner("⏳ 영상 분석 중..."):
        text_content = transcribe_audio_assemblyai(assemblyai_api_key, video_url)
        summary = summarize_text(openai_api_key, text_content)
        st.subheader("📌 요약 결과")
        st.write(summary)
elif video_url:
    st.warning("⚠️ OpenAI와 AssemblyAI API Key를 모두 입력해주세요!")
