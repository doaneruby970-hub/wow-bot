import os

# 这是你的标签路径，我已经根据你的截图写好了
label_paths = [
    r'.\WoW_Project\shiti\labels\train',
    r'.\WoW_Project\shiti\labels\val'
]

for path in label_paths:
    if not os.path.exists(path):
        continue
    for file in os.listdir(path):
        if file.endswith('.txt') and '-' in file:
            # 删掉横杠及其前面的乱码
            new_name = file.split('-', 1)[1]
            os.rename(os.path.join(path, file), os.path.join(path, new_name))
            print(f"更名成功: {new_name}")

print("✅ 文件名已洗白，现在图片和标签能对上了！")