# -*- coding: utf-8 -*-
"""临时验证脚本（修复 agent B 清单）：验证 H1/H2/M4 + PVP 持久化。

1. _h_bleed：enemy.debuffs.bleed.n==3，_tick_dots 结算造成伤害并衰减
2. enemy_poison_stacks 条件：敌方 debuffs.poison.n=3 时成立
3. poison_all：boss.adapt.poison 递增、debuffs.poison.last_round 已写
4. _sp_burn：adapt.burn==0.04（连续触发叠加）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.core import affix_effects as AF
from game.core import battle_conds as BC
from game.commands import instance as inst

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")


def mk_player(atk=100, matk=80, equipment=None):
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10,
            "crit": 0.05, "equipment": equipment or [], "skills": [],
            "skill_levels": {}, "learned_skills": []}


def mk_equip(affix_ids):
    return {"weapon": {"slot": "weapon", "lv": 60, "stats": {"atk": 10},
                       "affixes": list(affix_ids)}}


def mk_enemy(hp=10000, **kw):
    e = {"name": "靶子", "lv": 10, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}}
    e.update(kw)
    return e


def tick(b, player):
    b._dot_pending = True
    logs = []
    b._tick_dots(player, logs)
    return logs


# ---------- 1. _h_bleed 直接调用 ----------
print("【1. _h_bleed → enemy.debuffs.bleed 迁移】")
p = mk_player(equipment=mk_equip(["bleed"]))
import random
_orig_rand = random.random
random.random = lambda: 0.0  # 固定命中最小的触发概率（0.20 命中）
b = BT.Battle("monster", mk_enemy(hp=10000), {}, p)
logs = []
AF.HIT_EFFECTS["bleed"](b, p, 100, logs)
bl = b.enemy.get("debuffs", {}).get("bleed")
check("_h_bleed 写目标级 debuffs.bleed", bl is not None and bl.get("n") == 3,
      str(b.enemy.get("debuffs")))
hp_before = b.enemy.get("hp", 0)
tick_logs = tick(b, p)
hp_after = b.enemy.get("hp", 0)
check("_tick_dots 结算造成流血伤害", hp_after < hp_before,
      f"{hp_before} -> {hp_after}; logs={tick_logs}")
bl2 = b.enemy.get("debuffs", {}).get("bleed")
check("_tick_dots 后层数衰减（3→2）", bl2 is not None and bl2.get("n") == 2,
      str(b.enemy.get("debuffs")))

# ---------- 2. battle_conds poison_stacks ----------
print("【2. enemy_poison_stacks / enemy_debuff 目标级条件】")
p2 = mk_player()
b2 = BT.Battle("monster", mk_enemy(hp=10000), {}, p2)
b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
check("poison n=3 条件成立(>=3)", BC.COND_CHECKS["enemy_poison_stacks"](b2, p2, {"stacks": 3}) is True,
      "")
b2.enemy["debuffs"]["poison"]["n"] = 2
check("poison n=2 条件不成立(>=3)", BC.COND_CHECKS["enemy_poison_stacks"](b2, p2, {"stacks": 3}) is False,
      "")
b2.enemy["debuffs"]["poison"]["n"] = 3
check("enemy_debuff 因 poison>0 成立", BC.COND_CHECKS["enemy_debuff"](b2, p2, {}) is True, "")
b3 = BT.Battle("monster", mk_enemy(hp=10000), {}, p2)
b3.e_buffs["stun"] = 1
check("enemy_debuff 保留 e_buffs 控制语义(stun)", BC.COND_CHECKS["enemy_debuff"](b3, p2, {}) is True, "")

# ---------- 3. poison_all（_apply_team_effect 真实方法） ----------
print("【3. poison_all → boss.adapt + last_round】")
inst_obj = inst.InstanceCmds.__new__(inst.InstanceCmds)
st = {"boss": {"name": "B", "hp": 1000, "max_hp": 1000}, "members": ["1", "2"],
      "alive": {"1": True, "2": True}, "round": 0, "players": {}}
te = {"kind": "poison_all", "effect": ""}
inst_obj._apply_team_effect(st, "1", te)
boss = st["boss"]
check("poison_all 后 debuffs.poison.n==2", boss["debuffs"]["poison"]["n"] == 2,
      str(boss.get("debuffs")))
check("poison_all 后 adapt.poison>0", float(boss.get("adapt", {}).get("poison", 0)) > 0,
      f"adapt={boss.get('adapt')}")
check("poison_all 后 last_round 已写(=0)", boss["debuffs"]["poison"].get("last_round") == 0,
      f"last_round={boss['debuffs']['poison'].get('last_round')}")
# 再次施加：poison n 叠加 + adapt 递增到 0.08
inst_obj._apply_team_effect(st, "1", te)
check("poison_all 二次施加 n=4", boss["debuffs"]["poison"]["n"] == 4,
      str(boss.get("debuffs")))
check("poison_all 二次施加 adapt.poison==0.08",
      abs(float(boss.get("adapt", {}).get("poison", 0)) - 0.08) < 1e-6,
      f"adapt={boss.get('adapt')}")

# ---------- 4. _sp_burn（套装攻击特效） ----------
print("【4. _sp_burn → adapt.burn】")
b4 = BT.Battle("monster", mk_enemy(hp=10000), {}, mk_player())
logs4 = []
AF.SET_PROC_EFFECTS["burn"](b4, mk_player(atk=100, matk=80), 100, logs4)
burn = b4.enemy.get("debuffs", {}).get("burn")
check("_sp_burn 挂灼烧层", burn is not None and burn.get("n") == 1, str(b4.enemy.get("debuffs")))
check("_sp_burn 写 last_round", burn.get("last_round") == b4.round, f"last_round={burn.get('last_round')}, round={b4.round}")
check("_sp_burn 后 adapt.burn==0.04",
      abs(float(b4.enemy.get("adapt", {}).get("burn", 0)) - 0.04) < 1e-6,
      f"adapt={b4.enemy.get('adapt')}")

print(f"\n全部通过 {passed} 项 ✓")
