# -*- coding: utf-8 -*-
"""v131 副本 Boss 长盘化：按副本 ID 顺序精准替换 instances.py 的 hp_mult 值。
建议表来源：_tmp_preview_v4.py 扫描结果（4人蓝+5 → 100~150 轮）。
用法：python scripts/_tmp_apply_hpm.py（改完 git diff 核对 + import 验证）
"""
import os, re, sys
_PD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_PD))))
sys.path.insert(0, _PD)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))
from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game.data import instances as IM  # noqa: E402

# v131 建议 hpm（32 章一表）
NEW_HPM = {
    "inst_goblin_camp": 20.0, "inst_deer_fort": 13.5, "inst_sea_cave": 13.5,
    "inst_old_king_tomb": 5.0, "inst_holy_trial": 7.0, "inst_sunken_ship": 7.0,
    "inst_secret_crypt": 20.0, "inst_siren_nest": 8.5, "inst_elven_ruins": 7.0,
    "inst_moon_temple": 6.0, "inst_sea_god_temple": 7.0, "inst_deep_dragon_palace": 8.0,
    "inst_frost_throne": 6.5, "inst_gray_dwarf": 6.5, "inst_ash_temple": 7.0,
    "inst_under_dragon": 8.0, "inst_abyss_gate": 6.0, "inst_dragon_tomb": 6.0,
    "inst_storm_throne": 7.5, "inst_abyss_throne": 6.5, "inst_eye_of_storm": 8.5,
    "inst_cloud_sanctum": 8.5,
}

path = os.path.join(_PD, "game", "data", "instances.py")
with open(path, encoding="utf-8") as f:
    src = f.read()

ids_in_file = list(C.INSTANCES.keys())
missing = [i for i in NEW_HPM if i not in ids_in_file]
if missing:
    sys.exit(f"❌ 副本 ID 不在 INSTANCES: {missing}")

# 按文件顺序取 22 个 hp_mult 行（与 INSTANCES 顺序对应）
lines = src.split("\n")
hpm_lines = [(idx, line) for idx, line in enumerate(lines)
             if re.match(r'^\s+"hp_mult":\s+[\d.]+,?\s*$', line)]
if len(hpm_lines) != len(ids_in_file):
    sys.exit(f"❌ hp_mult 行数 {len(hpm_lines)} != 副本数 {len(ids_in_file)}")

changed = []
for (idx, line), iid in zip(hpm_lines, ids_in_file):
    new = re.sub(r'"hp_mult":\s+[\d.]+', f'"hp_mult": {NEW_HPM[iid]}', line)
    if new != line:
        changed.append((iid, line.strip(), new.strip()))
        lines[idx] = new

with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"✅ 替换 {len(changed)}/{len(ids_in_file)}：")
for iid, old, new in changed:
    print(f"  {iid:<24} {old:>20} → {new:>20}")

# 验证 import 可读 + 22 值一致
import importlib
importlib.reload(IM)
from data.plugins.dragonfall.game.data import instances as IM2
print("\n验证新值：")
ok = True
for iid, want in NEW_HPM.items():
    got = IM2.INSTANCES[iid].get("hp_mult")
    mark = "✅" if abs(got - want) < 1e-6 else "❌"
    if mark == "❌":
        ok = False
    print(f"  {iid:<24} want={want:<5} got={got} {mark}")
sys.exit(0 if ok else 1)