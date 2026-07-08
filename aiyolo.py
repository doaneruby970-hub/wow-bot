from ultralytics import YOLO
import cv2

# 1. 加载你刚练出来的模型
model = YOLO(r'.\runs\detect\train2\weights\best.pt')

# 2. 对图片进行推理 (放一张截图路径在这里)
results = model.predict(source=r'.\datasets\images\train\wow_auto_20260215_124600_31.jpg', save=True, conf=0.5)

# 3. 结果会自动保存在 runs/detect/predict 文件夹里
print("预测完成，快去 runs/detect 文件夹里看效果图！")