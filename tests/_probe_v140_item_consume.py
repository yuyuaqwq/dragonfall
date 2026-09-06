# -*- coding: utf-8 -*-
"""v140 波3.2 道具 handler 消费端——冒烟验证"""
import sys, os, random
random.seed(42)  # 固定随机种子：防闪避/暴击随机导致断言不稳定
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def mk_player(atk=100, matk=80):
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": 30, "class_name": "战士", "qq_id": "t"}

def mk_enemy(hp=100000, **kw):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}}
    e.update(kw)
    return e

print("【1. 不死鸟之羽复活】")
p = mk_player()
e = mk_enemy(hp=50)
b = BT.Battle("monster", e, player=p)
# 模拟使用不死鸟之羽
from game.core.potion_effects import eff_phoenix
val = {"revive_hp": 0.30, "dmg_reduce": 0.20, "turns": 3}
msg = eff_phoenix(b, p, val)
print(f"  使用效果: {msg}")
# 造成致死伤害
b._damage_actor(p, 99999, [], source="测试")
check("phoenix 复活", p["hp"] > 0, f"hp={p['hp']}")
check("phoenix 减伤 buff", "reduce_all" in b.p_buffs, str(b.p_buffs))

print("【2. 次元门扉符无敌】")
p = mk_player()
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
from game.core.potion_effects import eff_invuln
msg = eff_invuln(b, p, {"turns": 1, "stun_after": 1})
print(f"  使用效果: {msg}")
hp_before = p["hp"]
b._damage_actor(p, 5000, [], source="测试")
check("invuln 免疫伤害", p["hp"] == hp_before, f"hp={p['hp']}")

print("【3. 龙血变身受击+15%】")
p = mk_player()
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
from game.core.potion_effects import eff_morph
msg = eff_morph(b, p, {"turns": 3, "dmg_taken_up": 0.15})
print(f"  使用效果: {msg}")
hp_before = p["hp"]
b._damage_actor(p, 1000, [], source="测试")
check("morph 受击加成生效", p["hp"] < hp_before - 1000, f"hp={p['hp']} before={hp_before}")

print("【4. 连携增幅墨叠层】")
p = mk_player()
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
from game.core.potion_effects import eff_dot_amp
msg = eff_dot_amp(b, p, {"turns": 2, "layer_per_hit": 1})
print(f"  使用效果: {msg}")
# 给目标挂毒，直接调 _player_attack（跳过 _turn_start 的 DOT 结算会清层）
b.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
import random as _rnd; _rnd.seed(7)
st = b._player_stats(p)
b._player_attack(st, p)
_deb = b.enemy.get("debuffs") or {}
check("dot_amp 毒层+1", int(_deb.get("poison", {}).get("n", 0) or 0) >= 2, str(_deb))

print("【5. 弱点击破增伤】")
p = mk_player()
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
# 先给目标挂 3 种负面，再使用弱点击破石（eff_vuln 使用时按当前负面数算 bonus）
b.e_buffs["spd_down"] = 2
b.e_buffs["def_down"] = 2
b.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
from game.core.potion_effects import eff_vuln
msg = eff_vuln(b, p, {"turns": 3, "per_debuff": 0.12, "max_debuff": 3, "max_bonus": 0.36})
print(f"  使用效果: {msg}")
check("vuln 标记 bonus>0", float(b.p_eff.get("vuln", {}).get("bonus", 0) or 0) > 0,
      str(b.p_eff.get("vuln")))
# monkeypatch _player_stats 保证确定性面板
b._player_stats = lambda pl: {"atk": 100, "matk": 80, "def": 50, "mdef": 50,
                              "spd": 10, "crit": 0.05, "max_hp": 9999, "max_mp": 999}
orig_dmg = b._deal_damage
captured = []
def spy(d, l, wake_sleep=True, target=None, source=None):
    captured.append(d)
    return orig_dmg(d, l, wake_sleep, target, source)
b._deal_damage = spy
import random as _rnd2; _rnd2.seed(11)
st = b._player_stats(p)
b._player_attack(st, p)
# 基础普攻 100 攻 vs 100 防 ≈ 68；vuln 36% 后应 > 90
check("vuln 增伤生效", captured and captured[0] > 85, f"dmg={captured}")

print(f"\n结果: {passed} 通过, 0 失败 ✅")
