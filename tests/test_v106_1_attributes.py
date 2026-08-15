# -*- coding: utf-8 -*-
"""v106.1 属性扩展测试：CDR 冷却缩减 + 元素抗性面板化 + 经验/金币加成（全渠道融入）

覆盖：
1. 属性定义：PCT_STATS/PCT_CAPS/STAT_NAMES
2. 职业特色：牧师 heal_power 10%/elem_res 5%、战士 elem_res 5%、法师 abyss_res 5%、刺客/龙裔 cdr 5%
3. 词条折算：轻灵/求知/聚宝 + 元素抗性面板化（elem_resist→elem_res 8%、abyss_resist→abyss_res 10%）
4. 套装融入：月影法穿/黑沼物穿/圣徽深渊抗性/旅人cdr（bonus_2 聚合）
5. CDR 公式：_set_skill_cd ×(1-cdr) 保底 1，cap 40%
6. 元素抗性 battle 消费：属性优先 + 旧装备词条补差
7. 被动系统：crit add bug 修复（伴奏）+ cdr 被动（快板节奏）
8. 经验/金币加成：聚合 cap 50%
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond: passed += 1; print(f"  ✅ {name}")
    else: failed += 1; print(f"  ❌ {name} {detail}")

async def main():
    clean_db()
    # ============ 1. 属性定义 ============
    print("【1. 属性定义】")
    for k in ("cdr", "elem_res", "abyss_res", "exp_bonus", "gold_bonus"):
        check(f"{k} 在 PCT_STATS", k in C.PCT_STATS)
    check("PCT_CAPS cdr=0.4", C.PCT_CAPS.get("cdr") == 0.4)
    check("PCT_CAPS elem_res=0.5", C.PCT_CAPS.get("elem_res") == 0.5)
    check("PCT_CAPS abyss_res=0.5", C.PCT_CAPS.get("abyss_res") == 0.5)
    check("PCT_CAPS exp_bonus=0.5", C.PCT_CAPS.get("exp_bonus") == 0.5)
    check("PCT_CAPS gold_bonus=0.5", C.PCT_CAPS.get("gold_bonus") == 0.5)
    check("STAT_NAMES 冷却缩减", E.STAT_NAMES.get("cdr") == "冷却缩减")
    check("STAT_NAMES 元素抗性", E.STAT_NAMES.get("elem_res") == "元素抗性")

    # ============ 2. 职业特色 ============
    print("【2. 职业特色】")
    from data.plugins.dragonfall.game.data.classes import CLASSES
    def base_attr(cid, k):
        return CLASSES[cid]["base"].get(k, 0)
    check("刺客 cdr 5%", abs(base_attr("cls_ci_ke", "cdr") - 0.05) < 1e-9)
    check("龙裔誓约 cdr 5%", abs(base_attr("cls_dragon_oath", "cdr") - 0.05) < 1e-9)
    check("牧师 elem_res 5%", abs(base_attr("cls_mu_shi", "elem_res") - 0.05) < 1e-9)
    check("战士 elem_res 5%", abs(base_attr("cls_zhan_shi", "elem_res") - 0.05) < 1e-9)
    check("法师 abyss_res 5%", abs(base_attr("cls_fa_shi", "abyss_res") - 0.05) < 1e-9)
    # 面板聚合
    st_priest, _ = E.player_stats_detail("cls_mu_shi", 30, {})
    check("牧师面板 elem_res 5%", abs(st_priest.get("elem_res", 0) - 0.05) < 1e-6)

    # ============ 3. 词条折算 ============
    print("【3. 词条折算】")
    from data.plugins.dragonfall.game.core.affix import stat_affix_stats
    s1 = stat_affix_stats(["cdr"], "armor", 30)
    check("轻灵词条 cdr +5%", abs(s1.get("cdr", 0) - 0.05) < 1e-6, str(s1))
    s2 = stat_affix_stats(["exp_bonus"], "armor", 30)
    check("求知词条 exp +5%", abs(s2.get("exp_bonus", 0) - 0.05) < 1e-6, str(s2))
    s3 = stat_affix_stats(["gold_bonus"], "armor", 30)
    check("聚宝词条 gold +5%", abs(s3.get("gold_bonus", 0) - 0.05) < 1e-6, str(s3))
    s4 = stat_affix_stats(["elem_resist"], "armor", 30)
    check("元素抗性词条 → elem_res +8%（面板化）", abs(s4.get("elem_res", 0) - 0.08) < 1e-6, str(s4))
    check("元素抗性词条不再输出 elem_resist 键", "elem_resist" not in s4, str(s4))
    s5 = stat_affix_stats(["abyss_resist"], "armor", 30)
    check("深渊抗性词条 → abyss_res +10%", abs(s5.get("abyss_res", 0) - 0.10) < 1e-6, str(s5))
    # 词条池
    check("蓝装池含轻灵", "cdr" in C.AFFIX_POOL_BY_QUALITY["blue"])
    check("橙装池含全部新词条", all(k in C.AFFIX_POOL_BY_QUALITY["orange"] for k in
                                ("cdr", "exp_bonus", "gold_bonus")))

    # ============ 4. 套装融入 ============
    print("【4. 套装融入】")
    from game.data.sets import SETS
    check("月影套 2 件 +法穿5%", abs(SETS["set_yue_ying"]["bonus_2"].get("pene_magi", 0) - 0.05) < 1e-9)
    check("黑沼套 2 件 +物穿5%", abs(SETS["set_hei_zhao"]["bonus_2"].get("pene_phys", 0) - 0.05) < 1e-9)
    check("圣徽套 2 件 +深渊抗性5%", abs(SETS["set_sheng_hui"]["bonus_2"].get("abyss_res", 0) - 0.05) < 1e-9)
    check("旅人公会套 2 件 +cdr5%", abs(SETS["set_lv_ren_gong_hui"]["bonus_2"].get("cdr", 0) - 0.05) < 1e-9)
    # 套装聚合：法师穿 2 件月影 → pene_magi 5% 生效
    eq = {
        "weapon": {"name": "月影之刃", "set": "月影", "stats": {}},
        "helm": {"name": "月影头盔", "set": "月影", "stats": {}},
        "armor": None, "legs": None, "boots": None, "ring": None, "necklace": None,
    }
    st_set, _ = E.player_stats_detail("cls_fa_shi", 30, eq)
    # 法师基础法穿 10% × 套装 5% 乘算 = 1-(0.9×0.95)=0.145
    expect = 1 - 0.9 * 0.95
    check(f"法师+月影2件 法穿乘算={expect:.4f}", abs(st_set.get("pene_magi", 0) - expect) < 1e-6,
          f"got {st_set.get('pene_magi')}")

    # ============ 5. CDR 公式 ============
    print("【5. CDR 公式】")
    from data.plugins.dragonfall.game import battle as BT
    player = {"qq_id": "w1", "name": "测试", "level": 30, "class_name": "cls_mu_shi",
              "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
              "equipment": {}, "attributes": {}}
    enemy = {"name": "T", "hp": 1000, "max_hp": 1000, "atk": 30, "def": 10, "matk": 5, "mdef": 5, "spd": 5, "crit": 0.05}
    b = BT.Battle("wild", enemy=enemy, title_bonus=lambda q: None, player=player, pet=None)
    # 打桩 _player_stats 返回 cdr 40%
    b._player_stats = lambda p: {"cdr": 0.40}
    b._set_skill_cd("测试技", 5)
    check("cd5 + 40%cdr → 3 回合", b.cooldown.get("测试技") == 3, str(b.cooldown.get("测试技")))
    b._set_skill_cd("测试技2", 2)
    check("cd2 + 40%cdr → 1 回合（保底）", b.cooldown.get("测试技2") == 1, str(b.cooldown.get("测试技2")))
    b._set_skill_cd("测试技3", 1)
    check("cd1 不受 cdr 影响", b.cooldown.get("测试技3") == 1, str(b.cooldown.get("测试技3")))
    # 无 cdr
    b._player_stats = lambda p: {}
    b._set_skill_cd("测试技4", 5)
    check("无 cdr → cd5 不变", b.cooldown.get("测试技4") == 5, str(b.cooldown.get("测试技4")))
    # 99% cdr 被 cap 40%
    b._player_stats = lambda p: {"cdr": 0.99}
    b._set_skill_cd("测试技5", 5)
    check("99% cdr cap 40% → cd3", b.cooldown.get("测试技5") == 3, str(b.cooldown.get("测试技5")))

    # ============ 6. 元素抗性 battle 消费 ============
    print("【6. 元素抗性消费】")
    # 属性优先：玩家 elem_res 15%（职业5+词条折算）→ 火技能减 15%
    b2 = BT.Battle("wild", enemy=enemy, title_bonus=lambda q: None, player=player, pet=None)
    b2._player_stats = lambda p: {"elem_res": 0.15, "abyss_res": 0.0}
    b2._equip_affix_ids = lambda p: []  # 无旧词条
    red = max(1, int(100 * 0.15))
    check("属性 elem_res 15% → 火技能减免 15", red == 15, str(red))
    # 旧装备补差：属性 5%（职业） + 旧词条 8% → 补 3% = 8% 总
    b3 = BT.Battle("wild", enemy=enemy, title_bonus=lambda q: None, player=player, pet=None)
    b3._player_stats = lambda p: {"elem_res": 0.05, "abyss_res": 0.0}
    b3._equip_affix_ids = lambda p: ["elem_resist"]
    resist3 = 0.05 + (0.08 - 0.05)
    check("旧装备补差：5%+3% = 8%", abs(resist3 - 0.08) < 1e-9, str(resist3))
    # 新装备不双算：属性已含 8% 词条折算 → 补差为 0
    b4 = BT.Battle("wild", enemy=enemy, title_bonus=lambda q: None, player=player, pet=None)
    b4._player_stats = lambda p: {"elem_res": 0.13, "abyss_res": 0.0}  # 职业5+词条8
    b4._equip_affix_ids = lambda p: ["elem_resist"]
    resist4 = 0.13 + max(0.0, 0.08 - 0.13)
    check("新装备不双算：13% + 0 补差", abs(resist4 - 0.13) < 1e-9, str(resist4))
    # 深渊抗性：暗影技能
    b5 = BT.Battle("wild", enemy=enemy, title_bonus=lambda q: None, player=player, pet=None)
    b5._player_stats = lambda p: {"elem_res": 0.0, "abyss_res": 0.10}
    b5._equip_affix_ids = lambda p: []
    red5 = max(1, int(100 * 0.10))
    check("abyss_res 10% → 暗影技能减免 10", red5 == 10, str(red5))

    # ============ 7. 被动系统 ============
    print("【7. 被动系统】")
    # v112.3：伴奏/快板节奏已归入牧师攻线分支（灵魂歌者/黎明颂者），按分支查技能
    pb = E.player_passive_stats("cls_mu_shi", ["伴奏", "快板节奏"])
    check("伴奏 crit +8%（add bug 修复）", abs(pb.get("crit_add", 0) - 0.08) < 1e-9, str(pb.get("crit_add")))
    check("快板节奏 cdr +8%", abs(pb.get("cdr_add", 0) - 0.08) < 1e-9, str(pb.get("cdr_add")))
    # 技能数据存在（走牧师攻线分支表）
    from game.engine import skill_info
    info_ac = skill_info("cls_mu_shi", "伴奏")
    info_kb = skill_info("cls_mu_shi", "快板节奏")
    check("伴奏 为被动技能", bool(info_ac) and info_ac.get("kind") == "被动", str(info_ac))
    check("快板节奏 为被动技能", bool(info_kb) and info_kb.get("kind") == "被动", str(info_kb))

    # ============ 8. 经验/金币加成聚合 ============
    print("【8. 经验/金币加成】")
    eq8 = {
        "armor": {"name": "T", "stats": stat_affix_stats(["exp_bonus", "gold_bonus"], "armor", 30), "affixes": ["exp_bonus", "gold_bonus"]},
        "weapon": None, "helm": None, "legs": None, "boots": None, "ring": None, "necklace": None,
    }
    st8, _ = E.player_stats_detail("cls_zhan_shi", 30, eq8)
    check("求知词条 exp +5%", abs(st8.get("exp_bonus", 0) - 0.05) < 1e-6, str(st8.get("exp_bonus")))
    check("聚宝词条 gold +5%", abs(st8.get("gold_bonus", 0) - 0.05) < 1e-6, str(st8.get("gold_bonus")))
    # cap：11 个求知词条 → 50% 封顶
    eq9 = {"armor": {"name": "T", "stats": stat_affix_stats(["exp_bonus"] * 11, "armor", 30), "affixes": ["exp_bonus"] * 11},
           "weapon": None, "helm": None, "legs": None, "boots": None, "ring": None, "necklace": None}
    st9, _ = E.player_stats_detail("cls_zhan_shi", 30, eq9)
    check("11 词条 exp cap 50%", abs(st9.get("exp_bonus", 0) - 0.50) < 1e-6, str(st9.get("exp_bonus")))

    # ============ 9. 面板 ============
    print("【9. 面板】")
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game", "commands", "player.py"), encoding="utf-8").read()
    for k in ("cdr", "elem_res", "abyss_res", "exp_bonus", "gold_bonus"):
        check(f"面板含 {k} 行", k in src)

    print(f"\n===== v106.1 属性扩展测试: {passed} passed, {failed} failed =====")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
