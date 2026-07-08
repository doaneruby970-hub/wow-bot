import pyautogui
import pydirectinput
import time
import os
import sys

# 禁用保护
pyautogui.FAILSAFE = False


def auto_click_target():
    print("-" * 30)
    print(">>> [诊断模式] 子程序启动...")

    # ================= 1. 接收参数诊断 =================
    target_name = "img_jieshou.png"  # 默认值

    # 打印原始参数，看看主程序到底传了什么进来
    print(f"   🔍 原始参数列表 sys.argv: {sys.argv}")

    if len(sys.argv) > 1:
        target_name = sys.argv[1].strip()
        print(f"   ✅ 接收到参数 (去除空格后): [{target_name}]")
    else:
        print(f"   ⚠️ 未接收到参数，使用默认值: [{target_name}]")

    # ================= 2. 路径计算诊断 =================
    # 获取当前脚本 (wow11ocr.py) 所在的 WOW 文件夹路径
    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    # 强制修正路径分隔符（防止 Windows/Mac 混淆）
    # 直接在当前 WOW 目录下拼接 imgs 文件夹和图片名
    target_img_path = os.path.join(current_script_dir, "imgs",  target_name)
    target_img_path = os.path.normpath(target_img_path)  # 标准化路径

    print(f"   📂 正在寻找图片路径: {target_img_path}")

    # 【关键】文件存在性检查
    if not os.path.exists(target_img_path):
        print("   ❌❌❌ 致命错误：文件路径不存在！")
        print("   👉 请检查：")
        print("   1. 图片名字是否写对？(大小写敏感)")
        print("   2. 文件夹结构是否是 GameBot/imgs/actions/ ？")
        print("   3. 文件名后是否有隐藏的空格？")
        return  # 直接结束

    print("   ✅ 图片文件存在，准备识图...")

    # ================= 3. 循环找图 =================
    start_t = time.time()
    timeout = 30

    print("   👀 开始扫描屏幕... (请确保游戏未被遮挡)")

    while True:
        if time.time() - start_t > timeout:
            print("   ⌛ 超时未找到。")
            # 调试技巧：找不到时截图，看看机器到底看到了什么
            debug_shot = f"debug_fail_{int(time.time())}.png"
            try:
                pyautogui.screenshot(debug_shot)
                print(f"   📸 已保存当前屏幕截图为: {debug_shot} (请查看此图是否包含目标)")
            except:
                pass
            break

        try:
            # 这里的 confidence 如果太高(0.9)容易找不到，太低(0.5)容易乱点
            box = pyautogui.locateOnScreen(
                target_img_path,
                confidence=0.8,
                grayscale=True
            )

            if box is not None:
                center_x = int(box.left + box.width / 2)
                center_y = int(box.top + box.height / 2)

                print(f"   ✅ 找到目标! 坐标: ({center_x}, {center_y})")

                pydirectinput.moveTo(center_x, center_y)
                time.sleep(0.1)
                pydirectinput.click()
                time.sleep(1.0)

                print("   👋 点击完成。")
                break
            else:
                # 可以在这里打印个点，证明程序在活着
                # print(".", end="", flush=True)
                time.sleep(0.1)

        except Exception as e:
            print(f"   ⚠️ 报错: {e}")
            time.sleep(0.1)

    print("-" * 30)


if __name__ == "__main__":
    auto_click_target()