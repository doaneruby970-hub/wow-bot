import time
import math
import json
import os
import pydirectinput
import keyboard
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
PATHS_DIR = "paths_precision"
ARRIVE_RANGE = 0.04  # 🌟 4厘米判定
STOP_KEY = 'page down'


# ============================================

def calculate_nav(curr_x, curr_y, target_x, target_y):
    dist = math.sqrt((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2)
    angle_rad = math.atan2(-(target_x - curr_x), curr_y - target_y)
    target_deg = math.degrees(angle_rad)
    if target_deg < 0: target_deg += 360
    return dist, target_deg


def player():
    # --- 🟢 新增：启动菜单逻辑 ---
    if not os.path.exists(PATHS_DIR):
        print(f"❌ 错误：找不到文件夹 {PATHS_DIR}")
        return

    files = [f for f in os.listdir(PATHS_DIR) if f.endswith('.json')]
    if not files:
        print("❌ 错误：文件夹里没有录制文件！")
        return

    # 按字母顺序排序，方便观察
    files.sort()

    print("\n" + "=" * 30)
    print("📂 请选择要运行的路径文件:")
    for i, f in enumerate(files):
        print(f"  [{i}] {f}")
    print("=" * 30)

    try:
        choice = input(f"👉 输入编号 (0-{len(files) - 1}) 并回车: ")
        # 如果直接按回车，默认选第0个
        idx = int(choice) if choice.strip() != "" else 0
        if not (0 <= idx < len(files)):
            print("❌ 错误：编号超出范围！")
            return
    except ValueError:
        print("❌ 错误：请输入有效的数字！")
        return

    target_file = os.path.join(PATHS_DIR, files[idx])
    # ---------------------------

    with open(target_file, 'r') as f:
        path_nodes = json.load(f)

    print("\n========================================")
    print(f"🏎️ 丝滑高精度寻路启动 (去QE纯享版)")
    print(f"📂 已加载: {files[idx]}")
    print(f"🛑 紧急停止: [{STOP_KEY.upper()}]")
    print("========================================\n")
    time.sleep(2)

    current_node_idx = 0
    keys_state = {'w': False, 's': False, 'a': False, 'd': False}

    def set_key(key, press):
        if keys_state[key] != press:
            if press:
                pydirectinput.keyDown(key)
            else:
                pydirectinput.keyUp(key)
            keys_state[key] = press

    def release_all():
        for k in keys_state:
            set_key(k, False)

    while current_node_idx < len(path_nodes):
        if keyboard.is_pressed(STOP_KEY):
            release_all()
            print("\n🛑 用户强制停止！所有按键已松开。")
            return

        node_data = path_nodes[current_node_idx]
        target_x = node_data[0]
        target_y = node_data[1]

        curr_x, curr_y, curr_f_rad, _ = get_game_data()

        if curr_x is None or curr_x == 0:
            release_all()
            time.sleep(0.05)
            continue

        dist, target_deg = calculate_nav(curr_x, curr_y, target_x, target_y)
        curr_deg = math.degrees(curr_f_rad)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180

        active_keys = [k.upper() for k, v in keys_state.items() if v]
        print(
            f"📍 点[{current_node_idx + 1}/{len(path_nodes)}] | 距: {dist:.3f}m | 偏: {angle_diff:.1f}° | 按键: {active_keys}     ",
            end='\r')

        if dist < ARRIVE_RANGE or (dist < 0.15 and abs(angle_diff) > 90):
            current_node_idx += 1
            continue

        # 丝滑转向
        if angle_diff > 4.0:
            set_key('a', True);
            set_key('d', False)
        elif angle_diff < -4.0:
            set_key('d', True);
            set_key('a', False)
        else:
            set_key('a', False);
            set_key('d', False)

        # 前进逻辑
        if abs(angle_diff) < 45.0:
            set_key('w', True);
            set_key('s', False)
        elif abs(angle_diff) > 135.0 and dist < 0.2:
            set_key('w', False);
            set_key('s', True)
        else:
            set_key('w', False);
            set_key('s', False)

        time.sleep(0.01)

    release_all()
    print("\n\n🏁 丝滑精度寻路全部完成！")


if __name__ == "__main__":
    player()