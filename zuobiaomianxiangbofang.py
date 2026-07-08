import time
import math
import json
import os
import pydirectinput
import keyboard
from zuobiaoxianshi import get_game_data

# ================= 配置区域 =================
PATHS_DIR = "paths"
STOP_KEY = 'page down'

# 第一阶段参数 (跑路)
ARRIVE_RANGE = 0.3  # 到达判定距离 (米)
STOP_TURN_TOLERANCE = 35.0  # 偏离过大停下转弯
SMOOTH_TURN_LIMIT = 5.0  # 小于此值边跑边转

# 第二阶段参数 (面向校准)
FACING_TOLERANCE = 5.0  # 最终面向容差 (放宽到5度，防止原地抽搐)


# ============================================

def select_path_file():
    if not os.path.exists(PATHS_DIR):
        print(f"❌ 错误：找不到文件夹 [{PATHS_DIR}]")
        return None
    files = [f for f in os.listdir(PATHS_DIR) if f.endswith('.json')]
    if not files:
        print(f"❌ 错误：在 {PATHS_DIR} 文件夹下没有找到 .json 文件")
        return None
    files.sort()

    print("\n" + "=" * 40)
    print("📂 请选择要执行的目标文件:")
    for i, f in enumerate(files):
        print(f"  [{i}] {f}")
    print("=" * 40)

    while True:
        try:
            choice = input(f"👉 请输入编号 (0-{len(files) - 1}) [默认0]: ").strip()
            idx = int(choice) if choice != "" else 0
            if 0 <= idx < len(files):
                return files[idx]
            else:
                print("❌ 编号超出范围，请重新输入")
        except ValueError:
            print("❌ 输入无效，必须是数字，请重新输入")


def get_current_state():
    data = get_game_data()
    # 防止取不到数据时报错
    if not data or data[0] is None or data[0] == 0:
        return None, None, None
    x, y, f_rad = data[0], data[1], data[2]
    f_deg = math.degrees(f_rad)
    if f_deg < 0: f_deg += 360
    return x, y, f_deg


def execute_task():
    selected_file = select_path_file()
    if not selected_file: return

    with open(os.path.join(PATHS_DIR, selected_file), 'r') as f:
        path_nodes = json.load(f)

    print(f"\n✅ 加载成功: {selected_file}，包含 {len(path_nodes)} 个目标点")
    print("🚀 自动寻路已准备就绪，随时按 [PAGE DOWN] 停止\n")

    for idx, node in enumerate(path_nodes):
        target_x, target_y, target_facing = node[0], node[1], node[2]
        print(f"============== 正在执行目标 {idx + 1}/{len(path_nodes)} ==============")

        w_is_pressed = False
        stuck_check_time = time.time()
        last_pos = None

        # ==========================================
        # 🏃 第一阶段：寻路奔跑
        # ==========================================
        print(f"🏃 前往坐标 ({target_x:.2f}, {target_y:.2f})")
        while True:
            if keyboard.is_pressed(STOP_KEY):
                if w_is_pressed: pydirectinput.keyUp('w')
                print("\n🛑 已手动停止")
                return

            curr_x, curr_y, curr_deg = get_current_state()
            if curr_x is None:
                time.sleep(0.1)  # 取不到数据时必须稍微休息，防止卡死CPU
                continue

            dist = math.sqrt((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2)
            nav_rad = math.atan2(-(target_x - curr_x), curr_y - target_y)
            nav_deg = math.degrees(nav_rad)
            if nav_deg < 0: nav_deg += 360

            if dist <= ARRIVE_RANGE:
                if w_is_pressed:
                    pydirectinput.keyUp('w')
                    w_is_pressed = False
                print(f"🎯 坐标到达！误差: {dist:.2f}米")
                time.sleep(0.5)
                break

            angle_diff = (nav_deg - curr_deg + 180) % 360 - 180

            if abs(angle_diff) > STOP_TURN_TOLERANCE:
                if w_is_pressed:
                    pydirectinput.keyUp('w')
                    w_is_pressed = False
                turn_key = 'a' if angle_diff > 0 else 'd'
                pydirectinput.keyDown(turn_key)
                time.sleep(0.02)  # 【修改点】减少大转弯按压时间，防止转过头
                pydirectinput.keyUp(turn_key)
                time.sleep(0.1)  # 【修改点】至关重要：等待游戏内存角度更新
            else:
                if not w_is_pressed:
                    pydirectinput.keyDown('w')
                    w_is_pressed = True
                if abs(angle_diff) > SMOOTH_TURN_LIMIT:
                    turn_key = 'a' if angle_diff > 0 else 'd'
                    pydirectinput.press(turn_key)
                    time.sleep(0.05)  # 【修改点】小转弯也要稍微等一下内存更新

            # 【修改点】防卡死逻辑：只有在按住W往前走的时候，才判断是否卡死
            if w_is_pressed:
                if last_pos is None: last_pos = (curr_x, curr_y)
                if time.time() - stuck_check_time > 2.0:
                    if math.sqrt((curr_x - last_pos[0]) ** 2 + (curr_y - last_pos[1]) ** 2) < 0.05:
                        pydirectinput.press('space')
                    last_pos = (curr_x, curr_y)
                    stuck_check_time = time.time()
            else:
                # 如果停下来转弯，刷新卡死计时器，防止乱跳
                stuck_check_time = time.time()
                last_pos = (curr_x, curr_y)

            time.sleep(0.01)

        # ==========================================
        # 🔄 第二阶段：原地转向校准
        # ==========================================
        print(f"🔄 阶段二：校准面向，目标角度: {target_facing:.1f}°")
        while True:
            if keyboard.is_pressed(STOP_KEY):
                print("\n🛑 已手动停止")
                return

            _, _, curr_deg = get_current_state()
            if curr_deg is None:
                time.sleep(0.1)
                continue

            facing_diff = (target_facing - curr_deg + 180) % 360 - 180

            if abs(facing_diff) <= FACING_TOLERANCE:
                print(f"✅ 校准完成！当前偏差: {abs(facing_diff):.1f}°")
                break

            turn_key = 'a' if facing_diff > 0 else 'd'
            pydirectinput.keyDown(turn_key)
            time.sleep(0.005)
            pydirectinput.keyUp(turn_key)

            time.sleep(0.15)  # 【修改点】原地校准需要更长的缓冲读取内存，防止抽搐

        print(f"✨ 目标 {idx + 1} 彻底完成！\n")
        time.sleep(1)

    print("🏁 所有目标点已执行完毕！")


if __name__ == "__main__":
    execute_task()