import time
import json
import math
import os
import keyboard
# 引用你的坐标读取模块
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
# 1. 时间间隔 (秒)
TIME_INTERVAL = 1

# 2. 最小移动距离 (米)
MIN_MOVE_DIST = 0.1

SAVE_DIR = "paths"
# ============================================

def calculate_dist(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def recorder():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    print("========================================")
    print("⏱️ 时间密度录制器 (高精度版)")
    print(f"   策略: 每 {TIME_INTERVAL} 秒记录一次坐标")
    print(f"   过滤: 原地不动时不记录")
    print("   操作: 按 [Q] 保存并退出")
    print("========================================\n")

    path_points = []
    last_pos = None
    current_map_id = 0

    # 记录上一次保存的时间
    last_record_time = time.time()

    while True:
        if keyboard.is_pressed('q'):
            break

        x, y, _, map_id = get_game_data()

        if x is None or x == 0:
            print("等待信号...", end='\r')
            time.sleep(0.1)
            continue

        if map_id and map_id > 0:
            current_map_id = map_id

        current_pos = (x, y)
        current_time = time.time()

        # --- 核心逻辑：时间到了吗？ ---
        # 1. 检查时间间隔
        if current_time - last_record_time >= TIME_INTERVAL:
            should_record = False

            # 2. 检查是否真的移动了 (防原地堆积)
            if last_pos is None:
                should_record = True  # 第一个点必记
            else:
                dist = calculate_dist(current_pos, last_pos)
                if dist > MIN_MOVE_DIST:
                    should_record = True

            # 3. 执行记录
            if should_record:
                path_points.append(current_pos)
                last_pos = current_pos
                last_record_time = current_time  # 重置计时器
                print(f"📍 [{len(path_points)}] ⏱️ -> ({x:.2f}, {y:.2f})")

        # 循环稍微快一点，保证时间捕捉准确
        time.sleep(0.02)

    # 保存文件
    if len(path_points) > 0:
        filename = f"{SAVE_DIR}/map_{current_map_id}.json"
        with open(filename, 'w') as f:
            json.dump(path_points, f)
        print(f"\n💾 路书已保存: {filename}")
        print(f"   共 {len(path_points)} 个高密度点")
    else:
        print("\n❌ 未记录任何点")

if __name__ == "__main__":
    recorder()