import pyautogui
import time
import ctypes
from PIL import ImageDraw, ImageFont

# 强制高分屏适配
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

BLOCK_SIZE = 20


def find_anchor():
    print("🔍 正在扫描粉色锚点...")
    screen = pyautogui.screenshot()
    w, h = screen.size

    for y in range(0, 600, 5):
        row_pixels = []
        for x in range(0, w):
            r, g, b = screen.getpixel((x, y))
            if abs(r - 255) < 10 and abs(g - 0) < 10 and abs(b - 255) < 10:
                row_pixels.append(x)

        if len(row_pixels) > 10:
            true_center_x = (row_pixels[0] + row_pixels[-1]) // 2
            true_center_y = y + (BLOCK_SIZE // 2)
            return true_center_x, true_center_y
    return None, None


def analyze_blocks():
    ax, ay = find_anchor()
    if not ax:
        print("❌ 未找到锚点！无法诊断。")
        return

    print(f"✅ 锚点中心: ({ax}, {ay})")

    # 截取 8 个格子的长度
    left = ax - (BLOCK_SIZE // 2)
    top = ay - (BLOCK_SIZE // 2)
    img = pyautogui.screenshot(region=(left, top, BLOCK_SIZE * 9, BLOCK_SIZE))  # 截长一点

    # 在图片上标记读取点
    draw = ImageDraw.Draw(img)

    print("\n====== 【原始颜色数据分析】 ======")
    print("索引 | 预期内容      | 读取坐标(相对) | 读取到的颜色(R,G,B) | 原始数值")
    print("-" * 70)

    for i in range(8):
        # 计算采样点
        cx = i * BLOCK_SIZE + (BLOCK_SIZE // 2)
        cy = BLOCK_SIZE // 2

        # 获取颜色
        r, g, b = img.getpixel((cx, cy))

        # 标记图片
        draw.line((cx - 2, cy, cx + 2, cy), fill="cyan", width=1)
        draw.line((cx, cy - 2, cx, cy + 2), fill="cyan", width=1)

        # 推测含义
        desc = ""
        if i == 0:
            desc = "锚点(粉)"
        elif i == 1:
            desc = "HP高位"
        elif i == 2:
            desc = "HP低位"
        elif i == 3:
            desc = "MP高位"
        elif i == 4:
            desc = "MP低位"
        elif i == 5:
            desc = "目标HP"
        elif i == 6:
            desc = "目标Lv"
        elif i == 7:
            desc = "状态"

        print(f"[{i}]  | {desc:<10} | ({cx}, {cy})      | ({r:>3}, {g:>3}, {b:>3})       | R={r}")

    img.save("debug_final.png")
    print("-" * 70)
    print("📸 已保存诊断图: debug_final.png")
    print("请把上面表格里的数据发给我，或者截图发给我！")


if __name__ == "__main__":
    analyze_blocks()
    input("\n按回车键退出...")