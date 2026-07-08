import os
from ultralytics import YOLOWorld

model = YOLOWorld('yolov8s-worldv2.pt')

# 尝试更换更简单的描述词
# 换成这些最简单的现实世界词汇，看看它认不认
model.set_classes(["creature", "small red rectangle", "dead animal"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "datasets", "train", "val")
LABEL_DIR = os.path.join(BASE_DIR, "datasets", "val", "val")


def debug_labeling():
    images = [f for f in os.listdir(IMG_DIR) if f.endswith(('.jpg', '.png'))]

    for img_name in images:
        img_path = os.path.join(IMG_DIR, img_name)

        # 调整：将 conf 降到 0.1，并开启 save=True 来生成带框的预览图
        results = model.predict(img_path, conf=0.1, save=True, project="debug_labels")

        txt_name = os.path.splitext(img_name)[0] + ".txt"
        txt_path = os.path.join(LABEL_DIR, txt_name)

        with open(txt_path, 'w') as f:
            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    xywhn = box.xywhn[0].tolist()
                    f.write(f"{cls} {xywhn[0]:.6f} {xywhn[1]:.6f} {xywhn[2]:.6f} {xywhn[3]:.6f}\n")

    print(f"检查完成！请查看项目文件夹下的 'debug_labels' 文件夹，看看 AI 到底圈中没。")


if __name__ == "__main__":
    debug_labeling()