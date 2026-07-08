import pyautogui
import time
import ctypes
from PIL import ImageDraw

# 1. 开启高分屏支持
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

ESTIMATED_BLOCK_SIZE = 20


def find_anchor_and_width():
    print("🔍 正在扫描顶部锚点...")
    screen = pyautogui.screenshot()
    w, h = screen.size

    for y in range(0, 300, 5):
        row_pixels = []
        for x in range(0, w):
            r, g, b = screen.getpixel((x, y))
            if abs(r - 255) < 10 and abs(g - 0) < 10 and abs(b - 255) < 10:
                row_pixels.append(x)

        if len(row_pixels) > 5:
            min_x = row_pixels[0]
            max_x = row_pixels[-1]
            real_width = max_x - min_x

            center_x = (min_x + max_x) // 2
            center_y = y + (ESTIMATED_BLOCK_SIZE // 2)

            print(f"📏 实测步长: {real_width} px (中心 X={center_x}, Y={center_y})")
            return center_x, center_y, real_width

    return None, None, None


def read_data(ax, ay, block_w, save_debug=False):
    top_raw = ay - (block_w // 2) - 10
    top = max(0, top_raw)
    left = ax - (block_w // 2) - 10

    # 截图范围足够宽 (block_w * 16)，包含 11 个格子完全没问题
    img = pyautogui.screenshot(region=(left, top, block_w * 16, block_w * 3))

    debug_img = None
    draw = None
    if save_debug:
        debug_img = img.copy()
        draw = ImageDraw.Draw(debug_img)

    def get_color(i):
        target_screen_x = ax + (i * block_w)
        dynamic_offset = int(i * 0.5)
        target_screen_x += dynamic_offset

        local_x = target_screen_x - left
        local_y = ay - top

        if local_x >= img.width: local_x = img.width - 1
        if local_x < 0: local_x = 0
        if local_y >= img.height: local_y = img.height - 1

        if save_debug and draw:
            lx, ly = int(local_x), int(local_y)
            draw.line((lx - 3, ly, lx + 3, ly), fill="cyan", width=2)
            draw.line((lx, ly - 3, lx, ly + 3), fill="cyan", width=2)

        return img.getpixel((int(local_x), int(local_y)))

    d = {}

    d['hp'] = get_color(1)[0] * 256 + get_color(2)[0]
    d['mp'] = get_color(3)[0] * 256 + get_color(4)[0]
    d['t_hp_pct'] = get_color(5)[0]
    d['p_lvl'] = get_color(6)[0]

    c8 = get_color(7)
    d['combat'] = (c8[0] > 0)
    d['enemy'] = (c8[1] > 0)
    d['dead'] = (c8[2] > 0)

    d['has_target'] = d['enemy'] or (d['t_hp_pct'] > 0) or d['dead']
    d['p_hp_pct'] = get_color(8)[0]
    d['distance'] = get_color(9)[0]

    # 【新增读取】自身蓝量百分比 (第11格，索引为10)
    d['p_mp_pct'] = get_color(10)[0]

    if save_debug:
        filename = "debug_top.png"
        debug_img.save(filename)
        print(f"📸 已生成视觉校准图: {filename} (请检查青色十字是否覆盖了全部11个格子)")

    return d


def main():
    print(">>> 视觉校准版启动 (支持11格监控)...")
    ax, ay, real_w = find_anchor_and_width()

    if not ax:
        print("❌ 未找到锚点！请确保游戏内色块未被遮挡。")
        return

    if real_w < 10: real_w = 20

    print(f"✅ 锁定锚点: ({ax}, {ay}) | 步长: {real_w}")

    print("📸 正在生成校准图片...")
    read_data(ax, ay, real_w, save_debug=True)

    try:
        while True:
            d = read_data(ax, ay, real_w, save_debug=False)

            status = "⚔️战斗中" if d['combat'] else "✅安全"
            print("-" * 50)
            # 【输出修改】现在会同时打印出 HP百分比 和 MP百分比
            print(f"我: Lv.{d['p_lvl']} | HP {d['hp']} ({d['p_hp_pct']}%) | MP {d['mp']} ({d['p_mp_pct']}%) | {status}")

            if d['has_target']:
                dead_status = "(已死亡)" if d['dead'] else ""
                print(f"敌: HP {d['t_hp_pct']}% {dead_status} | 📏距离: {d['distance']} 码")
            else:
                print("敌: 无目标")

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n已停止监控。")


if __name__ == "__main__":
    main()