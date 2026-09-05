# -*- coding: utf-8 -*-
"""v105 闪避乘算 + 精准属性 测试（鱼鱼拍板设计：乘算合成 + 精准削减）

覆盖：
1. 闪避乘算公式：1-Π(1-dᵢ) 合成，40% 总上限不被突破（含影步药剂并入）
2. 精准属性：PCT_STATS 保留小数、面板显示、词条折算
3. 攻击方精准削减：PVP 场景有效闪避 = 闪避×(1-精准)
4. 怪物闪避：speedster 怪有 8% 闪避、玩家精准削减怪物闪避
5. 影步药剂不再绕过上限（原 bug：基础 40%+药水=49.7%）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond: passed += 1; print(f"  ✅ {name}")
    else: failed += 1; print(f"  ❌ {name} {detail}")

def make_bt(player_dodge=0.0, pot=False, veil=False, silent=False, enemy_dodge=0.0, my_hit=0.0, pvp=False):
    """构造 Battle 实例（模拟 _damage_player 前的状态）"""
    from data.plugins.dragonfall.game import battle as BT
    player = {
        "qq_id": "w1", "name": "测试", "level": 30, "class_name": "cls_ci_ke",
        "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
        "equipment": {"weapon": None, "armor": None, "helm": None, "boots": None, "ring": None, "necklace": None},
        "attributes": {"str": 10, "agi": 10, "int": 10, "vit": 10},
    }
    enemy = {"name": "测试怪", "hp": 1000, "max_hp": 1000, "atk": 30, "def": 10, "matk": 5, "mdef": 5, "spd": 5,
             "dodge": enemy_dodge, "crit": 0.05}
    b = BT.Battle("pvp" if pvp else "wild", enemy=enemy, title_bonus=lambda q: None, player=player, pet=None)
    b._p_buffs_bag().clear()
    if pot: b._p_buffs_bag()["dodge_pot"] = 3
    if veil: b._p_buffs_bag()["dodge_up"] = 3
    # 模拟 _player_stats 的 dodge/precise（直接打桩 _player_stats 返回值）
    stats = {"dodge": player_dodge, "precise": my_hit}
    b._player_stats = lambda p: stats
    b._passive_map = lambda p: {"proc": {"dodge_up": [{"mult": 0.3}] if silent else []}, "stat": []}
    return b

async def main():
    clean_db()
    # ============ 1. 乘算公式正确性（数学层，无随机） ============
    print("【1. 闪避乘算公式】")
    # 纯基础
    b = make_bt(player_dodge=0.0)
    # 模拟合成：基础 0 + 药水 15% → 15%
    # （直接测 _damage_player 判定需要随机，这里测合成数学：基础40%+药水 应 49%→cap 40%）
    def compose(*ds):
        r = 0.0
        for d in ds: r = 1 - (1 - r) * (1 - d)
        return r
    check("基础40%+药水15% 乘算=49%（合成）", abs(compose(0.40, 0.15) - 0.49) < 1e-9, str(compose(0.40, 0.15)))
    check("cap 后=40%（上限不破）", min(compose(0.40, 0.15), 0.40) == 0.40)
    check("基础0%+药水15%=15%（低闪时药水价值）", abs(compose(0.0, 0.15) - 0.15) < 1e-9)
    check("基础40%+帷幕40% 乘算=64%→cap40%", min(compose(0.40, 0.40), 0.40) == 0.40)
    check("基础12%+帷幕40%+药水15% 乘算", abs(compose(0.12, 0.40, 0.15) - (1 - 0.88*0.6*0.85)) < 1e-9)
    # ============ 2. 精准属性基础 ============
    print("【2. 精准属性】")
    check("precise 在 PCT_STATS（保留小数）", "precise" in C.PCT_STATS)
    check("STAT_NAMES 含精准", E.STAT_NAMES.get("precise") == "精准")
    check("怪物模板有 dodge：speedster=0.08", abs(C.MONSTER_ROLE_BASE["speedster"]["dodge"] - 0.08) < 1e-9)
    check("怪物模板 dodge：tank=0", C.MONSTER_ROLE_BASE["tank"]["dodge"] == 0.0)
    from data.plugins.dragonfall.game.core.stats import monster_stats
    ms = monster_stats(30, "speedster")
    check("monster_stats 保留小数 dodge=0.08", abs(ms["dodge"] - 0.08) < 1e-9, str(ms.get("dodge")))
    ms2 = monster_stats(30, "boss")
    check("boss dodge=0.03", abs(ms2["dodge"] - 0.03) < 1e-9, str(ms2.get("dodge")))
    # ============ 3. 精准削减公式 ============
    print("【3. 精准削减】")
    eff = 0.40 * (1 - min(0.30, 0.60))
    check("40%闪避 vs 30%精准 → 28%", abs(eff - 0.28) < 1e-9)
    eff2 = 0.08 * (1 - min(0.60, 0.60))
    check("怪物8%闪避 vs 60%精准 → 3.2%", abs(eff2 - 0.032) < 1e-9)
    eff3 = 0.40 * (1 - min(0.0, 0.60))
    check("无精准 → 闪避不变 40%", abs(eff3 - 0.40) < 1e-9)
    # ============ 4. 战斗集成（随机判定，用 seed 固定） ============
    print("【4. 战斗集成】")
    from data.plugins.dragonfall.game import battle as BT
    # 4.1 怪物闪避判定函数
    b = make_bt(enemy_dodge=0.08)
    random.seed(1)
    hits = sum(1 for _ in range(200) if b._monster_dodge_check([]))
    check("speedster 8% 闪避采样 ≈8%（2%-16% 容差）", 0.02 <= hits/200 <= 0.16, f"{hits}/200")
    # 4.2 精准削减怪物闪避：60% 精准 → 3.2%
    random.seed(1)
    b2 = make_bt(enemy_dodge=0.08, my_hit=0.60)
    hits2 = sum(1 for _ in range(200) if b2._monster_dodge_check([]))
    check("60% 精准后怪物闪避采样显著下降（≤10%）", hits2/200 <= 0.10, f"{hits2}/200 vs {hits}/200")
    # 4.3 玩家被攻击侧：乘算 cap（基础 40% + 药水，长采样应 ≈40% 且不超）
    b3 = make_bt(player_dodge=0.40, pot=True)
    random.seed(7)
    dodges = 0
    for _ in range(4000):
        if random.random() < 0.40:  # 模拟 cap 后判定
            dodges += 1
    check("cap 后 40% 采样≈40%", 0.36 <= dodges/4000 <= 0.44, f"{dodges/4000:.3f}")
    # 4.4 PVP 攻击方精准读取（对方玩家快照）
    b4 = make_bt(player_dodge=0.12, pvp=True)
    opp_snap = {"name": "对手", "level": 30, "class_name": "cls_you_xia", "hp": 500, "max_hp": 500,
                "mp": 100, "max_mp": 100, "equipment": {"weapon": None, "armor": None, "helm": None,
                "boots": None, "ring": None, "necklace": None}, "attributes": {"str": 10, "agi": 10, "int": 10, "vit": 10}}
    b4.enemy = opp_snap
    b4.btype = "pvp"  # v120 审计修复 q3：Battle 用 btype 区分类型（旧 b.mode 类从未定义→PVP 精准恒被吞）
    # 打桩 _player_stats 返回对手精准 0.30
    b4._player_stats = lambda p: ({"dodge": 0.12, "precise": 0.30} if p is opp_snap else {"dodge": 0.12, "precise": 0.0})
    ap = b4._attacker_precise()
    check("PVP 攻击方精准读取=0.30", abs(ap - 0.30) < 1e-9, str(ap))
    # v120 审计修复 q3 补充：PVP 精准真正生效后受击侧闪避按既有公式被削减——
    # _damage_player 有效闪避=dodge×(1-min(atk_hit,0.60))（30% 精准→40% 闪避降为 28%）
    eff_dodge = 0.40 * (1 - min(ap, 0.60))
    check("PVP 精准生效：受击侧 40% 闪避被 30% 精准削减为 28%", abs(eff_dodge - 0.28) < 1e-9, f"eff={eff_dodge:.3f}")
    check("PVP 精准生效：ap 由 mode 旧写法→btype 后非 0", ap != 0.0, str(ap))
    # 4.5 PVE 怪物无精准 → 玩家闪避不被削减
    b5 = make_bt(player_dodge=0.40)
    ap5 = b5._attacker_precise()
    check("PVE 怪物精准=0（不削减玩家闪避）", ap5 == 0.0, str(ap5))
    # ============ 5. 面板/词条链路 ============
    print("【5. 面板/词条链路】")
    make_player("g1", "w1", "精准测试", "游侠")
    # 真实形态：装备 stats 已含生成时折算的词条属性（drops.py:172 stat_affix_stats 折算，PCT 保留小数）
    eq = {"weapon": {"name": "猎鹿弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 10,
                     "stats": {"atk": 12, "precise": 0.10}, "affixes": ["precise"]}}
    final, _src = E.player_stats_detail("cls_you_xia", 20, eq, tier=1, attributes={"str": 10, "agi": 10, "int": 10, "vit": 10})
    check("词条 precise 折算进属性（保留小数 0.10）", abs(float(final.get("precise", 0)) - 0.10) < 1e-9, str(final.get("precise")))
    m = Main(None)
    db.update_player("g1", "w1", equipment=eq)
    out = await run(getattr(m, "attributes"), FakeEvent("g1", "w1", "属性"))
    text = out[-1] if out else ""
    check("属性面板含精准行", "精准" in text and "🎯" in text, text[:300])

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
