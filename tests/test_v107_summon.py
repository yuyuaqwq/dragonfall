#!/usr/bin/env python3
"""v107 召唤物系统测试（2026-08-13 鱼鱼拍板）

覆盖：
1. 召唤：技能带 summon 字段 → 实体生成（属性按玩家比例缩放）
2. 上限：骷髅海 limit=3，第 4 次召唤被拒
3. 自动攻击：_summons_act 每回合造成伤害（物理段吃敌 def）
4. 真伤召唤物（合成 synthetic_true）：dmg_type=true 绕过防御
5. 挡刀：_damage_player 概率转移伤害给召唤物
6. 受击死亡：挡刀扣血到 0 移除
7. summon_power 强化：生成属性加成
8. 序列化：to_state/from_state 保留 summons
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
    from data.plugins.dragonfall.game.data.summons import SUMMONS
    from data.plugins.dragonfall.game import engine as EG  # v109.2 P2-1 挡刀按 def 结算期望

    print("===== v107 召唤物系统 =====\n")

    # 0. 数据完整性
    print("— 数据 —")
    check("模板含骷髅/藤蔓守卫/古树守卫", all(k in SUMMONS for k in
                                          ("skeleton", "vine_guard", "treant")))
    check("骷髅 limit=3（数量流）", SUMMONS["skeleton"]["limit"] == 3)
    check("藤蔓守卫 limit=2（数量流）", SUMMONS["vine_guard"]["limit"] == 2)
    check("古树守卫 limit=1（重装）", SUMMONS["treant"]["limit"] == 1)
    check("v113 兽群进出（狼三形态已删）", not any(k in SUMMONS for k in
                                                 ("wolf_cub", "wolf_king", "shadow_wolf")))

    def mk_player(extra=None, cls="牧师", hp=500):
        p = {
            "class_name": cls, "level": 30, "hp": hp, "max_hp": hp,
            "mp": 100, "max_mp": 100,
            "equipment": {"weapon": {"name": "测试杖", "stats": {"atk": 100, "matk": 100},
                                     "affixes": [], "enhance": 0}},
            "attributes": {"str": 10, "int": 10},
            "learned_skills": [], "race": "human",
        }
        if extra:
            p.update(extra)
        return p

    def mk_enemy(def_=20, hp=50000):
        return {"name": "测试怪", "hp": hp, "max_hp": hp,
                "atk": 100, "def": def_, "mdef": 20, "spd": 10}

    summon_info = {"name": "召唤骷髅", "kind": "增益", "power": 0, "lv": 30,
                   "cd": 1, "summon": "skeleton"}

    # 1. 召唤实体生成
    print("\n— 召唤生成 —")
    p1 = mk_player()
    b1 = BT.Battle("怪物", mk_enemy(), {}, p1)
    st1 = b1._player_stats(p1)
    logs1 = []
    ok1 = b1._summon_entity("skeleton", p1, logs1)
    check("召唤成功", ok1, str(logs1))
    check("实体生成 1 个", len(b1.summons) == 1, str(len(b1.summons)))
    s1 = b1.summons[0]
    exp_hp = max(20, int(st1["max_hp"] * SUMMONS["skeleton"]["hp_ratio"]))
    exp_atk = max(5, int(st1["atk"] * SUMMONS["skeleton"]["atk_ratio"]))
    check(f"HP 按玩家比例 ({exp_hp})", abs(s1["hp"] - exp_hp) <= 1, f"got {s1['hp']}")
    check(f"ATK 按玩家比例 ({exp_atk})", abs(s1["atk"] - exp_atk) <= 1, f"got {s1['atk']}")
    check("日志有加入提示", any("加入战斗" in l for l in logs1), str(logs1))

    # 2. 上限：骷髅叠 3
    print("\n— 上限 —")
    b2 = BT.Battle("怪物", mk_enemy(), {}, mk_player())
    for i in range(3):
        b2._summon_entity("skeleton", mk_player(), [])
    check("骷髅叠满 3 个", len(b2.summons) == 3)
    logs2 = []
    ok2 = b2._summon_entity("skeleton", mk_player(), logs2)
    check("第 4 次被拒", not ok2, str(logs2))
    check("仍为 3 个", len(b2.summons) == 3)

    # 3. 自动攻击
    print("\n— 自动攻击 —")
    b3 = BT.Battle("怪物", mk_enemy(def_=10, hp=50000), {}, mk_player())
    b3._summon_entity("skeleton", mk_player(), [])
    hp3 = b3.enemy["hp"]
    logs3 = b3._summons_act(mk_player(), [])
    dealt3 = hp3 - b3.enemy["hp"]
    check("召唤物攻击造成伤害", dealt3 > 0, f"dealt {dealt3}")
    check("日志有攻击文案", any("攻击" in l for l in logs3), str(logs3))

    # 4. 真伤召唤物（合成 true-dmg 召唤，验证真伤绕过防御；v113 狼系真伤模板已删）
    print("\n— 真伤召唤物 —")
    p4 = mk_player()
    b4 = BT.Battle("怪物", mk_enemy(def_=5000, hp=50000), {}, p4)
    b4.summons.append({"tid": "synthetic_true", "name": "真伤灵", "icon": "✨",
                       "hp": 500, "max_hp": 500, "atk": 100, "def": 0,
                       "dmg_type": "true"})
    hp4 = b4.enemy["hp"]
    logs4 = b4._summons_act(p4, [])
    dealt4 = hp4 - b4.enemy["hp"]
    check("真伤召唤物无视 def=5000", 80 <= dealt4 <= 120, f"dealt {dealt4}")
    # 对照：物理召唤物（骷髅）被高防大幅削减
    p4b = mk_player()
    b4b = BT.Battle("怪物", mk_enemy(def_=5000, hp=50000), {}, p4b)
    b4b._summon_entity("skeleton", p4b, [])
    b4b.summons[0]["atk"] = 100
    hp4b = b4b.enemy["hp"]
    b4b._summons_act(p4b, [])
    dealt4b = hp4b - b4b.enemy["hp"]
    check("骷髅物理被高防削减", dealt4b < dealt4 * 0.5, f"phys {dealt4b} vs true {dealt4}")

    # 5. 挡刀
    print("\n— 挡刀 —")
    found = False
    for seed in range(60):
        random.seed(seed)
        p5 = mk_player(hp=1000)
        b5 = BT.Battle("怪物", mk_enemy(), {}, p5)
        b5._summon_entity("skeleton", p5, [])
        # 屏蔽随机闪避，保证受击断言确定性（挡刀/扣血精确断言）
        _orig_ps = b5._player_stats
        def _ps_nododge(p_):
            s = _orig_ps(p_)
            s["dodge"] = 0.0
            return s
        b5._player_stats = _ps_nododge
        hp5 = p5["hp"]
        b5.summons[0]["hp"] = 500
        logs5 = []
        b5._damage_player(p5, 100, logs5)
        if any("挡下" in l for l in logs5):
            found = True
            check(f"挡刀生效（seed {seed}）", p5["hp"] == hp5, f"player hp {p5['hp']}")
            # v109.2 P2-1：挡刀按召唤物 def 结算（原全额转移）——从对玩家伤害反推等效 atk 再套召唤物防御
            _pdef = max(0, int(b5._player_stats(p5).get("def", 0) or 0))
            _atk = (100 + int((100 * 100 + 4 * 100 * _pdef) ** 0.5)) // 2
            _sdef = max(0, int(b5.summons[0].get("def", 0) or 0))
            _taken = max(1, int(EG.calc_damage(_atk, _sdef, variance=0)))
            check(f"召唤物扣血按 def 结算（{_taken}）", b5.summons[0]["hp"] == 500 - _taken,
                  f"summon hp {b5.summons[0]['hp']}")
            break
    check("挡刀可触发", found)

    # 6. 受击死亡移除
    print("\n— 受击死亡 —")
    random.seed(1)
    p6 = mk_player(hp=1000)
    b6 = BT.Battle("怪物", mk_enemy(), {}, p6)
    b6._summon_entity("skeleton", p6, [])
    b6.summons[0]["hp"] = 30
    # 屏蔽随机闪避，保证受击断言确定性（挡刀致死精确断言）
    _orig_ps = b6._player_stats
    def _ps_nododge(p_):
        s = _orig_ps(p_)
        s["dodge"] = 0.0
        return s
    b6._player_stats = _ps_nododge
    for i in range(50):  # 反复打直到挡刀触发
        random.seed(10 + i)
        logs6 = []
        b6._damage_player(p6, 100, logs6)
        if not b6.summons:
            break
    check("挡刀致死移除", len(b6.summons) == 0, f"summons {len(b6.summons)}")
    check("玩家存活", p6["hp"] > 0, str(p6["hp"]))

    # 7. summon_power 强化
    print("\n— summon_power 强化 —")
    p7 = mk_player()
    p7["equipment"]["weapon"]["stats"]["summon_power"] = 0.50  # 50% 强化（直塞属性验证生效路径）
    b7 = BT.Battle("怪物", mk_enemy(), {}, p7)
    st7 = b7._player_stats(p7)
    check("summon_power 进聚合", abs(st7.get("summon_power", 0) - 0.50) < 1e-9, str(st7.get("summon_power")))
    b7._summon_entity("skeleton", p7, [])
    exp_hp7 = int(st7["max_hp"] * SUMMONS["skeleton"]["hp_ratio"] * 1.5)
    check(f"召唤物 HP 受强化 ({exp_hp7})", abs(b7.summons[0]["hp"] - exp_hp7) <= 1,
          f"got {b7.summons[0]['hp']}")

    # 8. 序列化
    print("\n— 序列化 —")
    b8 = BT.Battle("怪物", mk_enemy(), {}, mk_player())
    b8._summon_entity("skeleton", mk_player(), [])
    b8._summon_entity("skeleton", mk_player(), [])
    st8 = b8.to_state()
    check("to_state 含 summons", len(st8.get("summons", [])) == 2)
    b8r = BT.Battle.from_state(st8)
    check("from_state 恢复 summons", len(b8r.summons) == 2 and b8r.summons[0]["tid"] == "skeleton")
    check("老存档无 summons 兜底", BT.Battle.from_state({"type": "monster"}).summons == [])

    # 9. 技能字段触发召唤（_player_skill 挂点）
    print("\n— 技能召唤挂点 —")
    p9 = mk_player()
    b9 = BT.Battle("怪物", mk_enemy(), {}, p9)
    logs9 = b9._player_skill(b9._player_stats(p9), "召唤骷髅", summon_info, p9)
    check("技能召唤生成实体", len(b9.summons) == 1, f"summons {len(b9.summons)}")
    check("技能召唤有日志", any("加入战斗" in l for l in logs9), str(logs9))

    print()
    print(f"===== v107 召唤物系统测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
