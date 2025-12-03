import streamlit as st
import os
from video_engine import AutoTokEngine
from uploader import upload_video

st.set_page_config(page_title="AutoTok Creator", layout="centered")

st.title("🤖 AutoTok: AI Video Generator")
st.caption("Text-to-Video Pipeline: Groq (Script) -> Edge-TTS (Audio) -> Pexels (Visuals)")

# 初始化 Session State
if "generated_video" not in st.session_state:
    st.session_state.generated_video = None
if "generated_script" not in st.session_state:
    st.session_state.generated_script = None

# 输入区
with st.form("generation_form"):
    topic = st.text_input("Enter a Topic or Book Title:", placeholder="e.g., Atomic Habits")
    submitted = st.form_submit_button("🚀 Generate Video")

# 生成逻辑
if submitted and topic:
    engine = AutoTokEngine()
    
    # 进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_status(text):
        status_text.text(text)
    
    with st.spinner("Processing pipeline..."):
        video_path, script = engine.make_video(topic, update_status)
        progress_bar.progress(100)
    
    if video_path and not video_path.startswith("Error"):
        st.success("✅ Video Generated Successfully!")
        st.session_state.generated_video = video_path
        st.session_state.generated_script = script
    else:
        st.error(f"Generation Failed: {script}")

# 结果展示与上传区
if st.session_state.generated_video:
    st.divider()
    st.subheader("📺 Preview")
    
    # 显示视频
    st.video(st.session_state.generated_video)
    st.info(f"📜 Script: {st.session_state.generated_script}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 下载按钮
        with open(st.session_state.generated_video, "rb") as file:
            st.download_button(
                label="📥 Download MP4",
                data=file,
                file_name=st.session_state.generated_video,
                mime="video/mp4"
            )
            
    with col2:
        # 上传按钮
        if st.button("🚀 Upload to TikTok (Local Only)"):
            if not os.path.exists("auth.json"):
                st.warning("⚠️ Auth file not found. Please run login script first.")
            else:
                with st.spinner("Opening browser for upload..."):
                    msg = upload_video(
                        st.session_state.generated_video, 
                        f"{st.session_state.generated_script} #fyp #ai"
                    )
                    st.success(msg)