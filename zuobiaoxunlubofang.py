import time
import math
import json
import os
import pydirectinput
import keyboard
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
PATHS_DIR = "paths"
ARRIVE_RANGE = 0.2  # 到达判定距离
STOP_TURN_TOLERANCE = 35.0  # 超过这个角度才停下转身 (大转弯)
SMOOTH_TURN_LIMIT = 5.0  # 超过这个角度就点按 A/D (小修正)
TURN_TAP_TIME = 0.03  # 转向点按时长
STOP_KEY = 'page down'
# 原有的 TARGET_PATH_FILE 已移除，改为动态选择
# ============================================

def select_path_file():
    """在启动时列出菜单并返回选中的文件名"""
    if not os.path.exists(PATHS_DIR):
        print(f"❌ 错误：找不到文件夹 [{PATHS_DIR}]")
        return None

    files = [f for f in os.listdir(PATHS_DIR) if f.endswith('.json')]
    if not files:
        print(f"❌ 错误：在 {PATHS_DIR} 文件夹下没有找到 .json 文件")
        return None

    files.sort()  # 字母顺序排序

    print("\n" + "="*40)
    print("📂 请选择要执行的路书文件:")
    for i, f in enumerate(files):
        print(f"  [{i}] {f}")
    print("="*40)

    try:
        choice = input(f"👉 请输入编号 (0-{len(files)-1}) [默认0]: ").strip()
        idx = int(choice) if choice != "" else 0
        if 0 <= idx < len(files):
            return files[idx]
        else:
            print("❌ 编号超出范围")
            return None
    except ValueError:
        print("❌ 输入无效，必须是数字")
        return None

def load_specific_path(filename):
    """根据文件名加载路径数据"""
    full_path = os.path.join(PATHS_DIR, filename)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取出错: {e}")
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
    # --- 🟢 第一步：启动时先选文件 ---
    selected_file = select_path_file()
    if not selected_file:
        return

    # 加载数据
    path_nodes = load_specific_path(selected_file)
    if not path_nodes:
        return

    print(f"\n✅ 已加载: {selected_file}")
    print("========================================")
    print("🚀 自动导航启动 (按 [PAGE DOWN] 停止)")
    print("========================================\n")

    # --- 第二步：初始定位 (等待坐标信号) ---
    while True:
        if keyboard.is_pressed(STOP_KEY): return
        curr_x, curr_y, _, _ = get_game_data() # 解包 map_id
        if curr_x and curr_x > 0: break
        print("⏳ 等待游戏坐标信号...", end='\r')
        time.sleep(0.5)

    current_node_idx = find_nearest_node_index(curr_x, curr_y, path_nodes)
    print(f"📍 起始节点: {current_node_idx}, 总节点: {len(path_nodes)}")

    # 状态变量
    w_is_pressed = False
    stuck_check_time = time.time()
    last_pos = (curr_x, curr_y)

    # 主循环 (保持原有的转向逻辑不变)
    while current_node_idx < len(path_nodes):
        if keyboard.is_pressed(STOP_KEY):
            pydirectinput.keyUp('w')
            print("\n🛑 已手动停止")
            return

        node = path_nodes[current_node_idx]
        target_x, target_y = node[0], node[1]

        curr_x, curr_y, curr_f_rad, curr_map_id = get_game_data()

        if curr_x is None or curr_x == 0:
            time.sleep(0.1)
            continue

        dist, target_deg = calculate_nav(curr_x, curr_y, target_x, target_y)
        curr_deg = math.degrees(curr_f_rad)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180

        # --- 原有逻辑：转向与移动 ---
        if abs(angle_diff) > STOP_TURN_TOLERANCE:
            if w_is_pressed:
                pydirectinput.keyUp('w')
                w_is_pressed = False
            turn_key = 'a' if angle_diff > 0 else 'd'
            pydirectinput.keyDown(turn_key)
            time.sleep(0.05)
            pydirectinput.keyUp(turn_key)
        else:
            if not w_is_pressed:
                pydirectinput.keyDown('w')
                w_is_pressed = True
            if abs(angle_diff) > SMOOTH_TURN_LIMIT:
                turn_key = 'a' if angle_diff > 0 else 'd'
                pydirectinput.press(turn_key)

        # --- 原有逻辑：到达判定 ---
        if dist < ARRIVE_RANGE:
            current_node_idx += 1
            print(f"✅ 节点 {current_node_idx}/{len(path_nodes)} OK", end='\r')

        # --- 原有逻辑：防卡死检测 ---
        if time.time() - stuck_check_time > 2.0:
            if math.sqrt((curr_x - last_pos[0]) ** 2 + (curr_y - last_pos[1]) ** 2) < 0.01:
                pydirectinput.press('q')
            last_pos = (curr_x, curr_y)
            stuck_check_time = time.time()

        time.sleep(0.01)

    pydirectinput.keyUp('w')
    print("\n🏁 到达终点！")

if __name__ == "__main__":
    control_loop()