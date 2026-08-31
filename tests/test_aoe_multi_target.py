# -*- coding: utf-8 -*-
"""v114 AOE 多目标机制回归测试（v2 站位语义重写版）。

历史：本文件原本重度依赖 v1 的 `e_minions` 挡刀队列语义（援军挡刀吸收、e_minions
长度 pop 等）。v2 战斗引擎已改为多对多站位（阵营 `enemies` 阵列、单位级
rank/reach/buffs/stacks、`compact` 阵型压缩、AOE 按 `select_aoe_targets` 逐目标结算），
`e_minions` 的"挡刀吸收"逻辑已删除（站位天然承担）。

本版按 v2 语义重写，保持原测试意图不变：
1. 单目标回归：aoe 技能（旋风斩）打单怪，伤害 == 原单体等价技能路径（同种子同构造对比）
2. 多目标分配：AOE scope=all 打全阵——每目标（rank1/rank2）均吃（rank>1 受 aoe_falloff）
3. AOE 打阵列 vs 单体指定目标：AOE 覆盖多目标，单体技能只打命中目标（站位不挡 AOE）
4. 前排死亡 → compact 后原后排前移（主目标/后续计算一致）
5. 超载真 AOE：真实超载分支（火系技能 + 雷印）→ 全阵各吃 matk×1.2，印记清除
6. 星陨真 AOE：_affix_on_hit 强制触发星陨 → 全阵各吃 200%
7. multi×aoe：怒涛连斩 180%×3 全体——multi 循环累加 total 后一次 aoe 结算
8. 吸血分账：aoe 技能 + 吸血词条 → heal == 主目标实伤 × 吸血率（其余目标段不计入）

环境铁律：私有库 test_aoe_multi_target.db（绝不碰 game_data.db / test_game_data.db）；
确定性：同种子控制组对照；不改任何源码。
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
from data.plugins.dragonfall.game.core import formation as FM  # noqa: E402
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


def mk_player(cls="cls_zhan_shi", affixes=None, extra_stats=None, hp=5000,
              reach=3, learned=None):
    eq_stats = {"atk": 1000, "matk": 1000}
    if extra_stats:
        eq_stats.update(extra_stats)
    eq_stats.update(stat_affix_stats(affixes or [], "weapon", 30))
    return {
        "class_name": cls, "level": 30, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 100, "reach": reach,
        "equipment": {"weapon": {"name": "测试剑", "stats": eq_stats,
                                 "affixes": affixes or [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": learned or [], "race": "human",
    }


def mk_enemy(name="主怪", hp=10 ** 9, def_=0, mdef=0, rank=1, reach=3, spd=10, **kw):
    e = {"uid": name, "name": name, "side": "enemy", "rank": rank, "reach": reach,
         "hp": hp, "max_hp": hp, "atk": 0, "def": def_, "mdef": mdef,
         "matk": 0, "spd": spd, "crit": 0.0,
         "buffs": {}, "stacks": {}, "defending": False, "charging": None}
    e.update(kw)
    return e


def mk_group(n, prefix="敌人", rank_of=None, hp=10 ** 9, **kw):
    """构造 n 只敌方阵列单位；rank_of(i) 自定站位（缺省全 rank1）。"""
    out = []
    for i in range(n):
        r = rank_of(i) if rank_of else 1
        out.append(mk_enemy(name=f"{prefix}{i}", rank=r, hp=hp, **kw))
    return out


def bgroup(enemies):
    """可读摘要：名字@rank:剩余hp。"""
    return {u["name"]: (u["rank"], u["hp"]) for u in enemies}


def cast_skill_aoe(b, st, info, p, name, seed):
    """固定种子施放一次技能，返回 (logs, {name: 掉血量})。"""
    random.seed(seed)
    before = {u["name"]: u["hp"] for u in b.enemies}
    logs = b._player_skill(st, name, info, p)
    loss = {u["name"]: before[u["name"]] - u["hp"] for u in b.enemies
            if u["hp"] < before[u["name"]]}
    return logs, loss


def main():
    clean_db()
    info_xf = E.skill_info("cls_zhan_shi", "旋风斩")
    check("数据：旋风斩带 aoe=True", bool(info_xf and info_xf.get("aoe")), str(info_xf))
    info_single = dict(info_xf)
    info_single.pop("aoe", None)  # 对照组：等价单体技能（v2：单体技能只打 selected 目标）

    # ============ 1. 单目标回归 ============
    print("\n===== 1. 单目标回归：aoe 技能打单怪 == 原单体路径 =====\n")
    random.seed(11)
    p1 = mk_player()
    b1 = BT.Battle("monster", None, {}, p1, enemies=[mk_enemy()])
    logs1, dealt_aoe = cast_skill_aoe(b1, b1._player_stats(p1), info_xf, p1, "旋风斩", 11)
    check("aoe 技能单怪 Boss 掉血 > 0", dealt_aoe.get("主怪", 0) > 0, f"d={dealt_aoe}")
    check("单怪 hp 精确扣减", b1.enemy["hp"] == 10 ** 9 - dealt_aoe["主怪"],
          f"hp={b1.enemy['hp']}")
    random.seed(11)
    p2 = mk_player()
    b2 = BT.Battle("monster", None, {}, p2, enemies=[mk_enemy()])
    _, dealt_single = cast_skill_aoe(b2, b2._player_stats(p2), info_single, p2, "旋风斩", 11)
    check("aoe 单怪伤害 == 等价单体路径（同种子同构造）",
          dealt_aoe.get("主怪", 0) == dealt_single.get("主怪", 0),
          f"aoe={dealt_aoe} single={dealt_single}")
    check("单目标 AOE 无『对【多目标』文案",
          not sum(1 for x in logs1 if "💥 对【" in x) > 1, str(logs1[:3]))

    # ============ 2. 多目标分配（scope=all 打全阵，rank2/3 吃 falloff） ============
    print("\n===== 2. 多目标分配：rank1+rank2+rank3 全阵，AOE all，后排吃 falloff 衰减 =====\n")
    # 手造 all-AOE info（scope=all + reach 覆盖全阵 + falloff=0.7，仅含 AOE 结算所需字段）
    info_all = dict(info_xf)
    info_all["aoe"] = "all"
    info_all["aoe_falloff"] = 0.7
    random.seed(12)
    p3 = mk_player(reach=3, learned=["旋风斩"])
    b3 = BT.Battle("monster", None, {}, p3,
                   enemies=[mk_enemy("前排甲", rank=1, hp=10 ** 9),
                            mk_enemy("后排乙", rank=2, hp=10 ** 9),
                            mk_enemy("后排丙", rank=3, hp=10 ** 9)])
    st3 = b3._player_stats(p3)
    check("三怪入阵列且站位正确",
          [u["rank"] for u in b3.enemies] == [1, 2, 3], str([u["rank"] for u in b3.enemies]))
    logs3, loss3 = cast_skill_aoe(b3, st3, info_all, p3, "旋风斩", 12)
    check("rank1 前排吃全额 >0", loss3.get("前排甲", 0) > 0, f"loss={loss3}")
    check("rank2/rank3 后排也吃到（全阵 AOE）",
          loss3.get("后排乙", 0) > 0 and loss3.get("后排丙", 0) > 0, f"loss={loss3}")
    check("rank1 无衰减 == rank2 吃 0.7 衰减（front 全额 / back=front×0.7）",
          abs(loss3.get("前排甲", 0) - int(loss3.get("后排乙", 0) / 0.7)) <= 1
          and loss3.get("前排甲", 0) > loss3.get("后排乙", 0),
          f"loss={loss3}")
    check("rank2 与 rank3 衰减一致（同 falloff）",
          loss3.get("后排乙", 0) == loss3.get("后排丙", 0), f"loss={loss3}")
    check("逐目标独立伤害文案 3 行",
          sum(1 for x in logs3 if "💥 对【" in x) == 3, str(logs3))

    # ============ 2c. AOE scope=front 只打当前最前排（数据层 旋风斩 实为 front） ============
    print("\n===== 2c. AOE scope=front 只打当前最前排 =====\n")
    check("数据：旋风斩 aoe=front（近战 AOE 打前排）",
          str(info_xf.get("aoe")) == "front", f"aoe={info_xf.get('aoe')}")
    p3f = mk_player(reach=3, learned=["旋风斩"])
    b3f = BT.Battle("monster", None, {}, p3f,
                    enemies=[mk_enemy("F1", rank=1, hp=10 ** 9), mk_enemy("F2", rank=1, hp=10 ** 9),
                             mk_enemy("B1", rank=2, hp=10 ** 9)])
    logs3f, loss3f = cast_skill_aoe(b3f, b3f._player_stats(p3f), info_xf, p3f, "旋风斩", 13)
    check("front 只打 rank1 两只", loss3f.get("F1", 0) > 0 and loss3f.get("F2", 0) > 0,
          f"loss={loss3f}")
    check("front 不打 rank2 后排", loss3f.get("B1", 0) == 0, f"loss={loss3f}")

    # ============ 3. AOE vs 单体：单体只打目标，AOE 打全阵（站位不挡 AOE） ============
    print("\n===== 3. AOE 打阵列 vs 单体技能自动选目标 =====\n")
    # AOE（scope=all）：A(rank1)+B(rank2) 都吃（B 衰减）
    random.seed(14)
    p4 = mk_player(reach=3, learned=["旋风斩"])
    b4 = BT.Battle("monster", None, {}, p4,
                   enemies=[mk_enemy("A", rank=1, hp=10 ** 9), mk_enemy("B", rank=2, hp=10 ** 9)])
    _, loss4 = cast_skill_aoe(b4, b4._player_stats(p4), info_all, p4, "旋风斩", 14)
    check("AOE：A(rank1) 吃全额", loss4.get("A", 0) > 0, f"loss={loss4}")
    check("AOE：B(rank2) 也吃到（站位不挡 AOE）", loss4.get("B", 0) > 0, f"loss={loss4}")
    # 单体：同构造，单体技能只打（自动选）最前排 A，后排 B 不掉血（站位挡伤）
    random.seed(14)
    p5 = mk_player(reach=3, learned=["旋风斩"])
    b5 = BT.Battle("monster", None, {}, p5,
                   enemies=[mk_enemy("A", rank=1, hp=10 ** 9), mk_enemy("B", rank=2, hp=10 ** 9)])
    _, loss5 = cast_skill_aoe(b5, b5._player_stats(p5), info_single, p5, "旋风斩", 14)
    check("单体：最前排 A 吃到", loss5.get("A", 0) > 0, f"loss={loss5}")
    check("单体：后排 B 不掉血（站位挡伤）", loss5.get("B", 0) == 0, f"loss={loss5}")

    # ============ 4. 前排死亡：原后排被近战可及（站位/存活目标语义） ============
    print("\n===== 4. 前排死亡：近战(melee reach=1)可攻击原后排（存活/站位语义） =====\n")
    # A(rank1) 直接致死，B(rank2) 存活；引擎击杀即时压缩 → B 前移为 rank1。
    p6 = mk_player(reach=1, learned=["旋风斩"])
    b6 = BT.Battle("monster", None, {}, p6,
                   enemies=[mk_enemy("A", rank=1, hp=10), mk_enemy("B", rank=2, hp=10 ** 9)])
    b6._damage_enemy(10 ** 6, [], target=b6.enemies[0])  # 打死前排 A（即时压缩）
    check("引擎打死后 enemies 移除死亡单位", [u["name"] for u in b6.enemies] == ["B"],
          str([(u["name"], u["hp"]) for u in b6.enemies]))
    check("存活后排前移为 rank1（压缩后近战可及）", all(u["rank"] == 1 for u in b6.enemies),
          str([(u["name"], u["rank"]) for u in b6.enemies]))
    aliv = [u for u in b6.enemies if u.get("hp", 0) > 0]
    picked = b6._resolve_player_target(p6)  # 近战自动目标
    check("近战自动目标落到存活的 B", picked is not None and picked.get("name") == "B",
          f"picked={picked and picked.get('name')} alive={[u['name'] for u in aliv]}")
    check("enemy property 指向存活的 B", b6.enemy["name"] == "B",
          f"enemy={b6.enemy['name']}")

    # ============ 5. 超载真 AOE ============
    print("\n===== 5. 超载真 AOE（火系技能 + 雷印 → matk×1.2 全阵，印记清除）=====\n")
    info_fire = {"name": "火球测试", "kind": "魔法", "power": 1.0, "element": "fire", "cd": 1}
    random.seed(7)
    p7 = mk_player(reach=3)
    b7 = BT.Battle("monster", None, {}, p7,
                   enemies=[mk_enemy("T1", rank=1, hp=10 ** 9), mk_enemy("T2", rank=2, hp=10 ** 9)])
    st7 = b7._player_stats(p7)
    aoe_dmg = int(st7["matk"] * 1.2)
    b7.enemy["buffs"]["thunder_mark"] = 1
    # 主伤害（非 aoe 火球）落到主目标 T1，超载 AOE 段打到全阵
    before7 = {u["name"]: u["hp"] for u in b7.enemies}
    logs7 = b7._player_skill(st7, "火球测试", info_fire, p7)
    loss7 = {u["name"]: before7[u["name"]] - u["hp"] for u in b7.enemies
             if u["hp"] < before7[u["name"]]}
    check("超载 aoe 段 == int(matk×1.2)（T2 后排只吃 aoe 段）", loss7.get("T2", 0) == aoe_dmg,
          f"T2={loss7.get('T2', 0)} expect={aoe_dmg} loss={loss7}")
    check("主伤害落主目标 T1（T1 total = 主伤害 + aoe 段 > aoe 段）",
          loss7.get("T1", 0) > aoe_dmg and loss7.get("T1", 0) >= loss7.get("T2", 0),
          f"loss={loss7}")
    check("超载文案『💥超载爆发！』", any("超载爆发" in x for x in logs7), str(logs7))
    check("超载后雷印被清除", "thunder_mark" not in b7.enemy["buffs"], str(b7.enemy["buffs"]))

    # ============ 6. 星陨真 AOE ============
    print("\n===== 6. 星陨真 AOE（_affix_on_hit 强制触发：全阵各吃 200%）=====\n")
    p8 = mk_player(affixes=["starfall"], reach=3)
    b8 = BT.Battle("monster", None, {}, p8,
                   enemies=[mk_enemy("S1", rank=1, hp=10 ** 9), mk_enemy("S2", rank=2, hp=10 ** 9)])
    before8 = {u["name"]: u["hp"] for u in b8.enemies}
    _orig_random = random.random
    try:
        random.random = lambda: 0.0  # 0.0 < 0.10 → 强制触发
        logs8 = []
        b8._affix_on_hit(p8, 100, logs8)
    finally:
        random.random = _orig_random
    loss8 = {u["name"]: before8[u["name"]] - u["hp"] for u in b8.enemies
             if u["hp"] < before8[u["name"]]}
    check("星陨：S1 吃 200%（dmg×2.0）", loss8.get("S1", 0) == 200, f"loss={loss8}")
    check("星陨：S2 也吃 200%", loss8.get("S2", 0) == 200, f"loss={loss8}")
    check("星陨文案『☄️ 星陨！』", any("星陨" in x for x in logs8), str(logs8))
    check("星陨每目标一行文案", sum(1 for x in logs8 if "对【" in x and "造成" in x) == 2, str(logs8))
    # 不触发对照
    p8b = mk_player(affixes=["starfall"], reach=3)
    b8b = BT.Battle("monster", None, {}, p8b, enemies=[mk_enemy("X", rank=1, hp=10 ** 9)])
    try:
        random.random = lambda: 0.99
        b8b._affix_on_hit(p8b, 100, [])
    finally:
        random.random = _orig_random
    check("星陨 10% 概率：未触发无伤害", b8b.enemy["hp"] == 10 ** 9, f"hp={b8b.enemy['hp']}")

    # ============ 7. multi×aoe ============
    print("\n===== 7. multi×aoe：风刃乱舞 70%×3 全体（累加 total 后一次 aoe 结算）=====\n")
    info_multi = E.skill_info("cls_you_xia", "风刃乱舞")
    check("数据：风刃乱舞 multi=3 且 aoe=True",
          bool(info_multi and info_multi.get("multi") == 3 and info_multi.get("aoe")),
          str(info_multi and {k: info_multi.get(k) for k in ("multi", "aoe", "power")}))
    random.seed(15)
    p9 = mk_player(cls="cls_you_xia", reach=3)
    b9 = BT.Battle("monster", None, {}, p9,
                   enemies=[mk_enemy("M1", rank=1, hp=10 ** 9), mk_enemy("M2", rank=1, hp=10 ** 9)])
    logs9, loss9 = cast_skill_aoe(b9, b9._player_stats(p9), info_multi, p9, "风刃乱舞", 15)
    check("multi×aoe：M1 吃 3 段累加 total", loss9.get("M1", 0) > 0, f"loss={loss9}")
    check("multi×aoe：M2 与 M1 相同（同 rank 同衰减）", loss9.get("M1", 0) == loss9.get("M2", 0),
          f"loss={loss9}")
    check("连击文案『连击 3 次』",
          any("连击 3 次" in x for x in logs9), str(logs9))

    # ============ 8. 吸血分账（AOE：heal == 主目标实伤×吸血率） ============
    print("\n===== 8. 吸血分账：AOE heal == 主目标(最前排)实伤×吸血率 =====\n")
    p10 = mk_player(extra_stats={"lifesteal": 0.20}, reach=3)
    b10 = BT.Battle("monster", None, {}, p10,
                    enemies=[mk_enemy("V1", rank=1, hp=10 ** 9), mk_enemy("V2", rank=2, hp=10 ** 9)])
    st10 = b10._player_stats(p10)
    check("吸血属性生效（0.20）", abs(float(st10.get("lifesteal", 0)) - 0.20) < 1e-9,
          f"lifesteal={st10.get('lifesteal')}")
    p10["hp"] = st10["max_hp"] - 100000
    before = {u["name"]: u["hp"] for u in b10.enemies}
    hp0 = p10["hp"]
    random.seed(11)
    logs10 = b10._player_skill(st10, "旋风斩", info_xf, p10)
    loss10 = {u["name"]: before[u["name"]] - u["hp"] for u in b10.enemies
              if u["hp"] < before[u["name"]]}
    heal = p10["hp"] - hp0
    main_loss = loss10.get("V1", 0)  # 主目标 = 最前排
    check("吸血 heal == int(主目标实伤×0.2)", heal == int(main_loss * 0.20),
          f"heal={heal} expect={int(main_loss * 0.20)}")
    check("吸血文案『🩸 吸血：回复』",
          any(f"🩸 吸血：回复 {heal} 点生命！" in x for x in logs10), str(logs10))
    check("玩家血量精确增加 heal", p10["hp"] == hp0 + heal, f"hp={p10['hp']}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
