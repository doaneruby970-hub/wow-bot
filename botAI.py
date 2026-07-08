import threading
import time
import math
import cv2
import numpy as np
import pyautogui
import pydirectinput
import keyboard
import ctypes
from ultralytics import YOLO
from PIL import ImageDraw

# 引入你原本的坐标读取模块 (假设文件名叫 zuobiaoxianshi.py)
try:
    from zuobiaoxianshi import get_game_data
except ImportError:
    print("❌ 警告：未找到 zuobiaoxianshi.py，导航模块将无法获取坐标！")
    get_game_data = lambda: (0, 0, 0, 0)  # 替补桩

# ==========================================
#              1. 全局配置区
# ==========================================
MODEL_PATH = r'.\runs\detect\train2\weights\best.pt'  # 修改为你的路径
ATTACK_KEY = '1'  # 攻击键
EAT_KEY = '8'  # 吃喝键
STOP_KEY = 'page down'  # 停止脚本键

# 屏幕参数 (请根据实际分辨率修改)
SCREEN_W, SCREEN_H = 1920, 1080
CENTER_X, CENTER_Y = SCREEN_W // 2, SCREEN_H // 2

# 扇形攻击区配置
FAN_WIDTH = 400  # 屏幕中心左右各200像素算作“瞄准了”
ATTACK_DIST = 30.0  # 攻击距离
SAFE_HP_PCT = 40  # 低于多少血量开始恢复
FULL_HP_PCT = 90  # 恢复到多少血量继续挂机


# ==========================================
#              2. 共享数据区 (线程通信)
# ==========================================
class SharedState:
    def __init__(self):
        # 互斥锁，防止数据读写冲突
        self.lock = threading.Lock()

        # --- 状态数据 (来自数值读取线程) ---
        self.hp = 100
        self.mp = 100
        self.combat = False  # 是否进战
        self.has_target = False  # 是否有目标
        self.target_dist = 999  # 目标距离
        self.target_hp_pct = 0  # 目标血量

        # --- 视觉数据 (来自 YOLO 线程) ---
        self.enemy_found = False  # 是否发现红名
        self.enemy_box = None  # [x, y, w, h] 屏幕坐标

        # --- 控制指令 ---
        self.current_fsm_state = "INIT"  # 当前状态机状态

    def update_status(self, d):
        with self.lock:
            self.hp = d.get('hp', 0)
            self.mp = d.get('mp', 0)
            self.combat = d.get('combat', False)
            self.has_target = d.get('has_target', False)
            self.target_dist = d.get('distance', 999)
            self.target_hp_pct = d.get('t_hp_pct', 0)

    def update_enemy(self, found, box=None):
        with self.lock:
            self.enemy_found = found
            self.enemy_box = box


state = SharedState()


# ==========================================
#           3. 线程模块 A: 数值仪表盘
# ==========================================
# (原本的 Xueliangshuzhi.py 逻辑)
def thread_status_reader():
    print(">>> [线程A] 数值仪表盘启动...")

    # 1. 开启高分屏支持 & 寻找锚点 (复用你原本的代码逻辑)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        ctypes.windll.user32.SetProcessDPIAware()

    ESTIMATED_BLOCK_SIZE = 20
    # ... (这里省略寻找锚点的代码，为了简洁，假设已经找到) ...
    # 请务必把你原代码中的 find_anchor_and_width() 函数逻辑放进来
    # 这里我们模拟一个已找到的状态，实际使用请替换为你的完整扫描代码
    ax, ay, block_w = 100, 100, 20  # 假设值，请替换！

    # 模拟原 read_data 函数
    def read_pixel_data():
        # 这里应该填入你 Xueliangshuzhi.py 里 read_data 的完整代码
        # 为了演示，我写一个伪代码调用
        # return real_read_data(ax, ay, block_w)

        # ⚠️ 实际运行时，请把你的 read_data 函数原封不动搬进来
        # 这里我仅做占位，避免代码太长
        return {
            'hp': 100, 'mp': 100, 'combat': False,
            'has_target': False, 'distance': 0, 't_hp_pct': 0
        }

    while True:
        try:
            # 真正的读取逻辑（请替换为你的 read_data 调用）
            # d = read_data(ax, ay, block_w)

            # 这里为了不报错，我用占位符。请务必替换回你的真实函数！
            # 假设你的 read_data 已经能返回正确字典
            # d = ...

            # 将读取到的数据更新到全局共享区
            # state.update_status(d)

            time.sleep(0.05)  # 高频刷新
        except Exception as e:
            print(f"数值线程出错: {e}")
            time.sleep(1)


# ==========================================
#           4. 线程模块 B: 视觉雷达 (YOLO)
# ==========================================
# (原本的 hunter_logicAI.py 逻辑)
def thread_yolo_scanner():
    print(">>> [线程B] YOLO视觉雷达启动...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    while True:
        # 性能优化：如果已经正在打怪(COMBAT状态)，就暂停扫描，省CPU
        if state.current_fsm_state in ["COMBAT", "RECOVERY"]:
            time.sleep(0.5)
            continue

        try:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            results = model.predict(source=frame, conf=0.5, verbose=False)

            found = False
            target_box = None

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    # 假设 1 是红名怪
                    if cls == 1:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        center_x = int((x1 + x2) / 2)
                        center_y = int((y1 + y2) / 2)

                        # 简单的过滤：只找离屏幕中心最近的，或者特定区域的
                        found = True
                        target_box = (center_x, center_y)
                        break  # 只锁一个
                if found: break

            # 更新共享数据
            state.update_enemy(found, target_box)

            # 扫描频率控制（太快没必要）
            time.sleep(0.2)

        except Exception as e:
            print(f"YOLO线程出错: {e}")
            time.sleep(1)


# ==========================================
#           5. 辅助模块 C: 导航逻辑封装
# ==========================================
# (原本的 zuobiaoxunlubofang.py 逻辑，改为单步执行)
class Navigator:
    def __init__(self):
        self.path_nodes = []
        self.current_idx = 0
        self.target_map_id = 0
        self.w_pressed = False  # 记录W键状态

    def load_path(self, map_id):
        import json
        import os
        filename = f"paths/map_{map_id}.json"
        print(f"📂 正在读取文件: {filename}")
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.path_nodes = json.load(f)
                self.current_idx = 0
                self.target_map_id = map_id
                print(f"✅ 成功加载路书，共 {len(self.path_nodes)} 个节点")
            except Exception as e:
                print(f"❌ 文件格式错误: {e}")
        else:
            print(f"❌ 找不到路书文件: {filename}")

    def stop(self):
        """紧急停车"""
        if self.w_pressed:
            pydirectinput.keyUp('w')
            self.w_pressed = False
        pydirectinput.keyUp('a')
        pydirectinput.keyUp('d')

    def tick(self):
        """
        执行导航逻辑：计算一次角度，移动一步
        """
        # 1. 获取当前位置
        curr_x, curr_y, curr_face_rad, map_id = get_game_data()

        # 异常数据保护
        if curr_x == 0 and curr_y == 0:
            return

        # 2. 如果没路书，尝试加载
        if not self.path_nodes:
            if map_id > 0:
                self.load_path(map_id)
            return

        # 3. 检查是否跑完了
        if self.current_idx >= len(self.path_nodes):
            print("🏁 终点已到达！")
            self.stop()
            self.path_nodes = []  # 清空以停止
            return

        # 4. 获取目标点
        target_x, target_y = self.path_nodes[self.current_idx]

        # 5. 数学计算 (完全复用你原来的公式)
        dist = math.sqrt((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2)

        # 计算目标角度
        angle_rad = math.atan2(-(target_x - curr_x), curr_y - target_y)
        target_deg = math.degrees(angle_rad)
        if target_deg < 0: target_deg += 360

        # 计算当前角度
        curr_deg = math.degrees(curr_face_rad)

        # 计算最小转向角 (-180 到 180)
        angle_diff = (target_deg - curr_deg + 180) % 360 - 180

        # Debug 输出 (可选，太刷屏可以注释掉)
        # print(f"📍 目标:{self.current_idx} | 距离:{dist:.1f} | 角度差:{angle_diff:.1f}")

        # 6. 到达判断 (阈值可调，建议 0.5)
        if dist < 0.5:
            print(f"✨ 到达路点 {self.current_idx + 1}")
            self.current_idx += 1
            return  # 这一帧先不动，下一帧去新目标

        # 7. 移动控制逻辑
        # 如果角度偏差太大 (> 30度)，先原地转向
        if abs(angle_diff) > 30:
            if self.w_pressed:
                pydirectinput.keyUp('w')
                self.w_pressed = False

            # 点按转向
            key = 'a' if angle_diff > 0 else 'd'  # WoW坐标系通常这样，如果是反的请互换
            pydirectinput.keyDown(key)
            time.sleep(0.02)  # 短按
            pydirectinput.keyUp(key)

        # 角度合适，前进
        else:
            if not self.w_pressed:
                pydirectinput.keyDown('w')
                self.w_pressed = True

            # 微调方向 (边跑边转)
            if abs(angle_diff) > 5:
                key = 'a' if angle_diff > 0 else 'd'
                pydirectinput.keyDown(key)
                time.sleep(0.01)  # 极短按
                pydirectinput.keyUp(key)


navigator = Navigator()


# ==========================================
#           6. 主大脑: 有限状态机 (FSM)
# ==========================================
def main_controller():
    print("🧠 主控大脑已连接...")

    # 启动子线程
    t1 = threading.Thread(target=thread_status_reader, daemon=True)
    t2 = threading.Thread(target=thread_yolo_scanner, daemon=True)
    t1.start()
    t2.start()

    print("✅ 系统就绪，5秒后开始运行...")
    time.sleep(5)

    current_state = "PATROL"  # 初始状态：巡逻

    try:
        while True:
            if keyboard.is_pressed(STOP_KEY):
                print("🛑 手动停止！")
                navigator.stop()
                break

            # 更新 FSM 状态记录，方便其他线程读取
            state.current_fsm_state = current_state

            # 获取最新数据快照（原子操作）
            with state.lock:
                hp = state.hp
                combat = state.combat
                has_target = state.has_target
                dist = state.target_dist
                enemy_found = state.enemy_found
                enemy_pos = state.enemy_box  # (x, y)

            # ======================================
            #           状态机逻辑流
            # ======================================

            # --- 状态 0: 紧急生存检测 ---
            if hp < SAFE_HP_PCT and not combat:
                if current_state != "RECOVERY":
                    print(f"⚠️ 血量危 ({hp}%)，进入恢复模式...")
                    navigator.stop()
                    current_state = "RECOVERY"

            # --- 状态 1: 战后恢复 (RECOVERY) ---
            if current_state == "RECOVERY":
                if hp >= FULL_HP_PCT:
                    print("✅ 血量恢复完毕，继续巡逻。")
                    pydirectinput.press('space')  # 跳一下取消坐地
                    current_state = "PATROL"
                else:
                    # 应该加入判断是否已经坐下的逻辑（通常通过 buff 或简单的按键）
                    # 简单处理：每隔几秒按一次吃喝
                    print(f"💤 休息中... HP: {hp}%")
                    pydirectinput.press(EAT_KEY)
                    time.sleep(2)
                continue

            # --- 状态 2: 战斗中 (COMBAT) ---
            # 无论之前在干嘛，只要游戏显示进战，强制切入战斗
            if combat:
                current_state = "COMBAT"  # 强制覆盖
                # 战斗逻辑：输出循环
                print(f"⚔️ 战斗中 | 目标HP: {state.target_hp_pct}% | 距离: {dist}")

                # 1. 面向调整 (简单版)
                # 如果有目标但距离太远，或者是背对，需要这里处理
                # 但主要依靠“调整方向”状态来做精细操作，这里只负责按技能

                # 2. 距离判断
                if dist > ATTACK_DIST:
                    pydirectinput.keyDown('w')  # 追击
                else:
                    pydirectinput.keyUp('w')  # 站桩

                pydirectinput.press(ATTACK_KEY)
                time.sleep(0.2)  # GCD

                # 3. 战斗结束检查
                if not has_target:  # 怪死了
                    print("💀 目标倒地，战斗结束。")
                    pydirectinput.keyUp('w')
                    current_state = "PATROL"
                continue

            # --- 状态 3: 巡逻 (PATROL) ---
            if current_state == "PATROL":
                # 优先级检测：如果 YOLO 发现了怪
                if enemy_found and enemy_pos:
                    print(f"👁️ 发现目标！坐标: {enemy_pos}")
                    # 1. 立即停车
                    navigator.stop()
                    # 2. 切换状态
                    current_state = "FOUND_TARGET"
                    continue

                # 正常巡逻
                # print("🚶 巡逻中...")
                navigator.tick()
                time.sleep(0.05)
                continue

            # --- 状态 4: 发现目标并点击 (FOUND_TARGET) ---
            if current_state == "FOUND_TARGET":
                if not enemy_pos:
                    print("❌ 目标丢失（可能YOLO误报），返回巡逻")
                    current_state = "PATROL"
                    continue

                tx, ty = enemy_pos
                print(f"🖱️ 点击目标 -> ({tx}, {ty})")

                # 移动鼠标点击
                pyautogui.moveTo(tx, ty)
                pyautogui.rightClick()

                # 这里的 sleep 很重要，给游戏UI反应时间
                time.sleep(0.5)

                current_state = "CHECK_SELECTION"
                continue

            # --- 状态 5: 验证选中 (CHECK_SELECTION) ---
            if current_state == "CHECK_SELECTION":
                # 检查数值模块是否读到了距离（说明选中了）
                if has_target and dist > 0:
                    print(f"✅ 成功锁定目标！距离: {dist} 码")
                    current_state = "ALIGN_DIRECTION"
                else:
                    print("❌ 点击无效或未选中，重试/放弃...")
                    # 这里可以做一个重试计数器，为了简单直接放弃
                    current_state = "PATROL"
                continue

            # --- 状态 6: 调整方向与扇形判定 (ALIGN_DIRECTION) ---
            if current_state == "ALIGN_DIRECTION":
                # 这是你要求的核心：扇形对齐 + 距离控制

                # 1. 再次看 YOLO 确定目标现在的屏幕位置（用于对齐）
                # 注意：此时可能需要 YOLO 再次确认位置，或者直接用“选中目标”的像素逻辑
                # 简单起见，假设我们看屏幕中心

                # 理想情况：这里应该结合 YOLO 实时更新的 enemy_pos
                # 如果 YOLO 此时没数据（比如怪被UI挡住），尝试用键盘转向找

                aligned = False

                # 假设 enemy_pos 还在更新
                if enemy_pos:
                    ex, ey = enemy_pos
                    # 计算偏差
                    offset_x = ex - CENTER_X

                    if abs(offset_x) < (FAN_WIDTH // 2):
                        print("👌 目标已在扇形攻击面内")
                        pydirectinput.keyUp('a')
                        pydirectinput.keyUp('d')
                        aligned = True
                    elif offset_x < 0:
                        print("⬅️ 向左修正方向")
                        pydirectinput.keyDown('a')
                        time.sleep(0.05)
                        pydirectinput.keyUp('a')
                    else:
                        print("➡️ 向右修正方向")
                        pydirectinput.keyDown('d')
                        time.sleep(0.05)
                        pydirectinput.keyUp('d')
                else:
                    # 如果丢失视觉，直接依靠距离判断盲打，或者按D找怪
                    pass

                # 2. 距离判断
                if aligned:
                    if dist > ATTACK_DIST:
                        print(f"🏃 接近中... 距离 {dist}")
                        pydirectinput.keyDown('w')
                        time.sleep(0.1)
                        pydirectinput.keyUp('w')
                    else:
                        print("💥 进入射程，开火！")
                        current_state = "COMBAT"

                time.sleep(0.1)
                continue

            # 兜底 sleep
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("程序结束")
    finally:
        navigator.stop()


if __name__ == "__main__":
    main_controller()