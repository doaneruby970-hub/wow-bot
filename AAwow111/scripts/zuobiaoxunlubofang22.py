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
ARRIVE_RANGE = 0.04  # 🌟 4厘米判定（稍微放大1厘米，防止跑得太顺滑直接穿过判定点）
STOP_KEY = 'page down'

OVERRIDE_PATH_FILE = None  # 外部设置此变量可强制指定路书文件（含完整路径）

# ============================================

def calculate_nav(curr_x, curr_y, target_x, target_y):
    dist = math.sqrt((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2)
    angle_rad = math.atan2(-(target_x - curr_x), curr_y - target_y)
    target_deg = math.degrees(angle_rad)
    if target_deg < 0: target_deg += 360
    return dist, target_deg


def player():
    if OVERRIDE_PATH_FILE:
        target_file = OVERRIDE_PATH_FILE if os.path.isabs(OVERRIDE_PATH_FILE) else os.path.join(PATHS_DIR, OVERRIDE_PATH_FILE)
    else:
        files = [f for f in os.listdir(PATHS_DIR) if f.endswith('.json')]
        if not files:
            print("❌ 错误：文件夹里没有录制文件！")
            return
        files.sort(reverse=True)
        target_file = os.path.join(PATHS_DIR, files[0])

    with open(target_file, 'r') as f:
        path_nodes = json.load(f)

    print("========================================")
    print(f"🏎️ 丝滑高精度寻路启动 (去QE纯享版)")
    print(f"📂 加载路径: {target_file}")
    print(f"🛑 紧急停止: [{STOP_KEY.upper()}]")
    print("========================================\n")
    time.sleep(2)

    current_node_idx = 0

    # 🌟 核心引擎：按键状态记忆库 (确保按键被“长按”而不是“点按”)
    keys_state = {'w': False, 's': False, 'a': False, 'd': False}

    def set_key(key, press):
        """ 智能按键：只有当状态改变时才执行按下/松开，实现完美的平滑移动 """
        if keys_state[key] != press:
            if press:
                pydirectinput.keyDown(key)
            else:
                pydirectinput.keyUp(key)
            keys_state[key] = press

    def release_all():
        """ 紧急刹车：松开所有按键 """
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
            release_all()  # 没信号立刻停车
            time.sleep(0.05)
            continue

        dist, target_deg = calculate_nav(curr_x, curr_y, target_x, target_y)
        curr_deg = math.degrees(curr_f_rad)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180

        # 获取正在按下的键，方便在控制台显示
        active_keys = [k.upper() for k, v in keys_state.items() if v]
        print(
            f"📍 点[{current_node_idx + 1}/{len(path_nodes)}] | 距: {dist:.3f}m | 偏: {angle_diff:.1f}° | 按键: {active_keys}     ",
            end='\r')

        # 1. 🎯 智能到达判定
        # 由于我们是长按 W 跑动，速度很快，可能会瞬间冲过点位
        # 逻辑：如果距离小于 4cm，或者 已经跑到目标前面去了(角度>90且距离<0.15m)，都算到达！
        if dist < ARRIVE_RANGE or (dist < 0.15 and abs(angle_diff) > 90):
            current_node_idx += 1
            continue

        # 2. 🔄 丝滑转向逻辑 (方向盘微调)
        if angle_diff > 4.0:
            set_key('a', True)  # 偏右了，按住 A 往左打方向
            set_key('d', False)
        elif angle_diff < -4.0:
            set_key('d', True)  # 偏左了，按住 D 往右打方向
            set_key('a', False)
        else:
            set_key('a', False)  # 角度完美（误差<4度），松开方向盘
            set_key('d', False)

        # 3. 🚀 前进与刹车逻辑 (油门控制)
        if abs(angle_diff) < 45.0:
            # 只要脸没有严重歪掉（偏差小于45度），死死按住 W 不放
            set_key('w', True)
            set_key('s', False)
        elif abs(angle_diff) > 135.0 and dist < 0.2:
            # 严重走过了，倒个车
            set_key('w', False)
            set_key('s', True)
        else:
            # 遇到急转弯（偏差45~135度），松开 W 减速，让 A/D 把头转过来再走
            set_key('w', False)
            set_key('s', False)

        # 极高频刷新（让大脑反应极快，方向盘打得极准）
        time.sleep(0.01)

    release_all()
    print("\n\n🏁 丝滑精度寻路全部完成！")


if __name__ == "__main__":
    player()