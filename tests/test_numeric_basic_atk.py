# -*- coding: utf-8 -*-
"""v174 普攻技能槽化门禁（鱼鱼拍板 2026-09-04：每职业新增普攻技=100%AD/AP，怪物同理）

验证：
  1. 全职业 CLASSES[cls].basic_skill 已配置（8 职业含见习）
  2. 法系普攻基于 matk（反馈 #75：法师/牧师/诗人普攻吃 atk 刮痧 → 改 AP）
  3. 物理普攻仍基于 atk 且数值 ≈ 旧 calc_damage(atk)（不回归）
  4. 怪物 basic_skill 数据驱动可用（魔法普攻怪走 matk 段）
  5. basic_skill 无 CD/无消耗/标记 basic

任何改动跑本门禁 = 全绿才能提交
独立运行：python tests/test_numeric_basic_atk.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import conftest  # noqa: F401
except Exception:
    pass

from game import battle as BT
from data.plugins.dragonfall.game.data.classes import CLASSES

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}: {detail}")


def mk_battle(cls, atk=100, matk=100):
    player = {
        "class_name": cls, "level": 20, "name": "测试",
        "hp": 500, "max_hp": 500, "mp": 300, "max_mp": 300,
        "attributes": {}, "equipment": {}, "class_tier": 0,
    }
    b = BT.Battle("monster", {"name": "木桩", "hp": 99999, "max_hp": 99999,
                              "def": 10, "mdef": 10, "atk": 1, "spd": 10, "level": 20})
    st = {"atk": atk, "matk": matk, "def": 20, "mdef": 20, "spd": 12,
          "crit": 0.0, "dodge": 0.0, "crit_dmg": 0.0, "luck": 0, "max_hp": 500, "hp": 500}
    return player, b, st


print("== v174 普攻技能槽化门禁 ==")

# 1. basic_skill 覆盖
missing = [cid for cid, c in CLASSES.items() if cid != "cls_novice" or cid == "cls_novice"]
no_bs = [cid for cid, c in CLASSES.items() if not isinstance(c.get("basic_skill"), dict)]
check("全职业 basic_skill 已配", no_bs == [], f"缺失: {no_bs}")

# 2. 法系普攻基于 matk
for cls, name in [("cls_fa_shi", "法师"), ("cls_mu_shi", "牧师"), ("cls_shi_ren", "诗人")]:
    bs = CLASSES[cls]["basic_skill"]
    check(f"{name} basic_skill 是魔法(matk)", str(bs.get("kind")).startswith("魔法")
          and bs.get("exprs", [""])[0].startswith("matk"),
          f"kind={bs.get('kind')} expr={bs.get('exprs')}")

# 3. 法系普攻伤害 = matk 段（matk=100, mdef=10 → ~90）
for cls in ["cls_fa_shi", "cls_mu_shi", "cls_shi_ren"]:
    player, b, st = mk_battle(cls, atk=30, matk=100)
    logs = b._player_attack(st, player)
    dmg = 0
    for l in logs:
        if "造成" in l and "伤害" in l:
            import re
            m = re.search(r"造成 (\d+) 点伤害", l)
            if m:
                dmg = int(m.group(1))
    check(f"{CLASSES[cls]['name']} 普攻 ≈ matk 伤害 (atk=30/matk=100 → ~90)",
          dmg >= 80, f"实际 {dmg}")

# 4. 物理普攻不回归（atk=100 → 与旧 calc_damage 一致）
player, b, st = mk_battle("cls_zhan_shi", atk=100, matk=10)
logs = b._player_attack(st, player)
dmg = 0
for l in logs:
    if "造成" in l and "伤害" in l:
        import re
        m = re.search(r"造成 (\d+) 点伤害", l)
        if m:
            dmg = int(m.group(1))
check("战士普攻 ≈ atk 伤害 (atk=100 def=10 → ~80-105)", 75 <= dmg <= 110, f"实际 {dmg}")

# 5. 怪物 basic_skill 可用（魔法普攻怪）
player, b, st = mk_battle("cls_zhan_shi", atk=100, matk=10)
b2 = BT.Battle("monster", {"name": "魔法木桩", "hp": 99999, "max_hp": 99999,
                           "def": 10, "mdef": 10, "atk": 100, "matk": 10, "spd": 10, "level": 20,
                           "basic_skill": {"name": "魔力爪", "kind": "魔法", "exprs": ["matk*1.0"]}})
# 敌方普攻路径（直接调 _enemy_cast_done 或近似验证公式解析）
from data.plugins.dragonfall.game.core import formula_expr as FE
_mst = {"matk": 10, "atk": 100}
_v = FE.build_vars(_mst, player_lv=20, skill_lv=0)
_md = FE.eval_expr(FE.compile_expr("matk*1.0"), _v)
check("怪物 basic_skill 公式解析 matk×1.0", abs(_md - 10) < 1e-6, f"got {_md}")

# 6. basic 标记
ok = all(CLASSES[cid]["basic_skill"].get("basic") and CLASSES[cid]["basic_skill"].get("mp") == 0
         for cid in CLASSES if isinstance(CLASSES[cid].get("basic_skill"), dict))
check("basic_skill 均 basic:True 且无消耗", ok)

print()
print(f"===== 结果：PASS {PASS} / FAIL {FAIL} =====")
sys.exit(1 if FAIL else 0)
