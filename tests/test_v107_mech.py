#!/usr/bin/env python3
"""v107 机制层测试（2026-08-13 鱼鱼拍板）

覆盖 8 个新机制：
1. 斩杀（影武者）：目标 HP<30% 伤害 +40%
2. 吸MP（虚空行者）：魔法伤害 15% 回蓝
3. 毒爆（丛林猎手）：poison 层数≥3 引爆（魔法段），<3 不引爆
4. 格挡反击（圣殿骑士）：格挡成功概率反伤
5. 反击（武圣）：受击概率普攻反击
6. 血魔法（血法师）：hp_cost 扣血 +30% 伤害
7. 死亡契约（亡灵术士）：致死牺牲召唤物以 20% HP 存活（每场 1 次）
8. 单宠进化（兽王）：幼狼→狼王→影狼（真伤）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, make_player

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
    from data.plugins.dragonfall.game.data.skills import PLAYER_SKILLS
    from data.plugins.dragonfall.game.core import battle_mech as BM

    # 注入测试被动技能（key=中文名，resolve 原样返回可命中；测完清理）
    TEST_PASSIVES = {
        "斩杀测试": {"name": "斩杀测试", "kind": "被动",
                     "passive": {"proc": "execute", "mult": 0.40, "cond_hp": 0.30}},
        "格挡反击测试": {"name": "格挡反击测试", "kind": "被动",
                         "passive": {"proc": "block_counter", "chance": 1.0, "mult": 0.50}},
        "反击测试": {"name": "反击测试", "kind": "被动",
                     "passive": {"proc": "counter_attack", "chance": 1.0}},
        "死亡契约测试": {"name": "死亡契约测试", "kind": "被动",
                         "passive": {"proc": "death_pact"}},
    }
    PLAYER_SKILLS["cls_mech_test"] = {"skills": dict(TEST_PASSIVES)}

    def mk_player(passives=None, cls="cls_mech_test", hp=500):
        return {
            "class_name": cls, "level": 30, "hp": hp, "max_hp": hp,
            "mp": 50, "max_mp": 100,
            "equipment": {"weapon": {"name": "测试剑", "stats": {"atk": 100, "matk": 100},
                                     "affixes": [], "enhance": 0}},
            "attributes": {"str": 10, "int": 10},
            "learned_skills": passives or [], "race": "human",
        }

    def mk_enemy(def_=20, mdef=20, hp=10000):
        return {"name": "测试怪", "hp": hp, "max_hp": hp,
                "atk": 50, "def": def_, "mdef": mdef, "spd": 10}

    print("===== v107 机制层 =====\n")

    # 1. 斩杀
    print("— 斩杀 —")
    e_info = {"name": "斩击", "kind": "物理", "power": 1.0, "lv": 30, "cd": 1}
    p1 = mk_player(passives=["斩杀测试"])
    b1 = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, p1)
    b1.enemy["hp"] = 2000  # 20% 血
    st1 = b1._player_stats(p1)
    random.seed(3)
    hp1 = b1.enemy["hp"]
    logs1 = b1._player_skill(st1, "斩击", e_info, p1)
    dealt1 = hp1 - b1.enemy["hp"]
    # 无斩杀时应 ≈ atk×1.0（≈220±15%），斩杀 ×1.4 → ≈308
    base1 = int(st1["atk"] * 1.0 * 1.4)
    check(f"残血斩杀加成（≈{base1}±20%）", 0.8 * base1 <= dealt1 <= 1.2 * base1,
          f"dealt {dealt1}, atk {st1['atk']}")
    check("斩杀标签", any("斩杀" in l for l in logs1), str(logs1))

    p1b = mk_player(passives=["斩杀测试"])
    b1b = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, p1b)
    b1b.enemy["hp"] = 9000  # 90% 血
    st1b = b1b._player_stats(p1b)
    random.seed(3)
    hp1b = b1b.enemy["hp"]
    logs1b = b1b._player_skill(st1b, "斩击", e_info, p1b)
    dealt1b = hp1b - b1b.enemy["hp"]
    base1b = int(st1b["atk"] * 1.0)  # 无斩杀
    check("满血无斩杀加成", 0.8 * base1b <= dealt1b <= 1.25 * base1b,
          f"dealt {dealt1b} (斩杀版 {dealt1})")
    check("满血无斩杀标签", not any("斩杀" in l for l in logs1b), str(logs1b))

    # 2. 吸MP
    print("\n— 吸MP —")
    mp_info = {"name": "虚空箭", "kind": "魔法", "power": 1.0, "lv": 30, "cd": 1,
               "mp_steal": 0.15}
    p2 = mk_player(cls="cls_fa_shi", hp=500)
    p2["mp"] = 10
    b2 = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, p2)
    st2 = b2._player_stats(p2)
    random.seed(5)
    logs2 = b2._player_skill(st2, "虚空箭", mp_info, p2)
    check("吸MP 回蓝", p2["mp"] > 10, f"mp {p2['mp']}")
    check("吸MP 日志", any("虚空汲取" in l for l in logs2), str(logs2))

    # 3. 毒爆
    print("\n— 毒爆 —")
    b3 = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, mk_player(cls="cls_fa_shi"))
    b3._last_player = mk_player(cls="cls_fa_shi")
    b3.mech_stacks["poison"] = 3
    e_hp3 = b3.enemy["hp"]
    logs3 = []
    BM.MECH_EFFECTS["poison_burst"](b3, 1, b3.mech_stacks, 100, logs3, "毒爆术", False)
    check("毒爆造成伤害", b3.enemy["hp"] < e_hp3, f"{e_hp3}→{b3.enemy['hp']}")
    check("毒爆清层", b3.mech_stacks.get("poison", 0) == 0, str(b3.mech_stacks))
    check("毒爆魔法段日志", any("魔法伤害" in l for l in logs3), str(logs3))
    b3b = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, mk_player(cls="cls_fa_shi"))
    b3b.mech_stacks["poison"] = 2
    logs3b = []
    BM.MECH_EFFECTS["poison_burst"](b3b, 1, b3b.mech_stacks, 100, logs3b, "毒爆术", False)
    check("毒层<3 不引爆", b3b.mech_stacks.get("poison", 0) == 2, str(b3b.mech_stacks))
    check("毒层<3 提示", any("≥3" in l for l in logs3b), str(logs3b))

    # 4. 格挡反击
    print("\n— 格挡反击 —")
    found4 = False
    for seed in range(40):
        random.seed(seed)
        p4 = mk_player(passives=["格挡反击测试"], hp=2000)
        p4["equipment"]["weapon"]["stats"]["block"] = 1.0  # 必格挡
        b4 = BT.Battle("怪物", mk_enemy(hp=5000), {}, p4)
        e_hp4 = b4.enemy["hp"]
        logs4 = []
        b4._damage_player(p4, 100, logs4)
        if any("格挡反击" in l for l in logs4):
            found4 = True
            check(f"格挡反击反伤（seed {seed}）", b4.enemy["hp"] < e_hp4,
                  f"{e_hp4}→{b4.enemy['hp']}")
            break
    check("格挡反击可触发", found4)

    # 5. 反击（武圣）
    print("\n— 反击 —")
    found5 = False
    for seed in range(40):
        random.seed(seed)
        p5 = mk_player(passives=["反击测试"], hp=2000)
        b5 = BT.Battle("怪物", mk_enemy(hp=5000), {}, p5)
        e_hp5 = b5.enemy["hp"]
        logs5 = []
        b5._damage_player(p5, 100, logs5)
        if any("反击" in l for l in logs5):
            found5 = True
            check(f"受击反击（seed {seed}）", b5.enemy["hp"] < e_hp5,
                  f"{e_hp5}→{b5.enemy['hp']}")
            break
    check("反击可触发", found5)

    # 6. 血魔法
    print("\n— 血魔法 —")
    hm_info = {"name": "血之契约", "kind": "魔法", "power": 1.0, "lv": 30, "cd": 1,
               "hp_cost": 0.10}
    p6 = mk_player(cls="cls_fa_shi", hp=500)
    b6 = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, p6)
    st6 = b6._player_stats(p6)
    random.seed(3)
    logs6 = b6._player_skill(st6, "血之契约", hm_info, p6)
    check("血魔法扣血 10%", p6["hp"] <= 450, f"hp {p6['hp']}")
    check("血魔法日志", any("血之代价" in l for l in logs6), str(logs6))
    check("血祭标签", any("血祭" in l for l in logs6), str(logs6))
    # 对照：无 hp_cost 不扣血
    p6b = mk_player(cls="cls_fa_shi", hp=500)
    b6b = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, p6b)
    random.seed(3)
    b6b._player_skill(b6b._player_stats(p6b), "虚空箭", mp_info, p6b)
    check("无 hp_cost 不扣血", p6b["hp"] == 500, f"hp {p6b['hp']}")

    # 7. 死亡契约
    print("\n— 死亡契约 —")
    p7 = mk_player(passives=["死亡契约测试"], hp=100)
    b7 = BT.Battle("怪物", mk_enemy(), {}, p7)
    b7._summon_entity("skeleton", p7, [])
    b7._summon_entity("skeleton", p7, [])
    logs7 = []
    b7._damage_player(p7, 500, logs7)
    check("致死被契约救回", 0 < p7["hp"] <= p7["max_hp"] * 0.21, f"hp {p7['hp']} max {p7['max_hp']}")
    check("牺牲一个召唤物", len(b7.summons) == 1, f"summons {len(b7.summons)}")
    check("契约日志", any("死亡契约" in l for l in logs7), str(logs7))
    # 每场 1 次：第二次致死不再触发
    b7._summon_entity("skeleton", p7, [])
    logs7b = []
    b7._damage_player(p7, 500, logs7b)
    check("契约每场仅 1 次", p7["hp"] == 0, f"hp {p7['hp']}")
    check("第二次无契约日志", not any("死亡契约" in l for l in logs7b), str(logs7b))

    # 8. 单宠进化
    print("\n— 单宠进化 —")
    evo1 = {"name": "驯兽召唤", "kind": "增益", "power": 0, "lv": 30, "cd": 1, "summon": "wolf_cub"}
    evo2 = {"name": "狼群指令", "kind": "增益", "power": 0, "lv": 30, "cd": 1, "summon_evolve": 2}
    evo3 = {"name": "野性呼唤", "kind": "增益", "power": 0, "lv": 30, "cd": 1, "summon_evolve": 3}
    p8 = mk_player(cls="cls_beast_king")
    b8 = BT.Battle("怪物", mk_enemy(), {}, p8)
    b8._player_skill(b8._player_stats(p8), "驯兽召唤", evo1, p8)
    check("召唤幼狼", len(b8.summons) == 1 and b8.summons[0]["tid"] == "wolf_cub",
          str([s.get("tid") for s in b8.summons]))
    logs8 = []
    b8._summon_evolve(2, p8, logs8)
    check("进化狼王", b8.summons[0]["tid"] == "wolf_king", str(b8.summons[0]["tid"]))
    check("进化日志", any("进化" in l for l in logs8), str(logs8))
    b8._summon_evolve(3, p8, logs8)
    check("进化影狼", b8.summons[0]["tid"] == "shadow_wolf", str(b8.summons[0]["tid"]))
    check("影狼真伤类型", b8.summons[0]["dmg_type"] == "true", str(b8.summons[0]["dmg_type"]))
    # 无狼宠时进化提示
    b8c = BT.Battle("怪物", mk_enemy(), {}, p8)
    logs8c = []
    b8c._summon_evolve(2, p8, logs8c)
    check("无宠进化提示", any("先召唤" in l for l in logs8c), str(logs8c))

    # 清理注入
    del PLAYER_SKILLS["cls_mech_test"]

    print()
    print(f"===== v107 机制层测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
