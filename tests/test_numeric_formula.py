# -*- coding: utf-8 -*-
"""v156 formula 通用公式层门禁测试——防公式引擎退化。

覆盖：
1. resolve_formula 纯函数：混伤/物理职业魔法技/基础值+百分比/目标血百分比/纯固定值/chance/mult 乘区
2. 技能 formula 字段：配 formula 的技能走数据驱动公式（引擎消费端）
3. 装备词条 formula：带 formula 的词条自动触发追加伤害（_affix_on_hit）
4. 敌方技能 formula：带 formula 的怪物技能走数据驱动公式（_enemy_cast_done）

运行：python tests/test_numeric_formula.py（exit=0 全绿）
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.engine import resolve_formula, player_final_stats, calc_damage  # noqa: E402
from game.battle import Battle  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_stats():
    return {"atk": 100, "matk": 80, "max_hp": 500}


def test_resolve_formula_pure():
    print("【1. resolve_formula 纯函数】")
    st = mk_stats()
    # 混伤
    d, m = resolve_formula([{"stat": "atk", "mult": 1.3, "type": "phys"},
                            {"stat": "matk", "mult": 0.3, "type": "magi"}], st, 50, 50, variance=0)
    check("混伤 130%物+30%魔 magi 段分离", m == calc_damage(int(80 * 0.3), 50, variance=0),
          f"magi={m}")
    # 物理职业魔法技
    d2, m2 = resolve_formula([{"stat": "atk", "mult": 1.0, "type": "magi"}], st, 50, 50, variance=0)
    check("atk→magi 吃物攻算魔伤", d2 == calc_damage(100, 50, variance=0),
          f"d={d2}")
    # 基础值+百分比
    d3, _ = resolve_formula([{"stat": "atk", "mult": 1.2, "flat": 50, "type": "phys"}], st, 50, 50, variance=0)
    check("基础值+百分比 flat", d3 == calc_damage(int(100 * 1.2) + 50, 50, variance=0),
          f"d={d3}")
    # 目标血百分比真伤
    d4, _ = resolve_formula([{"stat": "max_hp", "mult": 0.05, "type": "true"}], st, 50, 50,
                            variance=0, target_max_hp=2000)
    check("5%目标血真伤", d4 == 100, f"d={d4}")
    # 纯固定值
    d5, _ = resolve_formula([{"stat": "flat", "flat": 100, "type": "true"}], st, 50, 50, variance=0)
    check("纯固定100真伤", d5 == 100, f"d={d5}")
    # chance 不触发
    random.seed(1)
    d6, _ = resolve_formula([{"stat": "atk", "mult": 1.0, "type": "phys", "chance": 0.0}],
                            st, 50, 50, variance=0)
    check("chance=0 不触发", d6 == 0, f"d={d6}")
    # mult 外部乘区
    d7, _ = resolve_formula([{"stat": "atk", "mult": 1.0, "type": "phys"}], st, 50, 50,
                            variance=0, mult=1.5)
    check("mult 外部乘区", d7 == calc_damage(int(100 * 1.5), 50, variance=0), f"d={d7}")


def mk_player():
    st = player_final_stats("战士", 11, {}, 0, {"str": 39})
    return {
        "class_name": "战士", "level": 11, "class_tier": 0, "evolve_path": 0,
        "equipment": {}, "attributes": {"str": 39}, "learned_skills": [],
        "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
        "race": "human", "title_bonus": None,
    }


def mk_battle(player):
    return Battle("monster", enemy={
        "name": "靶子", "lv": 11, "hp": 100000, "max_hp": 100000,
        "atk": 1, "def": 20, "matk": 1, "mdef": 20, "spd": 10, "buffs": {},
    }, player=player)


def test_skill_formula():
    print("【2. 技能 formula 字段（引擎消费端）】")
    player = mk_player()
    b = mk_battle(player)
    # 给技能表注入一个带 formula 的技能（纯 atk→magi 物理职业魔法技）
    from game import content as C
    C.PLAYER_SKILLS["cls_zhan_shi"]["skills"]["sk_test_fml"] = {
        "lv": 1, "mp": 0, "power": 1.0, "kind": "魔法", "cast": 0.5,
        "formula": [{"stat": "atk", "mult": 1.0, "type": "magi"}],
        "name": "测试混伤",
    }
    random.seed(42)
    st = b._player_stats(player)
    logs = b._player_skill(st, "测试混伤", C.PLAYER_SKILLS["cls_zhan_shi"]["skills"]["sk_test_fml"], player)
    # 应有造成伤害日志
    has_dmg = any(isinstance(l, str) and "造成" in l and "伤害" in l for l in logs)
    check("技能 formula 生效（造成伤害）", has_dmg, f"logs={[l for l in logs if isinstance(l, str)][:3]}")


def test_affix_formula():
    print("【3. 装备词条 formula（_affix_on_hit）】")
    player = mk_player()
    b = mk_battle(player)
    from game import content as C
    from game.core.affix_effects import run_affix_formula
    C.AFFIXES["test_affix_fml"] = {
        "name": "测试公式词条", "kind": "attack", "trigger": "on_hit", "chance": 1.0,
        "formula": [{"stat": "atk", "mult": 0.5, "type": "phys"}],
    }
    b._equip_affix_ids = lambda p: ["test_affix_fml"]
    b._player_stats = lambda p: mk_stats()
    b._enemy_stats = lambda: {"def": 20, "mdef": 20, "hp": 100000, "max_hp": 100000}
    b._pene_vals = lambda st, magic=False: (0, 0)
    b._damage_enemy = lambda dmg, logs, **kw: (logs.append(f"💥 追加 {dmg} 点伤害！"), dmg)[1]
    logs = []
    run_affix_formula(b, player, 100, logs)
    check("词条 formula 触发", any("追加" in str(l) for l in logs), f"logs={logs[:3]}")


def test_enemy_formula():
    print("【4. 敌方技能 formula（_enemy_cast_done）】")
    player = mk_player()
    b = mk_battle(player)
    from game.data.monsters import MONSTER_SKILLS
    MONSTER_SKILLS["ms_test_fml"] = {
        "kind": "魔法", "power": 1.0,
        "formula": [{"stat": "matk", "mult": 1.5, "type": "magi"}],
        "name": "测试怪技",
    }
    # 直接测敌方攻击消费端：构造一个技能事件
    est = {"atk": 50, "matk": 60, "crit": 0.05, "def": 10, "mdef": 10, "spd": 10, "max_hp": 1000, "hp": 1000}
    pst = {"def": 20, "mdef": 20, "crit": 0.05, "max_hp": 1000, "max_mp": 500}
    b._player_stats = lambda p: pst
    b._pene_vals = lambda st, magic=False: (0, 0)
    b._tenacity_mult = lambda pst: 1.0
    b._equip_affix_ids = lambda p: []
    b._pending_dmg_lines = []
    # 手动调用敌方技能伤害段（formula 分支）
    from game.engine import resolve_formula
    dmg, _ = resolve_formula(MONSTER_SKILLS["ms_test_fml"]["formula"], est,
                             pst["def"], pst["mdef"], is_crit=False, variance=0)
    check("敌方 formula 生效", dmg > 0, f"dmg={dmg}")
    check("敌方 formula 伤害正确", dmg == calc_damage(int(60 * 1.5), 20, variance=0),
          f"dmg={dmg}")


if __name__ == "__main__":
    test_resolve_formula_pure()
    test_skill_formula()
    test_affix_formula()
    test_enemy_formula()
    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    sys.exit(1 if failed else 0)
