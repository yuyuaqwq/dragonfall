# -*- coding: utf-8 -*-
"""v178 E1/E2 快速验证：副本 Boss mech 合并 + _boss_cfg 按 _inst_id 解析"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import conftest  # noqa: F401
except Exception:
    pass

from game import battle as BT
from game.core.drops import build_monster
from game.data.monster_mods import MONSTER_MODS
from game.data.instances import INSTANCES

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  ✅ {name}")
    else:
        FAIL += 1; print(f"  ❌ {name} {detail}")

print("== E1/E2 验证 ==")

# 1. b_moro 在 monster_mods 的 mech（enrage,phase_open）+ inst_abyss_throne 的 mech（stacks,summon）
# 验证合并逻辑（模拟 instance.py 新代码）
def merge_mech(mods_mech, inst_mech):
    if inst_mech:
        mods_mech = (mods_mech or "").strip()
        inst_mech = inst_mech.strip()
        if mods_mech and inst_mech:
            return ",".join(dict.fromkeys([x.strip() for x in (mods_mech + "," + inst_mech).split(",") if x.strip()]))
        return inst_mech or mods_mech
    return mods_mech

mods_m = MONSTER_MODS.get("b_moro", {}).get("mech", "")
check("b_moro mods mech = enrage,phase_open", mods_m == "enrage,phase_open", mods_m)
merged = merge_mech(mods_m, "stacks,summon")
check("合并去重 = enrage,phase_open,stacks,summon", merged == "enrage,phase_open,stacks,summon", merged)
merged2 = merge_mech(mods_m, "enrage")
check("重复 token 去重 = enrage,phase_open", merged2 == "enrage,phase_open", merged2)
check("mods 空 inst 有 → 取 inst", merge_mech("", "phase") == "phase")
check("inst 空 mods 有 → 取 mods", merge_mech("heal", "") == "heal")

# 2. _boss_cfg 按 _inst_id 解析副本 phases
mon = build_monster(("b_moro", "深渊领主·摩罗", "boss", 98,
                     ["ms_shen_yuan_zhi_nu", "ms_zhao_huan_e_mo"], []),
                    {"id": "inst_abyss_throne", "name": "inst_abyss_throne", "area": "instance"})
mon["_inst_id"] = "inst_abyss_throne"
mon["mech"] = merge_mech(mon.get("mech"), "stacks,summon")

b = BT.Battle("instance", mon, st={"inst_id": "inst_abyss_throne"})
cfg = b._boss_cfg(mon)
check("_boss_cfg 保留 mods phases（b_moro 配了 2 条）", len(cfg.get("phases") or []) >= 2,
      f"phases 数={len(cfg.get('phases') or [])}")

# 3. 旧行为回归：野外怪无 _inst_id → 按 id 查
wolf = build_monster(("m_wild_dog", "野狗", "dps", 3, ["ms_si_yao"], []),
                     {"id": "misty_forest", "name": "misty_forest", "area": "wild"})
b2 = BT.Battle("monster", wolf)
cfg2 = b2._boss_cfg(wolf)
check("野外普通怪 cfg 空（无 mech 不读剧本）", cfg2.get("phases") == [] and cfg2.get("opening") is None)

# 4. abyss_gate（inst 内联 phases 的唯一例）——用 b_eter 模拟
eter = build_monster(("b_eter", "蚀夜(真相形态)", "boss", 100,
                      ["ms_an_ying_zhan"], []),
                     {"id": "inst_abyss_gate", "name": "inst_abyss_gate", "area": "instance"})
eter["_inst_id"] = "inst_abyss_gate"
eter["mech"] = merge_mech(eter.get("mech"), "phase,phase,phase")
b3 = BT.Battle("instance", eter, st={"inst_id": "inst_abyss_gate"})
cfg3 = b3._boss_cfg(eter)
inst_phases = INSTANCES["inst_abyss_gate"].get("phases") or []
check("abyss_gate inst phases 现在能被 _boss_cfg 读到", len(cfg3.get("phases") or []) == len(inst_phases) and len(inst_phases) >= 1,
      f"cfg={len(cfg3.get('phases') or [])} inst={len(inst_phases)}")

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
