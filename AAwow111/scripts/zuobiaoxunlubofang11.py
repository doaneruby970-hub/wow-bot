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
ARRIVE_RANGE = 0.5  # 到达判定范围 (米)
STOP_TURN_TOLERANCE = 25.0  # 角度修正阈值 (度)
TURN_TAP_TIME = 0.04  # 转向微调点按时间
STOP_KEY = 'page down'  # 紧急停止键

OVERRIDE_PATH_FILE = None  # 外部设置此变量可强制指定路书文件（含完整路径）

# ============================================

def calculate_nav(curr_x, curr_y, target_x, target_y):
    """计算当前位置到目标的距离和角度"""
    dist = math.sqrt((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2)
    angle_rad = math.atan2(-(target_x - curr_x), curr_y - target_y)
    target_deg = math.degrees(angle_rad)
    if target_deg < 0: target_deg += 360
    return dist, target_deg


def player():
    # 1. 优先使用外部指定路书，否则自动找最新
    if OVERRIDE_PATH_FILE:
        target_file = OVERRIDE_PATH_FILE
    else:
        files = [f for f in os.listdir(PATHS_DIR) if f.endswith('.json')]
        if not files:
            print("❌ 错误：在 paths 文件夹下未找到任何 .json 路书文件")
            return
        files.sort(reverse=True)
        target_file = os.path.join(PATHS_DIR, files[0])

    with open(target_file, 'r') as f:
        path_nodes = json.load(f)

    print(f"========================================")
    print(f"📖 已加载路书: {target_file}")
    print(f"📍 总计节点: {len(path_nodes)}")
    print(f"🚀 状态: 准备就绪，按 [任意键] 后 2秒 开始")
    print(f"🛑 停止按键: [{STOP_KEY.upper()}]")
    print(f"========================================\n")
    time.sleep(2)

    current_node_idx = 0
    w_is_pressed = False
    stuck_check_time = time.time()
    last_dist = 9999

    while current_node_idx < len(path_nodes):
        # 监听紧急停止
        if keyboard.is_pressed(STOP_KEY):
            pydirectinput.keyUp('w')
            print("\n🛑 已人工紧急停止")
            return

        # 获取当前目标点数据 (x, y, map_id)
        target_x, target_y, target_map_id = path_nodes[current_node_idx]
        curr_x, curr_y, curr_f_rad, curr_map_id = get_game_data()

        # 实时状态前缀
        status_prefix = f"📍 [{current_node_idx + 1}/{len(path_nodes)}]"

        # --- 逻辑 A: 信号检测 ---
        if curr_x is None or curr_x == 0:
            print(f"{status_prefix} ⏳ 状态: 等待坐标信号...          ", end='\r')
            time.sleep(0.2)
            continue

        # --- 逻辑 B: 跨地图冲刺逻辑 (重点优化) ---
        if curr_map_id != target_map_id:
            # 如果当前地图还没切到目标地图，说明正处于传送门或地图边界
            if not w_is_pressed:
                pydirectinput.keyDown('w')
                w_is_pressed = True
            print(f"{status_prefix} 🏃 跨图冲刺中: {curr_map_id} -> {target_map_id} ", end='\r')
            time.sleep(0.1)
            continue

        # --- 逻辑 C: 正常导航逻辑 ---
        dist, target_deg = calculate_nav(curr_x, curr_y, target_x, target_y)
        curr_deg = math.degrees(curr_f_rad)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180

        # 打印实时仪表盘
        print(
            f"{status_prefix} 📏 距下个点: {dist:.2f}m | 🧭 偏角: {angle_diff:.1f}° | W: {'RUN' if w_is_pressed else 'STOP'}",
            end='\r')

        # 1. 到达判定
        if dist < ARRIVE_RANGE:
            print(f"\n✅ 成功到达节点 {current_node_idx + 1}")
            current_node_idx += 1
            stuck_check_time = time.time()  # 到达后重置防卡死计时
            last_dist = 9999
            continue

        # 2. 转向逻辑
        if abs(angle_diff) > STOP_TURN_TOLERANCE:
            # 角度偏离太大，松开W原地转向，避免跑偏
            if w_is_pressed:
                pydirectinput.keyUp('w')
                w_is_pressed = False

            turn_key = 'a' if angle_diff > 0 else 'd'
            pydirectinput.keyDown(turn_key)
            time.sleep(TURN_TAP_TIME)
            pydirectinput.keyUp(turn_key)
        else:
            # 角度正确，确保 W 按下
            if not w_is_pressed:
                pydirectinput.keyDown('w')
                w_is_pressed = True

        # 3. 防卡死检测
        if time.time() - stuck_check_time > 3.0:
            # 3秒内距离目标点变化不足 0.05米，判定为卡住
            if abs(last_dist - dist) < 0.05:
                print(f"\n⚠️ 检测到阻挡，尝试跳跃...")
                pydirectinput.press('q')
            stuck_check_time = time.time()
            last_dist = dist

        time.sleep(0.01)

    # 运行结束
    pydirectinput.keyUp('w')
    print("\n" + "=" * 40)
    print("🏁 跨图行程已圆满完成！")
    print("=" * 40)


if __name__ == "__main__":
    player()