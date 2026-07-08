# wow-bot

World of Warcraft (WoW Classic) automation bot. Uses pixel-level screen reading, YOLOv8 visual recognition, coordinate waypoint navigation, and a finite state machine (FSM) for combat logic — enabling a fully automated grinding loop from combat, pathfinding, and looting to town-return resupply.

## Features

- **Game state reading** -- The WoW addon `MyMonitor` draws pixel color blocks at the top of the screen. The Python side captures and decodes them to obtain real-time data: player coordinates, facing direction, map ID, HP/MP values and percentages, combat status, target health, target distance, player level, etc.
- **YOLOv8 visual recognition** -- Trains and deploys YOLO models to detect red-nameplate enemy health bars and corpses on screen for target acquisition and looting.
- **Coordinate waypoint recording and playback** -- During manual map traversal, coordinates are recorded at timed intervals into JSON waypoint files. During automated navigation, the bot follows waypoints sequentially, supporting tank-style navigation (rotate-in-place + move-forward).
- **FSM combat state machine** -- PATROL -> FOUND_TARGET -> CHECK_SELECTION -> ALIGN_DIRECTION -> COMBAT -> find and loot corpse -> RECOVERY: a complete loop.
- **Zoned radial turning** -- Uses different keyboard turn durations based on the target's near/mid/far screen position for precise target alignment.
- **Back-facing/stuck detection** -- During combat, if the bot keeps attacking but the target takes no damage, it automatically backs up to reposition.
- **Master scheduler** -- `Master.py` orchestrates travel and grinding scripts by level brackets, handles death respawn, full-bag town return, flight point unlocks, and programmable action sequences via TXT sequence files.
- **OCR template-match clicking** -- Uses pyautogui template matching to recognize and click game UI buttons (accept quest, confirm dialogs, etc.).
- **Bag monitoring** -- Parses WoW SavedVariables `MyBag.lua` to monitor available bag slots in real time.
- **Training data collection** -- Auto-interval screenshot tool for collecting YOLO training samples.

## Requirements

- Windows 10/11
- Python 3.8+
- NVIDIA GPU (recommended for YOLO inference/training; CPU works but is slower)
- World of Warcraft Classic

### Python Dependencies

Core dependencies:

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

Installation:

```bash
pip install ultralytics opencv-python numpy pyautogui pydirectinput keyboard pillow mss pywin32
```

## Installation

```bash
git clone https://github.com/doaneruby970-hub/wow-bot.git wow-bot
cd wow-bot
pip install ultralytics opencv-python numpy pyautogui pydirectinput keyboard pillow mss pywin32
```

## Configuration

### 1. Install WoW Addon

Place the `MyMonitor` addon folder from the project root into WoW's `Interface/AddOns/` directory. This addon depends on the `RangeDisplay` addon for distance measurement; install it as well.

**Addon structure:**
```
World of Warcraft\_classic_\Interface\AddOns\MyMonitor\
    MyMonitor.toc
    MyMonitor.lua
```

### 2. Train YOLO Models

The project requires two YOLO models:

- **Enemy health bar detection model**: Detects red-nameplate enemies on screen. Train using `trainyolo8.py`, dataset configured in `wow_data.yaml` (classes: 0=monster, 1=red_health_bar, 2=yellow_health_bar)
- **Corpse detection model**: Detects monster corpses on the ground for looting. Must be trained separately.

Model paths are configured in `botAIclaude.py`:

```python
MODEL_PATH = r'.\runs\detect\train2\weights\best.pt'          # Enemy health bar detection
SHITI_MODEL_PATH = r'.\WoW_Project\runs\detect\wow_shiti_v1\weights\best.pt'  # Corpse detection
```

### 3. Record Waypoints

Use `zuobiaoluzhi.py` to manually traverse the map and record coordinate waypoints. During traversal, coordinates are auto-recorded at timed intervals to `paths/map_{mapID}.json`.

```bash
python zuobiaoluzhi.py
# Manually control your character along the target route
# Press Q to save and exit
```

### 4. Configure the Schedule Plan

Edit `AAwow111/plan.txt` (format: `minLevel/maxLevel/travelFile/grindFile/returnTownSeq/deathSeq/startSeq`) and `AAwow111/tasks.txt` (format: `taskID/triggerLevel/type/description/sequenceFile`) to set up the automation flow.

## Usage

### Running Individual Scripts

```bash
# Coordinate waypoint playback (select waypoint file from paths/)
python zuobiaoxunlubofang.py

# Manual coordinate waypoint recording
python zuobiaoluzhi.py

# Real-time coordinate display
python zuobiaoxianshi.py

# Stat dashboard (HP/MP/status)
python xueliangshuzhi.py

# YOLO visual hunter (auto target acquisition and attack)
python hunter_logicAI.py

# Full FSM combat bot (navigation + combat + looting)
python botAIclaude.py

# Training data collection screenshot tool
python jietu.py

# YOLO model training
python trainyolo8.py
```

### Full Auto-Schedule Run

```bash
cd AAwow111
python Master.py
```

`Master.py` automatically runs travel and grinding scripts by level bracket according to `plan.txt`, and handles events such as death respawn and full-bag town return.

## Project Structure

```
wow-bot/
├── MyMonitor.lua / .toc          # WoW addon: encodes game data as pixel color blocks at screen top
├── zuobiaoxianshi.py             # Coordinate/facing/map ID reading module
├── xueliangshuzhi.py             # HP/MP/combat status numeric reading module
├── botAIclaude.py                # Full FSM combat bot (navigation + target acquisition + combat + looting + recovery)
├── botAI.py                      # Earlier version FSM combat bot
├── hunter_logicAI.py             # YOLO real-time target acquisition and attack script
├── zuobiaoluzhi.py               # Coordinate waypoint recording tool
├── zuobiaoxunlubofang.py         # Coordinate navigation playback (manual waypoint selection)
├── zuobiaoxunlubofang11.py       # Navigation playback (cross-map sprint mode)
├── zuobiaoxunlubofang22.py       # Navigation playback (capital city high-precision mode)
├── zuobiaomianxiang.py           # Coordinate + facing precision recording
├── zuobiaomianxiangbofang.py     # Coordinate + facing precision playback
├── zidongxunlu.py                # Tank-style pathfinding demo
├── shitidianji.py                # YOLO real-time corpse detection and right-click looting
├── jietu.py                      # Auto-interval screenshot training data collection
├── trainyolo8.py                 # YOLOv8 training script
├── aiyolo.py                     # YOLO single-image inference test
├── wowyolo.py                    # YOLO-World auto-labeling script
├── diagnostic.py                 # Pixel color block diagnostic/debug tool
├── combat.py                     # Pixel anchor coordinate positioning helper
├── FPTracker.py                  # Flight point unlock status reader
├── read_bag.py                   # Bag data parser
├── wow11ocr.py                   # Screen template-match clicking
├── wow22ocr.py                   # Screen template-match offset clicking
├── fix_names.py                  # Filename fixer tool
├── MMMMMMyDataTracker.py         # Data tracking experiment script
├── wow_data.yaml                 # YOLO dataset config file
├── paths/                        # Coordinate waypoint JSON files
├── paths_precision/              # Precision coordinate JSON files
├── quests/                       # Quest action recording JSON
├── datasets/                     # YOLO training datasets
├── imgs/                         # Template matching reference images
└── AAwow111/                     # Master scheduler and dependencies
    ├── Master.py                 # Full-auto task scheduler main program
    ├── plan.txt                  # Level bracket plan
    ├── tasks.txt                 # Special task list
    ├── scripts/                  # Sub-scripts used by Master.py
    ├── paths/                    # Waypoint file copies
    ├── sequences/                # TXT action sequence files
    └── quests/                   # Quest action files
```

## Notes

- This project is for technical research and educational reference only. Using automation scripts on official World of Warcraft servers violates Blizzard Entertainment's Terms of Service and may result in account bans.
- The pixel color block reading scheme requires the game window to remain unobstructed and the WoW addon `MyMonitor` to be correctly loaded and running.
- Changing game resolution will cause pixel read coordinate offsets; adjust `SCREEN_W`, `SCREEN_H`, and related parameters in the code accordingly.
- YOLO models must be retrained for the current game's visual style. Different server versions (Classic, Retail) have significantly different visuals.
- `pydirectinput` simulates DirectInput keyboard input; some anti-cheat systems may detect such input. Use on private servers or in research environments.
- Press `Page Down` to emergency-stop all automation operations.
