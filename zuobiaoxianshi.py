import time
import math
import win32gui
import win32con
import ctypes
from PIL import ImageGrab

# ================= 配置区 =================
WINDOW_TITLE = "魔兽世界"

# 地图名称数据库 (可以在这里手动增加)
MAP_DB = {
    1454: "奥格瑞玛",
    1411: "杜隆塔尔",
    1413: "贫瘠之地",
    1412: "莫高雷",
    1453: "暴风城",
    1429: "艾尔文森林",
    1417: "阿瑞斯高地",
}

# 强制开启高 DPI 识别（关键：防止缩放导致坐标偏移）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()


# =========================================

def get_game_center():
    """ 定位窗口顶部的像素条中心 """
    try:
        hwnd = win32gui.FindWindow(None, WINDOW_TITLE)
        if not hwnd or win32gui.IsIconic(hwnd):
            return None, None, 0

        # 获取客户区起始点（不含标题栏和边框）
        client_point = win32gui.ClientToScreen(hwnd, (0, 0))
        # 获取客户区宽度
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        width = right - left

        # 瞄准最上方中间：cx是宽度一半，cy是下移10像素(方块中心)
        cx = client_point[0] + (width // 2)
        cy = client_point[1] + 10

        return cx, cy, width
    except:
        return None, None, 0


def get_game_data(save_debug=False):
    """ 读取4个像素色块并解码 """
    cx, cy, width = get_game_center()
    if cx is None:
        return None, None, None, None

    # 抓取顶部 80x20 区域
    bbox = (cx - 40, cy - 10, cx + 40, cy + 10)

    try:
        img = ImageGrab.grab(bbox=bbox)

        if save_debug:
            img.save("debug_top.png")
            print(f"📸 诊断：已生成 debug_top.png，请检查截图是否对准了四个色块")

        # 采样点 (10, 30, 50, 70)
        pix_x = img.getpixel((10, 10))
        pix_y = img.getpixel((30, 10))
        pix_f = img.getpixel((50, 10))
        pix_m = img.getpixel((70, 10))

        # 解码 X/Y
        real_x = pix_x[0] + (pix_x[1] / 100.0)
        real_y = pix_y[0] + (pix_y[1] / 100.0)

        # 解码 朝向
        face_raw = pix_f[0] + (pix_f[1] / 100.0)
        real_face_rad = (face_raw / 100.0) * 6.283185

        # 解码 MapID
        map_id = pix_m[0] * 256 + pix_m[1]

        # 判定：全黑说明没读到
        if real_x == 0 and real_y == 0:
            return 0, 0, 0, 0

        return real_x, real_y, real_face_rad, map_id
    except:
        return None, None, None, None


def main():
    print("========================================")
    print("   魔兽世界全能追踪器 (置顶适配版)   ")
    print("========================================")

    # 第一次运行保存诊断图
    time.sleep(1)
    get_game_data(save_debug=True)

    print("\n>>> 开始实时数据追踪：")

    try:
        while True:
            # 获取 4 个核心数据
            x, y, face_rad, map_id = get_game_data()

            if x is None:
                print("❌ [错误] 找不到游戏窗口，请确认游戏已运行。")
            elif x == 0 and y == 0:
                print("⚠️ [警告] 信号丢失，屏幕顶部中间未见色块条。")
            else:
                # 弧度转角度
                face_deg = math.degrees(face_rad)

                # 翻译地图名
                area_name = MAP_DB.get(map_id, f"未知区域({map_id})")

                # 直接打印，不再使用 \r，确保 PyCharm 每一秒都会换行显示
                print(f"🌍 地图: {area_name:<8} | 坐标: ({x:>5.2f}, {y:>5.2f}) | 朝向: {face_deg:>5.1f}°")

            # 设置频率为每秒 5 次，既实时又不占CPU
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n\n✅ 监控已停止。")


if __name__ == "__main__":
    main()