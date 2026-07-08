import pyautogui
import time

# 取色点坐标
HS_P = (10, 10); BUFF_P = (30, 10); RES_P = (50, 10)

def main():
    print("--- 启动最终版监控 (炉石/霜甲术/虚弱) ---")
    while True:
        try:
            r_hs, _, _ = pyautogui.pixel(*HS_P)
            r_bf, g_bf, b_bf = pyautogui.pixel(*BUFF_P)
            r_rs, g_rs, b_rs = pyautogui.pixel(*RES_P)

            # 1. 炉石
            hs = "【可用】" if r_hs > 127 else "冷却中"

            # 2. 霜甲术：只要蓝色通道亮了，说明Buff存在
            if b_bf > 127:
                buff = f"剩余 {r_bf}分 {g_bf}秒" if r_bf < 255 else "永久/异常"
            else:
                buff = "【未开启】" # 此时屏幕上是纯绿色

            # 3. 复活虚弱：只要红色通道亮了，说明虚弱存在
            if r_rs > 127:
                res = f"【虚弱中】剩余 {g_rs}分 {b_rs}秒"
            else:
                res = "正常" # 此时屏幕上是纯黑色

            print(f"炉石:{hs} | 霜甲:{buff} | 状态:{res}          ", end="\r")
        except Exception as e:
            pass
        time.sleep(1)

if __name__ == "__main__":
    main()