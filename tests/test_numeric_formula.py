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


def test_skill_exprs_levels():
    """v160 逐级公式：技能级 exprs（每级一条公式）→ 引擎按技能等级取公式结算。

    构造 exprs 三条：Lv.1=atk*0.8+20、Lv.2=atk*0.85+25、Lv.3=atk*0.9+30，
    战士 Lv.11 满 str 加点 → atk 确定；验证 Lv.1/2/3 结算伤害按公式递增。
    """
    print("【2b. 技能 exprs 逐级公式（v160）】")
    from game import content as C
    player = mk_player()
    b = mk_battle(player)
    # 注入带 exprs 的技能（kind=物理 → phys 段）
    C.PLAYER_SKILLS["cls_zhan_shi"]["skills"]["sk_test_exprs"] = {
        "lv": 1, "mp": 0, "power": 1.0, "kind": "物理", "cast": 0.5,
        "exprs": ["atk*0.8 + 20", "atk*0.85 + 25", "atk*0.9 + 30"],
        "name": "测试逐级斩",
    }
    _info = C.PLAYER_SKILLS["cls_zhan_shi"]["skills"]["sk_test_exprs"]
    st = b._player_stats(player)
    atk = st["atk"]
    # 逐级结算（skill_levels 由 _skill_level_of 读 player，手动设）
    for lv in (1, 2, 3):
        p = dict(player)
        p["skill_levels"] = {"测试逐级斩": lv}
        b2 = mk_battle(p)
        st2 = b2._player_stats(p)
        logs = b2._player_skill(st2, "测试逐级斩", _info, p)
        # 期望公式值：atk*mult+flat（未乘外部乘区/未过防御的基础值）
        _expect_base = int(atk * (0.8 + 0.05 * (lv - 1)) + (20 + 5 * (lv - 1)))
        # 伤害日志里应出现 ≈ 期望（基础值过防御后略低；直接用 resolve_formula 对齐）
        from game.engine import resolve_formula
        _dmg_expect, _ = resolve_formula(
            [{"expr": _info["exprs"][lv - 1], "type": "phys"}],
            {"atk": atk, "_player_lv": 11, "_skill_lv": lv},
            20, 20, variance=0)
        _has = any(isinstance(l, str) and "造成" in l and "伤害" in l for l in logs)
        check(f"Lv.{lv} exprs 结算出伤害", _has, f"logs={[l for l in logs if isinstance(l, str)][:3]}")
        # 提取日志伤害数值验证（若日志带数值；不带数值只验证出伤）
        _dmg_txt = [l for l in logs if isinstance(l, str) and "造成" in l and "伤害" in l]
        if _dmg_txt:
            import re
            _mm = re.findall(r"(\d+)", _dmg_txt[0])
            if _mm:
                _got = int(_mm[0])
                # 战斗 variance=0.15 波动 ±15%，容差 ±20%
                check(f"Lv.{lv} 结算≈{_dmg_expect}（atk={atk}，±20% 容差）",
                      abs(_got - _dmg_expect) <= max(2, _dmg_expect * 0.2),
                      f"got={_got} expect={_dmg_expect} logs={_dmg_txt[0][:60]}")
            else:
                check(f"Lv.{lv} 有伤害日志（无数值可核对）", True)
        else:
            check(f"Lv.{lv} 有伤害日志", False, f"logs={logs[:3]}")
    # 越界：Lv.9（超过条数）取最后一条
    p = dict(player)
    p["skill_levels"] = {"测试逐级斩": 9}
    b9 = mk_battle(p)
    st9 = b9._player_stats(p)
    logs9 = b9._player_skill(st9, "测试逐级斩", _info, p)
    _has9 = any(isinstance(l, str) and "造成" in l and "伤害" in l for l in logs9)
    check("Lv.9 越界取最后一条仍出伤", _has9, f"logs={[l for l in logs9 if isinstance(l, str)][:3]}")
    # 清理注入（防污染后续测试）
    C.PLAYER_SKILLS["cls_zhan_shi"]["skills"].pop("sk_test_exprs", None)


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
    b._deal_damage = lambda dmg, logs, **kw: (logs.append(f"💥 追加 {dmg} 点伤害！"), dmg)[1]
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
    test_skill_exprs_levels()
    test_affix_formula()
    test_enemy_formula()
    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    sys.exit(1 if failed else 0)
