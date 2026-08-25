# -*- coding: utf-8 -*-
"""v106.2 职业特色收敛 + 种族天赋调整 + 治疗/护盾强度测试

覆盖：
1. 穿透职业特色收敛：仅刺客/法师天生穿透，其余职业归零（被动/词条/套装/药水渠道补偿）
2. 补偿被动：破甲精通/穿甲箭/魔力贯穿 战斗内生效（乘算）
3. 穿透药水：穿甲药剂/破法药剂 +15% 乘算合成
4. 种族天赋调整：人类勤学 exp_bonus 5%、半身人幸运儿 luck 10%（引擎结算支持新属性）
5. 治疗强度 heal_power：牧师 10%（v112.3：吟游诗人回归牧师攻线，无独立职业）、词条/套装、_skill_heal 消费
6. 护盾强度 shield_power：战士 5%、词条/套装、_add_shield 消费
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
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.data.classes import CLASSES
    from data.plugins.dragonfall.game.data.races import RACES
    from data.plugins.dragonfall.game.data.skills import PLAYER_SKILLS
    from data.plugins.dragonfall.game.core.affix import stat_affix_stats

    # ============ 1. 穿透职业收敛 ============
    print("【1. 穿透职业收敛】")
    def base_pene(cid):
        b = CLASSES[cid]["base"]
        return b.get("pene_phys", 0), b.get("pene_magi", 0)
    check("刺客 10% 物穿（唯一物理特色）", base_pene("cls_ci_ke") == (0.10, 0))
    check("法师 10% 法穿（唯一法系特色）", base_pene("cls_fa_shi") == (0, 0.10))
    # v112.5：隐藏线中时咒(法穿15%)/暮影(物穿15%)为穿透职业，其余线无天生穿透
    for cid in ("cls_zhan_shi", "cls_you_xia", "cls_mu_shi", "cls_wu_seng",
                "cls_dragon_oath", "cls_wild_hunter", "cls_hymn", "cls_wu_sheng", "cls_novice"):
        check(f"{CLASSES[cid]['name']} 无天生穿透", base_pene(cid) == (0, 0))
    check("时咒法师 15% 法穿（隐藏线特色）", base_pene("cls_chronomancer") == (0, 0.15))
    check("暮影行者 15% 物穿（隐藏线特色）", base_pene("cls_shadow_blade") == (0.15, 0))

    # ============ 2. 补偿被动 ============
    print("【2. 补偿被动】")
    enemy = {"name": "T", "hp": 1000, "max_hp": 1000, "atk": 30, "def": 10, "matk": 5, "mdef": 5, "spd": 5, "crit": 0.05}
    def btl(cls, skills):
        p = {"qq_id": "w", "name": "T", "level": 90, "class_name": cls,
             "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
             "equipment": {}, "attributes": {}, "learned_skills": skills}
        return BT.Battle("wild", enemy=enemy, title_bonus=None, player=p, pet=None), p
    b, p = btl("cls_zhan_shi", ["破甲精通"])
    check("破甲精通 → 物穿 5%", abs(b._player_stats(p).get("pene_phys", 0) - 0.05) < 1e-6,
          str(b._player_stats(p).get("pene_phys")))
    b, p = btl("cls_you_xia", ["穿甲箭"])
    check("穿甲箭 → 物穿 5%", abs(b._player_stats(p).get("pene_phys", 0) - 0.05) < 1e-6)
    # v130.2f 设计变更：魔力贯穿由法穿+5% 属性被动 → attack_res 节拍器（施法命中+1 时之沙，§14.3）
    # 时咒基础法穿 15% 不再叠加 5% → pene_magi = 0.15
    b, p = btl("cls_chronomancer", ["魔力贯穿"])
    check("魔力贯穿改版后法穿=基础 15%（不再乘算 5%）",
          abs(b._player_stats(p).get("pene_magi", 0) - 0.15) < 1e-6,
          str(b._player_stats(p).get("pene_magi")))
    b, p = btl("cls_zhan_shi", [])
    check("无被动 → 物穿 0", abs(b._player_stats(p).get("pene_phys", 0) - 0.0) < 1e-6)
    # 被动+词条乘算：刺客 10% + 词条 5% + 无被动
    names = {s.get("name") for s in PLAYER_SKILLS["cls_zhan_shi"]["skills"].values()}
    check("战士技能树含 破甲精通", "破甲精通" in names)
    names2 = {s.get("name") for s in PLAYER_SKILLS["cls_you_xia"]["skills"].values()}
    check("游侠技能树含 穿甲箭", "穿甲箭" in names2)
    names3 = {s.get("name") for s in PLAYER_SKILLS["cls_chronomancer"]["skills"].values()}
    check("时咒线级基础含 魔力贯穿", "魔力贯穿" in names3)

    # ============ 3. 穿透药水 ============
    print("【3. 穿透药水】")
    from data.plugins.dragonfall.game.data.items import ITEMS
    check("穿甲药剂存在", any(v.get("effect") == "pene_pot" for v in ITEMS.values()))
    check("破法药剂存在", any(v.get("effect") == "pene_magi_pot" for v in ITEMS.values()))
    b, p = btl("cls_zhan_shi", ["破甲精通"])  # 5% 基础
    b.p_buffs["pene_pot"] = 3
    pp, _pf = b._pene_vals({"pene_phys": 0.05})
    expect = 1 - 0.95 * 0.85
    check(f"药水+15% 与属性乘算 ={expect:.4f}", abs(pp - expect) < 1e-6, f"got {pp}")
    b.p_buffs = {}
    pp2, _ = b._pene_vals({"pene_phys": 0.05})
    check("无药水 → 5%", abs(pp2 - 0.05) < 1e-6)
    # 药水 cap：60% + 药水 → 仍 ≤60%
    b.p_buffs["pene_pot"] = 3
    pp3, _ = b._pene_vals({"pene_phys": 0.60})
    check("药水叠加 cap 60%", pp3 <= 0.6 + 1e-9, str(pp3))

    # ============ 4. 种族天赋调整 ============
    print("【4. 种族天赋】")
    check("人类 exp_bonus 5%（勤学）", abs(RACES["human"]["talents"].get("exp_bonus", 0) - 0.05) < 1e-9)
    check("人类不再有 heal_received", "heal_received" not in RACES["human"]["talents"])
    check("半身人 luck 10%（幸运儿）", abs(RACES["halfling"]["talents"].get("luck", 0) - 0.10) < 1e-9)
    check("半身人不再有 gold_bonus", "gold_bonus" not in RACES["halfling"]["talents"])
    # 面板聚合：人类 exp_bonus 5%、半身人 luck 10%
    st_h, _ = E.player_stats_detail("cls_zhan_shi", 30, {}, race="human")
    check("人类面板 exp_bonus 5%", abs(st_h.get("exp_bonus", 0) - 0.05) < 1e-6, str(st_h.get("exp_bonus")))
    st_hl, _ = E.player_stats_detail("cls_zhan_shi", 30, {}, race="halfling")
    check("半身人面板 luck 10%", abs(st_hl.get("luck", 0) - 0.10) < 1e-6, str(st_hl.get("luck")))

    # ============ 5. 治疗强度 ============
    print("【5. 治疗强度】")
    check("牧师 base heal_power 10%", abs(CLASSES["cls_mu_shi"]["base"].get("heal_power", 0) - 0.10) < 1e-9)
    check("无独立诗人职业（v112.3 回归牧师攻线）", "cls_bard" not in CLASSES)
    s = stat_affix_stats(["heal_power"], "armor", 30)
    check("圣愈词条 +5%", abs(s.get("heal_power", 0) - 0.05) < 1e-6)
    from game.data.sets import SETS
    check("圣徽套 heal_power 5%", abs(SETS["set_sheng_hui"]["bonus_2"].get("heal_power", 0) - 0.05) < 1e-9)
    check("晨光教会套 heal_power 5%", abs(SETS["set_chen_guang_jiao_hui"]["bonus_2"].get("heal_power", 0) - 0.05) < 1e-9)
    # 面板聚合：牧师 Lv.30 裸装 10%
    st_m, _ = E.player_stats_detail("cls_mu_shi", 30, {})
    check("牧师面板 heal_power 10%", abs(st_m.get("heal_power", 0) - 0.10) < 1e-6, str(st_m.get("heal_power")))
    # 战斗消费：治疗技能 ×(1+heal_power)
    p_m = {"qq_id": "w", "name": "T", "level": 30, "class_name": "cls_mu_shi",
           "hp": 300, "max_hp": 500, "mp": 100, "max_mp": 100,
           "equipment": {}, "attributes": {}, "learned_skills": []}
    b = BT.Battle("wild", enemy=enemy, title_bonus=None, player=p_m, pet=None)
    st_m2 = b._player_stats(p_m)
    check("牧师战斗 heal_power 10%", abs(st_m2.get("heal_power", 0) - 0.10) < 1e-6, str(st_m2.get("heal_power")))
    # 治疗公式 ×(1+heal_power) 的真实倍率交由 real 战斗疗伤段（risky）覆盖，此处去除假校验

    # ============ 6. 护盾强度 ============
    print("【6. 护盾强度】")
    check("战士 base shield_power 5%", abs(CLASSES["cls_zhan_shi"]["base"].get("shield_power", 0) - 0.05) < 1e-9)
    s2 = stat_affix_stats(["shield_power"], "armor", 30)
    check("坚盾词条 +5%", abs(s2.get("shield_power", 0) - 0.05) < 1e-6)
    st_z, _ = E.player_stats_detail("cls_zhan_shi", 30, {})
    check("战士面板 shield_power 5%", abs(st_z.get("shield_power", 0) - 0.05) < 1e-6, str(st_z.get("shield_power")))
    # 战斗消费：_add_shield ×(1+shield_power)
    p_z = {"qq_id": "w", "name": "T", "level": 30, "class_name": "cls_zhan_shi",
           "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
           "equipment": {}, "attributes": {}, "learned_skills": []}
    b = BT.Battle("wild", enemy=enemy, title_bonus=None, player=p_z, pet=None)
    b._add_shield("test", 100, 3)
    check("100 盾 × 战士盾强5% = 105", b.p_shields.get("test", {}).get("value") == 105, str(b.p_shields))
    # 无盾强职业
    p_n = {"qq_id": "w", "name": "T", "level": 30, "class_name": "cls_fa_shi",
           "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
           "equipment": {}, "attributes": {}, "learned_skills": []}
    b2 = BT.Battle("wild", enemy=enemy, title_bonus=None, player=p_n, pet=None)
    b2._add_shield("test", 100, 3)
    check("法师无盾强 → 100 不变", b2.p_shields.get("test", {}).get("value") == 100, str(b2.p_shields))
    # cap：50% 封顶
    b3 = BT.Battle("wild", enemy=enemy, title_bonus=None, player=p_z, pet=None)
    b3._player_stats = lambda p: {"shield_power": 0.99}
    b3._add_shield("test", 100, 3)
    check("盾强 99% cap 50% → 150", b3.p_shields.get("test", {}).get("value") == 150, str(b3.p_shields))

    # ============ 7. 面板 ============
    print("【7. 面板】")
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game", "commands", "player.py"), encoding="utf-8").read()
    check("面板含 heal_power 行", "heal_power" in src)
    check("面板含 shield_power 行", "shield_power" in src)
    check("面板含 gold_bonus 行（未被误删）", "gold_bonus" in src)

    print(f"\n===== v106.2 职业特色/种族/治疗护盾测试: {passed} passed, {failed} failed =====")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
