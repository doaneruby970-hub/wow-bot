import pydirectinput
import time
from ultralytics import YOLO

# 1. 核心：使用绝对路径，确保在哪都能运行
model_path = r'.\WoW_Project\runs\detect\wow_shiti_v1\weights\best.pt'
model = YOLO(model_path)

# 2. 游戏控制设置
pydirectinput.FAILSAFE = False


def start_bot():
    print("🚀 脚本实战启动中...")
    # 增加 stream=True 防止内存溢出，conf=0.6 提高准确度
    results = model.predict(source='screen', conf=0.6, stream=True)

    for r in results:
        boxes = r.boxes
        if len(boxes) > 0:
            # 拿到第一个 shiti 目标的坐标
            x, y, w, h = boxes[0].xywh[0].tolist()

            print(f"🎯 坐标锁定: ({int(x)}, {int(y)})，执行右键点击")

            # 3. 执行点击
            pydirectinput.moveTo(int(x), int(y))
            time.sleep(0.1)
            pydirectinput.rightClick()

            # 点击后必须停顿，否则会因为检测太快导致重复点击
            print("✅ 拾取中，暂停 2 秒...")
            time.sleep(2.0)
        else:
            # 没怪时别跑太快，稍微缓一下
            time.sleep(0.2)


if __name__ == "__main__":
    # 给自己预留切换到游戏的时间
    print("请在 3 秒内切换至魔兽窗口...")
    time.sleep(3)
    start_bot()