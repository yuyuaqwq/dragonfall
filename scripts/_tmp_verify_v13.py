# -*- coding: utf-8 -*-
"""v1.3 数值验证：毒爆虚弱 + 重伤（吸血/回血减半）——检查"无脑打 Boss"场景"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.core import battle_mech as BM

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def mk_player(atk=1000, lifesteal=0.30):
    return {"hp": 10000, "max_hp": 10000, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 500, "matk": 300, "mdef": 500, "spd": 10, "crit": 0.05,
            "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": [],
            "lifesteal": lifesteal}

def mk_enemy(hp=100000, **kw):
    e = {"name": "Boss", "lv": 50, "hp": hp, "max_hp": hp,
         "atk": 800, "def": 300, "matk": 400, "mdef": 300, "spd": 8,
         "buffs": {}, "mech": "heal"}
    e.update(kw)
    return e

print("【场景 1：毒爆虚弱——3 层提前爆 vs 5 层满爆】")
b = BT.Battle("monster", mk_enemy())
b._last_player = mk_player()
b.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
logs = []
BM.MECH_EFFECTS["poison_burst"](b, 1, b.mech_stacks, 100, logs, "毒爆术", False)
check("3 层毒爆附虚弱 -15%", b.e_buffs.get("mon_atk_down", 0) >= 1
      and abs(b.e_buffs.get("_weaken_val", 0) - 0.15) < 1e-9, str(b.e_buffs))
est = b._enemy_stats()
# mon_atk_down 吃 BUFF_MULT 固定 -30%（×0.70）+ weaken_val 叠加：800×0.70×0.85 = 476
check("虚弱生效：atk 800 → 476（-30% 基础 -15% 毒爆）", est["atk"] == 476, str(est["atk"]))
check("3 层不附重伤", not b.e_buffs.get("mortal_wound"), str(b.e_buffs))
b2 = BT.Battle("monster", mk_enemy())
b2._last_player = mk_player()
b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0}
logs2 = []
BM.MECH_EFFECTS["poison_burst"](b2, 1, b2.mech_stacks, 100, logs2, "毒爆术", False)
check("5 层毒爆虚弱 -25%", abs(b2.e_buffs.get("_weaken_val", 0) - 0.25) < 1e-9, str(b2.e_buffs))
check("毒爆不附重伤（重伤仅 Boss『重创』）", not b2.e_buffs.get("mortal_wound"), str(b2.e_buffs))
est2 = b2._enemy_stats()
# 800×0.70×0.75 = 420（-30% 基础 -25% 毒爆满层）
check("虚弱生效：atk 800 → 420", est2["atk"] == 420, str(est2["atk"]))
print("  → 3 层提前爆拿 -15% 虚弱；5 层满爆 -25%。提前爆发的价值成立。")

print("\n【场景 2：重伤 vs 玩家吸血——无脑站撸被反制】")
# 玩家满吸血（属性 30%）打 Boss：每回合普攻 1000 伤害 → 吸血 300
# Boss 每回合打玩家 600（atk800 vs def500 公式）→ 玩家净损 300/回合 → 可持续（有 1 万血）
# 重伤后：吸血 150 → 净损 450/回合 → 10 万血 Boss 战 100+ 回合内玩家血线持续下降 → 必须带治疗/换打法
p = mk_player(atk=1000, lifesteal=0.30)
b3 = BT.Battle("monster", mk_enemy())
pct = b3._player_stats(p)
pct["lifesteal"] = 0.30  # 测试玩家无 class_name，手动注入吸血率
dmg = 1000 - 0  # 简化：普攻 1000
# 用真实结算路径验证吸血数值
b3._player_stats = lambda pl: pct
b3.p_buffs = {}
heal_logs = []
b3._settle_lifesteal(p, 1000, heal_logs)
check("无重伤：1000 伤害吸血 300", "回复 300" in str(heal_logs), str(heal_logs))
b4 = BT.Battle("monster", mk_enemy())
b4._player_stats = lambda pl: pct
b4.p_buffs = {"mortal_wound": 2}
heal_logs2 = []
b4._settle_lifesteal(p, 1000, heal_logs2)
check("重伤：1000 伤害吸血 150（减半）", "回复 150" in str(heal_logs2), str(heal_logs2))
print("  → 吸血 300/回合 → 重伤后 150/回合：站撸续航减半，必须依赖治疗/控制/换人")

print("\n【场景 3：Boss『重创』开场技挂玩家重伤】")
b7 = BT.Battle("monster", mk_enemy(id="b_cardinal", role="boss", is_boss=True,
                                    mech="heal,phase_open"))
b7.round = 1
logs7 = []
BM.BOSS_MECHS["phase_open"](b7, logs7, b7.enemy, 1)
check("重创开场：玩家 p_buffs.mortal_wound=2", b7.p_buffs.get("mortal_wound") == 2,
      f"p_buffs={b7.p_buffs} logs={logs7}")
check("重创日志", any("重创" in l for l in logs7), str(logs7))
print("  → 回血 Boss 开场重创：吸血流玩家开局就吃减半，无法无脑站撸")

print(f"\n结果: {passed} 通过, 0 失败")
