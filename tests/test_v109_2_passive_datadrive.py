#!/usr/bin/env python3
"""v109.2 P2-9 数据驱动化验证（v153 适配重写）

v153 职业重做后：
- 元素共鸣（element_dmg proc）/ 奥术直觉（arcane_regen）/ 亡灵祭仪（turn_heal 旧格式）
  等旧被动已随旧表/隐藏线删除或改为新格式。
- **v153 被动新格式 = 字符串名**（passive: 'zhan_yi_lifesteal' 等 52 处），而引擎
  battle._passive_map / engine.player_passive_stats 仍按旧 dict 格式（passive.get('proc')）
  消费 → 字符串 passive 会抛 AttributeError = **v153 数据-引擎契约断裂（真 bug 已报告）**。
  任何携带 被动 技能的玩家进战斗即崩。

本文件改为覆盖 v153 仍存活的数据驱动路径：
1. pierce 技能无视防御（数据驱动字段）
2. 普通物理/魔法伤害基准（无被动，不触发崩溃路径）
3. 字符串被动契约断裂的**确定性复现断言**（AttributeError 证明 bug 存在，
   待引擎修复后此断言应改为正常行为断言）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, run
from data.plugins.dragonfall.game import engine as EG
from data.plugins.dragonfall.game import battle as BT
from data.plugins.dragonfall.game.core.affix import stat_affix_stats

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond: passed += 1; print(f"  ✅ {name}")
    else: failed += 1; print(f"  ❌ {name} {detail}")

async def main():
    clean_db()
    def mk_player(cls="战士", skills=None, extra_stats=None, hp=500):
        eq_stats = {"atk": 100, "matk": 100}
        if extra_stats: eq_stats.update(extra_stats)
        return {"class_name": cls, "level": 90, "hp": hp, "max_hp": hp,
                "mp": 200, "max_mp": 200,
                "equipment": {"weapon": {"name": "t", "stats": eq_stats, "affixes": [], "enhance": 0}},
                "attributes": {"str": 10, "int": 10},
                "learned_skills": skills or [], "race": "human"}
    def mk_enemy(def_=20, mdef=20, hp=10**9):
        return {"name": "怪", "hp": hp, "max_hp": hp, "atk": 0, "def": def_, "mdef": mdef, "spd": 10}

    print("===== P2-9 数据驱动化（v153 适配）=====\n")

    # 1. pierce 技能无视防御（v153 数据驱动字段保留）
    print("— 1. pierce 技能无视防御（数据驱动 pierce 字段）—")
    pierce_skill = {"name": "破甲测试", "kind": "物理", "power": 1.0, "lv": 40, "cd": 1, "pierce": True}
    random.seed(5)
    p1 = mk_player(cls="战士")
    b1 = BT.Battle("怪物", mk_enemy(def_=9999), {}, p1)
    st1 = b1._player_stats(p1)
    # v156 基础值：flat = 12 + 90(玩家) + 40×4(技能) = 262
    base1 = int(st1["atk"] * 1.0) + EG.skill_flat_value(90, 40, pierce_skill)
    h0 = b1.enemy["hp"]
    b1._player_skill(st1, "破甲测试", pierce_skill, p1)
    dealt1 = h0 - b1.enemy["hp"]
    check(f"pierce 技能伤害 ≈ atk×1.0（{base1}±15%，无视 def=9999）",
          0.85*base1 <= dealt1 <= 1.15*base1, f"dealt {dealt1}")

    # 2. 普通物理/魔法伤害基准（无被动）
    print("\n— 2. 普通物理/魔法伤害基准（无被动路径）—")
    phys_skill = {"name": "斩击测试", "kind": "物理", "power": 1.0, "lv": 40, "cd": 1}
    random.seed(7)
    p2 = mk_player(cls="战士")
    b2 = BT.Battle("怪物", mk_enemy(def_=0), {}, p2)
    st2 = b2._player_stats(p2)
    base2 = int(st2["atk"] * 1.0) + EG.skill_flat_value(90, 40, phys_skill)
    h0 = b2.enemy["hp"]
    b2._player_skill(st2, "斩击测试", phys_skill, p2)
    dealt2 = h0 - b2.enemy["hp"]
    check(f"物理伤害 ≈ atk×1.0（{base2}±15%）", 0.85*base2 <= dealt2 <= 1.15*base2, f"dealt {dealt2}")
    magi_skill = {"name": "魔法测试", "kind": "魔法", "power": 1.0, "lv": 40, "cd": 1}
    random.seed(9)
    p2m = mk_player(cls="法师")
    b2m = BT.Battle("怪物", mk_enemy(mdef=0), {}, p2m)
    st2m = b2m._player_stats(p2m)
    base2m = int(st2m["matk"] * 1.0) + EG.skill_flat_value(90, 40, magi_skill)
    h0 = b2m.enemy["hp"]
    b2m._player_skill(st2m, "魔法测试", magi_skill, p2m)
    dealt2m = h0 - b2m.enemy["hp"]
    check(f"魔法伤害 ≈ matk×1.0（{base2m}±15%）", 0.85*base2m <= dealt2m <= 1.15*base2m, f"dealt {dealt2m}")

    # 3. v153 被动 dict 格式验证（主 agent 已修复：passive 从字符串 → dict，引擎不崩）
    print("\n— 3. v153 被动 dict 格式（已修复，引擎不崩）—")
    p_quxue = (EG.skill_info("cls_zhan_shi", "淬血") or {}).get("passive")
    check("v153 淬血 passive 为 dict（非字符串）",
          isinstance(p_quxue, dict) and p_quxue.get("proc") == "zhan_yi_lifesteal",
          str(p_quxue))
    p3 = mk_player(cls="战士", skills=["淬血"])
    b3 = BT.Battle("怪物", mk_enemy(), {}, p3)
    crashed = False
    try:
        b3._turn_start(p3)
        b3._passive_map(p3)
    except AttributeError:
        crashed = True
    check("引擎 _passive_map 遇 dict 被动不崩溃（契约已修复）", not crashed, "")
    # 全部 passive 均为 dict 格式（无字符串残留）
    # v161：skills_v153.py 已合并入 skills.py 主表
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "game", "data", "skills.py"), encoding="utf-8").read()
    import re as _re
    dict_passives = _re.findall(r"'passive':\s*\{", src)
    str_passives = _re.findall(r"'passive':\s*'[^']+'", src)
    check(f"v153 全部 {len(dict_passives)} 处 passive 均为 dict（0 字符串）", len(str_passives) == 0,
          f"dict={len(dict_passives)} str={len(str_passives)}")

    # 4. 数据驱动 mech 字段（v153 战意 zhan_yi 叠层仍走 MECH_EFFECTS）
    print("\n— 4. 数据驱动 mech（v153 战意 zhan_yi）—")
    check("怒斩 mech=zhan_yi（数据驱动）",
          (EG.skill_info("cls_zhan_shi", "怒斩") or {}).get("mech") == "zhan_yi",
          str((EG.skill_info("cls_zhan_shi", "怒斩") or {}).get("mech")))
    p4 = mk_player(cls="战士", skills=["怒斩"], hp=10000)
    b4 = BT.Battle("怪物", mk_enemy(hp=10**9), {}, p4)
    random.seed(11)
    logs4, _ = b4.player_turn("skill", "怒斩", p4)
    # v154 读条命中制：出招读条结束（cast_done）才结算命中（战意叠层）——推进后生效
    b4._process_until(float(getattr(b4, "p_ct", 0) or 0) + 0.001, logs4, p4)
    check("怒斩施放 → 战意叠层（mech_zhan_yi 引擎挂点）",
          int(b4.mech_stacks.get("zhan_yi", 0) or 0) >= 1,
          f"zhan_yi={b4.mech_stacks.get('zhan_yi')} logs={logs4[:2]}")
    check("战意日志", any("战意" in l for l in logs4), str(logs4))

    print(f"\n===== 结果: {passed} passed, {failed} failed =====")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
