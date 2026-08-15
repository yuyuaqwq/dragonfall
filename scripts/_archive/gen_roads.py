# -*- coding: utf-8 -*-
# ⚠️ 已废弃（13.4.6 起城镇直连为合法设计，本族脚本前提失效），禁止运行
"""必经之路 v3：生成 game/data/roads.py + 输出 MAP_CONNECTIONS 改写清单

规则（策划案 02 章 13.4.5）：
- 同村近邻（maple_village ↔ oak_town）保留直连
- 已有野外中间图 → 删直连
- 其余城镇对 → 新增『XX路』图（type=野外，lv=两城平均，无怪，纯过渡带）

用法：python scripts/gen_roads.py --write  （默认仅打印；--write 写 roads.py）
"""
import sys as _sys
print("已废弃，禁止运行", file=_sys.stderr)
_sys.exit(1)

import os, sys, json

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)

from game.data.maps import MAPS, MAP_CONNECTIONS

byid = {m['id']: m for m in MAPS}

# 保留直连的近邻（同区域小村）
KEEP_DIRECT = {("maple_village", "oak_town")}

# 城镇直连边（唯一化，a<b）
pairs = set()
for a, bs in MAP_CONNECTIONS.items():
    for b in bs:
        if a in byid and b in byid and byid[a].get('type') == '城镇区域' and byid[b].get('type') == '城镇区域':
            pairs.add(tuple(sorted([a, b])))

via_existing = []
need_road = []
keep = []
for a, b in sorted(pairs):
    if (a, b) in KEEP_DIRECT or (b, a) in KEEP_DIRECT:
        keep.append((a, b))
        continue
    mids = [x for x in byid if x not in (a, b)
            and a in MAP_CONNECTIONS.get(x, []) and b in MAP_CONNECTIONS.get(x, [])]
    if mids:
        via_existing.append((a, b, mids))
    else:
        need_road.append((a, b))

# 生成路图数据
ROADS = []
for a, b in need_road:
    la, lb = byid[a].get('lv', 1), byid[b].get('lv', 1)
    lv = max(1, (la + lb) // 2)
    na, nb = byid[a]['name'], byid[b]['name']
    road_id = f"road_{a}_{b}"
    road_name = f"{na}-{nb}路"
    ROADS.append({
        "id": road_id,
        "name": road_name,
        "lv": lv,
        "region": "必经之路",
        "chapter": 1,
        "area": road_id,
        "area_name": road_name,
        "desc": f"连接{na}与{nb}的必经之路，商旅往来，偶有流寇出没。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [],
    })

# 输出
print(f"共 {len(pairs)} 条城镇直连边 → 保留 {len(keep)} / 删直连走野外 {len(via_existing)} / 新建路图 {len(need_road)}")
print("\n✅ 保留直连（同村近邻）:")
for a, b in keep:
    print(f"  {a} <-> {b}")
print("\n✅ 删直连走已有野外:")
for a, b, mids in via_existing:
    print(f"  {a} <-> {b} 经 {mids}")
print(f"\n🚧 新建 {len(ROADS)} 张路图:")
for r in ROADS:
    print(f"  {r['id']} | {r['name']} | lv={r['lv']}")

if "--write" in sys.argv:
    # 写 roads.py（json.dumps 布尔转 Python 大写）
    out = ["# -*- coding: utf-8 -*-",
           '"""奥兰迪亚·余烬纪年 数据层 - roads.py（必经之路，自动生成，2026-08-07）"""',
           "# 必经之路：02 章 13.4.5。城镇间过渡带，无怪无NPC，纯衔接。",
           "ROAD_MAPS = " + json.dumps(ROADS, ensure_ascii=False, indent=2)
           .replace(": false", ": False").replace(": true", ": True").replace(": null", ": None"),
           ""]
    path = os.path.join(PLUGIN_DIR, "game", "data", "roads.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"\n✅ 已写入 {path}")

    # 输出 MAP_CONNECTIONS 改写清单
    print("\n=== MAP_CONNECTIONS 改写清单（人工/脚本应用）===")
    for a, b in keep:
        print(f"  保留: {a} <-> {b}（不动）")
    for a, b, mids in via_existing:
        print(f"  删: {a} 移除 {b}; {b} 移除 {a}（经 {mids}）")
    for r in ROADS:
        a, b = r['id'].replace("road_", "").split("_", 1)
        # 注意：id 是 road_{a}_{b}，a/b 用 need_road 对应
    for (a, b), r in zip(need_road, ROADS):
        print(f"  加: {a} +{r['id']}; {b} +{r['id']}; {r['id']} +[{a}, {b}]")
