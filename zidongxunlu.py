import time
import math
import pydirectinput
import keyboard
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
# 1. 地图名字数据库 (在这里添加更多地图)
MAP_DB = {
    1454: "奥格瑞玛",
    1411: "杜隆塔尔",
    1413: "贫瘠之地",
    1412: "莫高雷",
    1453: "暴风城",
    1429: "艾尔文森林",
    # 如果你去了一个新地方显示"未知"，把那个数字加到这里
}

# 2. 路径点列表
PATH_NODES = [
    (52.55, 44.82),
    (53.00, 46.00),
]

# 3. 转向逻辑修正
REVERSE_KEYS = False

# 4. 运行参数
ARRIVE_RANGE = 0.25
STOP_TURN_TOLERANCE = 15.0
TURN_TAP_TIME = 0.04
STOP_KEY = 'page down'


# ============================================

def calculate_nav(curr_x, curr_y, target_x, target_y):
    dist = math.sqrt((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2)
    angle_rad = math.atan2(-(target_x - curr_x), curr_y - target_y)
    target_deg = math.degrees(angle_rad)
    if target_deg < 0: target_deg += 360
    return dist, target_deg


def control_loop():
    print("========================================")
    print("🤖 坦克式寻路系统 (地图识别版)")
    print(f"   当前逻辑：原地转向 -> 直线行驶")
    print("========================================\n")
    time.sleep(2)

    current_node_idx = 0
    stuck_check_time = time.time()
    last_pos = (0, 0)

    while current_node_idx < len(PATH_NODES):
        if keyboard.is_pressed(STOP_KEY):
            print("\n🛑 紧急停止")
            pydirectinput.keyUp('w')
            return

        target_x, target_y = PATH_NODES[current_node_idx]

        # 获取 4 个数据
        curr_x, curr_y, curr_f_rad, map_id = get_game_data()

        if curr_x is None or curr_x == 0:
            print("👁️ 信号丢失...", end='\r')
            pydirectinput.keyUp('w')
            time.sleep(0.5);
            continue

        # --- 翻译地图名字 ---
        # 如果 ID 在字典里就显示名字，否则显示 "未知区域"
        map_name = MAP_DB.get(map_id, f"未知区域({map_id})")

        # --- 计算导航数据 ---
        dist, target_deg = calculate_nav(curr_x, curr_y, target_x, target_y)
        curr_deg = math.degrees(curr_f_rad)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180

        # --- 实时解说 (带地图名) ---
        print(f"🌍 当前区域: [{map_name}] (ID: {map_id})")
        print(f"📍 目标:[{current_node_idx + 1}] 位置:({curr_x:.2f}, {curr_y:.2f}) | 距离:{dist:.2f}m")
        print(f"🧭 导航数据: 目标:{target_deg:.1f}° | 朝向:{curr_deg:.1f}° | 偏差:{angle_diff:.1f}°")

        # --- 1. 到达判定 ---
        if dist < ARRIVE_RANGE:
            print(f"✨ 已到达目标点 {current_node_idx + 1}")
            current_node_idx += 1
            pydirectinput.keyUp('w')
            continue

        # --- 2. 核心逻辑：原地转身 vs 前进 ---
        if abs(angle_diff) > STOP_TURN_TOLERANCE:
            print(f"   ↪️ [决策] 正在原地修正镜头角度...")
            pydirectinput.keyUp('w')

            if not REVERSE_KEYS:
                turn_key = 'a' if angle_diff > 0 else 'd'
            else:
                turn_key = 'd' if angle_diff > 0 else 'a'

            pydirectinput.keyDown(turn_key)
            time.sleep(TURN_TAP_TIME)
            pydirectinput.keyUp(turn_key)
        else:
            print("   前进 [OK] 方向已对准，正在直线行进")
            pydirectinput.keyDown('w')

        # --- 3. 防卡死 ---
        if time.time() - stuck_check_time > 3.0:
            move_dist = math.sqrt((curr_x - last_pos[0]) ** 2 + (curr_y - last_pos[1]) ** 2)
            if move_dist < 0.01 and dist > ARRIVE_RANGE:
                print("   ⚠️ 检测到原地踏步，尝试跳跃...")
                pydirectinput.press('space')
            last_pos = (curr_x, curr_y)
            stuck_check_time = time.time()

        print("-" * 40)
        time.sleep(0.02)

if __name__ == "__main__":
    control_loop()