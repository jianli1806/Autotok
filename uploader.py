from playwright.sync_api import sync_playwright
import os
import time

def upload_video(file_path, title):
    """
    使用 Playwright 模拟上传。
    修复了 set_files 报错，并增加了 iframe 检测。
    """
    # 1. 检查文件是否存在
    if not os.path.exists("auth.json"):
        return "❌ Error: auth.json not found. Please run login script first."
    
    # 确保传入的是绝对路径，Playwright 有时候不喜欢相对路径
    abs_file_path = os.path.abspath(file_path)
    if not os.path.exists(abs_file_path):
        return f"❌ Error: Video file not found: {abs_file_path}"

    print(f"🚀 Starting upload for: {abs_file_path}")

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.firefox.launch(headless=False) 
        try:
            context = browser.new_context(storage_state="auth.json")
            page = context.new_page()
            
            print("🌐 Going to TikTok upload page...")
            page.goto("https://www.tiktok.com/upload?lang=en")
            
            # 等待页面加载，TikTok 比较慢
            page.wait_for_load_state("networkidle", timeout=60000)
            
            # === 核心修复逻辑 ===
            print("🔍 Looking for upload input...")
            
            # 策略 A: 尝试在主页面找上传框
            upload_input = page.locator('input[type="file"]')
            
            # 策略 B: 如果主页面没有，尝试在 iframe 里找 (TikTok 经常变)
            if float(upload_input.count()) == 0:
                print("⚠️ Input not found in main frame, checking iframes...")
                # 遍历所有 iframe 寻找包含 file input 的那个
                for frame in page.frames:
                    potential_input = frame.locator('input[type="file"]')
                    if potential_input.count() > 0:
                        upload_input = potential_input
                        print("✅ Found input inside an iframe!")
                        break
            
            if float(upload_input.count()) == 0:
                raise Exception("Could not find file input element on the page.")

            print(f"📤 Uploading file: {abs_file_path}")
            
            # !!! 这里的关键修改：使用 set_input_files !!!
            upload_input.set_input_files(abs_file_path)
            
            # ===================
            
            print("✅ File selected! Waiting for upload to complete...")
            
            # 这里的 title 设置比较复杂，因为是富文本编辑器
            # 为了简单起见，我们只打印提示，让你手动填标题和点发布
            print("\n" + "="*50)
            print("⚠️  自动化部分结束")
            print(f"1. 视频已自动选定: {os.path.basename(file_path)}")
            print(f"2. 请手动复制标题填入: {title}")
            print("3. 等待上传进度条走完，手动点击【Post】")
            print("="*50 + "\n")
            
            # 留给你 2 分钟时间手动操作 (填标题、点发布)
            time.sleep(120)
            
            return "Upload sequence finished."
            
        except Exception as e:
            # 截图报错现场，方便调试
            page.screenshot(path="error_screenshot.png")
            print(f"❌ Upload failed. Screenshot saved to error_screenshot.png")
            return f"Upload failed: {e}"
        finally:
            browser.close()