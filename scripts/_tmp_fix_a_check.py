# -*- coding: utf-8 -*-
"""临时验证脚本：fix agent（M1/M2/M3/H3/L2/L3/L4/R1/R2）改动正确性。

覆盖：
① 反射 Boss（mech=reflect、hp<25%）dot 结算不反伤玩家（_tick_dots 后 player hp 不变）；
   并做对照组——同 Boss 非 dot 伤害走 _boss_dmg_filter 会正常反伤（证明反射路径本场景确实活跃）。
② mark 层衰减：debuffs.mark n=2 → 两次 _tick_dots 后移除。
③ 毒爆 5 层伤害 = atk×0.30×5 物理段。
④ 灼爆 5 层 = matk×0.40×5×易燃 1.3。
"""
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.core import battle_mech as BM

passed = 0


def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")


def mk_player(atk=100, matk=80):
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": []}


def mk_enemy(hp=1000, **kw):
    e = {"name": "靶子", "lv": 10, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}}
    e.update(kw)
    return e


def tick(b, player, atk=100, matk=80):
    """_tick_dots 直调（固定施放者快照 + 复位闸门）。"""
    b._player_stats = lambda pl: {"atk": atk, "matk": matk, "def": 50, "mdef": 50,
                                  "spd": 10, "crit": 0.05, "max_hp": 9999, "max_mp": 999}
    b._dot_pending = True
    logs = []
    b._tick_dots(player, logs)
    return logs


def no_variance():
    """毒爆/灼爆走 calc_damage 带 ±15% 波动，临时压平以便断言精确值。"""
    random.uniform = lambda a, b: 0.0


# ---------- ① 反射：dot 不反伤玩家 ----------
print("【1. 反射 Boss dot 不反伤玩家】")
p = mk_player()
# mech=reflect 且 hp=10% max（<25% 触发阈值）；毒 5 层
b = BT.Battle("monster", mk_enemy(hp=10000, max_hp=100000, mech="reflect"))
b.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0}
hp0 = p["hp"]
# 对照组：同一反射 Boss，非 dot 真伤路径应反伤玩家（证明反射本场景活跃）
rb = b._boss_dmg_filter(1000, p, [], dmg_type="phys")  # dot=False 默认
control_reflected = (p["hp"] < hp0)
check("对照组（非 dot）反射 Boss 会反伤玩家", control_reflected,
      f"hp {hp0}->{p['hp']}")

# 恢复玩家血量，走真实 dot 结算
p["hp"] = 9999
enemy_hp0 = b.enemy["hp"]
tick(b, p)
check("毒 dot 正常结算（boss 掉血）", b.enemy["hp"] < enemy_hp0,
      f"{enemy_hp0}->{b.enemy['hp']} 但 player={p['hp']}")
check("dot 结算后玩家 hp 不变（不反射）", p["hp"] == 9999,
      f"player hp={p['hp']}")

# ---------- ② mark 层衰减 ----------
print("【2. mark 层随回合衰减】")
b2 = BT.Battle("monster", mk_enemy(hp=100000))
b2.enemy.setdefault("debuffs", {})["mark"] = {"n": 2, "mult": 1.0}
b2._player_stats = lambda pl: {"atk": 100, "matk": 80, "def": 50, "mdef": 50,
                               "spd": 10, "crit": 0.05, "max_hp": 9999, "max_mp": 999}
b2._dot_pending = True
b2._tick_dots(mk_player(), [])
check("第一次 _tick_dots 后 mark n=1", b2.enemy["debuffs"]["mark"]["n"] == 1,
      str(b2.enemy["debuffs"]))
b2._dot_pending = True
b2._tick_dots(mk_player(), [])
check("第二次 _tick_dots 后 mark 被移除", "mark" not in b2.enemy.get("debuffs", {}),
      str(b2.enemy.get("debuffs")))

# ---------- ③ 毒爆 5 层 = atk×0.30×5 物理段 ----------
print("【3. 毒爆 5 层数值】")
no_variance()
p3 = mk_player(atk=100, matk=80)
b3 = BT.Battle("monster", mk_enemy(**{"def": 0}))
b3._last_player = p3
# 固定施放者快照（真实 _player_stats 对迷你玩家兜底 atk 偏低，无法断言精确值）
b3._player_stats = lambda pl: {"atk": 100, "matk": 80, "def": 50, "mdef": 50,
                               "spd": 10, "crit": 0.05, "max_hp": 9999, "max_mp": 999}
b3.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0}
logs3 = []
BM.MECH_EFFECTS["poison_burst"](b3, 1, b3.mech_stacks, 100, logs3, "毒爆术", False)
# 期望：calc_damage(atk=150, def=0) → atk*atk/(atk+0)=150；def=0 → 满伤害
check("毒爆 5 层 = atk×0.30×5 = 150 物理段", 1000 - b3.enemy["hp"] == 150,
      f"dmg={1000 - b3.enemy['hp']}")
check("毒爆物理段文案", any("物理伤害" in l for l in logs3), str(logs3))
check("毒爆清层", "poison" not in b3.enemy.get("debuffs", {}), str(b3.enemy.get("debuffs")))

# ---------- ④ 灼爆 5 层 = matk×0.40×5×易燃 1.3 ----------
print("【4. 灼爆 5 层数值】")
no_variance()
p4 = mk_player(atk=100, matk=80)
b4 = BT.Battle("monster", mk_enemy(**{"def": 0}))
b4._last_player = p4
b4._player_stats = lambda pl: {"atk": 100, "matk": 80, "def": 50, "mdef": 50,
                               "spd": 10, "crit": 0.05, "max_hp": 9999, "max_mp": 999}
b4.enemy.setdefault("debuffs", {})["burn"] = {"n": 5, "mult": 1.0}
logs4 = []
BM.MECH_EFFECTS["burn_burst"](b4, 1, b4.mech_stacks, 100, logs4, "灼烧引爆", False)
# 期望：int(80×0.40×5)=160，易燃(1+0.1×3)=1.3 → int(160×1.3)=208
check("灼爆 5 层 = matk×0.40×5×1.3 = 208", 1000 - b4.enemy["hp"] == 208,
      f"dmg={1000 - b4.enemy['hp']}")
check("灼爆易燃文案", any("易燃" in l for l in logs4), str(logs4))
check("灼爆清层", "burn" not in b4.enemy.get("debuffs", {}), str(b4.enemy.get("debuffs")))

print(f"\n结果: {passed} 通过, 0 失败")
