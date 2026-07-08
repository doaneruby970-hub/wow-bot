import time
import json
import math
import os
import keyboard
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
TIME_INTERVAL = 1
MIN_MOVE_DIST = 0.2  # 稍微调大一点，减少冗余
SAVE_DIR = "paths"
# ============================================

def calculate_dist(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def recorder():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    print("========================================")
    print("🚀 跨地图高精度录制器")
    print("   说明: 自动记录坐标及所属地图ID")
    print("   操作: 按 [Q] 保存并退出")
    print("========================================\n")

    path_points = [] # 存储格式: [[x, y, map_id], ...]
    last_pos = None
    last_record_time = time.time()

    while True:
        if keyboard.is_pressed('q'):
            break

        x, y, _, map_id = get_game_data()

        # 过滤无效信号
        if x is None or x == 0 or map_id is None or map_id == 0:
            print("⏳ 等待地图信号...", end='\r')
            time.sleep(0.2)
            continue

        current_pos = (x, y)
        current_time = time.time()

        # 检查时间间隔
        if current_time - last_record_time >= TIME_INTERVAL:
            should_record = False

            if last_pos is None:
                should_record = True
            else:
                dist = calculate_dist(current_pos, last_pos)
                if dist > MIN_MOVE_DIST:
                    should_record = True

            if should_record:
                # 🌟 核心改动：把 map_id 存进去
                path_points.append([x, y, map_id])
                last_pos = current_pos
                last_record_time = current_time
                print(f"📍 点 {len(path_points)} | 地图: {map_id} | 坐标: ({x:.2f}, {y:.2f})")

        time.sleep(0.05)

    if len(path_points) > 0:
        # 使用时间戳命名，防止覆盖
        timestamp = time.strftime("%m%d_%H%M")
        filename = f"{SAVE_DIR}/path_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(path_points, f)
        print(f"\n✅ 跨图路书已保存: {filename}")
    else:
        print("\n❌ 未记录有效数据")

if __name__ == "__main__":
    recorder()