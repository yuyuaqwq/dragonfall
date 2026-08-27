# -*- coding: utf-8 -*-
"""v131 副本 hpm 就地重标定（真实落地数据）：22 副本 × hpm ∈ [1,25] 找 4人蓝+5 击杀轮 100~150。
用法：python scripts/_tmp_recalib_hpm.py（自动更新 instances.py + 验证）
"""
import os, re, sys
_PD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PD, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_PD))))
sys.path.insert(0, _PD)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env  # noqa
from numeric_lib.player import PlayerOptions, build_player, per_action_dmg
from numeric_lib.gear import gear_loadout
from numeric_lib.constants import TEAM_BUFF
from data.plugins.dragonfall.game import content as C  # noqa
from data.plugins.dragonfall.game import engine as E  # noqa

def calc_rounds(boss_def, lv, hpm, mn):
    m = C.build_monster(boss_def, {"id": "x", "name": "x", "area": "instance"})
    if m.get("max_hp") and hpm:
        pass
    hp_tot = int(m["max_hp"] * (hpm + 0.65 * (4 - mn)))
    d = per_action_dmg("cls_zhan_shi", lv, gear_loadout(lv, "solo_mid"),
                       m["def"], m["mdef"], PlayerOptions(), potion_on=True)
    return hp_tot / (d * 4 * TEAM_BUFF), m, hp_tot

new_hpm = {}
report = []
for iid, inst in sorted(C.INSTANCES.items(), key=lambda x: x[1].get("lv", 0)):
    lv = inst.get("lv", 0)
    boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
    mn = inst.get("min_players", 1)
    best = None
    for hpm in [x / 2 for x in range(2, 51)]:  # 1.0 ~ 25.0
        k, _, _ = calc_rounds(boss_def, lv, hpm, mn)
        if 100 <= k <= 150:
            best = (hpm, k)
            break
    if best is None:
        k, m, hp = calc_rounds(boss_def, lv, 25.0, mn)
        report.append((iid, lv, inst.get("hp_mult"), "找不到", k))
        continue
    new_hpm[iid] = best[0]
    report.append((iid, lv, inst.get("hp_mult"), best[0], best[1]))

for r in report:
    print(f"  {r[0]:<24} Lv{r[1]:<3} {r[2]} → {r[3]}  轮数 {r[4]:.1f}" + ("" if r[3] != "找不到" else " ❌"))

if len(new_hpm) != len(C.INSTANCES):
    print("⚠️ 有副本未达标，需人工处理")
    sys.exit(1)

# 写回 instances.py
path = os.path.join(_PD, "game", "data", "instances.py")
with open(path, encoding="utf-8") as f:
    src = f.read()
lines = src.split("\n")
hpm_lines = [(idx, line) for idx, line in enumerate(lines)
             if re.match(r'^\s+"hp_mult":\s+[\d.]+,?\s*$', line)]
ids_in_file = list(C.INSTANCES.keys())
if len(hpm_lines) != len(ids_in_file):
    sys.exit(f"❌ hp_mult 行数 {len(hpm_lines)} != {len(ids_in_file)}")
changed = 0
for (idx, line), iid in zip(hpm_lines, ids_in_file):
    new = re.sub(r'"hp_mult":\s+[\d.]+', f'"hp_mult": {new_hpm[iid]}', line)
    if new != line:
        lines[idx] = new
        changed += 1
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\n✅ 写回 {changed} 处（instances.py）")