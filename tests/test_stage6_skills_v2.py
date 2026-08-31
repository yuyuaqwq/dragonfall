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

print("【战士：战意攒取与终结技】")
p = learn_all(mk("战士"), "cls_zhan_shi")
b = BT.Battle("monster", mkmon(), player=p)
check("战意初始 0", b.mech_stacks.get("zhan_yi", 0) == 0, str(b.mech_stacks))
logs = cast(b, p, "挥砍")
# v151：挥砍 mech=zhan_yi（叠层不消耗），怒气 rage 由 core_resource on_skill=2 攒取
check("挥砍战意+1", b.mech_stacks.get("zhan_yi", 0) == 1, str(b.mech_stacks))
check("挥砍怒气+2", b.resources.get("rage", 0) == 2, str(b.resources))
check("挥砍造成伤害", any("造成" in x for x in logs), str(logs)[:120])
# v151：裂地斩移至分支（狂战士 Lv.45，战意≥6 层条件技），基础表无终结技——
# 分支技能需 lv≥45 + 已学才可施放，用 lv=50 且显式学习裂地斩的玩家验证战意条件门槛
p50 = learn_all(mk("战士", lv=50), "cls_zhan_shi")
p50["learned_skills"] = list(p50["learned_skills"]) + ["裂地斩"]
b2 = BT.Battle("monster", mkmon(), player=p50)
b2.mech_stacks["zhan_yi"] = 2
logs2 = cast(b2, p50, "裂地斩")
check("裂地斩战意不足无增伤", not any("战意裂地" in x for x in logs2), str(logs2)[:120])
# 战意攒够 6 层 → 裂地斩增伤触发
b2.mech_stacks["zhan_yi"] = 6
logs3 = cast(b2, p50, "裂地斩")
check("裂地斩战意≥6 增伤", any("战意" in x for x in logs3), str(logs3)[:120])
check("裂地斩造成伤害", any("造成" in x for x in logs3), str(logs3)[:120])

print("【法师：元素系与元素反应】")
p = learn_all(mk("法师"), "cls_fa_shi")
b3 = BT.Battle("monster", mkmon(), player=p)
check("法师默认火系", b3.resources.get("element") == "fire", str(b3.resources))
# v151：基础元素技能（火球术/冰锥）不再挂元素印记——印记体系下沉到分支
# （元素法师 element=current 技能），基础层纯蓝施法（core_resource element on_skill=0）。
# 验证基础火球术不挂 fire_mark（v151 设计：印记在分支）
logs = cast(b3, p, "火球术")
check("火球术不挂火印（基础层纯蓝）", b3.e_buffs.get("fire_mark", 0) == 0, str(b3.e_buffs))
check("火球术造成伤害", any("造成" in x for x in logs), str(logs)[:120])
# v151：冰锥 mech=spd_down（30% 概率减速），不再消费火印蒸发——验证减速机制。
# 注意：减速回合数=1，player_turn 尾部 _end_round 会递减清掉（下回合才生效的语义），
# 因此断言用 _do_player_skill 后的即时 e_buffs + 减速日志（同 test_commands_battle 口径）
b4 = BT.Battle("monster", mkmon(), player=p)
random.seed(2)
logs4 = b4._do_player_skill("冰锥", p)
check("冰锥减速（spd_down）", b4.e_buffs.get("spd_down", 0) > 0, str(b4.e_buffs))
check("冰锥减速日志", any("减速" in x for x in logs4), str(logs4)[:120])
check("冰锥造成伤害", any("造成" in x for x in logs4), str(logs4)[:120])

print("【游侠：精力消耗不耗魔】")
# v130.2 引擎回归追踪：_init_resources 丢失 `elif k == "energy": =max(100)` 分支
# → 精力初始 0（docstring/设计稿仍写“精力满 100”），「精力初始满 100」「疾风连射耗 20 精力」
# 两断言挂红，待引擎修复后回归（不掩改断言）。
# v139 凝神屏息：精力=100 回合开始自动排气归零——初始 100 会被排空，改 80 测「不满 100 正常消耗」
p = learn_all(mk("游侠"), "cls_you_xia")
b5 = BT.Battle("monster", mkmon(), player=p)
check("精力初始满 100", b5.resources.get("energy", 0) == 100, str(b5.resources))
# v139：满 100 回合开始自动凝神屏息归零（签名机制），下一行动从 0 起
logs = cast(b5, p, "疾风连射")
check("精力初始满 100 触发凝神屏息归零", any("气息" in x or "排气" in x for x in logs), str(logs)[:120])
# 不满 100 正常消耗：重置精力到 50（50+回合回30=80 不满 100 不排气），疾风连射耗 20 → 60
b5.resources["energy"] = 50
logs = cast(b5, p, "疾风连射")
check("疾风连射耗 20 精力", b5.resources.get("energy", 0) == 60, str(b5.resources))
# v151：疾风连射 mp=5（有魔力消耗）——精力机制是主耗渠道，但技能仍带基础 mp 成本
check("疾风连射耗 5 魔", p["mp"] == 500 - 5, str(p["mp"]))
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
# v151：暗杀不再耗连击点（改 cd3+15mp 满血必暴爆发技，cp 留给分支终结·处刑 cp5）
logs8 = cast(b8, p, "暗杀")
check("暗杀不耗连击点", b8.resources.get("cp", 0) == 4, str(b8.resources))
check("暗杀造成伤害", any("造成" in x for x in logs8), str(logs8)[:120])
# 分支终结技消费连击点：终结·处刑 res_cost cp5（暗杀 cp 攒到 5 → 处刑清零）
finisher = None
for _t, _br in C.BRANCH_SKILLS["cls_ci_ke"]["branches"].items():
    for _bn, _sk in _br.items():
        for _kk, _vv in _sk.items():
            if (_vv.get("res_cost") or {}).get("cp") == 5:
                finisher = _vv.get("name")
if finisher:
    p2 = learn_all(mk("刺客"), "cls_ci_ke")
    b8b = BT.Battle("monster", mkmon(), player=p2)
    b8b.resources["cp"] = 5
    logs8b = cast(b8b, p2, finisher)
    check(f"终结·处刑消耗 5 连击点", b8b.resources.get("cp", 0) == 0, str(b8b.resources))
    check(f"终结·处刑造成伤害", any("造成" in x for x in logs8b), str(logs8b)[:120])

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
# v152 绝对时刻制：盾击 CD=3 秒；战士 lv30 默认 spd 27 → 行动窗口 p_ct = cost(1.48)+CAST_SKILL(1.6)
# = 3.08 ≥ 3.0 → 施放后推进时 CD 已到期（与 test_stage5 同款语义）。CD 拦截/到期逻辑由
# 手动置 CD 路径覆盖（确定性）：_set_skill_cd(3) → 拦截 → 推进 3×ACT_TICK → 放行。
b10._set_skill_cd("盾击", 3)
check("盾击后进入 CD（手动置 CD 3）", b10._skill_on_cd("盾击"), str(b10.cooldown))
logs10 = cast(b10, p, "盾击")
check("CD 中拦截", any("冷却" in x for x in logs10), str(logs10)[:120])
# v152 时刻制：推进 3 回合（3×ACT_TICK=3.0）使 ready_at 到期
b10._end_round(); b10._end_round(); b10._end_round()
check("CD 结束可再放", not b10._skill_on_cd("盾击"), str(b10.cooldown))

print("【被动保留】")
# v151：基础表无 kind=被动 技能（被动下沉到分支），改验证分支被动存在
for cls_id, names in [("cls_zhan_shi", ["淬血", "守护姿态", "内燃", "狂热", "坚韧", "坚城之姿"])]:
    have = set()
    for _t, _br in C.BRANCH_SKILLS[cls_id]["branches"].items():
        for _bn, _sk in _br.items():
            for _kk, _vv in _sk.items():
                if _vv.get("kind") == "被动":
                    have.add(_vv.get("name"))
    check(f"{cls_id} 分支被动保留", all(n in have for n in names), str(have))

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
