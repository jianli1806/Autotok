import streamlit as st
import os
from video_engine import AutoTokEngine
from uploader import upload_video

# ==================== 页面配置 ====================
st.set_page_config(page_title="AutoTok Creator", layout="centered", page_icon="🤖")

st.title("🤖 AutoTok: AI Video Generator")
st.caption("Text-to-Video Pipeline: Groq (Script) -> Edge-TTS (Audio) -> Pexels (Visuals)")

# ==================== 初始化 Session State ====================
if "generated_video" not in st.session_state:
    st.session_state.generated_video = None
if "generated_script" not in st.session_state:
    st.session_state.generated_script = None

# ==================== 输入区 ====================
with st.form("generation_form"):
    topic = st.text_input("Enter a Topic or Book Title:", placeholder="e.g., Atomic Habits")
    submitted = st.form_submit_button("🚀 Generate Video")

# ==================== 生成逻辑 ====================
if submitted and topic:
    engine = AutoTokEngine()
    
    # 初始化进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_status(text):
        status_text.text(text)
    
    with st.spinner("Processing pipeline..."):
        # 调用核心引擎
        video_path, script = engine.make_video(topic, update_status)
        progress_bar.progress(100)
    
    # 检查结果
    if video_path and not video_path.startswith("Error") and os.path.exists(video_path):
        st.success("✅ Video Generated Successfully!")
        st.session_state.generated_video = video_path
        st.session_state.generated_script = script
    else:
        st.error(f"Generation Failed: {script}")

# ==================== 结果展示与上传区 ====================
if st.session_state.generated_video:
    st.divider()
    st.subheader("📺 Preview")
    
    # 显示生成的视频
    st.video(st.session_state.generated_video)
    
    # 显示生成的文案
    with st.expander("📜 View Generated Script"):
        st.write(st.session_state.generated_script)
    
    st.divider()
    st.subheader("🚀 Distribution")
    
    col1, col2 = st.columns(2)
    
    # --- 列 1: 下载功能 ---
    with col1:
        st.markdown("#### 📥 Download")
        try:
            with open(st.session_state.generated_video, "rb") as file:
                st.download_button(
                    label="Download MP4",
                    data=file,
                    file_name=st.session_state.generated_video,
                    mime="video/mp4",
                    use_container_width=True
                )
        except FileNotFoundError:
            st.error("File not found. Please regenerate.")
            
    # --- 列 2: 上传功能 (核心修改部分) ---
    with col2:
        st.markdown("#### 📱 TikTok Upload")
        
        # 检查本地是否有 auth.json
        if os.path.exists("auth.json"):
            st.success("✅ Auth Session Found")
            
            if st.button("🚀 Upload to TikTok", use_container_width=True):
                with st.spinner("Opening browser automation..."):
                    # 组合文案和标签
                    caption = f"{st.session_state.generated_script[:100]}... #fyp #ai #autotok"
                    
                    # 调用 uploader.py
                    msg = upload_video(
                        st.session_state.generated_video, 
                        caption
                    )
                    
                    if "finished" in msg:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            # 如果没有 auth.json，显示明确的提示
            st.warning("⚠️ Local Session Missing")
            st.info("Browser automation requires a local login session.")
            st.markdown("Run this command in your terminal to login:")
            st.code("python login.py", language="bash")