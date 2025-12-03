import os
import random
import asyncio
import edge_tts
import requests
from moviepy.editor import *
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class AutoTokEngine:
    def __init__(self):
        # 检查 Key 是否存在
        if not os.getenv("PEXELS_API_KEY") or not os.getenv("GROQ_API_KEY"):
            raise ValueError("Missing API Keys in .env file!")
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        
        # 初始化 LLM
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
        self.voice = "en-US-ChristopherNeural" 

    def generate_content_data(self, topic: str):
        """同时生成文案和视觉关键词"""
        print(f"🧠 Analyzing topic: {topic}...")
        
        # === 核心修改：增加了字数要求，让视频变长 (约 15-20秒) ===
        prompt = (
            f"Topic: '{topic}'.\n"
            "Task 1: Write an engaging TikTok script (approx 40-60 words). "
            "Don't just write a headline, write 3 full sentences explaining why this topic is interesting. "
            "No emojis, no hashtags, just the spoken text.\n"
            "Task 2: Provide 1 simple, broad visual keyword to search for a background video (e.g., 'ocean', 'city', 'forest', 'technology').\n"
            "Format your answer exactly like this:\n"
            "Script: [Your script here]\n"
            "Search: [Your search keyword here]"
        )
        # ========================================================
        
        response = self.llm.invoke(prompt).content.strip()
        
        # 解析逻辑 (默认保底值)
        script = "This is a default script because the AI response was too short. Please try again." 
        search_term = "abstract background"       
        
        try:
            lines = response.split('\n')
            for line in lines:
                if "Script:" in line:
                    script = line.split("Script:")[1].strip()
                elif "Search:" in line:
                    search_term = line.split("Search:")[1].strip()
        except:
            pass 
            
        print(f"📝 Script ({len(script.split())} words): {script}")
        print(f"🔍 Visual Search: {search_term}")
        return script, search_term

    async def _gen_audio(self, text, filepath):
        """生成语音文件"""
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(filepath)

    def get_video_url(self, query, min_duration):
        """从 Pexels 获取素材链接"""
        headers = {"Authorization": self.pexels_key}
        # 搜索竖屏视频
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation=portrait"
        res = requests.get(url, headers=headers).json()
        videos = res.get("videos", [])
        
        if not videos: return None
        
        # 找最匹配时长的，或者默认第一个
        for v in videos:
            if v["duration"] >= min_duration:
                return v["video_files"][0]["link"]
        
        # 如果没有足够长的，也返回第一个，后面我们会用 loop 修复
        if videos:
            return videos[0]["video_files"][0]["link"]
        return None

    def make_video(self, topic, progress_callback=None):
        """主流程"""
        temp_audio = "temp_audio.mp3"
        temp_video = "temp_video.mp4"
        # 生成安全的文件名
        safe_filename = topic.replace(" ", "_").replace("'", "")[:15]
        output_file = f"tiktok_{safe_filename}.mp4"

        try:
            # 1. 生成内容策略 (文案 + 搜索词)
            if progress_callback: progress_callback("🧠 Generating Content Strategy...")
            script, search_term = self.generate_content_data(topic)
            
            # 2. 合成语音
            if progress_callback: progress_callback("🔊 Synthesizing Audio...")
            asyncio.run(self._gen_audio(script, temp_audio))
            
            # 获取音频时长 (加 0.5秒 缓冲)
            audio_clip = AudioFileClip(temp_audio)
            duration = audio_clip.duration + 0.5
            
            # 3. 下载视频素材 (使用 search_term 而不是 topic)
            if progress_callback: progress_callback(f"🎬 Downloading Visuals for '{search_term}'...")
            vid_url = self.get_video_url(search_term, duration)
            
            if not vid_url:
                raise Exception("Failed to find video on Pexels")
                
            with open(temp_video, "wb") as f:
                f.write(requests.get(vid_url).content)
                
            # 4. 剪辑合成
            if progress_callback: progress_callback("✂️ Rendering Video (This takes time)...")
            
            video = VideoFileClip(temp_video)
            
            # === 核心修复：强制循环视频 ===
            # Pexels 视频很短，这里强制重复播放直到覆盖音频时长
            if video.duration < duration:
                n_loops = int(duration / video.duration) + 1
                video = video.loop(n=n_loops)
            
            # 截取精确时长
            video = video.subclip(0, duration)
            
            # 裁剪成 9:16 竖屏
            w, h = video.size
            if w/h > 9/16:
                new_w = h * (9/16)
                video = video.crop(x1=w/2 - new_w/2, width=new_w, height=h)
            
            video = video.set_audio(audio_clip)
            
            # 添加字幕 (TextClip)
            # 使用 Helvetica-Bold 以兼容 Mac
            txt = TextClip(
                script, 
                fontsize=60, 
                color='white', 
                font='Helvetica-Bold', 
                stroke_color='black', 
                stroke_width=2, 
                size=(video.w*0.9, None), 
                method='caption'
            )
            txt = txt.set_pos('center').set_duration(duration)
            
            final = CompositeVideoClip([video, txt])
            
            # 写入文件
            final.write_videofile(
                output_file, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac",
                preset="fast"  # 加速渲染
            )
            
            return output_file, script

        except Exception as e:
            # 打印详细错误方便调试
            import traceback
            traceback.print_exc()
            return None, str(e)
            
        finally:
            # 清理资源
            try:
                if 'audio_clip' in locals(): audio_clip.close()
                if 'video' in locals(): video.close()
            except:
                pass
                
            if os.path.exists(temp_audio): os.remove(temp_audio)
            if os.path.exists(temp_video): os.remove(temp_video)

if __name__ == "__main__":
    # 测试代码
    bot = AutoTokEngine()
    print("Testing pipeline...")
    bot.make_video("The Three-Body Problem book")