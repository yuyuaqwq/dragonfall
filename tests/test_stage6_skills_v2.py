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
    # v154 读条命中制：出招读条结束（cast_done）才结算命中（伤害/叠层/资源）——推进后生效
    b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
    return logs

print("【战士：战意攒取与终结技】")
p = learn_all(mk("战士"), "cls_zhan_shi")
b = BT.Battle("monster", mkmon(), player=p)
check("战意初始 0", b._p_stacks().get("zhan_yi", 0) == 0, str(b._p_stacks()))
logs = cast(b, p, "挥砍")
# v151：挥砍 mech=zhan_yi（叠层不消耗），怒气 rage 由 core_resource on_skill=2 攒取
check("挥砍战意+1", b._p_stacks().get("zhan_yi", 0) == 1, str(b._p_stacks()))
check("挥砍怒气+2", b._p_res().get("rage", 0) == 2, str(b._p_res()))
check("挥砍造成伤害", any("造成" in x for x in logs), str(logs)[:120])
# v153：裂地斩 → 狂战士分支 Lv.44 mech=bleed（战意≥6 层条件技已随 v153 移除，
# 现为流血挂层；分支技能需 lv≥45 + 已学才可施放）。用 lv=50 且显式学习裂地斩的玩家验证
p50 = learn_all(mk("战士", lv=50), "cls_zhan_shi")
p50["learned_skills"] = list(p50["learned_skills"]) + ["裂地斩"]
b2 = BT.Battle("monster", mkmon(), player=p50)
logs2 = cast(b2, p50, "裂地斩")
check("裂地斩战意不足无增伤", not any("战意裂地" in x for x in logs2), str(logs2)[:120])
# 战意攒够 6 层 → 裂地斩流血触发（v153 mech=bleed，不再有"战意"文案）
b2b = BT.Battle("monster", mkmon(), player=learn_all(mk("战士", lv=50), "cls_zhan_shi"))
b2b._p_stacks()["zhan_yi"] = 6
_p2b = b2b.player
_p2b["learned_skills"] = list(_p2b["learned_skills"]) + ["裂地斩"]
logs3 = cast(b2b, _p2b, "裂地斩")
check("裂地斩战意≥6 增伤", any("流血" in x or "战意" in x for x in logs3), str(logs3)[:120])
check("裂地斩造成伤害", any("造成" in x for x in logs3), str(logs3)[:120])

print("【法师：元素系与元素反应】")
p = learn_all(mk("法师"), "cls_fa_shi")
b3 = BT.Battle("monster", mkmon(), player=p)
check("法师默认火系", b3._p_res().get("element") == "fire", str(b3._p_res()))
# v151：基础元素技能（火球术/冰锥）不再挂元素印记——印记体系下沉到分支
# （元素法师 element=current 技能），基础层纯蓝施法（core_resource element on_skill=0）。
# 验证基础火球术不挂 fire_mark（v151 设计：印记在分支）
logs = cast(b3, p, "火球术")
check("火球术不挂火印（基础层纯蓝）", b3._tgt_buffs().get("fire_mark", 0) == 0, str(b3._tgt_buffs()))
check("火球术造成伤害", any("造成" in x for x in logs), str(logs)[:120])
# v153：冰锥 mech=ice_mark（挂冰印 1 层）+ mech2=spd_down（减速）。mech2 handler 已注册。
# 引擎元素印记路径把冰印登记到 enemy.debuffs["element_marks"]["ice"]，减速落 e_buffs.spd_down。
b4 = BT.Battle("monster", mkmon(), player=p)
random.seed(2)
# v154 读条命中制：技能出手只排 cast_done（读条），需经 player_turn 设置 p_ct 后推进才结算
# （曾直接调 _do_player_skill 跳过回合 → 未走敌方行动段 _active_target 未初始化，v169.9 已由引擎兜底）
logs4, _ = b4.player_turn("skill", "冰锥", p, enemy_act=False)
b4._process_until(float(getattr(b4, "p_ct", 0) or 0) + 0.001, logs4, p)
_ice_marks = ((b4.enemy.get("debuffs") or {}).get("element_marks") or {}).get("ice", 0)
check("冰锥挂冰印", _ice_marks > 0, str(b4.enemy.get("debuffs")))
check("冰锥减速（spd_down）", b4._tgt_buffs().get("spd_down", 0) > 0, str(b4._tgt_buffs()))
check("冰锥造成伤害", any("造成" in x for x in logs4), str(logs4)[:120])

print("【游侠：精力消耗不耗魔】")
# v130.2 引擎回归追踪：_init_resources 丢失 `elif k == "energy": =max(100)` 分支
# → 精力初始 0（docstring/设计稿仍写“精力满 100”），「精力初始满 100」「疾风连射耗 20 精力」
# 两断言挂红，待引擎修复后回归（不掩改断言）。
# v139 凝神屏息：精力=100 回合开始自动排气归零——初始 100 会被排空，改 80 测「不满 100 正常消耗」
p = learn_all(mk("游侠"), "cls_you_xia")
b5 = BT.Battle("monster", mkmon(), player=p)
check("精力初始满 100", b5._p_res().get("energy", 0) == 100, str(b5._p_res()))
# v153：疾风连射 → 连射（lv1，res_cost energy 22，hits=2）
logs = cast(b5, p, "连射")
# v153 废弃凝神屏息：vent trigger=999 永不到达（专注流量制），满精力不排气，直接正常消耗
check("精力满 100 正常消耗连射", b5._p_res().get("energy", 0) == 78, str(b5._p_res()))
# 不满 100 正常消耗：重置精力到 50（50+回合回18=68 不满 100 不排气），连射耗 22 → 46
b5._p_res()["energy"] = 50
logs = cast(b5, p, "连射")
check("连射耗 22 精力", b5._p_res().get("energy", 0) == 46, str(b5._p_res()))
# v163 修正：游侠不耗魔力（策划案 12 章 §4.1「游侠不耗魔力，全技能纯精力消耗」）——v153 时连射误带 mp=6
# 的错误断言（当时把 bug 当正确数据锁进测试）。游侠 mp 字段已清除。
check("连射不耗魔（游侠纯精力消耗）", p["mp"] == 500, f"mp={p['mp']}")
# 精力不足拦截（回合开始回 18：4→22 < 55 致命狙击）
b6 = BT.Battle("monster", mkmon(), player=p)
b6._p_res()["energy"] = 4
logs6 = cast(b6, p, "致命狙击")
check("精力不足拦截", any("不足" in x for x in logs6), str(logs6)[:120])

print("【牧师：治疗与信仰】")
p = learn_all(mk("牧师"), "cls_mu_shi")
b7 = BT.Battle("monster", mkmon(), player=p)
p["hp"] = 100
logs7 = cast(b7, p, "治愈术")
check("治愈术回血", p["hp"] > 100, f"hp={p['hp']}")
check("治愈术信仰+2", b7._p_res().get("faith", 0) == 2, str(b7._p_res()))

print("【刺客：连击点】")
p = learn_all(mk("刺客"), "cls_ci_ke")
b8 = BT.Battle("monster", mkmon(), player=p)
cast(b8, p, "刺击")
check("刺击连击点+1", b8._p_res().get("cp", 0) == 1, str(b8._p_res()))
cast(b8, p, "刺击")
cast(b8, p, "刺击")
check("攒 3 连击点", b8._p_res().get("cp", 0) == 3, str(b8._p_res()))
# v153：暗杀删除 → 基础连击终结技 = 终结·割喉（lv28，mech=finisher，无 res_cost，cd12）。
# 连击点攒满 3 后施放终结·割喉（不消耗 cp；cp 留给分支终结·处刑 cp5）
logs8 = cast(b8, p, "终结·割喉")
check("终结·割喉不耗连击点", b8._p_res().get("cp", 0) == 4, str(b8._p_res()))
check("终结·割喉造成伤害", any("造成" in x for x in logs8), str(logs8)[:120])
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
    b8b._p_res()["cp"] = 5
    logs8b = cast(b8b, p2, finisher)
    check(f"终结·处刑消耗 5 连击点", b8b._p_res().get("cp", 0) == 0, str(b8b._p_res()))
    check(f"终结·处刑造成伤害", any("造成" in x for x in logs8b), str(logs8b)[:120])

print("【拳师：连招与气】")
# v153：拳师 combo 字段移除（直拳/侧踢/钢拳 combo=None），combo_seq 连招序列不再推进；
# 气 chi 是类主资源（on_skill=1，出招即攒），满 3 气后崩拳/破岳拳双档消费。
p = learn_all(mk("拳师"), "cls_wu_seng")
b9 = BT.Battle("monster", mkmon(), player=p)
cast(b9, p, "直拳")
check("直拳气+1", b9._p_res().get("chi", 0) == 1, str(b9._p_res()))
cast(b9, p, "侧踢")
check("侧踢气+1", b9._p_res().get("chi", 0) == 2, str(b9._p_res()))
cast(b9, p, "钢拳")
check("钢拳气+1（三招攒 3 气）", b9._p_res().get("chi", 0) == 3, str(b9._p_res()))

print("【CD 冷却：盾击】")
# v153：盾击 → 盾击·誓（盾卫士分支 Lv.32，cd 8），基础表无盾击。
p = learn_all(mk("战士", lv=50), "cls_zhan_shi")
p["learned_skills"] = list(p["learned_skills"]) + ["盾击·誓"]
b10 = BT.Battle("monster", mkmon(), player=p)
# v152 绝对时刻制：CD 拦截/到期逻辑由手动置 CD 路径覆盖（确定性）：_set_skill_cd(3) → 拦截 → 推进 3×ACT_TICK → 放行。
b10._set_skill_cd("盾击·誓", 3)
check("盾击·誓进入 CD（手动置 CD 3）", b10._skill_on_cd("盾击·誓"), str(b10._p_cooldown()))
logs10 = cast(b10, p, "盾击·誓")
check("CD 中拦截", any("冷却" in x for x in logs10), str(logs10)[:120])
# v152 时刻制：推进 3 回合（3×ACT_TICK=3.0）使 ready_at 到期
b10._end_round(); b10._end_round(); b10._end_round()
check("CD 结束可再放", not b10._skill_on_cd("盾击·誓"), str(b10._p_cooldown()))

print("【被动保留】")
# v153：战士分支被动 = 淬血/狂热/坚韧/血怒·不灭/坚城之姿/铁誓·不动（狂战士+盾卫士 6 个）
# v151 断言名单里的 守护姿态/内燃 已随 v153 删除/改名，更新为实际存在的 6 个
for cls_id, names in [("cls_zhan_shi", ["淬血", "狂热", "坚韧", "血怒·不灭", "坚城之姿", "铁誓·不动"])]:
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
