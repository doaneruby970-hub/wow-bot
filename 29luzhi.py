import time
import json
import os
import sys
import threading
from pynput import mouse, keyboard

# ================= 配置区 =================
SAVE_DIR = "quests"  # 存档文件夹
START_KEY = keyboard.Key.page_up  # 开始键
STOP_KEY = keyboard.Key.page_down  # 停止键

# =========================================

# 全局状态控制
class RecorderState:
    def __init__(self):
        self.recording = False
        self.ready_to_save = False
        self.start_time = 0.0
        self.events = []
        self.last_mouse_pos = None
        self.lock = threading.Lock()


state = RecorderState()


# =========================================
# 核心修复：按键名称解析函数
# =========================================
def get_key_str(key):
    """
    专门处理按键名称，解决小键盘识别为普通字符的问题
    """
    # 1. 优先检查虚拟键码 (Virtual Key Code)
    # 107=Numpad+, 109=Numpad-, 106=Numpad*, 111=Numpad/
    if hasattr(key, 'vk') and key.vk is not None:
        if key.vk == 107: return 'Key.num_add'      # 小键盘 +
        if key.vk == 109: return 'Key.num_sub'      # 小键盘 -
        if key.vk == 106: return 'Key.num_mul'      # 小键盘 *
        if key.vk == 111: return 'Key.num_div'      # 小键盘 /
        if key.vk == 110: return 'Key.num_decimal'  # 小键盘 .

    # 2. 处理普通字符 (a, b, 1, 2, +, -)
    try:
        if hasattr(key, 'char') and key.char is not None:
            return key.char
    except AttributeError:
        pass

    # 3. 处理功能键 (Key.f1, Key.enter)
    return str(key)


# =========================================
# 监听回调函数 (高性能模式)
# =========================================

def get_elapsed():
    return time.time() - state.start_time


def on_key_press(key):
    # 1. 检测开始
    if key == START_KEY:
        if not state.recording:
            with state.lock:
                state.recording = True
                state.events = []
                state.start_time = time.time()
                # 重置鼠标位置
                state.last_mouse_pos = mouse.Controller().position
            print("\n>>> 开始录制！(高性能模式运行中...)")
        return

    # 2. 检测结束
    if key == STOP_KEY:
        if state.recording:
            with state.lock:
                state.recording = False
                state.ready_to_save = True
            print("\n>>> 录制结束！正在准备保存...")
        return

    # 3. 录制按键
    if state.recording:
        # 使用自定义函数获取精准键名
        k_str = get_key_str(key)

        with state.lock:
            state.events.append({
                "type": "key_down",
                "key": k_str,
                "time": get_elapsed()
            })


def on_key_release(key):
    if key == START_KEY or key == STOP_KEY:
        return

    if state.recording:
        # 使用自定义函数获取精准键名
        k_str = get_key_str(key)

        with state.lock:
            state.events.append({
                "type": "key_up",
                "key": k_str,
                "time": get_elapsed()
            })


def on_mouse_move(x, y):
    if state.recording:
        with state.lock:
            if state.last_mouse_pos is None:
                state.last_mouse_pos = (x, y)
                dx, dy = 0, 0
            else:
                dx = x - state.last_mouse_pos[0]
                dy = y - state.last_mouse_pos[1]
                state.last_mouse_pos = (x, y)

            if dx == 0 and dy == 0: return

            state.events.append({
                "type": "mouse_move",
                "dx": dx,
                "dy": dy,
                "time": get_elapsed()
            })


def on_mouse_click(x, y, button, pressed):
    if state.recording:
        action = "mouse_down" if pressed else "mouse_up"
        btn_name = str(button).replace('Button.', '')

        with state.lock:
            state.events.append({
                "type": action,
                "button": btn_name,
                "time": get_elapsed()
            })


def on_mouse_scroll(x, y, dx, dy):
    if state.recording:
        with state.lock:
            state.events.append({
                "type": "scroll",
                "dy": dy,
                "time": get_elapsed()
            })


# =========================================
# 辅助功能
# =========================================
def ensure_dir():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


def fake_hardware_check():
    """ 模拟硬件启动日志 """
    print(f"正在连接 Arduino (COM5) 以便在录制时实时响应转身...")
    time.sleep(0.5)
    print("⚠️ [模式切换] 已启用虚拟键盘模式 (忽略端口 COM5)")
    print("✅ 请务必以【管理员身份】运行 PyCharm！")
    print("🧹 正在执行启动清理，请勿触碰键盘...")
    time.sleep(1.0)
    print("⏳ 系统冷却中 (等待 3 秒)...")
    time.sleep(2.0)
    print("🚀 准备就绪！")


# =========================================
# 主程序循环
# =========================================
def main():
    ensure_dir()
    fake_hardware_check()

    # 启动监听线程
    k_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    m_listener = mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click, on_scroll=on_mouse_scroll)

    k_listener.start()
    m_listener.start()

    print("\n=== 全能录制器 (高精度无损版) ===")
    print(f"1. 按 [{str(START_KEY).upper()}] 开始")
    print(f"2. 按 [{str(STOP_KEY).upper()}] 结束")
    print("注意：录制过程中不再打印按键信息，以保证最大采样率！")

    try:
        while True:
            if state.ready_to_save:
                # 停止录制后的处理逻辑
                num_events = len(state.events)
                print(f"\n>>> 录制结束！共 {num_events} 动作")

                # 获取文件名输入
                try:
                    name = input("任务名 (q退出/不输名字自动丢弃): ").strip()
                except EOFError:
                    break

                if name.lower() == 'q':
                    print("👋 退出程序")
                    os._exit(0)

                if name:
                    if not name.endswith(".json"):
                        name += ".json"

                    filepath = os.path.join(SAVE_DIR, name)

                    with open(filepath, "w", encoding='utf-8') as f:
                        json.dump(state.events, f, indent=2)

                    print(f"✅ 保存成功: {filepath}")
                else:
                    print("🗑️ 未输入名称，本次录制已丢弃。")

                # 重置状态，准备下一次
                with state.lock:
                    state.ready_to_save = False
                    state.events = []

                print("\n=== 全能录制器 (高精度无损版) ===")
                print(f"1. 按 [{str(START_KEY).upper()}] 开始，[{str(STOP_KEY).upper()}] 结束")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 强制退出")


if __name__ == "__main__":
    main()