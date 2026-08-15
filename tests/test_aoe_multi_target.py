# -*- coding: utf-8 -*-
"""v114 AOE 多目标机制正式回归测试（战斗结算侧）。

覆盖（每项一条用例，断言具体数值）：
1. 单目标回归：aoe 技能（旋风斩）打无援军 Boss，伤害 == 原单体路径（同种子同构造对比）
2. 多目标分配：Boss+2 援军，Boss 与每援军各吃全额 total（Boss 掉血精确断言 + 每目标文案行）
3. AOE 不走挡刀：aoe 技能 Boss 也掉血；对比单体技能同场景 Boss 不掉血只扣援军
4. 援军死亡 pop：打掉第一只 e_minions 长度减 1 + 击倒文案；全部打光后 Boss 继续承伤
5. 超载真 AOE：真实超载分支（火系技能+雷印）→ Boss+援军各吃 matk×1.2，不走挡刀，印记清除
6. 星陨真 AOE：_affix_on_hit 强制触发星陨 → Boss+援军各吃 200%（dmg×2.0）
7. multi×aoe：怒涛连斩 180%×3 全体——multi 循环累加 total 后一次 aoe 结算（Boss 与每援军各吃三段总和）
9. 吸血分账：aoe 技能 + 吸血词条 → heal == Boss 实伤 × 吸血率（援军段不计入）

环境铁律：私有库 test_aoe_multi_target.db（绝不碰 game_data.db / test_game_data.db）；
确定性：同种子控制组对照，概率（星陨）用强制 random 触发；不改任何源码。
"""
import os
import sys
import random

# 必须在 import 插件前设置私有库（db.py 模块级读取 DB_PATH）
os.environ["GWEN_GAME_DB"] = os.path.abspath("test_aoe_multi_target.db")
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.core.affix import stat_affix_stats  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(cls="cls_zhan_shi", affixes=None, extra_stats=None, hp=5000):
    eq_stats = {"atk": 1000, "matk": 1000}
    if extra_stats:
        eq_stats.update(extra_stats)
    eq_stats.update(stat_affix_stats(affixes or [], "weapon", 30))
    return {
        "class_name": cls, "level": 30, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 100,
        "equipment": {"weapon": {"name": "测试剑", "stats": eq_stats,
                                 "affixes": affixes or [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": [], "race": "human",
    }


def mk_enemy(hp=10 ** 9, def_=0, mdef=0, **kw):
    e = {"name": "测试怪", "hp": hp, "max_hp": hp, "atk": 0,
         "def": def_, "mdef": mdef, "spd": 10}
    e.update(kw)
    return e


def mk_minion(hp, name="测试怪爪牙"):
    return {"name": name, "hp": hp, "max_hp": hp, "atk": 100, "matk": 0}


def cast_once(b, st, p, info, name, seed):
    """固定种子施放一次技能，返回 (logs, boss实损)。Boss 血量巨大 → 实损==total。"""
    random.seed(seed)
    h0 = b.enemy["hp"]
    logs = b._player_skill(st, name, info, p)
    return logs, h0 - b.enemy["hp"]


def measure_total(seed, info, name):
    """控制组：无援军同种子施放，测该种子下的 total（Boss 实损）。"""
    pc = mk_player()
    bc = BT.Battle("monster", mk_enemy(), {}, pc)
    _, t = cast_once(bc, bc._player_stats(pc), pc, info, name, seed)
    return t


def main():
    clean_db()
    info_xf = E.skill_info("cls_zhan_shi", "旋风斩")
    check("数据：旋风斩带 aoe=True", bool(info_xf and info_xf.get("aoe")), str(info_xf))
    info_single = dict(info_xf)
    info_single.pop("aoe", None)  # 对照组：等价单体技能

    # ============ 1. 单目标回归 ============
    print("\n===== 1. 单目标回归：aoe 技能打无援军 Boss == 原单体路径 =====\n")
    random.seed(11)
    p1 = mk_player()
    b1 = BT.Battle("monster", mk_enemy(), {}, p1)
    logs1, dealt_aoe = cast_once(b1, b1._player_stats(p1), p1, info_xf, "旋风斩", 11)
    check("aoe 技能单目标 Boss 掉血 > 0", dealt_aoe > 0, f"dealt={dealt_aoe}")
    check("Boss 掉血 == 实损（hp 精确扣减）",
          b1.enemy["hp"] == 10 ** 9 - dealt_aoe, f"hp={b1.enemy['hp']}")
    random.seed(11)
    p2 = mk_player()
    b2 = BT.Battle("monster", mk_enemy(), {}, p2)
    _, dealt_single = cast_once(b2, b2._player_stats(p2), p2, info_single, "旋风斩", 11)
    check("aoe 单目标伤害 == 原单体路径伤害（同种子同构造）",
          dealt_aoe == dealt_single, f"aoe={dealt_aoe} single={dealt_single}")
    check("单体路径无援军文案（无『对【』行）",
          not any("对【" in x and "造成" in x for x in logs1), str(logs1[:3]))

    # ============ 2. 多目标分配 ============
    print("\n===== 2. 多目标分配：Boss + 2 援军各吃全额 =====\n")
    control2 = measure_total(12, info_xf, "旋风斩")
    random.seed(12)
    p3 = mk_player()
    b3 = BT.Battle("monster", mk_enemy(), {}, p3)
    b3.e_minions = [mk_minion(20000), mk_minion(20000)]
    st3 = b3._player_stats(p3)
    h0 = b3.enemy["hp"]
    m0 = [m["hp"] for m in b3.e_minions]
    logs3 = b3._player_skill(st3, "旋风斩", info_xf, p3)
    boss_loss = h0 - b3.enemy["hp"]
    ml = [m0[i] - b3.e_minions[i]["hp"] for i in range(2)]
    check("Boss 掉血 == 单体路径全额 total（同种子控制组）", boss_loss == control2,
          f"boss={boss_loss} expect={control2}")
    check("援军1 掉血 == 全额 total", ml[0] == boss_loss, f"m1={ml[0]} boss={boss_loss}")
    check("援军2 掉血 == 全额 total", ml[1] == boss_loss, f"m2={ml[1]} boss={boss_loss}")
    per_lines = [x for x in logs3 if "对【" in x and "造成" in x]
    check("文案含 2 行每目标行（数值==total）",
          len(per_lines) == 2 and all(f"造成 {boss_loss} 点伤害" in x for x in per_lines),
          str(per_lines))
    check("aoe 文案无挡刀行", not any("挡下" in x for x in logs3), str(logs3))

    # ============ 3. AOE 不走挡刀 ============
    print("\n===== 3. AOE 不走挡刀（对比单体挡刀）=====\n")
    control3 = measure_total(13, info_xf, "旋风斩")
    random.seed(13)
    p4 = mk_player()
    b4 = BT.Battle("monster", mk_enemy(), {}, p4)
    b4.e_minions = [mk_minion(20000)]
    _, aoe_boss_loss = cast_once(b4, b4._player_stats(p4), p4, info_xf, "旋风斩", 13)
    aoe_minion_loss = 20000 - b4.e_minions[0]["hp"]
    check("aoe：有援军时 Boss 也吃全额（核心价值）", aoe_boss_loss == control3,
          f"boss={aoe_boss_loss}")
    check("aoe：援军同时吃全额", aoe_minion_loss == control3, f"minion={aoe_minion_loss}")
    random.seed(13)
    p5 = mk_player()
    b5 = BT.Battle("monster", mk_enemy(), {}, p5)
    b5.e_minions = [mk_minion(20000)]
    logs5, single_boss_loss = cast_once(b5, b5._player_stats(p5), p5, info_single, "旋风斩", 13)
    single_minion_loss = 20000 - b5.e_minions[0]["hp"]
    check("单体：同场景 Boss 不掉血（挡刀）", single_boss_loss == 0,
          f"boss={single_boss_loss}")
    check("单体：援军扣全额", single_minion_loss == control3, f"minion={single_minion_loss}")
    check("单体：出现『挡下』文案", any("挡下" in x for x in logs5), str(logs5[:3]))

    # ============ 4. 援军死亡 pop ============
    print("\n===== 4. 援军死亡 pop：打掉第一只→长度-1；全灭后 Boss 继续承伤 =====\n")
    # 先用控制组精确测量各回合 total（同种子同构造），再据此设定援军血量保证确定性
    totals = []
    for sd in (21, 22, 23, 24):
        random.seed(sd)
        pc = mk_player()
        bc = BT.Battle("monster", mk_enemy(), {}, pc)
        _, t = cast_once(bc, bc._player_stats(pc), pc, info_xf, "旋风斩", sd)
        totals.append(t)
    # A 爪牙 hp=100（必被第一击打死）；B 爪牙 hp=t1+t2+10（前两击存活、第三击必死）
    A_HP, B_HP = 100, totals[0] + totals[1] + 10
    p6 = mk_player()
    b6 = BT.Battle("monster", mk_enemy(), {}, p6)
    b6.e_minions = [mk_minion(A_HP, "A爪牙"), mk_minion(B_HP, "B爪牙")]
    st6 = b6._player_stats(p6)
    logs6 = []
    for i, sd in enumerate((21, 22, 23, 24)):
        lg, bl = cast_once(b6, st6, p6, info_xf, "旋风斩", sd)
        logs6.append(lg)
        if i == 0:
            check("第1击打掉第一只：e_minions 长度 1", len(b6.e_minions) == 1,
                  f"len={len(b6.e_minions)}")
            check("第1击 Boss 照常吃全额", bl == totals[0], f"boss={bl}")
            check("第1击 B 爪牙扣全额", B_HP - b6.e_minions[0]["hp"] == totals[0],
                  f"B={b6.e_minions[0]['hp']}")
            check("第1击出现 A 爪牙击倒文案", any("援军【A爪牙】被击倒了" in x for x in lg), str(lg))
        elif i == 1:
            check("第2击 B 爪牙存活：长度仍 1", len(b6.e_minions) == 1, f"len={len(b6.e_minions)}")
            check("第2击无击倒文案", not any("被击倒了" in x for x in lg), str(lg))
        elif i == 2:
            check("第3击打光第二只：长度 0", len(b6.e_minions) == 0, f"len={len(b6.e_minions)}")
            check("第3击出现 B 爪牙击倒文案", any("援军【B爪牙】被击倒了" in x for x in lg), str(lg))
        else:
            check("第4击援军全灭后 Boss 继续承伤", bl == totals[3], f"boss={bl}")
            check("全灭后 e_minions 恒空", len(b6.e_minions) == 0)
    check("全程无挡刀文案", not any("挡下" in x for lg in logs6 for x in lg))

    # ============ 5. 超载真 AOE ============
    print("\n===== 5. 超载真 AOE（火系技能 + 雷印 → matk×1.2 全体，不走挡刀）=====\n")
    info_fire = {"name": "火球测试", "kind": "魔法", "power": 1.0, "element": "fire", "cd": 1}
    # 控制组：无印记无援军 → 测主伤害 total
    random.seed(7)
    p7c = mk_player()
    b7c = BT.Battle("monster", mk_enemy(), {}, p7c)
    _, main_total = cast_once(b7c, b7c._player_stats(p7c), p7c, info_fire, "火球测试", 7)
    # 主组：雷印 + 火 → 超载（真实 _player_skill 分支），1 只高血援军
    random.seed(7)
    p7 = mk_player()
    b7 = BT.Battle("monster", mk_enemy(), {}, p7)
    st7 = b7._player_stats(p7)
    aoe_dmg = int(st7["matk"] * 1.2)
    b7.e_buffs["thunder_mark"] = 1
    b7.e_minions = [mk_minion(10 ** 9)]
    h0 = b7.enemy["hp"]
    m0 = b7.e_minions[0]["hp"]
    logs7 = b7._player_skill(st7, "火球测试", info_fire, p7)
    boss_loss = h0 - b7.enemy["hp"]
    minion_loss = m0 - b7.e_minions[0]["hp"]
    check("超载 aoe_dmg == int(matk×1.2)", boss_loss == aoe_dmg,
          f"boss={boss_loss} expect={aoe_dmg}")
    check("超载不走挡刀：有援军 Boss 仍吃全额 aoe_dmg", boss_loss == aoe_dmg,
          f"boss={boss_loss}")
    check("援军同时吃 aoe_dmg（主伤害被挡 + aoe 全额）",
          minion_loss == main_total + aoe_dmg, f"minion={minion_loss} main={main_total} aoe={aoe_dmg}")
    check("超载文案『💥超载爆发！额外 {aoe_dmg} 点全体伤害！』",
          any(f"💥超载爆发！额外 {aoe_dmg} 点全体伤害！" in x for x in logs7), str(logs7))
    check("援军行文案数值 == aoe_dmg",
          any(f"对【测试怪爪牙】造成 {aoe_dmg} 点伤害" in x for x in logs7), str(logs7))
    check("超载后雷印被清除", "thunder_mark" not in b7.e_buffs, str(b7.e_buffs))
    # 火球主伤害段（非 aoe 技能）正常走挡刀（挡下 main_total）；
    # 但超载 aoe 段不走挡刀——挡刀值只含主伤害，不含 aoe_dmg（Boss 已吃全额 aoe_dmg 佐证）
    check("超载 aoe 段不走挡刀：挡下值 == 仅主伤害段",
          any(f"🛡️ 援军【测试怪爪牙】挡下了 {main_total} 点伤害" in x for x in logs7), str(logs7))

    # ============ 6. 星陨真 AOE ============
    print("\n===== 6. 星陨真 AOE（_affix_on_hit 强制触发：Boss+援军各吃 200%）=====\n")
    p8 = mk_player(affixes=["starfall"])
    b8 = BT.Battle("monster", mk_enemy(), {}, p8)
    b8.e_minions = [mk_minion(10 ** 9), mk_minion(10 ** 9)]
    h0 = b8.enemy["hp"]
    m0 = [m["hp"] for m in b8.e_minions]
    _orig_random = random.random
    try:
        random.random = lambda: 0.0  # 0.0 < 0.10 → 强制触发
        logs8 = []
        b8._affix_on_hit(p8, 100, logs8)
    finally:
        random.random = _orig_random
    boss_loss = h0 - b8.enemy["hp"]
    ml = [m0[i] - b8.e_minions[i]["hp"] for i in range(2)]
    check("星陨：Boss 吃 200%（dmg×2.0）", boss_loss == 200, f"boss={boss_loss}")
    check("星陨：援军1 各吃 200%", ml[0] == 200, f"m1={ml[0]}")
    check("星陨：援军2 各吃 200%", ml[1] == 200, f"m2={ml[1]}")
    check("星陨文案『☄️ 星陨！全体造成 200 点伤害！』",
          any("☄️ 星陨！全体造成 200 点伤害！" in x for x in logs8), str(logs8))
    check("星陨每援军一行文案", sum(1 for x in logs8 if "对【" in x and "造成" in x) == 2, str(logs8))
    check("星陨无挡刀行", not any("挡下" in x for x in logs8), str(logs8))
    # 不触发对照：random → 1.0 不触发
    p8b = mk_player(affixes=["starfall"])
    b8b = BT.Battle("monster", mk_enemy(), {}, p8b)
    b8b.e_minions = [mk_minion(10 ** 9)]
    h0b = b8b.enemy["hp"]
    try:
        random.random = lambda: 0.99
        b8b._affix_on_hit(p8b, 100, [])
    finally:
        random.random = _orig_random
    check("星陨 10% 概率：未触发时无伤害", b8b.enemy["hp"] == h0b,
          f"hp={b8b.enemy['hp']}")

    # ============ 7. multi×aoe ============
    print("\n===== 7. multi×aoe：怒涛连斩 180%×3 全体（累加 total 后一次 aoe 结算）=====\n")
    info_multi = E.skill_info("cls_zhan_shi", "怒涛连斩")
    check("数据：怒涛连斩 multi=3 且 aoe=True",
          bool(info_multi and info_multi.get("multi") == 3 and info_multi.get("aoe")),
          str(info_multi and {k: info_multi.get(k) for k in ("multi", "aoe", "power")}))
    random.seed(15)
    p9 = mk_player()
    b9 = BT.Battle("monster", mk_enemy(), {}, p9)
    b9.e_minions = [mk_minion(10 ** 9), mk_minion(10 ** 9)]
    st9 = b9._player_stats(p9)
    h0 = b9.enemy["hp"]
    m0 = [m["hp"] for m in b9.e_minions]
    logs9 = b9._player_skill(st9, "怒涛连斩", info_multi, p9)
    boss_loss = h0 - b9.enemy["hp"]
    ml = [m0[i] - b9.e_minions[i]["hp"] for i in range(2)]
    check("multi×aoe：Boss 吃 3 段累加 total", boss_loss > 0, f"boss={boss_loss}")
    check("multi×aoe：援军1 吃与 Boss 相同的 3 段总和", ml[0] == boss_loss,
          f"m1={ml[0]} boss={boss_loss}")
    check("multi×aoe：援军2 吃与 Boss 相同的 3 段总和", ml[1] == boss_loss,
          f"m2={ml[1]} boss={boss_loss}")
    check("连击文案『连击 3 次，共造成 {total} 点伤害！』",
          any(f"连击 3 次，共造成 {boss_loss} 点伤害" in x for x in logs9), str(logs9))

    # ============ 9. 吸血分账 ============
    print("\n===== 9. 吸血分账：heal == Boss 实伤 × 吸血率（援军段不计入）=====\n")
    p10 = mk_player(extra_stats={"lifesteal": 0.20})
    b10 = BT.Battle("monster", mk_enemy(), {}, p10)
    st10 = b10._player_stats(p10)
    check("吸血属性生效（0.20）", abs(float(st10.get("lifesteal", 0)) - 0.20) < 1e-9,
          f"lifesteal={st10.get('lifesteal')}")
    # 打伤自己（低于 max_hp），保证吸血可精确观测
    p10["hp"] = st10["max_hp"] - 100000
    p10["max_hp"] = st10["max_hp"]
    b10.e_minions = [mk_minion(10 ** 9), mk_minion(10 ** 9)]
    h0 = b10.enemy["hp"]
    m0 = [m["hp"] for m in b10.e_minions]
    hp0 = p10["hp"]
    random.seed(11)
    logs10 = b10._player_skill(st10, "旋风斩", info_xf, p10)
    boss_loss = h0 - b10.enemy["hp"]
    minion_total_loss = sum(m0[i] - b10.e_minions[i]["hp"] for i in range(2))
    heal = p10["hp"] - hp0
    expect = int(boss_loss * 0.20)
    check("吸血 heal == int(Boss实伤×0.2)", heal == expect,
          f"heal={heal} expect={expect}")
    check("援军段不计入吸血（heal < 全段×0.2）",
          heal < int((boss_loss + minion_total_loss) * 0.20),
          f"heal={heal} full={int((boss_loss + minion_total_loss) * 0.20)}")
    check("吸血文案『🩸 吸血：回复 {heal} 点生命！』",
          any(f"🩸 吸血：回复 {heal} 点生命！" in x for x in logs10), str(logs10))
    check("玩家血量精确增加 heal", p10["hp"] == hp0 + heal,
          f"hp={p10['hp']} expect={hp0 + heal}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
