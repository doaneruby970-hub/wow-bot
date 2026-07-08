import pyautogui
import pydirectinput
import time
import os

# 禁用保护
pyautogui.FAILSAFE = False

def auto_click_with_offset(img_name, offset_x, offset_y):
    """
    根据基准图和偏移量进行点击
    :param img_name: 图片文件名（如 img_7.png）
    :param offset_x: X轴偏移量
    :param offset_y: Y轴偏移量
    """
    print("-" * 30)
    print(f">>> [OCR点击] 图片={img_name}, 偏移=({offset_x}, {offset_y})")

    # ================= 1. 配置 =================
    imgs_dir = r".\AAwow111\imgs"
    anchor_img = os.path.normpath(os.path.join(imgs_dir, img_name))

    OFFSET_X = offset_x
    OFFSET_Y = offset_y

    if not os.path.exists(anchor_img):
        print(f"   ❌ 错误：找不到基准图 {anchor_img}")
        return

    # ================= 2. 识别与点击 =================
    try:
        # 在屏幕中寻找“更新”按钮
        location = pyautogui.locateOnScreen(anchor_img, confidence=0.8, grayscale=True)

        if location is not None:
            # 计算锚点中心坐标
            ax = int(location.left + location.width / 2)
            ay = int(location.top + location.height / 2)
            print(f"   ✅ 找到锚点: ({ax}, {ay})")

            # 计算目标位置
            tx = ax + OFFSET_X
            ty = ay + OFFSET_Y
            print(f"   🎯 目标点击位置: ({tx}, {ty})")

            # 执行移动并点击
            pydirectinput.moveTo(tx, ty)
            time.sleep(0.1)
            pydirectinput.click()
            print("   🖱️ 点击动作已执行。")

        else:
            print("   ⌛ 未能识别到基准图标，请确认界面未被遮挡。")

    except Exception as e:
        print(f"   ⚠️ 脚本异常: {e}")

def auto_click_only():
    """兼容旧版本的无参数调用"""
    auto_click_with_offset("img_7.png", -240, -175)

if __name__ == "__main__":
    auto_click_only()