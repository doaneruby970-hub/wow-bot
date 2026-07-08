import os
import time
import mss
import mss.tools
from datetime import datetime
import keyboard

# ================= 配置区域 =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 依然使用你习惯的直观路径
SAVE_PATH = os.path.join(BASE_DIR, "jietu", "shiti1")
INTERVAL = 2.0

START_KEY = 'page up'  # 开始/恢复
PAUSE_KEY = 'page down'  # 暂停
EXIT_KEY = 'esc'  # 彻底退出脚本


# ============================================

def setup_dir():
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
        print(f"✅ 已检查目录: {SAVE_PATH}")


def capture_worker():
    setup_dir()
    sct = mss.mss()
    monitor = sct.monitors[1]

    is_running = False
    count = 0

    print("========================================")
    print("📸 魔兽世界尸体素材采集器 (手动打怪版)")
    print(f"   ▶️ [{START_KEY.upper()}] 开始/恢复采集")
    print(f"   ⏸️ [{PAUSE_KEY.upper()}] 暂停采集")
    print(f"   🛑 [{EXIT_KEY.upper()}] 彻底关闭脚本")
    print(f"   🕒 当前间隔: {INTERVAL}秒/张")
    print("========================================\n")

    try:
        while True:
            # 1. 检查按键状态
            if keyboard.is_pressed(START_KEY):
                if not is_running:
                    is_running = True
                    print("▶️ 状态：已开启/恢复 (正在拍照...)")
                # 稍微延时防止按键抖动重复触发
                time.sleep(0.2)

            if keyboard.is_pressed(PAUSE_KEY):
                if is_running:
                    is_running = False
                    print("⏸️ 状态：已暂停 (停止拍照)")
                time.sleep(0.2)

            if keyboard.is_pressed(EXIT_KEY):
                print("\n🛑 脚本已彻底关闭")
                break

            # 2. 执行拍照逻辑
            if is_running:
                timestamp = datetime.now().strftime("%H%M%S")
                filename = f"shiti_{timestamp}_{count}.jpg"
                file_path = os.path.join(SAVE_PATH, filename)

                # 截图
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=file_path)

                print(f"📷 自动快门：已保存 {filename}")
                count += 1

                # 等待间隔
                time.sleep(INTERVAL)
            else:
                # 暂停期间低功耗运行
                time.sleep(0.1)

    except Exception as e:
        print(f"❌ 出错啦: {e}")


if __name__ == "__main__":
    capture_worker()