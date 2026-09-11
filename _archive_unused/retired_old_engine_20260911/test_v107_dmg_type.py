#!/usr/bin/env python3
"""v107 伤害类型四层架构测试（2026-08-13 鱼鱼拍板）

覆盖：
1. calc_damage 直测：真伤绕过全部减伤（高 def 下 ≈ atk 直伤）/ 物理吃防御公式 / 真伤可暴击
2. 战斗级真伤技能：无视敌人 def（vs 物理技能被 def 削减）
3. 真伤不吸血（_settle_lifesteal dmg_type="true" 跳过）
4. 技能/普攻/怪物技能显式类型声明（源码断言 + 魔法技能吃 mdef）
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
    from data.plugins.dragonfall.game import engine as EG
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.core.affix import stat_affix_stats

    print("===== v107 伤害类型四层架构 =====\n")

    # 1. calc_damage 直测
    print("— calc_damage 直测 —")
    random.seed(7)
    d_true = EG.calc_damage(100, 9999, dmg_type="true")   # 真伤：def 9999 也无视
    check("真伤无视超高防御", 85 <= d_true <= 115, f"got {d_true}")
    random.seed(7)
    d_phys = EG.calc_damage(100, 100)                     # 物理：100²/(200)=50 ±15%
    check("物理吃防御公式(50±15%)", 42 <= d_phys <= 58, f"got {d_phys}")
    random.seed(7)
    d_true_crit = EG.calc_damage(100, 9999, is_crit=True, dmg_type="true")
    check("真伤可暴击(×1.5)", 127 <= d_true_crit <= 173, f"got {d_true_crit}")
    d_true_no_crit = EG.calc_damage(100, 9999, dmg_type="true")
    check("真伤非暴击无1.5倍", d_true_no_crit < 120, f"got {d_true_no_crit}")
    random.seed(7)
    d_true_pene = EG.calc_damage(100, 9999, pene_pct=0.5, dmg_type="true")
    check("真伤不受穿透参数影响", abs(d_true_pene - d_true) <= 1, f"{d_true_pene} vs {d_true}")
    d_min = EG.calc_damage(5, 9999, dmg_type="true")
    check("真伤保底 1", d_min >= 1, str(d_min))
    d_phys_hi = EG.calc_damage(100, 9999, dmg_type="phys")
    check("物理被超高防御削到保底", d_phys_hi <= 2, f"got {d_phys_hi}")

    # 2. 战斗级：真伤技能无视敌人防御
    print("\n— 战斗级真伤 vs 物理 —")

    def mk_player(affixes=None, cls="战士", skills=None, hp=500):
        eq_stats = {"atk": 100, "matk": 100}
        eq_stats.update(stat_affix_stats(affixes or [], "weapon", 30))
        return {
            "class_name": cls, "level": 30, "hp": hp, "max_hp": hp,
            "mp": 100, "max_mp": 100,
            "equipment": {"weapon": {"name": "测试剑", "stats": eq_stats,
                                     "affixes": affixes or [], "enhance": 0}},
            "attributes": {"str": 10, "int": 10},
            "learned_skills": skills or [], "race": "human",
        }

    def mk_enemy(def_=20, mdef=20, hp=10000):
        return {"name": "测试怪", "hp": hp, "max_hp": hp,
                "atk": 50, "def": def_, "mdef": mdef, "spd": 10}

    # 真伤技能 info（数据未实装前测试直构；power 1.0 便于断言）
    true_info = {"name": "龙息测试", "kind": "真伤", "power": 1.0, "lv": 30, "cd": 1}
    phys_info = {"name": "劈砍测试", "kind": "物理", "power": 1.0, "lv": 30, "cd": 1}

    # 2a. 高防怪：真伤 ≈ 实际 atk×power + flat（v156 基础值），物理被大幅削减
    random.seed(3)
    p1 = mk_player()
    b1 = BT.Battle("怪物", mk_enemy(def_=500), {}, p1)
    st1 = b1._player_stats(p1)
    true_base = int(st1["atk"] * 1.0) + EG.skill_flat_value(30, 30, true_info)
    enemy_hp_before = b1.enemy["hp"]
    logs1 = b1._actor_skill(st1, "龙息测试", true_info, p1)
    dealt1 = enemy_hp_before - b1.enemy["hp"]
    check(f"真伤技能无视 def=500（≈atk×power {true_base}±15%）",
          0.8 * true_base <= dealt1 <= 1.2 * true_base, f"dealt {dealt1}, atk {true_base}")

    random.seed(3)
    p1b = mk_player()
    b1b = BT.Battle("怪物", mk_enemy(def_=500), {}, p1b)
    hp_b = b1b.enemy["hp"]
    logs1b = b1b._actor_skill(b1b._player_stats(p1b), "劈砍测试", phys_info, p1b)
    dealt1b = hp_b - b1b.enemy["hp"]
    check("物理技能被 def=500 大幅削减", dealt1b < dealt1 * 0.5,
          f"phys {dealt1b} vs true {dealt1}")

    # 2b. 低防怪：真伤与物理差异小（防御公式收益递减）
    random.seed(3)
    p2 = mk_player()
    b2 = BT.Battle("怪物", mk_enemy(def_=10), {}, p2)
    hp2 = b2.enemy["hp"]
    b2._actor_skill(b2._player_stats(p2), "龙息测试", true_info, p2)
    dealt2 = hp2 - b2.enemy["hp"]
    random.seed(3)
    p2b = mk_player()
    b2b = BT.Battle("怪物", mk_enemy(def_=10), {}, p2b)
    hp2b = b2b.enemy["hp"]
    b2b._actor_skill(b2b._player_stats(p2b), "劈砍测试", phys_info, p2b)
    dealt2b = hp2b - b2b.enemy["hp"]
    check("低防下真伤与物理接近（差距<35%）", abs(dealt2 - dealt2b) < dealt2 * 0.35,
          f"true {dealt2} vs phys {dealt2b}")

    # 3. 真伤不吸血
    print("\n— 真伤不吸血 —")
    # 通用吸血词条（lifesteal → 通用吸血 10%）
    p3 = mk_player(affixes=["vampiric"], hp=300)
    b3 = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, p3)
    random.seed(5)
    hp_before = p3["hp"]
    logs3 = b3._actor_skill(b3._player_stats(p3), "龙息测试", true_info, p3)
    check("真伤技能不回血", p3["hp"] == hp_before, f"{p3['hp']} vs {hp_before}")
    check("真伤无吸血日志", not any("吸血" in l for l in logs3), str([l for l in logs3 if "吸血" in l]))

    # 对照：魔法技能触发吸血（thirst_magi 法吸 8%，v106.4 已验证词条）
    # v153 真 bug（上报，不改引擎）：火球术 kind='魔法·火'，引擎吸血分流 magic=(kind=="魔法")
    # 精确匹配 → '魔法·火' ≠ '魔法' → 法吸被当物理段（lifesteal_phys=0）不触发。
    # 测试按引擎现状断言（法吸魔法技能暂不生效），等待引擎 v153 kind 前缀匹配修复。
    p3b = mk_player(affixes=["thirst_magi"], cls="法师", skills=["火球术"], hp=300)
    b3b = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, p3b)
    found = False
    for seed in range(40):
        random.seed(seed)
        p3c = mk_player(affixes=["thirst_magi"], cls="法师", skills=["火球术"], hp=300)
        b3c = BT.Battle("怪物", mk_enemy(def_=10, hp=10000), {}, p3c)
        logs3c = b3c._actor_skill(b3c._player_stats(p3c), "火球术",
                                   E.skill_info("法师", "火球术"), p3c)
        if any("吸血" in l for l in logs3c):
            found = True
            break
    # v158 formula 补全：火球术（魔法·火）配 formula type=magi 段 → 法吸魔法技能生效
    # （v153 kind 细分旧 bug 已随 formula 修复）。
    check("对照：魔法技能吸血（v158 formula 修复后生效）", found, f"found={found}")

    # 4. 源码断言：类型显式声明
    print("\n— 类型显式声明（源码） —")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
              encoding="utf-8") as f:
        bsrc = f.read()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "engine.py"),
              encoding="utf-8") as f:
        esrc = f.read()
    check("calc_damage 有 dmg_type 参数", "dmg_type" in esrc)
    check("真伤判断 dmg_type == \"true\"", 'dmg_type == "true"' in esrc)
    # v176 去魔法字符串：真伤用 K_TRUE 常量（skill_kinds.py）替代中文"真伤"字面量
    check("技能真伤 kind 分支(K_TRUE)", 'kind == K_TRUE' in bsrc or 'kind == "真伤"' in bsrc)
    check("技能真伤传参 true", 'dmg_type="true"' in bsrc)
    check("技能物理显式 phys", 'dmg_type="phys"' in bsrc)
    check("技能魔法显式 magi", 'dmg_type="magi"' in bsrc)
    check("普攻显式 phys", 'dmg_type="phys")' in bsrc)
    check("吸血真伤跳过", 'dmg_type == "true"' in bsrc)

    print()
    print(f"===== v107 伤害类型测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
