import pydirectinput
import time
import json
import os
import sys

# ================= 配置 =================
# 录制文件存放目录 (必须和录制器保持一致)
QUESTS_DIR = "quests"

# ⚠️ 必须设置：防止鼠标移动到角落时报错
pydirectinput.FAILSAFE = False
# ⚠️ 必须设置：设为0以保证连贯性，由代码控制延迟
pydirectinput.PAUSE = 0.001

# 键名映射表：将 pynput 录制的名称转换为 pydirectinput 能识别的名称
KEY_MAPPING = {
    # --- 1. 普通功能键 ---
    'Key.space': 'space',
    'Key.enter': 'enter',
    'Key.tab': 'tab',
    'Key.esc': 'esc',
    'Key.backspace': 'backspace',
    'Key.caps_lock': 'capslock',
    'Key.delete': 'delete',
    'Key.insert': 'insert',
    'Key.home': 'home',
    'Key.end': 'end',
    'Key.page_up': 'pageup',
    'Key.page_down': 'pagedown',
    'Key.print_screen': 'printscreen',
    'Key.scroll_lock': 'scrolllock',
    'Key.pause': 'pause',

    # --- 2. 方向键 ---
    'Key.left': 'left',
    'Key.right': 'right',
    'Key.up': 'up',
    'Key.down': 'down',

    # --- 3. 修饰键 (分左右) ---
    'Key.shift': 'shift',       # 有些系统不分左右
    'Key.shift_r': 'shiftright',
    'Key.ctrl_l': 'ctrlleft',
    'Key.ctrl_r': 'ctrlright',
    'Key.alt_l': 'altleft',
    'Key.alt_r': 'altright',
    'Key.cmd': 'win',           # Windows 键
    'Key.cmd_l': 'winleft',
    'Key.cmd_r': 'winright',
    'Key.menu': 'apps',         # 菜单键

    # --- 4. F 功能键 ---
    'Key.f1': 'f1', 'Key.f2': 'f2', 'Key.f3': 'f3', 'Key.f4': 'f4',
    'Key.f5': 'f5', 'Key.f6': 'f6', 'Key.f7': 'f7', 'Key.f8': 'f8',
    'Key.f9': 'f9', 'Key.f10': 'f10', 'Key.f11': 'f11', 'Key.f12': 'f12',

    # --- 5. 小键盘区 (Numpad) ---
    # 录制器修复后会输出这些名字，必须在这里接住
    'Key.num_lock': 'numlock',
    'Key.num_add': 'add',          # 小键盘 +
    'Key.num_sub': 'subtract',     # 小键盘 -
    'Key.num_mul': 'multiply',     # 小键盘 *
    'Key.num_div': 'divide',       # 小键盘 /
    'Key.num_decimal': 'decimal',  # 小键盘 . (点)
    'Key.num_enter': 'enter',      # 小键盘回车 (pydirectinput 通常不区分主回车和小回车，都叫 enter)

    # --- 6. 小键盘数字 (必须开启 NumLock) ---
    # 注意：pynput 在 NumLock 开启时通常录制为字符 '0'-'9'，但在某些驱动下可能识别为特定 Key 对象
    '<96>': 'num0',
    '<97>': 'num1',
    '<98>': 'num2',
    '<99>': 'num3',
    '<100>': 'num4',
    '<101>': 'num5',
    '<102>': 'num6',
    '<103>': 'num7',
    '<104>': 'num8',
    '<105>': 'num9',

    # 备用兼容 (以防录制器把小键盘数字记成了特殊对象)
    'Key.num_0': 'num0', 'Key.num_1': 'num1', 'Key.num_2': 'num2',
    'Key.num_3': 'num3', 'Key.num_4': 'num4', 'Key.num_5': 'num5',
    'Key.num_6': 'num6', 'Key.num_7': 'num7', 'Key.num_8': 'num8',
    'Key.num_9': 'num9',
}


def get_pydirectinput_key(raw_key):
    """ 将录制的键名转换为 pydirectinput 可用的键名 """
    if raw_key in KEY_MAPPING:
        return KEY_MAPPING[raw_key]
    return raw_key.replace("'", "").lower()


def fake_hardware_init():
    """ 模拟硬件启动日志 (纯粹为了仪式感，实际无硬件连接) """
    print("⚠️ [模式切换] 已启用虚拟键盘模式 (忽略端口 COM5)")
    print("✅ 请务必以【管理员身份】运行 PyCharm！")
    print("🧹 正在执行启动清理，请勿触碰键盘...")
    time.sleep(1.0)
    print("⏳ 系统冷却中 (等待 3 秒)...")
    time.sleep(2.0)
    print("🚀 准备就绪！")


def list_files():
    """ 列出 quests 文件夹下的所有 json 文件 """
    if not os.path.exists(QUESTS_DIR):
        os.makedirs(QUESTS_DIR)
        print(f"📂 已自动创建目录: {QUESTS_DIR}")
        return []

    files = [f for f in os.listdir(QUESTS_DIR) if f.endswith(".json")]
    # 按文件名排序，保证列表顺序固定
    files.sort()
    return files


def play_recording(filename):
    filepath = os.path.join(QUESTS_DIR, filename)

    if not os.path.exists(filepath):
        print(f"❌ 错误：找不到文件 {filepath}")
        return

    try:
        with open(filepath, "r", encoding='utf-8') as f:
            events = json.load(f)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    print(f"🚀 3秒后开始播放: {filename} ({len(events)} 动作)")
    time.sleep(3)

    start_play_time = time.time()
    print("▶️ 开始执行...")

    for i, event in enumerate(events):
        # --- 1. 时间同步控制 ---
        target_time = event['time']
        current_elapsed = time.time() - start_play_time

        wait_time = target_time - current_elapsed
        if wait_time > 0:
            time.sleep(wait_time)

        # --- 2. 动作分发 ---
        action_type = event['type']

        try:
            if action_type == 'key_down':
                key = get_pydirectinput_key(event['key'])
                pydirectinput.keyDown(key)

            elif action_type == 'key_up':
                key = get_pydirectinput_key(event['key'])
                pydirectinput.keyUp(key)

            elif action_type == 'mouse_move':
                dx, dy = int(event['dx']), int(event['dy'])
                if dx != 0 or dy != 0:
                    pydirectinput.moveRel(dx, dy, relative=True)

            elif action_type == 'mouse_down':
                btn = event['button']
                pydirectinput.mouseDown(button=btn)

            elif action_type == 'mouse_up':
                btn = event['button']
                pydirectinput.mouseUp(button=btn)

            elif action_type == 'scroll':
                pydirectinput.scroll(int(event['dy'] * 120))  # 修正滚轮系数

        except Exception as e:
            print(f"⚠️ 动作执行失败 [{i}]: {e}")

    print("✅ 播放结束")


def main():
    fake_hardware_init()

    while True:
        files = list_files()

        print("\n--- 任务列表 ---")
        if not files:
            print("(空) 请先使用录制器录制一些动作...")
        else:
            for i, f in enumerate(files):
                print(f"[{i + 1}] {f}")

        print("\n[Q] 退出")
        choice = input("请选择 (输入序号): ").strip()

        if choice.lower() == 'q':
            print("👋 再见")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                play_recording(files[idx])
                input("\n按回车键返回菜单...")
            else:
                print("❌ 序号无效，请重新输入。")
        except ValueError:
            print("❌ 输入错误，请输入数字。")


if __name__ == "__main__":
    main()