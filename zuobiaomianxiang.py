import time
import json
import math
import os
import keyboard
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
SAVE_DIR = "paths"
RECORD_KEY = 'e'  # 按下 E 键记录当前位置和面向
QUIT_KEY = 'q'  # 按下 Q 键保存并退出


# ============================================

def recorder():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    print("========================================")
    print("🎯 定点与面向录制器")
    print(f"   操作: 走到目标点并对准方向，按 [{RECORD_KEY.upper()}] 记录")
    print(f"   退出: 按 [{QUIT_KEY.upper()}] 保存并退出")
    print("========================================\n")

    path_points = []
    current_map_id = 0

    while True:
        if keyboard.is_pressed(QUIT_KEY):
            break

        # 检测按键记录点位
        if keyboard.is_pressed(RECORD_KEY):
            x, y, f_rad, map_id = get_game_data()

            if x is None or x == 0:
                print("❌ 未获取到有效坐标，请重试！")
                time.sleep(0.5)
                continue

            # 将弧度转换为 0-360 的角度，方便人类阅读和后续计算
            f_deg = math.degrees(f_rad)
            if f_deg < 0:
                f_deg += 360

            if map_id and map_id > 0:
                current_map_id = map_id

            # 记录数据：[X坐标, Y坐标, 面向角度]
            point_data = [x, y, f_deg]
            path_points.append(point_data)

            print(f"📍 [{len(path_points)}] 已记录 -> 坐标:({x:.2f}, {y:.2f}), 面向:{f_deg:.2f}°")

            # 防抖动：防止按一次记录了好多条
            time.sleep(0.5)

        time.sleep(0.02)

    # 保存文件
    if len(path_points) > 0:
        filename = f"{SAVE_DIR}/target_map_{current_map_id}.json"
        with open(filename, 'w') as f:
            json.dump(path_points, f)
        print(f"\n💾 任务已保存: {filename} (共 {len(path_points)} 个目标点)")
    else:
        print("\n❌ 未记录任何点位。")


if __name__ == "__main__":
    recorder()