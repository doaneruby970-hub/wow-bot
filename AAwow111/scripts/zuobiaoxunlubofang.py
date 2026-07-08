import time
import math
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
import pydirectinput
import keyboard
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
PATHS_DIR = "paths"

MAP_DB = {
    1454: "奥格瑞玛",
    1411: "杜隆塔尔",
    1413: "贫瘠之地",
    1412: "莫高雷",
    1453: "暴风城",
    1429: "艾尔文森林",
}

REVERSE_KEYS = False
ARRIVE_RANGE = 0.2
STOP_TURN_TOLERANCE = 35.0
SMOOTH_TURN_LIMIT = 5.0
TURN_TAP_TIME = 0.03
STOP_KEY = 'page down'


# ============================================

OVERRIDE_PATH_FILE = None  # 外部设置此变量可强制指定路书文件名（含路径）

def load_path_by_map_id(map_id):
    import glob
    if OVERRIDE_PATH_FILE:
        filename = os.path.join(PATHS_DIR, OVERRIDE_PATH_FILE)
    else:
        matches = sorted(glob.glob(os.path.join(PATHS_DIR, f"map_{map_id}*.json")))
        if not matches:
            print(f"\n❌ 错误：找不到地图文件 paths/map_{map_id}*.json")
            return None
        filename = matches[-1]
        print(f"📂 自动匹配路书: {os.path.basename(filename)}")
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


def control_loop():
    print("========================================")
    print("📂 自动导航播放器 (丝滑防卡顿版)")
    print(f"   退出按键: [{STOP_KEY.upper()}]")
    print("========================================\n")
    time.sleep(2)

    # ... (省略之前的初始化代码，保持不变) ...
    # ... 直到 "while current_node_idx < len(path_nodes):" 之前 ...

    # 补全初始化部分，方便你直接复制
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
    # ================= 🌟 重点 1：定义状态变量 =================
    w_is_pressed = False  # 记录当前 W 键是不是按下的状态
    # ========================================================

    while current_node_idx < len(path_nodes):
        if keyboard.is_pressed(STOP_KEY):
            print("\n🛑 紧急停止")
            pydirectinput.keyUp('w')  # 退出时必须松开
            return

        target_x, target_y = path_nodes[current_node_idx]
        curr_x, curr_y, curr_f_rad, current_map_id = get_game_data()

        if curr_x is None or curr_x == 0:
            # 信号丢失时，不要松开 W，保持惯性，防止卡顿
            time.sleep(0.5)
            continue

        dist, target_deg = calculate_nav(curr_x, curr_y, target_x, target_y)
        curr_deg = math.degrees(curr_f_rad)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180

        # ... (打印状态保持不变) ...

        if dist < ARRIVE_RANGE:
            print(f"\n✨ 到达节点 {current_node_idx + 1}")
            current_node_idx += 1
            # 注意：这里千万不要松开 W，也不要改状态
            continue

        # ================= 🌟 重点 2：状态机移动逻辑 =================

        # 情况 A：需要原地转身（角度偏差太大）
        if abs(angle_diff) > STOP_TURN_TOLERANCE:
            # 只有当 W 正在按着的时候，才去松开它
            if w_is_pressed:
                pydirectinput.keyUp('w')
                w_is_pressed = False  # 更新状态：我现在没按 W

            # 转向操作 (点按一下)
            turn_key = ('d' if angle_diff > 0 else 'a') if REVERSE_KEYS else ('a' if angle_diff > 0 else 'd')
            pydirectinput.keyDown(turn_key)
            time.sleep(0.05)  # 使用代码A的时长
            pydirectinput.keyUp(turn_key)

        # 情况 B：方向正确，可以奔跑
        else:
            # 只有当 W 没按着的时候，才去按下它
            if not w_is_pressed:
                pydirectinput.keyDown('w')
                w_is_pressed = True  # 更新状态：我现在按着 W 呢

            # 小修正：角度偏差超过5°时点按A/D微调
            if abs(angle_diff) > SMOOTH_TURN_LIMIT:
                turn_key = ('d' if angle_diff > 0 else 'a') if REVERSE_KEYS else ('a' if angle_diff > 0 else 'd')
                pydirectinput.press(turn_key)

        # ==========================================================

        # 防卡死检测
        if time.time() - stuck_check_time > 2.0:
            move_dist = math.sqrt((curr_x - last_pos[0]) ** 2 + (curr_y - last_pos[1]) ** 2)
            if move_dist < 0.01 and dist > ARRIVE_RANGE:
                print("\n⚠️ 卡死检测：尝试跳跃")
                pydirectinput.press('q')
            last_pos = (curr_x, curr_y)
            stuck_check_time = time.time()

        time.sleep(0.01)  # 改为10ms，提升响应速度

    print("\n🏁 路书行程结束！")
    pydirectinput.keyUp('w')  # 最后必须松开，否则人会一直跑


if __name__ == "__main__":
    control_loop()