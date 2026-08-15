# -*- coding: utf-8 -*-
"""v115 文档同步：重建 02 章 §六 野外详表的子区域列（以实际数据为准），删除过期 2-3 房明细。

- 保留原表 PROPS/NPC/POI 列（旧房间内容未变，仍有效）
- 子区域列替换为实际房间列表（含 🔒 隐藏标记），地图 id 修正为数据层真实 id
- 节首加 v115 更新横幅
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data import SUBAREAS
from game.data.maps import MAP_BY_ID

DOC = os.path.join("design", "new_world", "02_地图系统_余烬纪元合并版.md")
with open(DOC, encoding="utf-8") as f:
    text = f.read()

# 旧 id → 实际 id（文档遗留旧名）
ID_FIX = {"oak_meadow": "oak_plain", "oak_forest": "white_deer_forest"}

def real_id(tok):
    return ID_FIX.get(tok, tok)

BANNER = (
    "> ⚠️ **v115 更新**：本节原「每图 2-3 子区域线性」明细已过期——v115 起全部野外/隐藏图\n"
    "> 已网状化为 **5-7 个房间**（含 🔒 隐藏密室与死胡同奖励房），下表「子区域」列已按\n"
    "> 实际数据重建（房间名/等级/隐藏标记）；连接拓扑见 §13 与 `game/data/mesh_rooms_*.py`。\n"
    "> 规则（v115）：野外 3 房→5-7 房、走廊 2 房→3-4 房；每图 ≥1 岔路或环、死胡同 ≤1（挂精英/高价值\n"
    "> POI）、隐藏房 ≤1（探索 N 次揭示）；相邻房间等级差 ≤15；入口子区域挂引路型 NPC，深处挂精英/boss。\n"
)

# 解析原 §六 表格：按小节拆分，逐行取 [地图, 子区域, PROPS, NPC, POI]
sec_start = text.index("## 六、野外详表")
sec_end = text.index("## 七、副本与隐藏区域入口挂载")
section = text[sec_start:sec_end]

subsections = re.split(r"(?=^### 6\.\d)", section, flags=re.M)
new_parts = []
for sub in subsections:
    if not sub.strip().startswith("### 6."):
        new_parts.append(sub)  # 标题与旧规则行（将被横幅替换）
        continue
    lines = sub.splitlines()
    header = lines[0]
    new_lines = [header]
    in_table = False
    for ln in lines[1:]:
        if ln.startswith("| 地图 |"):
            in_table = True
            new_lines.append(ln)
            continue
        if in_table and ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 5:
                map_cell = cells[0]
                # 地图列：中文名 + id（容忍旧 id）
                mtok = map_cell.split()[-1] if map_cell.split() else ""
                mid = real_id(mtok)
                m = MAP_BY_ID.get(mid)
                sas = SUBAREAS.get(mid, [])
                if m and sas:
                    rooms = []
                    for s in sas:
                        nm = s.get("name", "?")
                        lv = s.get("lv", "")
                        hid = "🔒" if s.get("hidden") else ""
                        rooms.append(f"{hid}{nm}({lv})")
                    new_map_cell = f"{m['name']} {mid}"
                    new_lines.append(f"| {new_map_cell} | {' / '.join(rooms)} | {cells[2]} | {cells[3]} | {cells[4]} |")
                    continue
        new_lines.append(ln)
    new_parts.append("\n".join(new_lines))

new_section = new_parts[0] + "\n" + BANNER + "\n" + "".join(p if p is new_parts[0] else p + "\n" for p in new_parts[1:])
# new_section 开头是原小节标题前的规则行（旧规则），替换掉
new_section = new_section.replace("> 规则：每野外图 2-3 个子区域；**每个子区域至少 1 个专属 PROPS + 1 个 POI**；入口子区域挂 1 个\"引路型\"NPC（猎人/向导/商贩）或 lore NPC；深处挂精英/boss。\n\n", "")

text2 = text[:sec_start] + new_section + "\n" + text[sec_end:]
with open(DOC, "w", encoding="utf-8") as f:
    f.write(text2)
print("done, section length:", len(new_section))
