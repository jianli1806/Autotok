from playwright.sync_api import sync_playwright
import os

def manual_login():
    print("🚀 正在启动本机的 Google Chrome...")
    
    with sync_playwright() as p:
        # 核心修改：channel="chrome"
        # 这会直接调用你 Mac 上安装的 Google Chrome，而不是 Playwright 的测试版浏览器
        # 这样 TikTok 会认为你是真人用户，从而发送验证码
        try:
            browser = p.chromium.launch(
                channel="chrome", 
                headless=False,
                args=['--disable-blink-features=AutomationControlled'] # 进一步隐藏机器人特征
            )
        except Exception as e:
            print("❌ 启动失败：请确保你的电脑上安装了 Google Chrome 浏览器！")
            print(f"错误信息: {e}")
            return

        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        
        print("🌐 正在打开 TikTok 登录页...")
        page.goto("https://www.tiktok.com/login")
        
        print("\n" + "="*50)
        print("✅ 真实 Chrome 已启动！")
        print("1. 现在请尝试【手机验证码】或【扫码】登录。")
        print("2. 因为是真实浏览器，验证码应该能收到了。")
        print("3. 登录成功跳转到首页后，回到这里按回车。")
        print("="*50 + "\n")
        
        input("👉 登录成功了吗？请按回车键保存 Cookie (Enter to save): ")
        
        # 保存 Cookie
        context.storage_state(path="auth.json")
        print("✅ 登录状态已保存到 auth.json！")
        
        browser.close()

if __name__ == "__main__":
    manual_login()