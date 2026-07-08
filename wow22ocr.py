import pyautogui
import pydirectinput
import time
import os
import cv2
import numpy as np

# 禁用保护
pyautogui.FAILSAFE = False


def draw_marker_on_frame(frame, pos, color=(255, 255, 0)):
    """
    直接用代码在图像上画一个青色加号标记
    """
    x, y = pos
    size = 20  # 加号的大小
    thickness = 3  # 线条粗细

    # 画横线
    cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
    # 画竖线
    cv2.line(frame, (x, y - size), (x, y + size), color, thickness)
    return frame


def auto_click_and_draw():
    print("-" * 30)
    print(">>> [覆盖模式] 启动 (720p 优化)...")

    # ================= 1. 配置 =================
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 你提供的识别基准图
    anchor_img = os.path.normpath(os.path.join(current_dir, "imgs", "img_AGfeixingditu.png"))

    # 720p 偏移量
    OFFSET_X = -65
    OFFSET_Y = -60

    if not os.path.exists(anchor_img):
        print(f"   ❌ 错误：找不到基准图 {anchor_img}")
        return

    # ================= 2. 识别与点击 =================
    try:
        # 在屏幕中寻找“更新”按钮
        location = pyautogui.locateOnScreen(anchor_img, confidence=0.8, grayscale=True)

        if location is not None:
            # 计算锚点（更新按钮）中心
            ax = int(location.left + location.width / 2)
            ay = int(location.top + location.height / 2)
            print(f"   ✅ 找到锚点: ({ax}, {ay})")

            # 计算目标（商品框）位置
            tx = ax + OFFSET_X
            ty = ay + OFFSET_Y
            print(f"   🎯 目标点击位置: ({tx}, {ty})")

            # 执行点击
            pydirectinput.moveTo(tx, ty)
            time.sleep(0.1)
            pydirectinput.click()
            print("   🖱️ 点击动作已执行。")

            # ================= 3. 截图并覆盖旧图 =================
            time.sleep(0.5)  # 等待点击反馈
            screenshot = pyautogui.screenshot()
            # 转换为 OpenCV 格式 (BGR)
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 在图上画出识别到的位置和点击的位置 (青色加号)
            frame = draw_marker_on_frame(frame, (ax, ay), color=(255, 255, 0))  # 锚点标记
            frame = draw_marker_on_frame(frame, (tx, ty), color=(255, 255, 0))  # 目标标记

            # 【修改点】使用固定文件名，实现每次运行自动覆盖
            save_path = os.path.join(current_dir, "last_debug_result.png")
            cv2.imwrite(save_path, frame)
            print(f"   📸 反馈截图已更新(已覆盖): {save_path}")

        else:
            print("   ⌛ 未能识别到基准图标，请确认界面未被遮挡。")

    except Exception as e:
        print(f"   ⚠️ 脚本异常: {e}")


if __name__ == "__main__":
    auto_click_and_draw()