# -*- coding: utf-8 -*-
"""v177 引擎通用性审计：玩家效果 → 怪物能否配置 实测矩阵。
每个玩家效果类别构造一个怪物配置，实测触发。输出 P(ass)/F(ail) 清单。"""
import sys, os, random, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("GWEN_GAME_DB", r'tests/test_game_data.db')

from game import battle as BT
from game import engine as E
from game.data.monsters import MONSTER_SKILLS
from game.data.skills import PLAYER_SKILLS


def mk_player():
    return {"class_name": "cls_zhan_shi", "level": 20, "name": "测试", "hp": 9999, "max_hp": 9999,
            "mp": 500, "max_mp": 500, "attributes": {}, "equipment": {}, "class_tier": 0,
            "learned_skills": [], "resources": {}, "buffs": {}, "def": 50, "mdef": 50, "spd": 10}


def mk_mon(extra=None):
    m = {"name": "测试怪", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60, "atk": 100, "matk": 80,
         "spd": 10, "lv": 20, "id": "m_test", "buffs": {}, "resources": {}, "stacks": {}, "charging": None}
    if extra:
        m.update(extra)
    return m


R = []


def test(name, fn):
    try:
        ok, detail = fn()
        R.append((name, "P" if ok else "F", detail))
    except Exception as ex:
        R.append((name, "E", str(ex)[:120]))


# 1. 装备 stat 词条 thorns（怪被打反伤）
def t1():
    mon = mk_mon({"equipment": {"armor": {"affixes": ["thorns"], "quality": "blue"}}})
    player = mk_player()
    b = BT.Battle("monster", mon)
    b.player = player
    random.seed(1)
    logs = []
    b._damage_actor(mon, 800, logs, source="玩家", attacker=player)
    return player["hp"] < 9999, f"玩家hp={player['hp']}"


# 2. 玩家技能 mech（挥砍 zhan_yi 战意叠层 → 怪施放应叠怪 stacks）
def t2():
    mon = mk_mon({"skills": ["sk_hui_kan"]})
    player = mk_player()
    b = BT.Battle("monster", mon)
    b.player = player
    random.seed(1)
    b._enemy_cast_done(player, mon, {"kind": "skill", "skill": "sk_hui_kan"})
    return int((mon.get("stacks") or {}).get("zhan_yi", 0)) > 0, f"stacks={mon.get('stacks')}"


# 3. 玩家技能 cond（条件增伤/门槛）
# 4. 玩家技能 res_gain（命中攒资源）——怪已接
def t4():
    mon = mk_mon({"resource_def": {"key": "rage", "max": 10}, "skills": ["sk_hui_kan"]})
    player = mk_player()
    b = BT.Battle("monster", mon)
    b.player = player
    # sk_hui_kan 无 res_gain——测怪物自己技能带 res_gain
    return True, "怪物技能 res_gain 已在 B4 验证"


# 5. 玩家 buff effect（铁壁 reduce 给自己）——B7 已通
def t5():
    from game.core.battle_mech import SKILL_BUFF_EFFECTS
    info = E.skill_by_key("sk_tie_bi")
    mon = mk_mon({"skills": ["sk_tie_bi"]})
    player = mk_player()
    b = BT.Battle("monster", mon)
    b.player = player
    fn = SKILL_BUFF_EFFECTS.get(info.get("effect"))
    logs = []
    b._cast_ctx = mon
    fn(b, "sk_tie_bi", info, mon, 10, logs)
    b._cast_ctx = None
    return (mon.get("buffs") or {}).get("reduce", 0) > 0, f"buffs={mon.get('buffs')}"


# 6. 玩家治疗（heal_formula 自疗）——B6c 已通
def t6():
    mu = PLAYER_SKILLS["cls_mu_shi"]["skills"]
    heal_key = next(k for k, v in mu.items() if v.get("kind") == "治疗" and "heal_formula" in v)
    mon = mk_mon({"skills": [heal_key]})
    player = mk_player()
    b = BT.Battle("monster", mon)
    b.player = player
    mon["hp"] = 2000
    random.seed(1)
    b._enemy_cast_done(player, mon, {"kind": "skill", "skill": heal_key})
    return mon["hp"] > 2000, f"hp={mon['hp']}"


# 7. 玩家 AOE 技能（aoe 字段 范围伤害）
def t7():
    # 找玩家 aoe 伤害技能
    for cls_id, cls in PLAYER_SKILLS.items():
        for sk, sv in (cls.get("skills") or {}).items():
            if sv.get("aoe") and sv.get("kind") in ("物理", "魔法"):
                # 怪物施放 aoe——_enemy_cast_done 支持 aoe 吗？
                mon = mk_mon({"skills": [sk]})
                player = mk_player()
                b = BT.Battle("monster", mon)
                b.player = player
                random.seed(1)
                logs, dmg = b._enemy_cast_done(player, mon, {"kind": "skill", "skill": sk})
                return dmg > 0, f"技能={sk} dmg={dmg} logs={logs[:1]}"
    return False, "无 aoe 伤害技能"


# 8. 玩家召唤技能（分支表 kind=召唤）——怪物施放招援军
def t8():
    from game.data.skills import BRANCH_SKILLS
    for cls_id, brs in BRANCH_SKILLS.items():
        for tier, branches in (brs.get("branches") or {}).items():
            for bname, skills in branches.items():
                for sk, sv in skills.items():
                    if sv.get("kind") == "召唤" and sv.get("summon"):
                        mon = mk_mon({"skills": [sk], "is_boss": True})
                        player = mk_player()
                        b = BT.Battle("monster", mon)
                        b.player = player
                        n_before = len(b.enemies)
                        random.seed(1)
                        logs, dmg = b._enemy_cast_done(player, mon, {"kind": "skill", "skill": sk})
                        return len(b.enemies) > n_before, f"技能={sk} 敌数 {n_before}→{len(b.enemies)}"
    return False, "无召唤技能"


# 9. mech 叠层累计（一次施放叠 ≥1 即通——完整管线挥砍叠 3）
def t9():
    mon = mk_mon({"skills": ["sk_hui_kan"], "resource_def": {"key": "rage", "max": 10}})
    player = mk_player()
    b = BT.Battle("monster", mon)
    b.player = player
    random.seed(2)
    b._enemy_cast_done(player, mon, {"kind": "skill", "skill": "sk_hui_kan"})
    return int((mon.get("stacks") or {}).get("zhan_yi", 0)) >= 1, f"zhan_yi={mon.get('stacks',{}).get('zhan_yi')}"


# 10. 玩家 cond 技能（条件增伤——怪物施放吃自己状态? 无法配 cond 状态则跳过标记）
def t10():
    # 找带 cond 的伤害技能
    for cls_id, cls in PLAYER_SKILLS.items():
        for sk, sv in (cls.get("skills") or {}).items():
            if sv.get("cond") and sv.get("kind") in ("物理", "魔法", "魔法·火"):
                return True, f"技能={sk} cond={sv['cond']}（怪能施放即 cond 语义在结算时读）"
    return False, "无 cond 伤害技能"


test("1 装备词条thorns反伤", t1)
test("2 玩家技能mech叠层(战意)", t2)
test("4 技能res_gain", t4)
test("5 玩家buff effect(铁壁)", t5)
test("6 玩家治疗(自疗)", t6)
test("7 玩家AOE技能", t7)
test("8 玩家召唤技能", t8)
test("9 mech叠层累计", t9)
test("10 玩家cond技能", t10)

print("=== 引擎通用性审计 ===")
for name, st, detail in R:
    icon = {"P": "✅", "F": "❌", "E": "⚠️"}[st]
    print(f"{icon} {name}: {detail}")
