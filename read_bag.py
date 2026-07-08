import re
import os

# ================= 配置区域 =================
FILE_PATH = r"G:\World of Warcraft\_classic_titan_\WTF\Account\617688853#1\SavedVariables\MyBag.lua"


# ===========================================

def parse_wow_data():
    if not os.path.exists(FILE_PATH):
        print(f"找不到文件，请确认路径。")
        return

    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 提取汇总信息
    free_slots = re.search(r'\["free"\] = (\d+)', content)
    total_slots = re.search(r'\["total"\] = (\d+)', content)
    print("--- 背包状态汇总 ---")
    if free_slots and total_slots:
        print(f"总格子: {total_slots.group(1)} | 剩余空间: {free_slots.group(1)}")
        print(f"是否已满: {'是' if free_slots.group(1) == '0' else '否'}")

    print("\n--- 物品详细清单 ---")

    # 2. 改进后的智能提取逻辑
    # 先把整个 items 列表区域切出来
    items_section = re.search(r'\["items"\] = \{(.*?)\},\s+\["summary"\]', content, re.DOTALL)
    if not items_section:
        # 如果 summary 在前面，尝试另一种切法
        items_section = re.search(r'\["items"\] = \{(.*)\}', content, re.DOTALL)

    if items_section:
        section_text = items_section.group(1)
        # 找到每一个物品的数据块 { ... }
        item_blocks = re.findall(r'\{(.*?)\}', section_text, re.DOTALL)

        count_found = 0
        for block in item_blocks:
            # 在每个数据块里分别找 name, count, id，不管它们顺序如何
            name_match = re.search(r'\["name"\] = "(.*?)"', block)
            count_match = re.search(r'\["count"\] = (\d+)', block)
            id_match = re.search(r'\["id"\] = (\d+)', block)

            if name_match:
                name = name_match.group(1)
                count = count_match.group(1) if count_match else "1"
                item_id = id_match.group(1) if id_match else "0"
                print(f"物品: {name.ljust(15)} | 数量: {count.ljust(3)} | ID: {item_id}")
                count_found += 1

        if count_found == 0:
            print("清单解析失败，可能文件格式有变。")
    else:
        print("未发现物品清单区域。")


if __name__ == "__main__":
    parse_wow_data()