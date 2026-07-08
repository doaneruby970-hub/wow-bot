import time
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
import pydirectinput
import pyautogui
import xueliangshuzhi as xlsz
import zuobiaoxianshi as zxs
import zuobiaoxunlubofang as zxlbf
import zuobiaoxunlubofang11 as zxlbf11
import zuobiaoxunlubofang22 as zxlbf22
import zuobiaomianxiangbofang as zmxbf
import botAIclaude11 as bot
import read_bag
import wow11ocr
import wow22ocr
import FPTracker
import bofang29 as bfang

PLAN_FILE = "plan.txt"
TASKS_FILE = "tasks.txt"
COMPLETED_FILE = "completed_tasks.txt"
SEQ_DIR = "sequences"  # TXT序列文件夹

# ========== 起点检测配置 ==========
# 奥格瑞玛指定起点坐标（在游戏里站到目标位置后记录 x/y 填入）
START_MAP_ID = 1454  # 奥格瑞玛 map_id
START_X = 54.13  # ← 填入实际 X 坐标
START_Y = 68.38  # ← 填入实际 Y 坐标
START_TOLERANCE = 0.1  # 坐标容差（游戏单位）


# ========== 状态读取 ==========

def get_status():
    """一次性读取所有状态，返回dict"""
    ax, ay, real_w = xlsz.find_anchor_and_width()
    stats = xlsz.read_data(ax, ay, real_w) if ax else {}
    x, y, _, map_id = zxs.get_game_data()
    bag = read_bag.parse_wow_data() or {}
    return {
        'lvl': stats.get('p_lvl', 0),
        'hp_pct': stats.get('p_hp_pct', 100),
        'mp_pct': stats.get('p_mp_pct', 100),
        'combat': stats.get('combat', False),
        'x': x, 'y': y, 'map_id': map_id,
        'bag_free': bag.get('free', 99),
    }


def get_current_level():
    ax, ay, real_w = xlsz.find_anchor_and_width()
    if not ax: return 0
    return xlsz.read_data(ax, ay, real_w).get('p_lvl', 0)


# ========== TXT序列执行器 ==========

def run_sequence(txt_file):
    """逐行解析执行TXT动作序列（支持循环）"""
    path = os.path.join(SEQ_DIR, txt_file) if not os.path.isabs(txt_file) else txt_file
    if not os.path.exists(path):
        print(f"❌ 找不到序列文件: {path}")
        return

    print(f"📜 执行序列: {txt_file}")
    with open(path, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    _execute_lines(lines)


def _execute_lines(lines):
    """执行动作行列表（支持循环嵌套）"""
    i = 0
    while i < len(lines):
        line = lines[i]
        if '|' not in line:
            i += 1
            continue

        action, param = line.split('|', 1)
        action, param = action.strip(), param.strip()

        # 处理循环开始
        if action == 'LOOP_START':
            max_loops = int(param) if param else 0  # 0表示无限循环
            loop_start = i + 1
            loop_end = _find_loop_end(lines, i)

            if loop_end == -1:
                print(f"❌ 错误：LOOP_START 缺少对应的 LOOP_END（第{i + 1}行）")
                return

            loop_body = lines[loop_start:loop_end]

            # 检查无限循环是否有退出条件
            if max_loops == 0:
                has_break = any('LOOP_BREAK_IF_IMG' in l for l in loop_body)
                if not has_break:
                    print(f"⚠️ 警告：无限循环必须包含 LOOP_BREAK_IF_IMG 退出条件")

            print(f"   🔁 开始循环（最多{max_loops if max_loops > 0 else '无限'}次）")

            # 执行循环
            loop_count = 0
            while True:
                if max_loops > 0 and loop_count >= max_loops:
                    print(f"   🔁 循环达到上限 {max_loops} 次，退出")
                    break

                loop_count += 1
                print(f"   🔁 第 {loop_count} 次循环")

                # 执行循环体，检查是否需要退出
                should_break = _execute_loop_body(loop_body)
                if should_break:
                    print(f"   ✅ 检测到退出条件，跳出循环")
                    break

            i = loop_end + 1  # 跳过整个循环块
            continue

        # 跳过 LOOP_END（已在 LOOP_START 中处理）
        if action == 'LOOP_END':
            i += 1
            continue

        # 执行单个动作
        print(f"   👉 {action}: {param}")
        _execute_action(action, param)
        i += 1


def _find_loop_end(lines, start_index):
    """查找对应的 LOOP_END 位置（支持嵌套）"""
    depth = 1
    for i in range(start_index + 1, len(lines)):
        line = lines[i].strip()

        # LOOP_END 可以没有参数，直接检查
        if line == 'LOOP_END':
            depth -= 1
            if depth == 0:
                return i
            continue

        # 其他动作需要有 | 符号
        if '|' not in line:
            continue

        action = line.split('|', 1)[0].strip()
        if action == 'LOOP_START':
            depth += 1
        elif action == 'LOOP_END':
            depth -= 1
            if depth == 0:
                return i
    return -1


def _execute_loop_body(loop_body):
    """执行循环体，返回是否需要退出循环"""
    for line in loop_body:
        if '|' not in line:
            continue

        action, param = line.split('|', 1)
        action, param = action.strip(), param.strip()

        # 检查退出条件
        if action == 'LOOP_BREAK_IF_IMG':
            # 使用 wow11ocr.check_image_exists() 进行检测
            # 自动拼接 imgs 目录路径
            if wow11ocr.check_image_exists(param, timeout=0.5):
                return True  # 检测到图片，退出循环
            continue  # 未检测到，继续执行

        # 执行普通动作
        print(f"      👉 {action}: {param}")
        _execute_action(action, param)

    return False  # 循环体执行完毕，不退出


def _execute_action(action, param):
    """执行单个动作"""
    if action == 'RUN_PATH':
        # 长途跨图寻路 (zuobiaoxunlubofang.py)
        zxlbf.OVERRIDE_PATH_FILE = param
        zxlbf.control_loop()
        zxlbf.OVERRIDE_PATH_FILE = None

    elif action == 'CLICK_OCR':
        # 识图点击（带超时30秒，调用 wow11ocr）
        wow11ocr.auto_click_target(param)

    elif action == 'CLICK_OCR_TRY':
        # 可选识图点击：尝试查找并点击图片，找不到不报错
        # 格式: CLICK_OCR_TRY | 图片名,超时秒数
        # 例如: CLICK_OCR_TRY | img_jieshou.png,10
        # 用于处理可能出现也可能不出现的界面元素
        parts = param.split(',')
        img_name = parts[0].strip()
        timeout = int(parts[1].strip()) if len(parts) > 1 else 10
        wow11ocr.auto_click_target(img_name, timeout=timeout, optional=True)

    elif action == 'CLICK_OCR22':
        # 识图点击（调用 wow22ocr，从 .\AAwow111\imgs 读取图片）
        # 格式: CLICK_OCR22 | 图片名,X偏移,Y偏移
        # 例如: CLICK_OCR22 | img_7.png,-240,-175
        parts = param.split(',')
        if len(parts) == 3:
            img_name = parts[0].strip()
            offset_x = int(parts[1].strip())
            offset_y = int(parts[2].strip())
            wow22ocr.auto_click_with_offset(img_name, offset_x, offset_y)
        else:
            print(f"      ⚠️ CLICK_OCR22 参数格式错误，应为: 图片名,X偏移,Y偏移")

    elif action == 'CHECK_FP':
        # 检查飞行点是否已开通
        fps = FPTracker.get_unlocked_flight_points()
        if param in fps:
            print(f"      ✅ 飞行点 [{param}] 已开通")
        else:
            print(f"      ❌ 飞行点 [{param}] 未开通")

    elif action == 'RUN_PATH_CROSS':
        # 跨图冲刺寻路 (zuobiaoxunlubofang11.py)
        zxlbf11.OVERRIDE_PATH_FILE = os.path.join("paths", param) if not os.path.isabs(param) and not param.startswith(
            "paths") else param
        zxlbf11.player()
        zxlbf11.OVERRIDE_PATH_FILE = None

    elif action == 'RUN_PATH_FACING':
        # 坐标+面向精确定位 (zuobiaomianxiangbofang.py)
        zmxbf.OVERRIDE_PATH_FILE = param
        zmxbf.player()
        zmxbf.OVERRIDE_PATH_FILE = None

    elif action == 'RUN_PATH_PRECISE':
        # 主城高精度寻路 (zuobiaoxunlubofang22.py)
        zxlbf22.OVERRIDE_PATH_FILE = param
        zxlbf22.player()
        zxlbf22.OVERRIDE_PATH_FILE = None

    elif action == 'RUN_QUEST':
        # 播放录制的任务动作 (29bofang.py)
        bfang.play_recording(param)

    elif action == 'CLICK_IMG':
        # 图像识别点击：在屏幕上查找指定图片并点击其中心位置
        # 使用 pyautogui 进行图像匹配（置信度0.7，灰度模式加速）
        try:
            box = pyautogui.locateOnScreen(param, confidence=0.7, grayscale=True)
            if box:
                pydirectinput.click(int(box.left + box.width / 2), int(box.top + box.height / 2))
                time.sleep(0.5)
        except Exception as e:
            print(f"      ⚠️ 识图失败: {e}")

    elif action == 'WAIT_IMG':
        # 等待图片出现：循环检测屏幕直到指定图片出现
        # 用于等待界面加载、对话框弹出等场景
        print(f"      ⏳ 等待图片出现...")
        while True:
            try:
                if pyautogui.locateOnScreen(param, confidence=0.7, grayscale=True):
                    break
            except:
                pass
            time.sleep(0.5)

    elif action == 'PRESS_KEY':
        # 按键操作：模拟按下指定键盘按键
        # 例如：PRESS_KEY | w（前进）、PRESS_KEY | space（跳跃）
        pydirectinput.press(param)
        time.sleep(0.3)

    elif action == 'SLEEP':
        # 延时等待：暂停执行指定秒数
        # 用于等待动画、技能CD、界面响应等
        time.sleep(float(param))

    elif action == 'SEQUENCE':
        # 嵌套序列：调用另一个TXT序列文件
        # 实现序列的模块化和复用
        run_sequence(param)

    elif action == 'RUN_SCRIPT':
        # 运行外部脚本：启动指定的Python脚本文件
        # 用于执行复杂的独立功能模块
        subprocess.run([sys.executable, param])


# ========== 任务系统 ==========

def load_tasks():
    """加载特殊任务列表（飞行点等）"""
    if not os.path.exists(TASKS_FILE):
        return []
    tasks = []
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split('/')
            if len(parts) >= 5:
                tasks.append({
                    'id': parts[0].strip(),
                    'level': int(parts[1]),
                    'type': parts[2].strip(),
                    'desc': parts[3].strip(),
                    'sequence': parts[4].strip()
                })
    return tasks


def load_completed_tasks():
    """加载已完成任务ID列表"""
    if not os.path.exists(COMPLETED_FILE):
        return set()
    with open(COMPLETED_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def save_completed_task(task_id):
    """追加已完成任务ID"""
    with open(COMPLETED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{task_id}\n")


# ========== 计划加载 ==========

def load_plan():
    plans = []
    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split('/')
            if len(parts) >= 4:
                city_seq = parts[4].strip() if len(parts) > 4 else None
                death_seq = parts[5].strip() if len(parts) > 5 else None
                init_seq = parts[6].strip() if len(parts) > 6 else None
                plans.append(
                    (int(parts[0]), int(parts[1]), parts[2].strip(), parts[3].strip(), city_seq, death_seq, init_seq))
    return plans


_death_start = None


def check_death(hp_pct, death_seq, confirm_secs=3):
    """非阻塞死亡检测：hp_pct为0持续confirm_secs秒返回True"""
    global _death_start
    if not death_seq:
        return False
    if hp_pct == 0:
        if _death_start is None:
            _death_start = time.time()
        elif time.time() - _death_start >= confirm_secs:
            _death_start = None
            return True
    else:
        _death_start = None
    return False


def run_path(path_file):
    """支持 .json（直接跑路）或 .txt（序列，可组合多个动作）"""
    if path_file.lower().endswith('.txt'):
        run_sequence(path_file)
    else:
        zxlbf.OVERRIDE_PATH_FILE = path_file
        zxlbf.control_loop()
        zxlbf.OVERRIDE_PATH_FILE = None


def run_combat(json_file):
    bot.CUSTOM_PATH_FILE = os.path.join("paths", json_file)
    bot.navigator = bot.Navigator()
    bot.main_controller()


def is_at_start_position():
    """检测角色是否在奥格瑞玛指定起点"""
    x, y, _, map_id = zxs.get_game_data()
    if x is None:
        return False
    return (
            map_id == START_MAP_ID
            and abs(x - START_X) <= START_TOLERANCE
            and abs(y - START_Y) <= START_TOLERANCE
    )


# ========== 主循环 ==========

def main():
    plans = load_plan()
    if not plans:
        print("❌ plan.txt 为空或格式错误")
        return

    tasks = load_tasks()
    completed = load_completed_tasks()

    print("========== 任务调度器启动 ==========")
    for p in plans:
        city = f", 城镇={p[4]}" if p[4] else ""
        init = f", 起点={p[6]}" if len(p) > 6 and p[6] else ""
        print(f"  Lv.{p[0]}-{p[1]}: 跑路={p[2]}, 打怪={p[3]}{city}{init}")
    if tasks:
        print(f"\n特殊任务: {len(tasks)} 个")
        for t in tasks:
            status = "✅" if t['id'] in completed else "⏳"
            print(f"  {status} Lv.{t['level']} {t['type']}: {t['desc']}")
    print("====================================")
    time.sleep(2)

    last_phase = None
    first_run = True

    while True:
        status = get_status()
        lvl = status['lvl']

        if lvl == 0:
            print("⚠️ 无法读取等级，5秒后重试...")
            time.sleep(5)
            continue

        matched = next((p for p in plans if p[0] <= lvl < p[1]), None)
        if not matched:
            print(f"✅ 当前 Lv.{lvl} 已超出所有计划，任务完成！")
            break

        min_lv, max_lv, run_file, combat_json, city_seq, death_seq, init_seq = matched
        print(f"\n>>> 当前 Lv.{lvl}，执行阶段 [{min_lv}-{max_lv}]")

        # --- 启动或阶段切换时执行起点检测（仅一次）---
        if first_run or matched != last_phase:
            if init_seq:
                print(f"🚀 {'[脚本启动]' if first_run else '[阶段切换]'} 执行起点检测...")
                if not is_at_start_position():
                    print(f"📍 不在起点，执行初始化序列: {init_seq}")
                    run_sequence(init_seq)
                else:
                    print(f"✅ 已在起点，跳过初始化序列")
            last_phase = matched
            first_run = False

        # --- 死亡检测：hp数值为0 持续3秒 ---
        hp_pct = status['hp_pct']
        if check_death(hp_pct, death_seq, confirm_secs=3):
            print("💀 检测到角色死亡！停止一切动作，执行复活序列...")
            run_sequence(death_seq)
            time.sleep(3)
            continue

        # --- 特殊任务检测：等级达标且未完成 ---
        for task in tasks:
            if lvl >= task['level'] and task['id'] not in completed:
                print(f"🎯 触发特殊任务: {task['desc']} (Lv.{task['level']})")
                run_sequence(task['sequence'])
                save_completed_task(task['id'])
                completed.add(task['id'])
                print(f"✅ 任务完成: {task['id']}")
                continue

        # --- 城镇判断：背包满 或 血量过低 ---
        need_city = (status['bag_free'] == 0) or (status['hp_pct'] < 30)
        if need_city and city_seq:
            print(f"🏙️ 触发城镇任务: bag_free={status['bag_free']}, hp={status['hp_pct']}%")
            run_sequence(city_seq)
            continue

        print(f"[1/2] 跑路: {run_file}")
        run_path(run_file)

        print(f"[2/2] 打怪: {combat_json}，目标升到 Lv.{max_lv}")
        run_combat(combat_json)

        print(f">>> 打怪结束，当前 Lv.{get_current_level()}")


if __name__ == "__main__":
    main()
