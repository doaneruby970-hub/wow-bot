import threading
import time
import math
import statistics
import cv2
import numpy as np
import pyautogui
import pydirectinput
import keyboard
import ctypes
import json
import os
from collections import deque
from ultralytics import YOLO

try:
    from zuobiaoxianshi import get_game_data
except ImportError:
    print("❌ 警告：未找到 zuobiaoxianshi.py")
    get_game_data = lambda: (0, 0, 0, 0)

# ==========================================
#              1. 全局配置区
# ==========================================

# --- 模型与按键 ---
MODEL_PATH = r'.\runs\detect\train2\weights\best.pt'
SHITI_MODEL_PATH = r'.\WoW_Project\runs\detect\wow_shiti_v1\weights\best.pt'
ATTACK_KEY = '1'  # 攻击技能键
EAT_KEY = '8'  # 吃东西/回血键
STOP_KEY = 'page down'  # 手动紧急停止键
KEY_LEFT = 'a'  # 左转键
KEY_RIGHT = 'd'  # 右转键
KEY_BACK = 's'  # 后退键

# --- 屏幕与中心 ---
SCREEN_W, SCREEN_H = pyautogui.size()
CENTER_X, CENTER_Y = SCREEN_W // 2, SCREEN_H // 2

# --- YOLO 识别 ---
CONF_LEVEL = 0.5
# 置信度阈值：调高→漏检少误报，调低→更灵敏但可能误识别

# --- 大方框（搜索区）配置，格式：(x起始比例, y起始比例, 宽比例, 高比例) ---
# 只有中心点在此框内的怪才会被处理；调整可缩小/扩大搜索范围
BIG_BOX_CONFIG = (0.05, 0.25, 0.9, 0.57)

# --- 小方框（警戒/后退区）配置，格式同上 ---
# 怪进入此框说明太近，触发后退；调小→更早后退，调大→允许怪更近
SMALL_BOX_CONFIG = (0.43, 0.45, 0.14, 0.15)

# --- 后退时长 ---
BACK_DURATION = 4.0
# 单位：秒。怪进入小方框时后退的持续时间；调大→退更远，调小→退一点点

# --- 扇形转向参数 ---
TIME_PER_PIXEL = 0.0005
# 每像素偏差对应的按键时长系数；调大→每次转更多，调小→更精细但可能转不到位

FACTOR_FAR = 0.8
# 远区（屏幕上方1/3）倍率；远处怪视觉偏差大但实际角度小，倍率小防止过转

FACTOR_MID = 1.5
# 中区（屏幕中间1/3）倍率；标准区域，基准值

FACTOR_CLOSE = 3
# 近区（屏幕下方1/3）倍率；近处怪需要更大转角，倍率大

PRESS_MAX = 0.8
# 单次按键最大时长（秒）；防止转圈圈，调大→允许大幅转向，调小→更保守

PRESS_MIN = 0.05
# 单次按键最小时长（秒）；防止时间太短系统无响应，调大→最小转动更明显

AIM_DEAD_ZONE = 60
# 瞄准死区（像素）；目标X偏差小于此值视为对准，直接攻击；调大→更宽松，调小→要求更精准

# --- 战斗参数 ---
ATTACK_DIST = 35.0
# 攻击距离（码）；目标距离小于此值才停止前进开始攻击；调大→远距离也攻击，调小→要求更近

SAFE_HP_PCT = 40
# 危险血量百分比；低于此值且安全状态则停止主动寻路；调大→更保守更早休息

SAFE_MP_PCT = 30
# 危险蓝量百分比；低于此值且安全状态则停止主动寻路打怪；调大→更保守

FULL_HP_PCT = 90
# 恢复完成血量百分比；高于此值才结束恢复继续巡逻；调大→要求更满才出发，调小→低血也出发

FULL_MP_PCT = 90
# 恢复完成蓝量百分比；高于此值才结束恢复继续巡逻

MAX_ACTIVE_KILLS = 1
# 每段路点间最多主动击杀数；达到后强制继续寻路防止跑偏；调大→打更多再走

# --- 导航参数 ---
NAV_ARRIVE_DIST = 0.5
CUSTOM_PATH_FILE = 'paths/map_14111.json'
# 🌟 新增：强制指定路书文件。如果想让脚本自动按地图ID加载，就把这里改成 CUSTOM_PATH_FILE = None
# 到达路点的判定距离；小于此值视为到达当前路点；调大→更早切换下一路点（可能走捷径），调小→要求更精确到位

NAV_TURN_THRESHOLD = 30
# 开始前进前的最大允许偏角（度）；偏差大于此值先转向再走；调大→歪着也走，调小→要求更正对才走

NAV_FINE_TURN = 5
# 行进中微调的偏角阈值（度）；小于此值不微调；调大→更频繁微调，调小→只在偏差大时才微调

NAV_TURN_STEP = 0.02
# 转向时单次按键时长（秒）；调大→每步转更多，调小→更精细

NAV_FINE_STEP = 0.01
# 行进中微调单次按键时长（秒）；调大→微调幅度更大

# --- 重试与延迟 ---
MAX_CLICK_ATTEMPTS = 3
# 点击选中目标的最大重试次数；超过则放弃返回巡逻；调大→更执着，调小→更快放弃

FSM_SLEEP = 0.05
# 主循环每轮最小休眠（秒）；调大→降低CPU占用但反应变慢，调小→更灵敏但更耗CPU

COMBAT_SLEEP = 0.2
# 战斗状态每轮休眠（秒）；控制攻击频率；调大→攻击更慢，调小→攻击更频繁

ALIGN_SLEEP = 0.1
# 转向状态每轮休眠（秒）；转向后等待画面稳定；调大→更稳但更慢，调小→更快但可能抖动

ALIGN_AFTER_TURN_SLEEP = 0.2
# 执行一次转向按键后的额外等待（秒）；让画面稳定再判断；调大→更稳，调小→更快

CHECK_SLEEP = 0.3
# CHECK_SELECTION状态每轮休眠（秒）；等待游戏响应选中；调大→更宽容，调小→更快但可能误判

CLICK_SLEEP = 0.5
# 点击目标后等待游戏响应的时间（秒）；调大→更稳定，调小→更快但可能未响应

EAT_SLEEP = 2
# 吃东西后等待的时间（秒）；调大→每次吃完多等，调小→更频繁触发吃东西

YOLO_SLEEP = 0.2
# YOLO线程每轮扫描间隔（秒）；调大→降低GPU/CPU占用，调小→识别更实时

STATUS_SLEEP = 0.1
# 数值读取线程间隔（秒）；调大→降低截图频率，调小→数值更实时

ESTIMATED_BLOCK_SIZE = 20
# 数值读取锚点的预估像素块大小；与游戏UI像素块尺寸对应，一般不需要改

# ==========================================
#   自动计算（勿动）
# ==========================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()


def _get_rect(cfg, w, h):
    px, py = int(cfg[0] * w), int(cfg[1] * h)
    pw, ph = int(cfg[2] * w), int(cfg[3] * h)
    return (px, py, px + pw, py + ph)  # (x1, y1, x2, y2)


BIG_BOX = _get_rect(BIG_BOX_CONFIG, SCREEN_W, SCREEN_H)
SMALL_BOX = _get_rect(SMALL_BOX_CONFIG, SCREEN_W, SCREEN_H)
ZONE_Y1 = SCREEN_H // 3  # 远区/中区分界线（Y坐标）
ZONE_Y2 = (SCREEN_H * 2) // 3  # 中区/近区分界线（Y坐标）


# ==========================================
#              2. 共享数据区
# ==========================================
class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.hp = 0
        self.mp = 0
        self.hp_pct = 0
        self.mp_pct = 0
        self.combat = False
        self.has_target = False
        self.target_dist = 999
        self.target_hp_pct = 0
        self.player_lvl = 0
        self.enemy_found = False
        self.enemy_box = None
        self.current_fsm_state = "INIT"
        self.monitor_frame = None  # 供监视器线程显示的最新画面
        self.active_kills = 0  # 当前路点段主动击杀计数
        self.shiti_found = False  # 是否识别到尸体
        self.shiti_box = None  # 尸体屏幕坐标 (cx, cy)


state = SharedState()


# ==========================================
#    3. 数值读取核心函数
# ==========================================
def find_anchor_and_width():
    screen = pyautogui.screenshot()
    w, h = screen.size
    for y in range(0, 300, 5):
        row_pixels = []
        for x in range(0, w):
            r, g, b = screen.getpixel((x, y))
            if abs(r - 255) < 10 and abs(g - 0) < 10 and abs(b - 255) < 10:
                row_pixels.append(x)
        if len(row_pixels) > 5:
            min_x = row_pixels[0]
            max_x = row_pixels[-1]
            real_width = max_x - min_x
            center_x = (min_x + max_x) // 2
            center_y = y + (ESTIMATED_BLOCK_SIZE // 2)
            return center_x, center_y, real_width
    return None, None, None


def read_data(ax, ay, block_w):
    top = max(0, ay - (block_w // 2) - 10)
    left = ax - (block_w // 2) - 10
    img = pyautogui.screenshot(region=(left, top, block_w * 16, block_w * 3))

    def get_color(i):
        target_screen_x = ax + (i * block_w) + int(i * 0.5)
        local_x = max(0, min(target_screen_x - left, img.width - 1))
        local_y = max(0, min(ay - top, img.height - 1))
        return img.getpixel((int(local_x), int(local_y)))

    d = {}
    d['hp'] = get_color(1)[0] * 256 + get_color(2)[0]
    d['mp'] = get_color(3)[0] * 256 + get_color(4)[0]
    d['t_hp_pct'] = get_color(5)[0]
    d['p_lvl'] = get_color(6)[0]
    c8 = get_color(7)
    d['combat'] = (c8[0] > 0)
    d['enemy'] = (c8[1] > 0)
    d['dead'] = (c8[2] > 0)
    d['has_target'] = d['enemy'] or (d['t_hp_pct'] > 0) or d['dead']
    d['p_hp_pct'] = get_color(8)[0]
    d['distance'] = get_color(9)[0]
    d['p_mp_pct'] = get_color(10)[0]
    return d


# ==========================================
#    4. 打印状态日志
# ==========================================
def print_status():
    with state.lock:
        hp = state.hp
        mp = state.mp
        hp_pct = state.hp_pct
        mp_pct = state.mp_pct
        combat = state.combat
        has_target = state.has_target
        t_hp_pct = state.target_hp_pct
        p_lvl = state.player_lvl
        dist = state.target_dist
    status_str = "⚔️战斗" if combat else "✅安全"
    print(f"我: Lv.{p_lvl} HP {hp} ({hp_pct}%) | MP {mp} ({mp_pct}%) | {status_str}")
    if has_target:
        print(f"敌: HP:{t_hp_pct}% | 📏距离: {dist:.1f} 码")
    else:
        print("敌: 无目标")
    print("-" * 35)


# ==========================================
#           5. 线程A：数值仪表盘
# ==========================================
def thread_status_reader():
    print(">>> [线程A] 数值仪表盘启动...")
    ax, ay, real_w = find_anchor_and_width()
    if not ax:
        print("❌ [线程A] 未找到锚点，数值读取失败")
        return
    print(f"✅ [线程A] 锚点锁定: ({ax}, {ay}) | 步长: {real_w}")
    history = deque(maxlen=3)
    # maxlen=3：保留最近3帧数据做滤波；调大→更平滑但响应更慢，调小→更实时但抗噪差
    while True:
        try:
            d = read_data(ax, ay, real_w)
            history.append(d)
            if len(history) == 3:
                with state.lock:
                    # 数值类：取中位数，自动剔除单次极端乱码
                    state.hp = int(statistics.median([x['hp'] for x in history]))
                    state.mp = int(statistics.median([x['mp'] for x in history]))
                    state.hp_pct = int(statistics.median([x['p_hp_pct'] for x in history]))
                    state.mp_pct = int(statistics.median([x['p_mp_pct'] for x in history]))
                    state.target_hp_pct = int(statistics.median([x['t_hp_pct'] for x in history]))
                    state.player_lvl = int(statistics.median([x['p_lvl'] for x in history]))
                    new_dist = statistics.median([x['distance'] for x in history])
                    # 距离超过80码视为读取错误，保留上次有效值
                    if new_dist <= 60.0:
                        state.target_dist = new_dist
                    # 状态类：多数表决，3次里至少2次True才承认，防止闪烁误触发
                    state.combat = sum(x['combat'] for x in history) >= 2
                    state.has_target = sum(x['has_target'] for x in history) >= 2
        except Exception:
            pass
        time.sleep(STATUS_SLEEP)


# ==========================================
#           6. 线程B：YOLO视觉雷达
# ==========================================
def thread_yolo_scanner():
    print(">>> [线程B] YOLO视觉雷达启动...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    while True:
        if state.current_fsm_state in ["COMBAT", "RECOVERY"]:
            time.sleep(YOLO_SLEEP)
            continue
        # 找尸体阶段由专用线程处理，跳过普通怪物扫描
        if state.current_fsm_state == "找尸体":
            time.sleep(YOLO_SLEEP)
            continue
        try:
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            results = model.predict(source=frame, conf=CONF_LEVEL, verbose=False)
            found = False
            target_box = None
            debug = frame.copy()
            candidates = {1: None, 2: None}  # 按优先级收集候选
            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    if cls not in (1, 2):
                        continue
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    if BIG_BOX[0] < cx < BIG_BOX[2] and BIG_BOX[1] < cy < BIG_BOX[3]:
                        if candidates[cls] is None:
                            candidates[cls] = (cx, cy, int(x1), int(y1), int(x2), int(y2))
            # 优先 class 1 (red_health_bar)，其次 class 2 (yellow_health_bar)
            chosen = candidates[1] or candidates[2]
            if chosen:
                cx, cy, x1, y1, x2, y2 = chosen
                target_box = (cx, cy)
                found = True
                cv2.rectangle(debug, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.circle(debug, (cx, cy), 5, (0, 0, 255), -1)
            with state.lock:
                state.enemy_found = found
                state.enemy_box = target_box
                state.monitor_frame = debug
        except Exception:
            pass
        time.sleep(YOLO_SLEEP)


# ==========================================
#           7. 导航器
# ==========================================
class Navigator:
    def __init__(self):
        self.path_nodes = []
        self.current_idx = 0
        self.w_pressed = False

    def load_path(self, map_id):
        filename = CUSTOM_PATH_FILE if CUSTOM_PATH_FILE else f"paths/map_{map_id}.json"
        print(f"📂 正在读取文件: {filename}")
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                self.path_nodes = json.load(f)
            self.current_idx = 0
            print(f"✅ 成功加载路书，共 {len(self.path_nodes)} 个节点")
        else:
            print(f"❌ 找不到路书文件: {filename}")

    def stop(self):
        if self.w_pressed:
            pydirectinput.keyUp('w')
            self.w_pressed = False
        pydirectinput.keyUp('a')
        pydirectinput.keyUp('d')

    def tick(self):
        curr_x, curr_y, curr_face_rad, map_id = get_game_data()
        if curr_x == 0 and curr_y == 0:
            return
        if not self.path_nodes:
            if map_id > 0:
                self.load_path(map_id)
            return
        if self.current_idx >= len(self.path_nodes):
            self.stop()
            self.path_nodes = []
            return
        target_x, target_y = self.path_nodes[self.current_idx]
        dist = math.sqrt((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2)
        if dist < NAV_ARRIVE_DIST:
            # NAV_ARRIVE_DIST：到达判定距离，调大→更早切换路点，调小→要求更精确
            print(f"✨ 到达路点 {self.current_idx + 1}")
            self.current_idx += 1
            with state.lock:
                state.active_kills = 0
            return
        angle_rad = math.atan2(-(target_x - curr_x), curr_y - target_y)
        target_deg = math.degrees(angle_rad) % 360
        curr_deg = math.degrees(curr_face_rad)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180
        if abs(angle_diff) > NAV_TURN_THRESHOLD:
            # NAV_TURN_THRESHOLD：超过此偏角先停下转向；调大→歪着也走，调小→要求更正对
            if self.w_pressed:
                pydirectinput.keyUp('w')
                self.w_pressed = False
            key = 'a' if angle_diff > 0 else 'd'
            pydirectinput.keyDown(key)
            time.sleep(NAV_TURN_STEP)  # NAV_TURN_STEP：转向单步时长，调大→每步转更多
            pydirectinput.keyUp(key)
        else:
            if not self.w_pressed:
                pydirectinput.keyDown('w')
                self.w_pressed = True
            if abs(angle_diff) > NAV_FINE_TURN:
                # NAV_FINE_TURN：行进中微调阈值；调大→更频繁微调
                key = 'a' if angle_diff > 0 else 'd'
                pydirectinput.keyDown(key)
                time.sleep(NAV_FINE_STEP)  # NAV_FINE_STEP：微调单步时长，调大→微调幅度更大
                pydirectinput.keyUp(key)


navigator = Navigator()


# ==========================================
#    线程C：小屏幕监视器
# ==========================================
def thread_monitor():
    print(">>> [线程C] 监视器启动...")
    while True:
        with state.lock:
            frame = state.monitor_frame
            fsm = state.current_fsm_state
            hp = state.hp
            mp = state.mp
            t_hp_pct = state.target_hp_pct
            dist = state.target_dist
            combat = state.combat
            kills = state.active_kills
        if frame is not None:
            vis = frame.copy()
            # 画大方框（绿）
            cv2.rectangle(vis, (BIG_BOX[0], BIG_BOX[1]), (BIG_BOX[2], BIG_BOX[3]), (0, 255, 0), 2)
            # 画小方框（红）
            cv2.rectangle(vis, (SMALL_BOX[0], SMALL_BOX[1]), (SMALL_BOX[2], SMALL_BOX[3]), (0, 0, 255), 2)
            # 画扇形分区线（黄）
            cv2.line(vis, (0, ZONE_Y1), (SCREEN_W, ZONE_Y1), (0, 255, 255), 1)
            cv2.line(vis, (0, ZONE_Y2), (SCREEN_W, ZONE_Y2), (0, 255, 255), 1)
            # 画中心线（蓝）
            cv2.line(vis, (CENTER_X, 0), (CENTER_X, SCREEN_H), (255, 0, 0), 1)
            # 状态文字
            color = (0, 0, 255) if combat else (0, 255, 0)
            cv2.putText(vis, f"FSM:{fsm}  HP:{hp} MP:{mp}  E:{t_hp_pct}%  D:{dist:.1f}  K:{kills}/{MAX_ACTIVE_KILLS}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            small = cv2.resize(vis, (500, 300))
            cv2.imshow("AI Monitor", small)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        time.sleep(0.05)
    cv2.destroyAllWindows()


# ==========================================
#    8. 扇形转向核心函数（来自hunter_logicAI111）
# ==========================================
def do_aim_turn(cx, cy):
    """
    根据目标屏幕坐标执行一次键盘转向。
    返回 True 表示已对准（在死区内），False 表示执行了转向。
    """
    offset_x = cx - CENTER_X
    if abs(offset_x) <= AIM_DEAD_ZONE:
        return True  # 已对准

    # 根据Y坐标判断远近区，选择倍率
    if cy < ZONE_Y1:
        zone_factor = FACTOR_FAR  # 远区：偏差大但实际角度小，倍率小
    elif cy > ZONE_Y2:
        zone_factor = FACTOR_CLOSE  # 近区：需要更大转角，倍率大
    else:
        zone_factor = FACTOR_MID  # 中区：标准倍率

    press_duration = abs(offset_x) * TIME_PER_PIXEL * zone_factor
    press_duration = min(press_duration, PRESS_MAX)  # 防止转圈圈
    press_duration = max(press_duration, PRESS_MIN)  # 防止时间太短无响应

    direction_key = KEY_RIGHT if offset_x > 0 else KEY_LEFT
    dir_str = "RIGHT" if offset_x > 0 else "LEFT"
    zone_name = "FAR" if cy < ZONE_Y1 else ("CLOSE" if cy > ZONE_Y2 else "MID")
    print(f"🔄 转向: {dir_str} | 区域: {zone_name} | 时长: {press_duration:.3f}s")

    pydirectinput.keyDown(direction_key)
    time.sleep(press_duration)
    pydirectinput.keyUp(direction_key)
    return False


# 加载尸体识别模型（全局，避免重复加载）
try:
    shiti_model = YOLO(SHITI_MODEL_PATH)
    print(f"✅ 尸体识别模型加载成功")
except Exception as e:
    print(f"❌ 尸体模型加载失败: {e}")
    shiti_model = None


# ==========================================
#           9. 主大脑：有限状态机 (FSM)
# ==========================================
def main_controller():
    print("🧠 主控大脑已连接...")
    t1 = threading.Thread(target=thread_status_reader, daemon=True)
    t2 = threading.Thread(target=thread_yolo_scanner, daemon=True)
    t3 = threading.Thread(target=thread_monitor, daemon=True)
    t1.start()
    t2.start()
    t3.start()

    print("✅ 系统就绪，5秒后开始运行...")
    time.sleep(5)  # 启动等待时间，给线程初始化留出时间

    current_state = "PATROL"
    click_attempts = 0
    align_pos = None  # 进入ALIGN_DIRECTION时锁定的坐标
    align_wait_start = 0
    combat_timer = 0
    recorded_enemy_hp = 100
    safe_combat_timer = time.time()
    is_active_hunt = False  # 标记本次战斗是否由主动巡逻发起
    loot_start_time = 0  # 进入找尸体状态的时间戳
    loot_click_pos = None  # 尸体点击坐标

    try:
        while True:
            if keyboard.is_pressed(STOP_KEY):
                print("🛑 手动停止！")
                navigator.stop()
                break

            state.current_fsm_state = current_state

            with state.lock:
                hp = state.hp
                mp = state.mp
                hp_pct = state.hp_pct
                mp_pct = state.mp_pct
                combat = state.combat
                has_target = state.has_target
                dist = state.target_dist
                enemy_found = state.enemy_found
                enemy_pos = state.enemy_box
                t_hp_pct = state.target_hp_pct

            # --- 血量/蓝量危险检测（仅安全状态触发恢复）---
            if hp_pct > 0 and not combat and current_state != "RECOVERY":
                if hp_pct < SAFE_HP_PCT or mp_pct < SAFE_MP_PCT:
                    reason = f"HP:{hp_pct}%" if hp_pct < SAFE_HP_PCT else f"MP:{mp_pct}%"
                    print(f"⚠️ {reason} 过低，进入恢复模式...")
                    navigator.stop()
                    current_state = "RECOVERY"

            # --- RECOVERY ---
            if current_state == "RECOVERY":
                # 被攻击时强制应战
                if combat:
                    print("⚔️ 被攻击！强制应战...")
                    current_state = "COMBAT"
                    continue
                if hp_pct >= FULL_HP_PCT and mp_pct >= FULL_MP_PCT:
                    print("✅ 恢复完毕，继续巡逻。")
                    current_state = "PATROL"
                else:
                    print(f"💤 休息中... HP:{hp_pct}% MP:{mp_pct}%")
                    if hp_pct < SAFE_HP_PCT:
                        time.sleep(1)
                        pydirectinput.press('-')
                    elif mp_pct < SAFE_MP_PCT:
                        time.sleep(1)
                        pydirectinput.press('=')
                    pydirectinput.press(EAT_KEY)
                    time.sleep(EAT_SLEEP)
                continue

            # --- 进战强制切COMBAT ---
            if combat and current_state not in ["COMBAT", "FOUND_TARGET", "CHECK_SELECTION", "ALIGN_DIRECTION"]:
                current_state = "COMBAT"

            # --- COMBAT ---
            if current_state == "COMBAT":
                print_status()

                # 1. 距离远，跑向目标
                if dist > ATTACK_DIST:
                    pydirectinput.keyDown('w')
                    # 跑动时不停刷新计时器，因为还没站定输出
                    combat_timer = time.time()
                    recorded_enemy_hp = t_hp_pct

                # 2. 距离近，站定攻击！
                else:
                    pydirectinput.keyUp('w')

                    # --- 🌟 你的核心战术：背对/重合检测 ---
                    # 如果目标掉血了，说明朝向是对的，攻击有效，重置计时器！
                    if t_hp_pct < recorded_enemy_hp:
                        combat_timer = time.time()
                        recorded_enemy_hp = t_hp_pct

                    # 如果没掉血，且在战斗中、距离≤3码、持续5秒
                    elif combat and dist <= 3.0 and time.time() - combat_timer >= 5.0 and t_hp_pct > 0:
                        print(f"⚠️ 警告：脸滚键盘5秒了，敌人(HP:{t_hp_pct}%)还没掉血！")
                        print("🔙 触发实战战术：疑为背对或模型重合，按 S 后退拉开距离...")

                        # 按下 S 键 4 秒，强行让怪物重新跑到自己面前
                        pydirectinput.keyDown(KEY_BACK)
                        time.sleep(3.0)
                        pydirectinput.keyUp(KEY_BACK)

                        # 退完之后，重新开始计算 5 秒
                        combat_timer = time.time()
                        recorded_enemy_hp = t_hp_pct

                # 无论如何，狂按攻击键
                pydirectinput.press(ATTACK_KEY)

                # 安全状态超时检测：10秒没进战斗说明角度歪了打不到
                if combat:
                    safe_combat_timer = time.time()  # 进战就重置
                elif time.time() - safe_combat_timer >= 10.0:
                    print("⚠️ 安全状态持续10秒，角度可能歪了，左键取消目标，返回巡逻")
                    pyautogui.click(CENTER_X, CENTER_Y)
                    pydirectinput.keyUp('w')
                    safe_combat_timer = time.time()
                    current_state = "PATROL"
                    time.sleep(COMBAT_SLEEP)
                    continue

                # 判断怪物是否死亡或丢失
                if not has_target or t_hp_pct == 0:
                    print("💀 目标倒地或脱战，战斗结束。")
                    pydirectinput.keyUp('w')
                    pydirectinput.keyUp(KEY_BACK)  # 防止卡键
                    print_status()
                    # 主动击杀计数
                    if is_active_hunt:
                        with state.lock:
                            state.active_kills += 1
                            kills = state.active_kills
                        print(f"📊 主动击杀计数: {kills}/{MAX_ACTIVE_KILLS}")
                        is_active_hunt = False
                    current_state = "找尸体"
                    loot_start_time = time.time()
                    loot_click_pos = None

                time.sleep(COMBAT_SLEEP)
                continue

            # --- 找尸体 ---
            if current_state == "找尸体":
                elapsed = time.time() - loot_start_time
                if elapsed > 5.0:
                    print("⏰ 5秒内未找到尸体，继续巡逻")
                    with state.lock:
                        state.shiti_found = False
                        state.shiti_box = None
                    current_state = "PATROL"
                    continue

                # 用尸体模型扫描当前画面
                screenshot = pyautogui.screenshot()
                frame_s = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                results_s = shiti_model.predict(source=frame_s, conf=0.6, verbose=False)
                found_s = False
                for r in results_s:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)
                        loot_click_pos = (cx, cy)
                        found_s = True
                        break
                    if found_s:
                        break

                if found_s:
                    print(f"🦴 发现尸体！坐标: {loot_click_pos}，左键点击...")
                    pyautogui.moveTo(loot_click_pos[0], loot_click_pos[1])
                    pyautogui.click()
                    time.sleep(0.5)
                    # 验证是否点中：安全状态 + 目标HP=0
                    with state.lock:
                        _combat = state.combat
                        _t_hp = state.target_hp_pct
                        _has_t = state.has_target
                    print_status()
                    if not _combat and _has_t and _t_hp == 0:
                        print("✅ 尸体点中！右键走向尸体...")
                        pydirectinput.rightClick()
                        time.sleep(3.0)
                        print("⌨️ 按 F9 (第1次)")
                        pydirectinput.press('f9')
                        time.sleep(3.0)
                        print("⌨️ 按 F9 (第2次)")
                        pydirectinput.press('f9')
                        time.sleep(3.0)
                        print("🖱️ 重置视角（左右键同按1秒）")
                        pydirectinput.mouseDown(button='left')
                        pydirectinput.mouseDown(button='right')
                        time.sleep(1.0)
                        pydirectinput.mouseUp(button='right')
                        pydirectinput.mouseUp(button='left')
                        print("✅ 视角重置完成，继续巡逻")
                        current_state = "PATROL"
                    else:
                        print("❌ 未点中尸体（无目标或HP不为0），继续扫描...")
                else:
                    time.sleep(0.2)
                continue

            # --- PATROL ---
            if current_state == "PATROL":
                with state.lock:
                    kills = state.active_kills
                # 低血/低蓝时不主动找怪（但被攻击会在上方检测中切COMBAT）
                low_resource = (hp_pct > 0 and (hp_pct < SAFE_HP_PCT or mp_pct < SAFE_MP_PCT))
                # 达到主动击杀上限，强制继续寻路
                kill_limit_reached = (kills >= MAX_ACTIVE_KILLS)
                if kill_limit_reached and kills > 0:
                    # 到达新路点时重置计数
                    pass  # 计数重置在Navigator.tick到达路点时处理
                if enemy_found and enemy_pos and not low_resource and not kill_limit_reached:
                    print(f"👁️ 发现目标！坐标: {enemy_pos}")
                    navigator.stop()
                    click_attempts = 0
                    is_active_hunt = True
                    current_state = "FOUND_TARGET"
                    continue
                if low_resource:
                    print(f"⏸️ HP:{hp_pct}% MP:{mp_pct}% 过低，暂停主动攻击，继续寻路...")
                elif kill_limit_reached:
                    print(f"🔄 已主动击杀{kills}个目标，强制继续寻路...")
                navigator.tick()
                time.sleep(FSM_SLEEP)
                continue

            # --- FOUND_TARGET ---
            if current_state == "FOUND_TARGET":
                if not enemy_pos:
                    print("❌ 目标丢失，返回巡逻")
                    current_state = "PATROL"
                    continue
                tx, ty = enemy_pos
                locked_pos = (tx, ty)  # 死锁坐标，后续转向用此值，不受YOLO闪烁影响
                print(f"🖱️ 左键点击目标 -> ({tx}, {ty})")
                pyautogui.moveTo(tx, ty)
                pyautogui.click()
                time.sleep(CLICK_SLEEP)
                current_state = "CHECK_SELECTION"
                continue

            # --- CHECK_SELECTION ---
            if current_state == "CHECK_SELECTION":
                if has_target:
                    print("🎯 目标已选中！")
                    align_pos = enemy_pos or locked_pos  # 优先YOLO坐标，没有则用点击时锁定的坐标
                    current_state = "ALIGN_DIRECTION"
                else:
                    click_attempts += 1
                    print(f"❌ 点击无效或未选中，重试/放弃... (第{click_attempts}次)")
                    if click_attempts >= MAX_CLICK_ATTEMPTS:
                        current_state = "PATROL"
                    else:
                        current_state = "FOUND_TARGET"
                time.sleep(CHECK_SLEEP)
                continue

            # --- ALIGN_DIRECTION（强行单次转向版）---
            if current_state == "ALIGN_DIRECTION":

                # YOLO有更新就刷新记忆，否则用进入时锁定的坐标
                if enemy_pos:
                    align_pos = enemy_pos
                if not align_pos:
                    print("⚠️ 无坐标，强行进战")
                    current_state = "COMBAT"
                    continue

                ex, ey = align_pos
                print_status()

                # 小方框检测：目标太近，后退
                if SMALL_BOX[0] < ex < SMALL_BOX[2] and SMALL_BOX[1] < ey < SMALL_BOX[3]:
                    print(f"⚠️ 目标进入警戒区！后退 {BACK_DURATION}秒")
                    pydirectinput.keyDown(KEY_BACK)
                    time.sleep(BACK_DURATION)
                    pydirectinput.keyUp(KEY_BACK)
                    time.sleep(ALIGN_SLEEP)
                    continue

                # 先转一次向
                do_aim_turn(ex, ey)
                time.sleep(ALIGN_AFTER_TURN_SLEEP)

                # 再按W走到攻击距离
                if dist > ATTACK_DIST:
                    print(f"🚶 转向完成，走近中... 当前 {dist:.1f} 码")
                    pydirectinput.keyDown('w')
                    while True:
                        with state.lock:
                            dist = state.target_dist
                        if dist <= ATTACK_DIST:
                            break
                        time.sleep(0.1)
                    pydirectinput.keyUp('w')

                print("🚀 到位，强制切换 -> COMBAT")
                current_state = "COMBAT"
                continue

            time.sleep(FSM_SLEEP)

    except KeyboardInterrupt:
        print("程序结束")
    finally:
        navigator.stop()


if __name__ == "__main__":
    main_controller()
