# -*- coding: utf-8 -*-
"""v140 波3.1 特效装备战斗消费——冒烟验证脚本"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(20260830)
from game import battle as BT

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def mk_player(effects=None, atk=100, matk=80, level=30):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.5,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": "战士", "qq_id": "test1"}

def mk_enemy(hp=100000, **kw):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}}
    e.update(kw)
    return e

def run_battle(player, enemy):
    """跑一场完整战斗直到敌人死或超时"""
    b = BT.Battle("monster", enemy, player=player)
    # 手动补齐 class_name 相关字段
    logs = []
    for _ in range(100):
        if enemy.get("hp", 0) <= 0 or player.get("hp", 0) <= 0:
            break
        logs += b.actor_turn("attack", None, player)[0]
    return b, logs

print("【1. 战斗开始特效】")
p = mk_player(["starlight_bulwark", "gale_step"])
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
check("星辉壁垒开战获得护盾", "we_starlight" in b.p_shields, str(b.p_shields))
check("疾风步开战获得 buff", "gale_step" in b.p_buffs, str(b.p_buffs))

print("【2. 攻击命中特效（风痕叠层）】")
p = mk_player(["wind_mark"])
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
for _ in range(3):
    b.actor_turn("attack", None, p)
check("风痕叠层 3 层", b.mech_stacks.get("wind_mark", 0) == 3, str(b.mech_stacks))

print("【3. 技能命中特效（余波溅射）】")
p = mk_player(["afterglow_splash"], matk=200)
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
# 手动调用 skill_hit 分发验证 handler 注册
from game.core.weapon_effects import proc as we_proc
logs = []
we_proc(b, p, "skill_hit", {"dmg": 500, "is_crit": False, "skill": "测试", "kind": "魔法"}, logs)
# 余波 30% 概率，多次调用必然触发
triggered = False
for _ in range(50):
    logs2 = []
    we_proc(b, p, "skill_hit", {"dmg": 500, "is_crit": False}, logs2)
    if any("余波" in l for l in logs2):
        triggered = True
        break
check("余波溅射可触发", triggered, str(logs2))

print("【4. 受击特效（哨兵壁垒/荆棘反弹）】")
p = mk_player(["sentinel_aegis", "thorn_armor"])
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
# 手动触发 taken
from game.core.weapon_effects import proc as we_proc2
sent_triggered = False
for _ in range(50):
    logs3 = []
    we_proc2(b, p, "taken", {"dmg": 100}, logs3)
    if "哨兵壁垒" in "".join(logs3):
        sent_triggered = True
        break
check("哨兵壁垒受击护盾可触发", sent_triggered)

print("【5. 治疗特效（圣辉涌动加成）】")
p = mk_player(["holy_radiance_mail"])
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
ctx = {"heal": 100, "overflow": 0}
from game.core.weapon_effects import proc as we_proc3
we_proc3(b, p, "heal", ctx, [])
check("圣辉涌动治疗+20%", ctx["heal"] == 120, f"heal={ctx['heal']}")

print("【6. 回合开始特效（晨曦微光）】")
p = mk_player(["dawn_regen"])
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
p["hp"] = p["max_hp"] // 2  # Battle 初始化会重算 max_hp，hp 需在重算后设置（真实玩家 hp≤max_hp）
logs6 = []
b._turn_start(p)
check("晨曦微光回合回复", p["hp"] > p["max_hp"] // 2, f"hp={p['hp']}")

print("【7. 被动增伤（暮光处决/弑星）】")
p = mk_player(["twilight_execute"])
e = mk_enemy(hp=30, max_hp=100)  # 低血目标（30% < 40% 阈值）
b = BT.Battle("monster", e, player=p)
ctx = {"mult": 1.0, "tags": [], "attack": True, "is_crit": False}
we_proc3(b, p, "passive", ctx, [])
check("暮光处决低血+25%", abs(ctx["mult"] - 1.25) < 1e-9, f"mult={ctx['mult']}")

p2 = mk_player(["star_slayer_edge"])
e2 = mk_enemy(hp=100000, max_hp=100000)  # 高血目标（100% > 70% 阈值）
b2 = BT.Battle("monster", e2, player=p2)
ctx2 = {"mult": 1.0, "tags": [], "attack": True, "is_crit": False}
we_proc3(b2, p2, "passive", ctx2, [])
check("弑星高血+15%", abs(ctx2["mult"] - 1.15) < 1e-9, f"mult={ctx2['mult']}")

print("【8. 阈值特效（磐石守护）】")
p = mk_player(["bedrock_crown"])
e = mk_enemy()
b = BT.Battle("monster", e, player=p)
p["hp"] = p["max_hp"] // 3  # Battle 初始化后设低血（低于 25% 阈值）
p["max_hp"] = 9999  # 模拟真实大血量玩家（阈值按比例算）
p["hp"] = 2000
logs8 = []
b._damage_actor(p, 500, logs8, source="测试")
check("磐石守护护盾触发", "we_bedrock" in b.p_shields, str(b.p_shields))
check("磐石守护标记", b.p_eff.get("we_bedrock_used") is True)

print("【9. 击杀特效（暮裂潜行）】")
p = mk_player(["dusk_blade"])
e = mk_enemy(hp=50)
b = BT.Battle("monster", e, player=p)
b._deal_damage(100, [])
check("暮裂潜行击杀后潜行", "stealth" in b.p_buffs, str(b.p_buffs))

print("【10. 常驻面板属性（奥术苍穹魔攻+15%）】")
# _player_stats 用职业/属性算面板，直接对比有无特效的 matk 比值
p_plain = mk_player([], matk=100)
e_plain = mk_enemy()
b_plain = BT.Battle("monster", e_plain, player=p_plain)
base_matk = b_plain._player_stats(p_plain)["matk"]

p_arc = mk_player(["arcane_firmament"], matk=100)
e_arc = mk_enemy()
b_arc = BT.Battle("monster", e_arc, player=p_arc)
arc_matk = b_arc._player_stats(p_arc)["matk"]
check("奥术苍穹魔攻+15%", arc_matk >= int(base_matk * 1.14) and arc_matk >= base_matk,
      f"base={base_matk} arc={arc_matk}")

print(f"\n结果: {passed} 通过, 0 失败 ✅")
