import time
import json
import math
import os
import keyboard
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
MIN_MOVE_DIST = 0.05  # 精度录制：每走 5 厘米就记录一个点 (极为密集)
SAVE_DIR = "paths_precision" # 独立文件夹，不与普通路书混淆
# ============================================

def calculate_dist(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def recorder():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    print("========================================")
    print("🔬 高精度录制器 (窄门/飞艇专用)")
    print("   建议: 请用点按 W 的方式慢速走过危险区域")
    print("   操作: 按 [Q] 保存并退出")
    print("========================================\n")

    path_points = []
    last_pos = None

    while True:
        if keyboard.is_pressed('q'):
            break

        x, y, f_rad, map_id = get_game_data()

        if x is None or x == 0:
            time.sleep(0.1)
            continue

        current_pos = (x, y)

        should_record = False
        if last_pos is None:
            should_record = True
        else:
            dist = calculate_dist(current_pos, last_pos)
            if dist >= MIN_MOVE_DIST:
                should_record = True

        if should_record:
            # 🌟 重点：不仅存 x,y,地图，还存了 f_rad (朝向)
            path_points.append([x, y, map_id, f_rad])
            last_pos = current_pos
            print(f"📍 精度点 {len(path_points)} | 坐标: ({x:.2f}, {y:.2f}) | 朝向: {math.degrees(f_rad):.1f}°")

        time.sleep(0.01) # 极高频扫描

    if len(path_points) > 0:
        timestamp = time.strftime("%m%d_%H%M%S")
        filename = f"{SAVE_DIR}/precision_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(path_points, f)
        print(f"\n✅ 高精度路书已保存: {filename}")
    else:
        print("\n❌ 未记录任何点")

if __name__ == "__main__":
    recorder()