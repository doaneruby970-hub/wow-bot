import os
import re


def get_unlocked_flight_points():
    file_path = r"G:\World of Warcraft\_classic_titan_\WTF\Account\617688853#1\SavedVariables\EnhancedFlightMap.lua"

    if not os.path.exists(file_path):
        print(f"❌ 找不到文件:\n{file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return []

    # 1. 抓取所有作为主节点记录的地名 ["name"] = "xxx"
    main_nodes = re.findall(r'\["name"\]\s*=\s*"([^"]+)"', content)

    # 2. 抓取所有藏在 routes (航线) 里面的地名
    # 先把 ["routes"] = { ... } 整个块切出来
    routes_blocks = re.findall(r'\["routes"\]\s*=\s*\{([^}]+)\}', content)

    route_nodes = []
    for block in routes_blocks:
        # 再把块里面被双引号包围的地名提出来
        nodes_in_block = re.findall(r'"([^"]+)"', block)
        route_nodes.extend(nodes_in_block)

    # 3. 将两部分合并，并使用 set 去重（防止主节点和航线里有重复项）
    all_unlocked_fps = list(set(main_nodes + route_nodes))

    return all_unlocked_fps


if __name__ == "__main__":
    print("🚀 开始读取飞行点数据库...")
    my_flights = get_unlocked_flight_points()

    if my_flights:
        print(f"\n✅ 成功获取！共找到 {len(my_flights)} 个已开通的飞行点：")
        for i, fp in enumerate(my_flights, 1):
            print(f"  [{i}] {fp}")
    else:
        print("\n⚠️ 飞行点列表为空，请确认是否记录成功。")