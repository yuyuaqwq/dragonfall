# -*- coding: utf-8 -*-
"""阶段六：基础技能 v2.0 数据 + 战斗消费验证（12 章）"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run
from data.plugins.dragonfall.game import battle as BT

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk(cls, lv=30, mp=500):
    return {'class_name': cls, 'level': lv, 'hp': 999, 'max_hp': 999, 'mp': mp, 'max_mp': mp,
            'atk': 60, 'def': 20, 'matk': 60, 'mdef': 20, 'spd': 15, 'crit': 0.05, 'dodge': 0.03,
            'equipment': {}, 'learned_skills': [], 'skill_levels': {}}

def mkmon(name='木桩', hp=99999, spd=1):
    return {'name': name, 'hp': hp, 'max_hp': hp, 'atk': 5, 'def': 10, 'matk': 0, 'mdef': 10,
            'spd': spd, 'lv': 30, 'role': 'dps', 'skills': []}

def learn_all(p, cls):
    """学习该职业全部主动技能"""
    sk = C.PLAYER_SKILLS[cls]["skills"]
    p["learned_skills"] = [v["name"] for v in sk.values() if v.get("kind") != "被动"]
    return p

def cast(b, p, skill):
    """施放技能（跳过回合流转）"""
    logs, _ = b.player_turn("skill", skill, p, enemy_act=False)
    return logs

print("【战士：怒气攒取与终结技】")
p = learn_all(mk("战士"), "cls_zhan_shi")
b = BT.Battle("monster", mkmon(), player=p)
check("怒气初始 0", b.resources.get("rage", 0) == 0, str(b.resources))
logs = cast(b, p, "挥砍")
check("挥砍怒气+1", b.resources.get("rage", 0) == 1, str(b.resources))
check("挥砍造成伤害", any("造成" in x for x in logs), str(logs)[:120])
# 怒气不足拦截终结技
b2 = BT.Battle("monster", mkmon(), player=p)
logs2 = cast(b2, p, "裂地斩")
check("裂地斩怒气不足拦截", any("不足" in x for x in logs2), str(logs2)[:120])
# 攒够 3 怒气后可用
b2.resources["rage"] = 3
logs3 = cast(b2, p, "裂地斩")
check("裂地斩消耗 3 怒气", b2.resources.get("rage", 0) == 0, str(b2.resources))
check("裂地斩造成伤害", any("造成" in x for x in logs3), str(logs3)[:120])

print("【法师：元素系与元素反应】")
p = learn_all(mk("法师"), "cls_fa_shi")
b3 = BT.Battle("monster", mkmon(), player=p)
check("法师默认火系", b3.resources.get("element") == "fire", str(b3.resources))
logs = cast(b3, p, "火球术")
check("火球挂火印", b3.e_buffs.get("fire_mark", 0) == 1, str(b3.e_buffs))
# 冰锥打火印 → 蒸发增伤
b4 = BT.Battle("monster", mkmon(), player=p)
b4.e_buffs["fire_mark"] = 1
random.seed(7)
b4.player_turn("skill", "冰锥", p, enemy_act=False)
check("冰锥对火印蒸发", b4.e_buffs.get("fire_mark", 0) == 0, str(b4.e_buffs))

print("【游侠：精力消耗不耗魔】")
p = learn_all(mk("游侠"), "cls_you_xia")
b5 = BT.Battle("monster", mkmon(), player=p)
check("精力初始满 100", b5.resources.get("energy", 0) == 100, str(b5.resources))
logs = cast(b5, p, "疾风连射")
check("疾风连射耗 20 精力", b5.resources.get("energy", 0) == 80, str(b5.resources))
check("游侠不耗魔", p["mp"] == 500, str(p["mp"]))
# 精力不足拦截（回合开始回 25：5→30 < 35）
b6 = BT.Battle("monster", mkmon(), player=p)
b6.resources["energy"] = 4
logs6 = cast(b6, p, "致命狙击")
check("精力不足拦截", any("不足" in x for x in logs6), str(logs6)[:120])

print("【牧师：治疗与信仰】")
p = learn_all(mk("牧师"), "cls_mu_shi")
b7 = BT.Battle("monster", mkmon(), player=p)
p["hp"] = 100
logs7 = cast(b7, p, "治愈术")
check("治愈术回血", p["hp"] > 100, f"hp={p['hp']}")
check("治愈术信仰+2", b7.resources.get("faith", 0) == 2, str(b7.resources))

print("【刺客：连击点】")
p = learn_all(mk("刺客"), "cls_ci_ke")
b8 = BT.Battle("monster", mkmon(), player=p)
cast(b8, p, "刺击")
check("刺击连击点+1", b8.resources.get("cp", 0) == 1, str(b8.resources))
cast(b8, p, "刺击")
cast(b8, p, "刺击")
check("攒 3 连击点", b8.resources.get("cp", 0) == 3, str(b8.resources))
logs8 = cast(b8, p, "暗杀")
check("暗杀消耗 3 连击点", b8.resources.get("cp", 0) == 0, str(b8.resources))
check("暗杀造成伤害", any("造成" in x for x in logs8), str(logs8)[:120])

print("【拳师：连招与气】")
p = learn_all(mk("拳师"), "cls_wu_seng")
b9 = BT.Battle("monster", mkmon(), player=p)
cast(b9, p, "直拳")
check("直拳连招拳", b9.combo_seq == ["拳"], str(b9.combo_seq))
check("直拳气+1", b9.resources.get("chi", 0) == 1, str(b9.resources))
cast(b9, p, "侧踢")
check("侧踢连招拳→踢", b9.combo_seq == ["拳", "踢"], str(b9.combo_seq))
cast(b9, p, "钢拳")
check("钢拳三连触发", b9.combo_seq == [] and b9.resources.get("combo_ready") == 1, str((b9.combo_seq, b9.resources)))

print("【CD 冷却：盾击】")
p = learn_all(mk("战士"), "cls_zhan_shi")
b10 = BT.Battle("monster", mkmon(), player=p)
cast(b10, p, "盾击")
check("盾击后进入 CD", b10._skill_on_cd("盾击"), str(b10.cooldown))
logs10 = cast(b10, p, "盾击")
check("CD 中拦截", any("冷却" in x for x in logs10), str(logs10)[:120])
b10._tick_cooldowns(); b10._tick_cooldowns(); b10._tick_cooldowns()
check("CD 结束可再放", not b10._skill_on_cd("盾击"), str(b10.cooldown))

print("【被动保留】")
for cls_id, names in [("cls_zhan_shi", ["战意高涨", "铁壁之心", "破甲本能", "战争咆哮"])]:
    sk = C.PLAYER_SKILLS[cls_id]["skills"]
    have = {v.get("name") for v in sk.values() if v.get("kind") == "被动"}
    check(f"{cls_id} 被动保留", all(n in have for n in names), str(have))

print("【BUILDS 流派引用】")
bad = []
for cls_id, builds in C.BUILDS.items():
    sk_names = {v.get("name") for v in C.PLAYER_SKILLS[cls_id]["skills"].values()}
    # v112：隐藏线推荐方案引用流派分支技能（BRANCH_SKILLS），一并校验
    for _t, _br in (C.BRANCH_SKILLS.get(cls_id, {}).get("branches", {}) or {}).items():
        for _bn, _skills in _br.items():
            sk_names |= {v.get("name") for v in _skills.values()}
    for bname, b in builds.items():
        for s in b["skills"]:
            if s not in sk_names:
                bad.append(f"{cls_id}/{bname}:{s}")
check("BUILDS 无坏引用", not bad, str(bad))

print(f"\n结果: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
