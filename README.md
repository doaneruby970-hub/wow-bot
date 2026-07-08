# wow-bot

魔兽世界（WoW Classic）自动化机器人。基于像素级屏幕读取、YOLOv8 视觉识别、坐标路书导航和有限状态机（FSM）战斗逻辑，实现从打怪、寻路、拾取到回城补给的全自动挂机流程。

## 功能特性

- **游戏状态读取** -- 通过 WoW 插件 `MyMonitor` 在屏幕顶部绘制像素色块，Python 端截图解码获取：玩家坐标、朝向、地图 ID、HP/MP 数值与百分比、战斗状态、目标血量、目标距离、玩家等级等实时数据
- **YOLOv8 视觉识别** -- 训练并部署 YOLO 模型，识别屏幕上的红名怪物血条和尸体，用于索敌和拾取
- **坐标路书录制与播放** -- 手动跑图时按时间间隔录制坐标到 JSON 路书文件，自动导航时按路点依次寻路，支持原地转向 + 直线行进的坦克式导航
- **FSM 战斗状态机** -- 巡逻（PATROL） -> 发现目标（FOUND_TARGET） -> 点击选中（CHECK_SELECTION） -> 方向对齐（ALIGN_DIRECTION） -> 战斗（COMBAT） -> 找尸体拾取 -> 恢复（RECOVERY）的完整循环
- **分区域扇形转向** -- 根据目标在屏幕上的远/中/近位置，使用不同倍率的键盘转向时长，精准对准目标
- **背对/重合检测** -- 战斗中若持续攻击但目标未掉血，自动后退拉开距离重新站位
- **主调度器** -- `Master.py` 按等级区间分阶段调度跑路和打怪脚本，支持死亡复活、背包满回城、飞行点开通等特殊任务，以及基于 TXT 序列文件的可编程动作编排
- **OCR 识图点击** -- 基于 pyautogui 模板匹配，识别并点击游戏 UI 按钮（如接受任务、确认对话框等）
- **背包监控** -- 解析 WoW SavedVariables 的 `MyBag.lua`，实时监控背包空余格数
- **训练数据采集** -- 自动间隔截图工具，用于采集 YOLO 训练样本

## 环境要求

- Windows 10/11
- Python 3.8+
- NVIDIA 显卡（YOLO 推理/训练推荐，CPU 也可运行但较慢）
- 魔兽世界经典怀旧服（WoW Classic）

### Python 依赖

核心依赖包：

```
ultralytics>=8.0.0
opencv-python
numpy
pyautogui
pydirectinput
keyboard
pillow
mss
pywin32
```

安装命令：

```bash
pip install ultralytics opencv-python numpy pyautogui pydirectinput keyboard pillow mss pywin32
```

## 安装

```bash
git clone <repo-url> wow-bot
cd wow-bot
pip install ultralytics opencv-python numpy pyautogui pydirectinput keyboard pillow mss pywin32
```

## 配置

### 1. 安装 WoW 插件

将项目根目录下的 `MyMonitor` 插件文件夹放入魔兽世界的 `Interface/AddOns/` 目录。该插件依赖 `RangeDisplay` 插件提供测距功能，请一并安装。

**插件结构：**
```
World of Warcraft\_classic_\Interface\AddOns\MyMonitor\
    MyMonitor.toc
    MyMonitor.lua
```

### 2. 训练 YOLO 模型

项目需要两个 YOLO 模型：

- **怪物血条检测模型**：识别屏幕上的红名怪物。使用 `trainyolo8.py` 训练，数据集配置在 `wow_data.yaml`（类别：0=monster, 1=red_health_bar, 2=yellow_health_bar）
- **尸体检测模型**：识别地面上的怪物尸体用于拾取。需单独训练

模型路径在 `botAIclaude.py` 中配置：

```python
MODEL_PATH = r'.\runs\detect\train2\weights\best.pt'          # 怪物血条检测
SHITI_MODEL_PATH = r'.\WoW_Project\runs\detect\wow_shiti_v1\weights\best.pt'  # 尸体检测
```

### 3. 录制路书

使用 `zuobiaoluzhi.py` 手动跑图录制坐标路书。跑图过程中按时间间隔自动记录坐标到 `paths/map_{地图ID}.json`。

```bash
python zuobiaoluzhi.py
# 手动控制角色移动到目标路线
# 按 Q 保存并退出
```

### 4. 配置调度计划

编辑 `AAwow111/plan.txt`（格式：`最低等级/最高等级/跑路文件/打怪文件/回城序列/死亡序列/起点序列`）和 `AAwow111/tasks.txt`（格式：`任务ID/触发等级/类型/描述/序列文件`）来设定自动化流程。

## 使用方式

### 单脚本运行

```bash
# 坐标导航回放（从 paths/ 目录选择路书）
python zuobiaoxunlubofang.py

# 手动录制坐标路书
python zuobiaoluzhi.py

# 实时坐标显示
python zuobiaoxianshi.py

# 数值仪表盘（HP/MP/状态）
python xueliangshuzhi.py

# YOLO 视觉猎人（自动索敌攻击）
python hunter_logicAI.py

# 完整 FSM 战斗机器人（导航+战斗+拾取）
python botAIclaude.py

# 训练数据采集截图
python jietu.py

# YOLO 模型训练
python trainyolo8.py
```

### 全自动调度运行

```bash
cd AAwow111
python Master.py
```

`Master.py` 将自动按照 `plan.txt` 的等级区间分阶段运行跑路和打怪脚本，并处理死亡复活、背包满回城等事件。

## 项目结构

```
wow-bot/
├── MyMonitor.lua / .toc          # WoW 插件：将游戏数据编码为屏幕顶部像素色块
├── zuobiaoxianshi.py             # 坐标/朝向/地图ID 读取模块
├── xueliangshuzhi.py             # HP/MP/战斗状态等数值读取模块
├── botAIclaude.py                # 完整 FSM 战斗机器人（导航+索敌+战斗+拾取+恢复）
├── botAI.py                      # 早期版 FSM 战斗机器人
├── hunter_logicAI.py             # YOLO 实时索敌攻击脚本
├── zuobiaoluzhi.py               # 坐标路书录制工具
├── zuobiaoxunlubofang.py         # 坐标导航回放（手动选路书）
├── zuobiaoxunlubofang11.py       # 导航回放（跨图冲刺模式）
├── zuobiaoxunlubofang22.py       # 导航回放（主城高精度模式）
├── zuobiaomianxiang.py           # 坐标+面向 精确录制
├── zuobiaomianxiangbofang.py     # 坐标+面向 精确回放
├── zidongxunlu.py                # 坦克式寻路演示
├── shitidianji.py                # YOLO 实时尸体检测与右键拾取
├── jietu.py                      # 自动间隔截图采集训练素材
├── trainyolo8.py                 # YOLOv8 训练脚本
├── aiyolo.py                     # YOLO 单张图片推理测试
├── wowyolo.py                    # YOLO-World 自动标注脚本
├── diagnostic.py                 # 像素色块诊断调试工具
├── combat.py                     # 像素锚点坐标定位辅助
├── FPTracker.py                  # 飞行点开通状态读取
├── read_bag.py                   # 背包数据解析
├── wow11ocr.py                   # 屏幕识图点击（模板匹配）
├── wow22ocr.py                   # 屏幕识图偏移点击
├── fix_names.py                  # 文件名修正工具
├── MMMMMMyDataTracker.py         # 数据追踪实验脚本
├── wow_data.yaml                 # YOLO 数据集配置文件
├── paths/                        # 坐标路书 JSON 文件
├── paths_precision/              # 精密坐标 JSON 文件
├── quests/                       # 任务动作录制 JSON
├── datasets/                     # YOLO 训练数据集
├── imgs/                         # 模板匹配参考图片
└── AAwow111/                     # 主调度器及其依赖
    ├── Master.py                 # 全自动任务调度主程序
    ├── plan.txt                  # 等级阶段计划
    ├── tasks.txt                 # 特殊任务列表
    ├── scripts/                  # Master.py 依赖的子脚本
    ├── paths/                    # 路书文件副本
    ├── sequences/                # TXT 动作序列文件
    └── quests/                   # 任务动作文件
```

## 注意事项

- 本项目仅供技术研究和学习参考。在魔兽世界官方服务器上使用自动化脚本违反暴雪娱乐的用户协议，可能导致账号被封禁。
- 像素色块读取方案依赖游戏窗口不被遮挡，且需确保 WoW 插件 `MyMonitor` 正确加载运行。
- 游戏分辨率变化会导致像素读取坐标偏移，需在代码中调整 `SCREEN_W`、`SCREEN_H` 等参数。
- YOLO 模型需针对当前游戏画面风格重新训练，不同服务器（如经典怀旧服、正式服）的画面差异较大。
- `pydirectinput` 模拟的是 DirectInput 键盘输入，部分反作弊系统可能检测此类输入。在私服或研究环境中使用。
- 按下 `Page Down` 键可紧急停止所有自动化操作。
