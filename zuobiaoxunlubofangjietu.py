import time
import math
import json
import os
import sys
import pydirectinput
import keyboard
import mss  # 新增：高性能截图
import mss.tools
from datetime import datetime
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
PATHS_DIR = "paths"


# 获取当前脚本所在的文件夹路径 (不要再手动输入 E:\... 了)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 自动拼接路径：它会自动找到当前项目下的 datasets/train/val
SCREENSHOT_SAVE_PATH = os.path.join(BASE_DIR, "datasets", "train", "val")

# 打印一下，让你亲眼看到图片到底存哪了
print(f"🚀 系统确定图片保存路径为: {SCREENSHOT_SAVE_PATH}")
# ============================================
# 新增：截图间隔（秒）
SCREENSHOT_INTERVAL = 1

MAP_DB = {
    1454: "奥格瑞玛",
    1411: "杜隆塔尔",
    1413: "贫瘠之地",
    1412: "莫高雷",
    1453: "暴风城",
    1429: "艾尔文森林",
}

REVERSE_KEYS = False
ARRIVE_RANGE = 0.3
STOP_TURN_TOLERANCE = 30.0
TURN_TAP_TIME = 0.04
STOP_KEY = 'page down'


# ============================================

def load_path_by_map_id(map_id):
    filename = os.path.join(PATHS_DIR, f"map_{map_id}.json")
    if not os.path.exists(filename):
        print(f"\n❌ 错误：找不到地图文件 {filename}")
        return None
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取文件出错: {e}")
        return None


def find_nearest_node_index(curr_x, curr_y, path_nodes):
    min_dist = 999999
    nearest_idx = 0
    for i, node in enumerate(path_nodes):
        dist = math.sqrt((node[0] - curr_x) ** 2 + (node[1] - curr_y) ** 2)
        if dist < min_dist:
            min_dist = dist
            nearest_idx = i
    return nearest_idx


def calculate_nav(curr_x, curr_y, target_x, target_y):
    dist = math.sqrt((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2)
    angle_rad = math.atan2(-(target_x - curr_x), curr_y - target_y)
    target_deg = math.degrees(angle_rad)
    if target_deg < 0: target_deg += 360
    return dist, target_deg


# 新增：执行截图的函数
def take_screenshot(sct, monitor, count):
    if not os.path.exists(SCREENSHOT_SAVE_PATH):
        os.makedirs(SCREENSHOT_SAVE_PATH)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wow_auto_{timestamp}_{count}.jpg"
    file_path = os.path.join(SCREENSHOT_SAVE_PATH, filename)

    sct_img = sct.grab(monitor)
    mss.tools.to_png(sct_img.rgb, sct_img.size, output=file_path)
    return filename


def control_loop():
    print("========================================")
    print("📂 自动导航播放器 + AI数据集自动采集")
    print(f"   退出按键: [{STOP_KEY.upper()}]")
    print(f"   截图间隔: {SCREENSHOT_INTERVAL}秒")
    print("========================================\n")

    # 初始化截图工具
    sct = mss.mss()
    monitor = sct.monitors[1]  # 默认截取主屏幕
    last_screenshot_time = time.time()
    screenshot_count = 0

    time.sleep(2)

    while True:
        if keyboard.is_pressed(STOP_KEY): return
        curr_x, curr_y, _, map_id = get_game_data()
        if curr_x and curr_x > 0 and map_id > 0: break
        time.sleep(0.5)

    target_map_id = map_id
    path_nodes = load_path_by_map_id(target_map_id)
    if not path_nodes: return
    current_node_idx = find_nearest_node_index(curr_x, curr_y, path_nodes)

    stuck_check_time = time.time()
    last_pos = (0, 0)
    w_is_pressed = False

    while current_node_idx < len(path_nodes):
        if keyboard.is_pressed(STOP_KEY):
            print("\n🛑 紧急停止")
            pydirectinput.keyUp('w')
            return

        target_x, target_y = path_nodes[current_node_idx]
        curr_x, curr_y, curr_f_rad, current_map_id = get_game_data()

        if current_map_id != target_map_id and current_map_id != 0:
            pydirectinput.keyUp('w')
            print("\n🗺️ 检测到地图切换，停止导航")
            return

        if curr_x is None or curr_x == 0:
            time.sleep(0.5)
            continue

        dist, target_deg = calculate_nav(curr_x, curr_y, target_x, target_y)
        curr_deg = math.degrees(curr_f_rad)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180

        # === 智能到达判定 ===
        is_last_point = (current_node_idx == len(path_nodes) - 1)
        required_dist = 0.1 if is_last_point else ARRIVE_RANGE

        if dist < required_dist:
            print(f"✨ 到达节点 {current_node_idx + 1}/{len(path_nodes)}")
            current_node_idx += 1
            continue

        # ================= 状态机移动逻辑 =================
        if abs(angle_diff) > STOP_TURN_TOLERANCE:
            if w_is_pressed:
                pydirectinput.keyUp('w')
                w_is_pressed = False
                print("   🛑 [转身] 修正方向...")

            turn_key = ('d' if angle_diff > 0 else 'a') if REVERSE_KEYS else ('a' if angle_diff > 0 else 'd')
            pydirectinput.keyDown(turn_key)
            time.sleep(TURN_TAP_TIME)
            pydirectinput.keyUp(turn_key)
        else:
            if not w_is_pressed:
                pydirectinput.keyDown('w')
                w_is_pressed = True
                print("   🏃 [奔跑] 正在采集训练素材...")

        # ================= 🌟 新增：自动截图逻辑 =================
        # 只有在跑动过程中才截图，避免在原地转弯或卡住时截取重复画面
        if w_is_pressed and (time.time() - last_screenshot_time > SCREENSHOT_INTERVAL):
            fname = take_screenshot(sct, monitor, screenshot_count)
            print(f"📸 自动捕获素材: {fname}")
            last_screenshot_time = time.time()
            screenshot_count += 1

        # 防卡死
        if time.time() - stuck_check_time > 3.0:
            move_dist = math.sqrt((curr_x - last_pos[0]) ** 2 + (curr_y - last_pos[1]) ** 2)
            if move_dist < 0.02 and dist > ARRIVE_RANGE:
                print("⚠️ 检测到障碍，尝试跳跃")
                pydirectinput.press('space')
            last_pos = (curr_x, curr_y)
            stuck_check_time = time.time()

        time.sleep(0.01)  # 略微加快循环频率，响应更灵敏

    print("\n🏁 导航结束，模型素材已保存！")
    pydirectinput.keyUp('w')


if __name__ == "__main__":
    control_loop()