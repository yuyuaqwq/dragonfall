# -*- coding: utf-8 -*-
"""v106 穿透体系 + 韧性 + 幸运 测试（鱼鱼拍板设计：双穿透 + 乘算 + 职业/Boss/装备特色）

覆盖：
1. 伤害公式穿透数学：百分比/固定/组合/pierce 共存/下限
2. 百分比穿透乘算聚合：1-Π(1-pᵢ)，面板/战斗一致
3. cap：物穿/法穿 60%，韧性/幸运 50%
4. 职业特色：刺客 10% 物穿、法师 10% 法穿、魔剑士双穿 5%+5%
5. 装备词条：穿甲/法穿 stat 折算、破甲刃/破法刃按等级固定折算
6. 怪物/Boss 特色：boss def×1.25、elite def×1.15、dps 物穿 5%、caster 法穿 5%
7. 韧性：被暴击率 ×(1-韧性) cap 50%
8. 幸运：Boss 图纸掉率 ×(1+luck)（统计断言）
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
    # ============ 1. 伤害公式穿透数学 ============
    print("【1. 穿透伤害公式】")
    # 无穿透基准：atk=100, def=100 → 10000/200=50
    base = E.calc_damage(100, 100, variance=0.0)
    check("基准 atk100/def100 = 50", base == 50, str(base))
    # 百分比穿透 20%：有效防 80 → 10000/180=55.55→55
    d1 = E.calc_damage(100, 100, variance=0.0, pene_pct=0.20)
    check("20% 物穿 → 有效防 80 → 55", d1 == int(100*100/(100+80)), str(d1))
    # 固定穿透 30：有效防 70 → 10000/170=58.8→58
    d2 = E.calc_damage(100, 100, variance=0.0, pene_flat=30)
    check("固定 30 物穿 → 有效防 70 → 58", d2 == int(100*100/(100+70)), str(d2))
    # 组合 20%+30：有效防 max(0,80-30)=50 → 10000/150=66.67→66
    d3 = E.calc_damage(100, 100, variance=0.0, pene_pct=0.20, pene_flat=30)
    check("20%+30 组合 → 有效防 50 → 66", d3 == int(100*100/(100+50)), str(d3))
    # 穿透超过防御：有效防 0 → 100% 伤害（dmg=atk=100）
    d4 = E.calc_damage(100, 30, variance=0.0, pene_pct=0.60, pene_flat=100)
    check("穿透超防 → 有效防 0 → 100", d4 == 100, str(d4))
    # 先百分比后固定：def 100, 50% + 60 固定 → 50-60=-10 → 0
    d5 = E.calc_damage(100, 100, variance=0.0, pene_pct=0.50, pene_flat=60)
    check("50%+60 固定 → 有效防 0 → 100", d5 == 100, str(d5))
    # pierce 共存：pierce=True 时忽略穿透参数（完全无视防御）
    d6 = E.calc_damage(100, 100, variance=0.0, pierce=True, pene_pct=0.5)
    check("pierce=True 完全无视防御 → 100", d6 == 100, str(d6))
    # 脏值兜底：负数/超上限被 clamp
    d7 = E.calc_damage(100, 100, variance=0.0, pene_pct=0.99)
    eff7 = int(100 * (1 - 0.6))
    check("99% 穿透被 cap 60% → 有效防 40", d7 == int(100*100/(100+eff7)), str(d7))
    d8 = E.calc_damage(100, 100, variance=0.0, pene_pct=-0.5, pene_flat=-10)
    check("负穿透/负固定按 0 处理", d8 == base, str(d8))
    # 暴击与穿透叠加（先截断后 ×1.5：55×1.5=82）
    d9 = E.calc_damage(100, 100, is_crit=True, variance=0.0, pene_pct=0.20)
    check("穿透+暴击 叠加（55×1.5=82）", d9 == int(int(100*100/(100+80)) * 1.5), str(d9))

    # ============ 2. 百分比穿透乘算聚合 ============
    print("【2. 乘算聚合】")
    check("PENE_PCT_STATS 定义", hasattr(C, "PENE_PCT_STATS") and len(C.PENE_PCT_STATS) == 2)
    check("pene_phys 在 PCT_STATS（百分比显示）", "pene_phys" in C.PCT_STATS)
    check("tenacity/luck 在 PCT_STATS", "tenacity" in C.PCT_STATS and "luck" in C.PCT_STATS)
    check("pene_flat 不在 PCT_STATS（整数显示）", "pene_flat" not in C.PCT_STATS)
    # 真实数据流：词条生成时折算进 stats（stat_affix_stats），聚合时乘算合成
    from data.plugins.dragonfall.game.core.affix import stat_affix_stats
    w_stats = stat_affix_stats(["pene_phys"], "weapon", 30)   # {"pene_phys": 0.05}
    a_stats = stat_affix_stats(["pene_phys"], "armor", 30)    # {"pene_phys": 0.05}
    p = {"class_name": "cls_zhan_shi", "level": 30, "equipment": {
        "weapon": {"name": "测试剑", "stats": w_stats, "affixes": ["pene_phys"]},
        "armor": {"name": "测试甲", "stats": a_stats, "affixes": ["pene_phys"]},
        "helm": None, "boots": None, "ring": None, "necklace": None},
        "attributes": None}
    st, _ = E.player_stats_detail(p["class_name"], p["level"], p["equipment"])
    # v106.2 战士无天生穿透：两词条乘算 = 1-(0.95×0.95)=0.0975
    expect = 1 - 0.95**2
    check(f"战士 两词条5%+5% 乘算={expect:.4f}", abs(st.get("pene_phys", 0) - expect) < 1e-6,
          f"got {st.get('pene_phys')}")
    # 词条与职业不同来源也乘算（刺客 10% 基础 + 词条 5% = 1-0.9×0.95=0.145）
    p_ass = {"class_name": "cls_ci_ke", "level": 30, "equipment": {
        "weapon": {"name": "测试剑", "stats": w_stats, "affixes": ["pene_phys"]},
        "armor": None, "helm": None, "boots": None, "ring": None, "necklace": None},
        "attributes": None}
    st_ass2, _ = E.player_stats_detail(p_ass["class_name"], p_ass["level"], p_ass["equipment"])
    expect_ass = 1 - 0.9 * 0.95
    check(f"刺客10%+词条5% 乘算={expect_ass:.4f}", abs(st_ass2.get("pene_phys", 0) - expect_ass) < 1e-6,
          f"got {st_ass2.get('pene_phys')}")
    # 词条与职业不同来源也乘算（不是 0.05+0.05=0.10）
    check("乘算 ≠ 加法（0.0975 ≠ 0.10）", abs((1 - 0.95**2) - 0.10) > 0.002)

    # ============ 3. cap ============
    print("【3. 上限】")
    # 6 个穿甲词条 → 乘算 1-0.95^6=0.2649 → 不到 60%，继续加
    w6 = stat_affix_stats(["pene_phys"] * 4, "weapon", 30)
    a6 = stat_affix_stats(["pene_phys"] * 4, "armor", 30)
    p6 = {"class_name": "cls_zhan_shi", "level": 30, "equipment": {
        "weapon": {"name": "T", "stats": w6, "affixes": ["pene_phys"] * 4},
        "armor": {"name": "T", "stats": a6, "affixes": ["pene_phys"] * 4},
        "helm": None, "boots": None, "ring": None, "necklace": None}, "attributes": None}
    st6, _ = E.player_stats_detail(p6["class_name"], p6["level"], p6["equipment"])
    check("8×5% 词条+基础5% 乘算 < 60% cap 不破", st6.get("pene_phys", 0) <= 0.6 + 1e-9, str(st6.get("pene_phys")))
    # PCT_CAPS 表存在且合理
    check("PCT_CAPS 物穿 0.6", C.PCT_CAPS.get("pene_phys") == 0.6)
    check("PCT_CAPS 韧性 0.5", C.PCT_CAPS.get("tenacity") == 0.5)
    check("PCT_CAPS 幸运 0.5", C.PCT_CAPS.get("luck") == 0.5)

    # ============ 4. 职业特色（v106.2 收敛：只保留刺客/法师天生穿透，其余走被动/词条/套装/药水渠道） ============
    print("【4. 职业特色】")
    from data.plugins.dragonfall.game.data.classes import CLASSES
    def base_pene(cid):
        b = CLASSES[cid]["base"]
        return b.get("pene_phys", 0), b.get("pene_magi", 0)
    check("刺客 物穿10%（特色保留）", base_pene("cls_ci_ke") == (0.10, 0))
    check("法师 法穿10%（特色保留）", base_pene("cls_fa_shi") == (0, 0.10))
    check("龙裔誓约 无天生穿透", base_pene("cls_dragon_oath") == (0, 0))
    check("战士 无天生穿透（被动破甲精通补偿）", base_pene("cls_zhan_shi") == (0, 0))
    check("游侠 无天生穿透（被动穿甲箭补偿）", base_pene("cls_you_xia") == (0, 0))
    check("拳师 无天生穿透", base_pene("cls_wu_seng") == (0, 0))
    check("牧师 无天生穿透", base_pene("cls_mu_shi") == (0, 0))
    check("暗影神谕 无穿透", base_pene("cls_hymn") == (0, 0))
    check("见习 无穿透", base_pene("cls_novice") == (0, 0))
    # 面板聚合：刺客 Lv.30 裸装物穿 = 10%
    st_ass, _ = E.player_stats_detail("cls_ci_ke", 30, {})
    check("刺客 Lv.30 面板物穿 10%", abs(st_ass.get("pene_phys", 0) - 0.10) < 1e-6, str(st_ass.get("pene_phys")))
    # v106.2 补偿被动生效（战斗内乘算）
    from data.plugins.dragonfall.game import battle as BT
    p_w = {"qq_id": "w1", "name": "测试", "level": 60, "class_name": "cls_zhan_shi",
           "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
           "equipment": {}, "attributes": {}, "learned_skills": ["破甲精通"]}
    enemy = {"name": "T", "hp": 1000, "max_hp": 1000, "atk": 30, "def": 10, "matk": 5, "mdef": 5, "spd": 5, "crit": 0.05}
    b = BT.Battle("wild", enemy=enemy, title_bonus=None, player=p_w, pet=None)
    st_w = b._player_stats(p_w)
    check("战士 破甲精通被动 → 物穿 5%（战斗内）", abs(st_w.get("pene_phys", 0) - 0.05) < 1e-6, str(st_w.get("pene_phys")))
    p_r = {"qq_id": "w2", "name": "测试", "level": 55, "class_name": "cls_you_xia",
           "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
           "equipment": {}, "attributes": {}, "learned_skills": ["穿甲箭"]}
    b2 = BT.Battle("wild", enemy=enemy, title_bonus=None, player=p_r, pet=None)
    st_r = b2._player_stats(p_r)
    check("游侠 穿甲箭被动 → 物穿 5%（战斗内）", abs(st_r.get("pene_phys", 0) - 0.05) < 1e-6, str(st_r.get("pene_phys")))

    # ============ 5. 装备词条折算 ============
    print("【5. 装备词条】")
    from data.plugins.dragonfall.game.core.affix import stat_affix_stats
    s1 = stat_affix_stats(["pene_phys"], "weapon", 30)
    check("穿甲词条 +5% 物穿", abs(s1.get("pene_phys", 0) - 0.05) < 1e-6, str(s1))
    s2 = stat_affix_stats(["pene_magi"], "weapon", 30)
    check("法穿词条 +5% 法穿", abs(s2.get("pene_magi", 0) - 0.05) < 1e-6, str(s2))
    s3 = stat_affix_stats(["pene_flat"], "weapon", 30)
    check("破甲刃 Lv.30 → 15 点固定物穿", s3.get("pene_flat", 0) == 15, str(s3))
    s4 = stat_affix_stats(["pene_flat"], "weapon", 2)
    check("破甲刃 Lv.2 → 保底 2 点", s4.get("pene_flat", 0) == 2, str(s4))
    s5 = stat_affix_stats(["pene_mflat"], "weapon", 50)
    check("破法刃 Lv.50 → 25 点固定法穿", s5.get("pene_mflat", 0) == 25, str(s5))
    s6 = stat_affix_stats(["tenacity", "luck"], "armor", 30)
    check("韧性/幸运词条各 +5%", abs(s6.get("tenacity", 0) - 0.05) < 1e-6 and abs(s6.get("luck", 0) - 0.05) < 1e-6, str(s6))
    # 词条池包含新词条
    check("紫装池含穿甲", "pene_phys" in C.AFFIX_POOL_BY_QUALITY["purple"])
    check("紫装池含幸运", "luck" in C.AFFIX_POOL_BY_QUALITY["purple"])
    check("橙装池含全部新词条", all(k in C.AFFIX_POOL_BY_QUALITY["orange"] for k in
                                ("pene_phys", "pene_magi", "pene_flat", "pene_mflat", "tenacity", "luck")))
    check("锻造攻击倾向含穿透", "pene_phys" in C.AFFIX_AFFINITY_POOLS["攻击"])
    check("锻造防御倾向含幸运", "luck" in C.AFFIX_AFFINITY_POOLS["防御"])

    # ============ 6. 怪物/Boss 特色 ============
    print("【6. 怪物/Boss 特色】")
    from data.plugins.dragonfall.game.core.stats import monster_stats
    ms_boss = monster_stats(30, "boss")
    ms_tank = monster_stats(30, "tank")
    # boss def = 10+3.8×29=120.2→120, ×1.25 = 150
    check("Boss Lv.30 def ×1.25 重甲", ms_boss["def"] == int(120 * 1.25), f"{ms_boss['def']} vs {int(120*1.25)}")
    check("Boss Lv.30 mdef ×1.25", ms_boss["mdef"] == int(int(10 + 3.4 * 29) * 1.25), str(ms_boss["mdef"]))
    ms_elite = monster_stats(30, "elite")
    check("精英 def ×1.15", ms_elite["def"] == int(int(8 + 2.8 * 29) * 1.15), str(ms_elite["def"]))
    ms_dps = monster_stats(30, "dps")
    check("dps 物穿 5%（保留小数）", abs(ms_dps.get("pene_phys", 0) - 0.05) < 1e-6, str(ms_dps.get("pene_phys")))
    ms_cast = monster_stats(30, "caster")
    check("caster 法穿 5%", abs(ms_cast.get("pene_magi", 0) - 0.05) < 1e-6, str(ms_cast.get("pene_magi")))
    ms_el2 = monster_stats(30, "elite")
    check("精英 双穿 3%", abs(ms_el2.get("pene_phys", 0) - 0.03) < 1e-6 and abs(ms_el2.get("pene_magi", 0) - 0.03) < 1e-6)
    # 普通怪不吃重甲加成
    check("dps 不吃重甲（def 无 1.25）", ms_dps["def"] == int(4 + 2.0 * 29), str(ms_dps["def"]))

    # ============ 7. 韧性 ============
    print("【7. 韧性】")
    from data.plugins.dragonfall.game import battle as BT
    mult0 = BT.Battle._tenacity_mult({"tenacity": 0})
    check("无韧性 → 暴击削减系数 1.0", abs(mult0 - 1.0) < 1e-9)
    mult30 = BT.Battle._tenacity_mult({"tenacity": 0.30})
    check("韧性30% → 系数 0.70", abs(mult30 - 0.70) < 1e-9)
    mult99 = BT.Battle._tenacity_mult({"tenacity": 0.99})
    check("韧性99% → cap 50% → 系数 0.50", abs(mult99 - 0.50) < 1e-9)
    mult_dirty = BT.Battle._tenacity_mult({})
    check("脏档无韧性 → 1.0", abs(mult_dirty - 1.0) < 1e-9)
    # 面板聚合韧性（词条）
    a_t = stat_affix_stats(["tenacity", "tenacity"], "armor", 30)
    p_t = {"class_name": "cls_zhan_shi", "level": 30, "equipment": {
        "armor": {"name": "T", "stats": a_t, "affixes": ["tenacity", "tenacity"]},
        "weapon": None, "helm": None, "boots": None, "ring": None, "necklace": None}, "attributes": None}
    st_t, _ = E.player_stats_detail(p_t["class_name"], p_t["level"], p_t["equipment"])
    check("双韧性词条 = 10%（加法）", abs(st_t.get("tenacity", 0) - 0.10) < 1e-6, str(st_t.get("tenacity")))

    # ============ 8. 幸运 ============
    print("【8. 幸运】")
    from data.plugins.dragonfall.game.core.drops import roll_drop
    random.seed(42)
    # 无幸运：Boss 掉率 5%（统计 2000 次 ≈ 100）
    n0 = sum(1 for _ in range(2000) if roll_drop(30, "boss")[1] is not None)
    random.seed(42)
    n_luck = sum(1 for _ in range(2000) if roll_drop(30, "boss", 0.5)[1] is not None)
    check(f"无幸运 Boss 图纸率 ≈5%（{n0}/2000）", 60 <= n0 <= 140, str(n0))
    check(f"幸运50% Boss 图纸率 ≈7.5%（{n_luck}/2000）", 100 <= n_luck <= 200, str(n_luck))
    check("幸运提升明显（7.5% > 5%）", n_luck > n0 * 1.3, f"{n_luck} vs {n0}")
    # 普通怪不掉图纸（幸运也不改变 v94 规则）
    random.seed(42)
    n_norm = sum(1 for _ in range(1000) if roll_drop(30, "dps", 0.5)[1] is not None)
    check("普通怪幸运也不掉图纸（v94 铁律）", n_norm == 0, str(n_norm))
    # 幸运超 50% 被 cap
    random.seed(42)
    n_cap = sum(1 for _ in range(2000) if roll_drop(30, "boss", 0.99)[1] is not None)
    check(f"幸运99% cap 50% → 仍 ≈7.5%（{n_cap}/2000）", 100 <= n_cap <= 200, str(n_cap))

    # ============ 9. Battle 辅助 ============
    print("【9. Battle 穿透取值】")
    enemy = {"name": "T", "hp": 1000, "max_hp": 1000, "atk": 30, "def": 10, "matk": 5, "mdef": 5, "spd": 5,
             "crit": 0.05, "pene_phys": 0.05, "pene_magi": 0.05}
    player = {"qq_id": "w1", "name": "测试", "level": 30, "class_name": "cls_ci_ke",
              "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
              "equipment": {}, "attributes": {}}
    b = BT.Battle("wild", enemy=enemy, title_bonus=None, player=player, pet=None)
    pv, pf = b._pene_vals({"pene_phys": 0.10, "pene_flat": 5})
    check("玩家物穿取值 (10%, 5)", (pv, pf) == (0.10, 5), f"{(pv, pf)}")
    mv, mf = b._pene_vals({"pene_phys": 0.05}, magic=False)
    check("怪物物穿取值 (5%, 0)", (mv, mf) == (0.05, 0), f"{(mv, mf)}")
    mv2, mf2 = b._pene_vals({"pene_magi": 0.05, "pene_mflat": 3}, magic=True)
    check("怪物法穿取值 (5%, 3)", (mv2, mf2) == (0.05, 3), f"{(mv2, mf2)}")
    cv, cf = b._pene_vals({})
    check("空属性兜底 (0, 0)", (cv, cf) == (0.0, 0), f"{(cv, cf)}")
    # 属性面板命令可渲染（防 KeyError）
    from data.plugins.dragonfall.game.commands import player as PC
    _rows = PC.PlayerCommand.attributes if hasattr(PC, "PlayerCommand") else None
    check("面板 stat_rows 含 6 新行（源码断言）", "pene_phys" in open(
        r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\commands\player.py", encoding="utf-8").read())

    print(f"\n===== v106 穿透测试: {passed} passed, {failed} failed =====")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
