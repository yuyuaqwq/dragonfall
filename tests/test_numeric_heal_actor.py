#!/usr/bin/env python3
"""v180E 阶段1 _heal_actor 统一治疗核心门禁。

语义锚（鱼鱼 2026-09-07 拍板）：
- 治疗落地统一 _heal_actor：clamp + 受疗（target 自身 race heal_received）+ 禁疗/重伤
  （target 自身 buffs heal_down/_anti_heal_pct）
- 怪奶自己（monster heal_self 走管线）→ 不吃玩家治疗被动（heal_power/圣光套/神恩/信念档位）——
  actor 一视同仁：怪奶只按怪自身公式结算
- 禁疗/重伤收口后：宠物吸血/食物回血/词条回血同样吃 target 的 heal_down/_anti_heal_pct
  （原来只有玩家技能治疗吃——语义修正）
- 玩家技能治疗溢出转盾（cloth_heal_overflow）行为不变（旧锚）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import clean_db

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def main():
    clean_db()
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.data.monsters import MONSTER_SKILLS

    print("===== v180E _heal_actor 统一治疗核心 =====\n")

    def mk_player(cls="牧师", lv=30, learned=None, hp=300):
        # Battle.__init__ 会按 _player_stats 重算 max_hp（测试装备下≈441）；
        # hp 传低于该值的数，让 _heal_actor 有 clamp 空间
        mx = 10000  # 最终会被 init 覆盖为真实面板值；此处仅防未 init 直用
        return {
            "class_name": cls, "level": lv, "hp": hp, "max_hp": mx,
            "mp": 200, "max_mp": 200,
            "equipment": {"weapon": {"name": "测试杖", "stats": {"matk": 500, "atk": 300}, "affixes": [], "enhance": 0}},
            "attributes": {"int": 20, "str": 10},
            "learned_skills": learned or [], "race": "human",
            "class_tier": 0, "evolve_path": 0,
        }

    def mk_enemy(hp=50000):
        return {"name": "测试怪", "hp": hp, "max_hp": hp,
                "atk": 100, "def": 50, "mdef": 50, "spd": 10, "lv": 30, "buffs": {}}

    def mk_monster_healer(mid="m_heal_test", lv=22):
        # build_monster 造一只带再生技能的怪（heal_self 15% max_hp 已归一 kind=治疗）
        m = BT.C.build_monster((mid, "数值测试怪", "healer", lv, [], ["ms_zai_sheng"]),
                               {"id": mid, "name": "数值测试图", "area": "field"})
        return m

    # ---------- 1. _heal_actor 基础：clamp + 实际回血 ----------
    p = mk_player()
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    mx = p["max_hp"]  # init 后真实 max_hp（测试装备下约 441）
    p["hp"] = mx - 1000
    actual = b._heal_actor(p, 1000, [])
    check("_heal_actor 基础回血", actual == 1000 and p["hp"] == mx, f"hp={p['hp']} max={mx} actual={actual}")
    p["hp"] = mx - 500
    actual2 = b._heal_actor(p, 99999, [])
    check("_heal_actor clamp 到 max_hp", actual2 == 500 and p["hp"] == mx,
          f"hp={p['hp']} max={mx} actual2={actual2}")

    # ---------- 2. 禁疗 heal_down 收口：target 自身 buffs ----------
    p2 = mk_player()
    b2 = BT.Battle("怪物", mk_enemy(), {}, p2)
    mx2 = p2["max_hp"]
    p2["hp"] = mx2 - 5000
    p2.setdefault("buffs", {})["heal_down"] = 3  # 30% 禁疗
    logs = []
    actual3 = b2._heal_actor(p2, 1000, logs)
    check("heal_down 禁疗生效(3层=30%)", actual3 == 700, f"actual={actual3} logs={logs}")

    # 重伤 _anti_heal_pct
    p3 = mk_player()
    b3 = BT.Battle("怪物", mk_enemy(), {}, p3)
    p3["hp"] = p3["max_hp"] - 5000
    p3.setdefault("buffs", {})["_anti_heal_pct"] = 0.50
    logs3 = []
    actual4 = b3._heal_actor(p3, 1000, logs3)
    check("_anti_heal_pct 重伤生效(50%)", actual4 == 500, f"actual={actual4} logs={logs3}")

    # ---------- 3. 怪奶自己：不吃玩家被动（核心语义锚） ----------
    # 造一个带 heal_power 玩家被动的高配牧师，怪奶量不该被污染
    # 直接验证：怪 heal_self 走管线后奶量 ≈ max_hp×15%（无玩家被动加成）
    m = mk_monster_healer()
    p4 = mk_player(cls="牧师", lv=50, learned=["神恩"])
    b4 = BT.Battle("怪物", m, {}, p4)
    # 打掉怪一半血
    m["hp"] = m["max_hp"] // 2
    mhp0 = m["hp"]
    maxhp = m["max_hp"]
    b4._cast_ctx = m
    b4._target_ctx = p4
    try:
        logs4, _ = b4._monster_cast_playerskill(m, "ms_zai_sheng", p4, {"kind": "skill", "skill": "ms_zai_sheng"})
    finally:
        b4._cast_ctx = None
        b4._target_ctx = None
    gain = int(m["hp"]) - mhp0
    expect = int(maxhp * 0.15)
    # 玩家神恩被动（治疗×1.1）若误吃 → gain 会是 1.1 倍。误差 ±2 内判定
    check("怪奶不吃玩家治疗被动(神恩×1.1)", abs(gain - expect) <= 2,
          f"gain={gain} expect={expect} (若误吃应≈{int(expect*1.1)}) hp0={mhp0}→{m['hp']}")

    # 玩家自己有 heal_power 高属性 → 怪奶也不该吃
    p5 = mk_player(cls="牧师", lv=50)
    p5["attributes"] = {"int": 20, "heal_power": 0.5}  # 高治疗强度
    m2 = mk_monster_healer()
    b5 = BT.Battle("怪物", m2, {}, p5)
    m2["hp"] = m2["max_hp"] // 2
    mhp0 = m2["hp"]
    maxhp2 = m2["max_hp"]
    b5._cast_ctx = m2
    b5._target_ctx = p5
    try:
        logs5, _ = b5._monster_cast_playerskill(m2, "ms_zai_sheng", p5, {"kind": "skill", "skill": "ms_zai_sheng"})
    finally:
        b5._cast_ctx = None
        b5._target_ctx = None
    gain2 = int(m2["hp"]) - mhp0
    expect2 = int(maxhp2 * 0.15)
    check("怪奶不吃玩家 heal_power(0.5)", abs(gain2 - expect2) <= 2,
          f"gain={gain2} expect={expect2} (若误吃应≈{int(expect2*1.5)})")

    # ---------- 4. 怪奶吃自身禁疗（玩家给怪挂 heal_down 后怪再生被减） ----------
    m3 = mk_monster_healer()
    p6 = mk_player()
    b6 = BT.Battle("怪物", m3, {}, p6)
    m3["hp"] = m3["max_hp"] // 2
    m3.setdefault("buffs", {})["heal_down"] = 3  # 玩家挂的禁疗 30%
    mhp0 = m3["hp"]
    maxhp3 = m3["max_hp"]
    b6._cast_ctx = m3
    b6._target_ctx = p6
    try:
        logs6, _ = b6._monster_cast_playerskill(m3, "ms_zai_sheng", p6, {"kind": "skill", "skill": "ms_zai_sheng"})
    finally:
        b6._cast_ctx = None
        b6._target_ctx = None
    gain3 = int(m3["hp"]) - mhp0
    expect3 = int(maxhp3 * 0.15 * 0.70)  # 30% 禁疗
    check("怪奶吃自身禁疗(heal_down 3层=30%)", abs(gain3 - expect3) <= 2,
          f"gain={gain3} expect={expect3} (无禁疗应≈{int(maxhp3*0.15)})")

    # ---------- 5. 玩家技能治疗照常工作（旧锚不回归） ----------
    # 治愈术 heal_formula 走管线，玩家能正常奶、满血不溢出
    p7 = mk_player(cls="牧师", lv=30)
    b8 = BT.Battle("怪物", mk_enemy(hp=999999), {}, p7)
    base_hp = p7["max_hp"] // 2
    p7["hp"] = base_hp
    b8._player_skill(b8._player_stats(p7), "治愈术", BT.E.skill_info("牧师", "治愈术"), p7)
    gain_p0 = int(p7["hp"]) - base_hp
    check("玩家技能治疗正常奶(治愈术>0)", gain_p0 > 0, f"gain={gain_p0}")
    # 满血时不溢出、clamp 到 max_hp
    p7b = mk_player(cls="牧师", lv=30)
    b7b = BT.Battle("怪物", mk_enemy(hp=999999), {}, p7b)
    p7b["hp"] = p7b["max_hp"]
    hp_before = p7b["hp"]
    b7b._player_skill(b7b._player_stats(p7b), "治愈术", BT.E.skill_info("牧师", "治愈术"), p7b)
    check("玩家技能治疗满血 clamp 不溢出", p7b["hp"] == p7b["max_hp"] and hp_before == p7b["max_hp"],
          f"hp={p7b['hp']} max={p7b['max_hp']}")

    # 玩家奶队友（队友龙裔受疗 -10%）照旧
    p8 = mk_player(cls="牧师", lv=30)
    ally = mk_player(cls="战士", lv=30)
    ally["race"] = "dragonborn"  # 龙裔 heal_received -0.10
    ally["hp"] = ally["max_hp"] - 5000
    b9 = BT.Battle("怪物", mk_enemy(), {}, p8, allies=[ally])
    ally2 = dict(ally)  # 快照
    ally2["hp"] = ally["max_hp"] - 5000
    logs9 = []
    h9 = b9._heal_actor(ally2, 1000, logs9)
    check("玩家奶龙裔队友受疗-10%", h9 == 900, f"h={h9} logs={logs9}")

    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
