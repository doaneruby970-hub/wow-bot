import cv2
import numpy as np
from ultralytics import YOLO
import pyautogui
import time

# ================= 配置区 =================
# 1. 确保这是你最新的模型路径，如果 train4 没找到，请改成你实际找到 best.pt 的文件夹
MODEL_PATH = r'.\runs\detect\train2\weights\best.pt'

# 2. 攻击快捷键
ATTACK_KEY = '1'

# 3. 置信度阈值（0.5 表示 AI 有 50% 把握是红怪就开打）
CONF_LEVEL = 0.5
# ==========================================

# 加载模型
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ 成功加载模型: {MODEL_PATH}")
except Exception as e:
    print(f"❌ 加载模型失败，请检查路径！错误: {e}")
    exit()

print("🚀 AI 猎人已启动！正在实时扫描屏幕上的红名目标...")
print("💡 提示：请确保游戏窗口没被遮挡。按 Ctrl+C 可以强行停止脚本。")

while True:
    try:
        # 1. 抓取屏幕
        screenshot = pyautogui.screenshot()
        # 转换格式供 AI 识别
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # 2. AI 推理识别 (不开启 show=True，避免 OpenCV 报错)
        results = model.predict(source=frame, conf=CONF_LEVEL, verbose=False)

        # 3. 解析结果
        target_found = False
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # 获取类别 ID：0-monster, 1-red_health_bar, 2-yellow_health_bar
                cls = int(box.cls[0])

                # 只锁定红名血条 (类别 1)
                if cls == 1:
                    # 获取坐标
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)

                    print(f"🎯 发现红名怪！坐标: ({center_x}, {center_y})")

                    # 执行攻击动作
                    # 移动鼠标到血条中心稍微偏下一点（通常是怪物身体位置）
                    pyautogui.moveTo(center_x, center_y, duration=0.1)
                    pyautogui.rightClick()  # 右键选怪

                    time.sleep(0.2)  # 等待 0.2 秒让游戏选中目标
                    pyautogui.press(ATTACK_KEY)  # 按下攻击键
                    print(f"💥 已按下 {ATTACK_KEY} 键发起攻击！")

                    target_found = True
                    # 攻击完一个目标后，休息 3 秒防止操作太鬼畜被封号
                    time.sleep(3)
                    break  # 退出当前循环，重新扫描

            if target_found:
                break

        # 如果没发现目标，稍微等一下再扫，减轻 CPU 负担
        if not target_found:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n🛑 AI 猎人已手动停止。")
        break
    except Exception as e:
        print(f"⚠️ 运行中出现错误: {e}")
        time.sleep(1)