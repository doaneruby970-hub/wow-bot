import cv2
import numpy as np
from ultralytics import YOLO
import pyautogui
import time

# ================= 核心配置区 (所有修改都在这里) =================

# 1. 模型路径
MODEL_PATH = r'.\runs\detect\train2\weights\best.pt'

# 2. 基础按键设置
KEY_ATTACK = '1'  # 攻击键
KEY_LEFT = 'a'  # 左转
KEY_RIGHT = 'd'  # 右转
KEY_BACK = 's'  # 后退
CONF_LEVEL = 0.6  # AI 识别置信度

# 3. 大方框 (Big Box - 搜索区) 设置
# 只有在这个范围内的红名怪，脚本才会去打
# 格式：(x_start_percent, y_start_percent, width_percent, height_percent)
# 解释：(0.1, 0.1, 0.8, 0.8) 表示从屏幕 10%的位置开始，宽占80%，高占80% (即去掉了四周边缘)
BIG_BOX_CONFIG = (0.05, 0.25, 0.9, 0.57)

# 4. 小方框 (Small Box - 警戒/后退区) 设置
# 如果怪的中心点进入这个框，说明太近了，触发后退
# 格式同上。建议设在屏幕正中心脚底位置
SMALL_BOX_CONFIG = (0.43, 0.45, 0.14, 0.15)
# 后退时长 (秒)
BACK_DURATION = 4.0

# 5. 扇形转向灵敏度 (A/D键 按压时长系数)
# 键盘转向是靠时间控制的。公式：按键时间 = 像素偏差 * 时间系数 * 区域倍率
# 这个数值越小，每次按键时间越短
TIME_PER_PIXEL = 0.0005

# 分区倍率 (解决扇形透视问题)
# 远区(屏幕上方): 偏差很大也只需要转一点点
FACTOR_FAR = 0.8
# 中区(屏幕中间): 标准
FACTOR_MID = 1.5
# 近区(屏幕下方): 需要转很久才能把头转过来
FACTOR_CLOSE = 2.5

# 6. 瞄准死区 (像素)
# 如果怪距离中心 X 轴小于这个值，认为对准了，直接打，不转
AIM_DEAD_ZONE = 60

# =============================================================

# 获取屏幕分辨率
SCREEN_W, SCREEN_H = pyautogui.size()
SCREEN_CENTER_X = SCREEN_W // 2


# === 计算方框的实际像素坐标 (自动计算，勿动) ===
def get_rect_from_config(config, w, h):
    px = int(config[0] * w)
    py = int(config[1] * h)
    pw = int(config[2] * w)
    ph = int(config[3] * h)
    return (px, py, px + pw, py + ph)  # 返回 (x1, y1, x2, y2)


BIG_BOX = get_rect_from_config(BIG_BOX_CONFIG, SCREEN_W, SCREEN_H)
SMALL_BOX = get_rect_from_config(SMALL_BOX_CONFIG, SCREEN_W, SCREEN_H)

# === 计算扇形分界线 (用于监视器画线) ===
ZONE_Y1 = SCREEN_H // 3  # 远区界限
ZONE_Y2 = (SCREEN_H * 2) // 3  # 近区界限

# 加载模型
print("⏳ 正在加载 YOLO 模型...")
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ 模型加载成功! 分辨率: {SCREEN_W}x{SCREEN_H}")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    exit()

print("🚀 AI 猎人 (键盘转向版) 已启动！")
print("📺 监视器窗口已打开，按 'q' 键在监视器窗口聚焦时退出")


# 辅助函数：画监视器 UI
def draw_debug_overlay(img):
    # 1. 画大方框 (绿色) - 搜索区
    cv2.rectangle(img, (BIG_BOX[0], BIG_BOX[1]), (BIG_BOX[2], BIG_BOX[3]), (0, 255, 0), 2)
    cv2.putText(img, "SEARCH ZONE", (BIG_BOX[0], BIG_BOX[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    # 2. 画小方框 (红色) - 后退区
    cv2.rectangle(img, (SMALL_BOX[0], SMALL_BOX[1]), (SMALL_BOX[2], SMALL_BOX[3]), (0, 0, 255), 2)
    cv2.putText(img, "TOO CLOSE", (SMALL_BOX[0], SMALL_BOX[3] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    # 3. 画扇形分割线 (黄色)
    # 画横线区分远近
    cv2.line(img, (0, ZONE_Y1), (SCREEN_W, ZONE_Y1), (0, 255, 255), 1)  # 远中分界
    cv2.line(img, (0, ZONE_Y2), (SCREEN_W, ZONE_Y2), (0, 255, 255), 1)  # 中近分界
    # 画模拟扇形射线 (从底边中心发出) - 仅供视觉参考
    bottom_center = (SCREEN_W // 2, SCREEN_H - 350)
    # === 新增扇形宽度控制 ===
    # 调整这个数值：数值越小，扇形越窄；数值越大，扇形越宽。
    # 比如 400 表示在屏幕顶端，从中心点向左/右各偏 400 像素
    offset = 550
    # 左边的线：连向屏幕顶部偏左
    cv2.line(img, bottom_center, (SCREEN_W // 2 - offset, 0), (0, 255, 255), 1)
    # 右边的线：连向屏幕顶部偏右
    cv2.line(img, bottom_center, (SCREEN_W // 2 + offset, 0), (0, 255, 255), 1)
    # 标记中心线
    cv2.line(img, (SCREEN_CENTER_X, 0), (SCREEN_CENTER_X, SCREEN_H), (255, 0, 0), 1)


# 主循环
while True:
    try:
        start_time = time.time()

        # 1. 截图
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # 用于识别和画图

        # 2. 准备画图层 (复制一份干净的画面用于画框)
        debug_frame = frame_bgr.copy()
        draw_debug_overlay(debug_frame)

        # 3. AI 识别
        results = model.predict(source=frame_bgr, conf=CONF_LEVEL, verbose=False)

        target_action_taken = False  # 标记本轮是否执行了动作

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])

                if cls == 1:  # 红名怪
                    # 获取坐标
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    # --- 逻辑判断 A: 是否在大方框内? ---
                    # 如果中心点不在大方框内，直接忽略，不画线，不打
                    if not (BIG_BOX[0] < cx < BIG_BOX[2] and BIG_BOX[1] < cy < BIG_BOX[3]):
                        continue

                        # 画出识别到的怪 (黄色框)
                    cv2.rectangle(debug_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)
                    cv2.circle(debug_frame, (cx, cy), 5, (0, 0, 255), -1)

                    # --- 逻辑判断 B: 是否在小方框内 (太近)? ---
                    if SMALL_BOX[0] < cx < SMALL_BOX[2] and SMALL_BOX[1] < cy < SMALL_BOX[3]:
                        print(f"⚠️ 警告: 目标进入警戒区! 执行后退 {BACK_DURATION}秒")
                        cv2.putText(debug_frame, "BACKING UP!", (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                        # 刷新一下监视器让用户看到提示
                        small_view = cv2.resize(debug_frame, (500, 300))
                        cv2.imshow("AI Monitor", small_view)
                        cv2.waitKey(1)

                        # 执行后退
                        pyautogui.keyDown(KEY_BACK)
                        time.sleep(BACK_DURATION)
                        pyautogui.keyUp(KEY_BACK)

                        target_action_taken = True
                        break  # 后退完重新扫描

                    # --- 逻辑判断 C: 键盘扇形转向 ---
                    offset_x = cx - SCREEN_CENTER_X

                    # 如果没对准 (在死区外)
                    if abs(offset_x) > AIM_DEAD_ZONE:
                        # 1. 判断区域 (Y轴)
                        zone_factor = FACTOR_MID
                        zone_name = "MID"

                        if cy < ZONE_Y1:
                            zone_factor = FACTOR_FAR
                            zone_name = "FAR"
                        elif cy > ZONE_Y2:
                            zone_factor = FACTOR_CLOSE
                            zone_name = "CLOSE"

                        # 2. 计算按键时长
                        # 时长 = 偏差像素 * 基础系数 * 区域倍率
                        press_duration = abs(offset_x) * TIME_PER_PIXEL * zone_factor

                        # 限制一下最大按键时长，防止转圈圈 (比如最多按0.8秒)
                        press_duration = min(press_duration, 0.8)
                        # 限制一下最小按键时长，防止太短系统没反应
                        press_duration = max(press_duration, 0.05)

                        direction_key = KEY_RIGHT if offset_x > 0 else KEY_LEFT
                        dir_str = "RIGHT" if offset_x > 0 else "LEFT"

                        print(f"🔄 转向: {dir_str} | 区域: {zone_name} | 时长: {press_duration:.3f}s")

                        # 在监视器上显示转向状态
                        cv2.arrowedLine(debug_frame, (SCREEN_CENTER_X, cy), (cx, cy), (255, 0, 255), 2)

                        # 执行点击选中 (这一步很重要，不点中没法打)
                        pyautogui.moveTo(cx, cy)
                        pyautogui.rightClick()

                        # 执行键盘转向
                        pyautogui.keyDown(direction_key)
                        time.sleep(press_duration)
                        pyautogui.keyUp(direction_key)

                        target_action_taken = True
                        # 稍微等一下让画面稳定
                        time.sleep(0.2)
                        break

                    else:
                        # --- 逻辑判断 D: 已对准，攻击 ---
                        print("✅ 已对准，执行攻击！")
                        # 确保选中
                        pyautogui.moveTo(cx, cy)
                        pyautogui.rightClick()
                        time.sleep(0.1)
                        pyautogui.press(KEY_ATTACK)

                        target_action_taken = True
                        time.sleep(2.0)  # 攻击间隔
                        break

            if target_action_taken:
                break

        # 4. 显示 Mini 监视器 (放在最后)
        # 将画面缩放到 500x300
        small_view = cv2.resize(debug_frame, (500, 300))
        cv2.imshow("AI Monitor", small_view)

        # 按 q 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # 如果没找到怪，稍微休息省CPU
        if not target_action_taken:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("停止")
        break
    except Exception as e:
        print(f"错误: {e}")