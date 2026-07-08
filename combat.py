import pyautogui
import time

print("请在 3 秒内把鼠标指在【最左边】那个信号方块上...")
time.sleep(3)
x, y = pyautogui.position()
print(f"你的起始坐标是: START_X = {x}, START_Y = {y}")