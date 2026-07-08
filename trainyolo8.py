from ultralytics import YOLO

# 加载 YOLOv8 官方最小模型，2080Ti 跑这个飞快
model = YOLO('yolov8n.pt')

if __name__ == '__main__':
    # 开始训练！
    model.train(
        data='wow_data.yaml',   # 指向你写好的那个路径配置文件
        epochs=100,             # 练 100 遍
        imgsz=640,              # 图片缩放大小
        device=0                # 指定用你的显卡跑
    )