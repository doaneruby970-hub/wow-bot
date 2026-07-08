import pyautogui
import pydirectinput
import time
import os
import sys

# 禁用保护
pyautogui.FAILSAFE = False


def auto_click_target(img_name=None, timeout=30, optional=False):
    """
    图像识别点击函数

    参数:
        img_name: 图片名称
        timeout: 超时时间（秒），默认30秒
        optional: 可选模式，True时找不到图片不报错，默认False
    """
    if not optional:
        print("-" * 30)
        print(">>> [诊断模式] 子程序启动...")

    # ================= 1. 接收参数诊断 =================
    target_name = "img_4.png"  # 默认值

    if img_name is not None:
        # 直接传参调用（被 Master.py 的 run_sequence 调用）
        target_name = img_name.strip()
        if not optional:
            print(f"   ✅ 接收到直接传参: [{target_name}]")
    else:
        # 命令行调用（独立运行时）
        if not optional:
            print(f"   🔍 原始参数列表 sys.argv: {sys.argv}")
        if len(sys.argv) > 1:
            target_name = sys.argv[1].strip()
            if not optional:
                print(f"   ✅ 接收到参数 (去除空格后): [{target_name}]")
        else:
            if not optional:
                print(f"   ⚠️ 未接收到参数，使用默认值: [{target_name}]")

    # ================= 2. 路径计算诊断 =================
    # 获取当前脚本 (wow11ocr.py) 所在的 WOW 文件夹路径
    current_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 强制修正路径分隔符（防止 Windows/Mac 混淆）
    # 直接在当前 WOW 目录下拼接 imgs 文件夹和图片名
    target_img_path = os.path.join(current_script_dir, "imgs", target_name)
    target_img_path = os.path.normpath(target_img_path)  # 标准化路径

    if not optional:
        print(f"   📂 正在寻找图片路径: {target_img_path}")

    # 【关键】文件存在性检查
    if not os.path.exists(target_img_path):
        if not optional:
            print("   ❌❌❌ 致命错误：文件路径不存在！")
            print("   👉 请检查：")
            print("   1. 图片名字是否写对？(大小写敏感)")
            print("   2. 文件夹结构是否是 GameBot/imgs/actions/ ？")
            print("   3. 文件名后是否有隐藏的空格？")
        return False  # 返回False表示失败

    if not optional:
        print("   ✅ 图片文件存在，准备识图...")

    # ================= 3. 循环找图 =================
    start_t = time.time()

    if not optional:
        print("   👀 开始扫描屏幕... (请确保游戏未被遮挡)")
    else:
        print(f"      🔍 尝试查找图片（{timeout}秒超时）: {target_name}")

    while True:
        if time.time() - start_t > timeout:
            if optional:
                print(f"      ⏭️ 未找到图片，跳过: {target_name}")
                return False
            else:
                print("   ⌛ 超时未找到。")
                # 调试技巧：找不到时截图，看看机器到底看到了什么
                debug_shot = f"debug_fail_{int(time.time())}.png"
                try:
                    pyautogui.screenshot(debug_shot)
                    print(f"   📸 已保存当前屏幕截图为: {debug_shot} (请查看此图是否包含目标)")
                except:
                    pass
                return False

        try:
            # 这里的 confidence 如果太高(0.9)容易找不到，太低(0.5)容易乱点
            box = pyautogui.locateOnScreen(
                target_img_path,
                confidence=0.85,
                grayscale=True
            )

            if box is not None:
                center_x = int(box.left + box.width / 2)
                center_y = int(box.top + box.height / 2)

                if optional:
                    print(f"      ✅ 找到并点击: {target_name}")
                else:
                    print(f"   ✅ 找到目标! 坐标: ({center_x}, {center_y})")

                pydirectinput.moveTo(center_x, center_y)
                time.sleep(0.1)
                pydirectinput.click()
                time.sleep(1.0)

                if not optional:
                    print("   👋 点击完成。")
                return True
            else:
                # 可以在这里打印个点，证明程序在活着
                # print(".", end="", flush=True)
                time.sleep(0.5)

        except Exception as e:
            if not optional:
                print(f"   ⚠️ 报错: {e}")
            time.sleep(0.5)

    if not optional:
        print("-" * 30)
    return False


def check_image_exists(img_name, timeout=0.5):
    """
    检测图片是否存在（不点击）

    参数:
        img_name: 图片名称
        timeout: 检测超时时间（秒），默认0.5秒

    返回:
        True: 图片存在
        False: 图片不存在
    """
    # 计算图片路径
    current_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_img_path = os.path.join(current_script_dir, "imgs", img_name)
    target_img_path = os.path.normpath(target_img_path)

    # 检查文件是否存在
    if not os.path.exists(target_img_path):
        return False

    # 检测图片
    start_t = time.time()
    while time.time() - start_t < timeout:
        try:
            box = pyautogui.locateOnScreen(
                target_img_path,
                confidence=0.7,
                grayscale=True
            )
            if box is not None:
                return True
        except:
            pass
        time.sleep(0.1)

    return False


if __name__ == "__main__":
    auto_click_target()