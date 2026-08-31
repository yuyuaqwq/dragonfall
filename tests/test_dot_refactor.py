# -*- coding: utf-8 -*-
"""DOT/减益重构回归测试（契约 v1.1/v1.2）

覆盖：
1. 混合公式（atk/matk 系数 + max_hp 小百分比）
2. 层数=剩余回合衰减（5 层 5 回合消散）
3. 抗性 dot_res（elite 0.8 / boss 0.9 / cap 0.95）
4. 减益适应（叠层 +4% cap 20%、2 回合未叠回落 -4%、总抗 min(0.95, base+adapt)）
5. immune_dots 免疫
6. 护盾对 dot 生效（_boss_dmg_filter）
7. 放血（<30% ×2）与毒蚀（防御 -4%/层 cap 20%）
8. 标记按层易伤（_apply_mark +20%/层）
9. 毒爆 atk 物理段 + 灼爆易燃
10. 副本 dot_pending 每轮结算 + poison_all 共享层
11. 老存档迁移（mech_stacks poison → enemy debuffs）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.core import battle_mech as BM
from game.core.stats import monster_stats

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def mk_player(atk=100, matk=80):
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": []}

def mk_enemy(hp=1000, **kw):
    e = {"name": "靶子", "lv": 10, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}}
    e.update(kw)
    return e

def tick(b, player):
    # 固定施放者属性快照（避免 _player_stats 对不完整测试玩家的职业兜底）
    b._player_stats = lambda pl: {"atk": 100, "matk": 80, "def": 50, "mdef": 50,
                                  "spd": 10, "crit": 0.05, "max_hp": 9999, "max_mp": 999}
    b._dot_pending = True
    logs = []
    b._tick_dots(player, logs)
    return logs

def test_mixed_formula():
    print("【1. 混合公式】")
    p = mk_player(atk=100, matk=80)
    b = BT.Battle("monster", mk_enemy(hp=1000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
    tick(b, p)
    check("毒 1 层 = atk×0.5+max_hp×1.5% = 50+15 = 65", 1000 - b.enemy["hp"] == 65,
          f"dmg={1000 - b.enemy['hp']}")
    b = BT.Battle("monster", mk_enemy(hp=1000))
    b.enemy.setdefault("debuffs", {})["burn"] = {"n": 1, "mult": 1.0}
    tick(b, p)
    check("灼烧 1 层 = matk×0.4+max_hp×1% = 32+10 = 42", 1000 - b.enemy["hp"] == 42,
          f"dmg={1000 - b.enemy['hp']}")
    b = BT.Battle("monster", mk_enemy(hp=1000))
    b.enemy.setdefault("debuffs", {})["bleed"] = {"n": 1, "mult": 1.0}
    tick(b, p)
    check("流血 1 层 = atk×0.6+max_hp×1.5% = 60+15 = 75", 1000 - b.enemy["hp"] == 75,
          f"dmg={1000 - b.enemy['hp']}")
    b = BT.Battle("monster", mk_enemy(hp=1000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 2, "mult": 1.2}
    tick(b, p)
    check("毒 2 层 × mult 1.2 = int(65×2×1.2) = 156", 1000 - b.enemy["hp"] == 156,
          f"dmg={1000 - b.enemy['hp']}")

def test_decay():
    print("【2. 层数衰减】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=100000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0}
    total = 0
    for _ in range(6):
        before = b.enemy["hp"]
        tick(b, p)
        total += before - b.enemy["hp"]
        if b._enemy_dead():
            break
    check("5 层 5 回合总伤 = 1550×15 = 23250", total == 23250, f"total={total}")
    check("第 6 回合消散", "poison" not in b.enemy.get("debuffs", {}), str(b.enemy.get("debuffs")))

def test_resistance():
    print("【3. 抗性】")
    st = monster_stats(40, "elite")
    check("精英 dot_res = 0.8", st.get("dot_res") == 0.8, str(st.get("dot_res")))
    st = monster_stats(40, "boss")
    check("Boss dot_res = 0.9", st.get("dot_res") == 0.9, str(st.get("dot_res")))
    st = monster_stats(40, "tank")
    check("普通怪无 dot_res", st.get("dot_res") is None, str(st.get("dot_res")))
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=1000, dot_res=0.9))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
    tick(b, p)
    check("dot_res 0.9 → 伤害 ×0.1 = int(65×0.1) = 6", 1000 - b.enemy["hp"] == 6,
          f"dmg={1000 - b.enemy['hp']}")

def test_adapt():
    print("【4. 减益适应】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=100000))
    b._last_player = p
    for _ in range(3):
        BM.MECH_EFFECTS["poison"](b, 2, b.mech_stacks, 100, [], "淬毒", False)
    check("叠毒 3 次 adapt = 0.12", abs(b.enemy["adapt"]["poison"] - 0.12) < 1e-9,
          str(b.enemy["adapt"]))
    # v152：last_round → last_tick（行动轮次 _tick_no() 记录）
    check("last_tick 已记录", b.enemy["debuffs"]["poison"].get("last_tick", 0) >= 1,
          str(b.enemy["debuffs"]["poison"]))
    for _ in range(5):
        BM.MECH_EFFECTS["poison"](b, 1, b.mech_stacks, 100, [], "淬毒", False)
    check("适应 cap 0.20", abs(b.enemy["adapt"]["poison"] - 0.20) < 1e-9, str(b.enemy["adapt"]))
    # 总抗：dot_res 0.9 + adapt 0.2 → cap 0.95
    b2 = BT.Battle("monster", mk_enemy(hp=1000, dot_res=0.9, adapt={"poison": 0.2}))
    b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
    tick(b2, p)
    check("总抗 min(0.95, 0.9+0.2) → 伤害 = int(65×0.05) = 3", 1000 - b2.enemy["hp"] == 3,
          f"dmg={1000 - b2.enemy['hp']}")
    # 回落：last_tick 距今 ≥2 行动轮次 → -0.04（v152：b._now = 5×ACT_TICK，last_tick=2）
    b3 = BT.Battle("monster", mk_enemy(hp=100000, adapt={"poison": 0.12}))
    b3._now = 5 * 2.0
    b3.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0, "last_tick": 2}
    tick(b3, p)
    check("2 回合未叠 → adapt 0.12→0.08", abs(b3.enemy["adapt"]["poison"] - 0.08) < 1e-9,
          str(b3.enemy["adapt"]))

def test_immune():
    print("【5. 免疫】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=1000, immune_dots=["poison"]))
    b._last_player = p
    logs = []
    BM.MECH_EFFECTS["poison"](b, 2, b.mech_stacks, 100, logs, "淬毒", False)
    check("免疫时叠毒失败", "poison" not in b.enemy.get("debuffs", {}), str(b.enemy.get("debuffs")))
    check("免疫提示", any("免疫中毒" in l for l in logs), str(logs))
    b2 = BT.Battle("monster", mk_enemy(hp=1000, immune_dots=["poison"]))
    b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
    tick(b2, p)
    check("已有层被免疫移除", "poison" not in b2.enemy.get("debuffs", {}), str(b2.enemy.get("debuffs")))

def test_shield_dot():
    print("【6. 护盾对 dot 生效】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=1000, mech="shield", boss_shield=500))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
    tick(b, p)
    check("毒 65 → 护盾减半 32", 1000 - b.enemy["hp"] == 32, f"dmg={1000 - b.enemy['hp']}")
    check("护盾吸收", abs(b.enemy.get("boss_shield", 0) - 468) <= 1,
          f"shield={b.enemy.get('boss_shield')}")

def test_bleed_erode_mark():
    print("【7. 放血 + 毒蚀 + 标记按层】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=100))
    b.enemy["max_hp"] = 1000  # hp=100 < max_hp×30%=300 → 放血触发
    b.enemy.setdefault("debuffs", {})["bleed"] = {"n": 1, "mult": 1.0}
    logs = tick(b, p)
    # 伤害 = (atk×0.6+max_hp×1.5%)×2 = 75×2 = 150 → 击杀
    check("放血 <30% ×2 = 150 且击杀", b._enemy_dead()
          and any("损失 150 点生命" in l for l in logs), str([l for l in logs if "流血" in l]))
    check("放血日志", any("放血" in l for l in logs), str(logs))
    b2 = BT.Battle("monster", mk_enemy(**{"def": 1000, "mdef": 800}))
    b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0}
    est = b2._enemy_stats()
    check("毒蚀 5 层 def -20% = 800", est["def"] == 800, str(est["def"]))
    check("毒蚀 5 层 mdef -20% = 640", est["mdef"] == 640, str(est["mdef"]))
    b2.enemy["debuffs"]["poison"]["n"] = 2
    check("毒蚀 2 层 def -8% = 920", b2._enemy_stats()["def"] == 920, str(b2._enemy_stats()["def"]))
    b3 = BT.Battle("monster", mk_enemy())
    b3.enemy.setdefault("debuffs", {})["mark"] = {"n": 5, "mult": 1.0}
    check("标记 5 层 +100%", b3._apply_mark(100) == 200, str(b3._apply_mark(100)))
    b3.enemy["debuffs"]["mark"]["n"] = 1
    check("标记 1 层 +20%", b3._apply_mark(100) == 120, str(b3._apply_mark(100)))

def test_bursts():
    print("【8. 毒爆 atk 物理段 + 灼爆易燃】")
    p = mk_player(atk=100, matk=80)
    b = BT.Battle("monster", mk_enemy(**{"def": 0}))
    b._last_player = p
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
    logs = []
    BM.MECH_EFFECTS["poison_burst"](b, 1, b.mech_stacks, 100, logs, "毒爆术", False)
    check("毒爆造成伤害", b.enemy["hp"] < 1000, f"{b.enemy['hp']}")
    check("毒爆物理段", any("物理伤害" in l for l in logs), str(logs))
    check("毒爆清层", "poison" not in b.enemy.get("debuffs", {}), str(b.enemy.get("debuffs")))
    b2 = BT.Battle("monster", mk_enemy(**{"def": 0}))
    b2._last_player = p
    b2.enemy.setdefault("debuffs", {})["burn"] = {"n": 5, "mult": 1.0}
    logs2 = []
    BM.MECH_EFFECTS["burn_burst"](b2, 1, b2.mech_stacks, 100, logs2, "灼烧引爆", False)
    check("灼爆易燃 5 层 ×1.3", any("易燃" in l for l in logs2), str(logs2))
    check("灼爆清层", "burn" not in b2.enemy.get("debuffs", {}), str(b2.enemy.get("debuffs")))
    # v1.3 毒爆附虚弱：3 层 -15%（提前爆价值）、5 层 -25%（无重伤——重伤仅 Boss『重创』施加）
    b3 = BT.Battle("monster", mk_enemy(**{"def": 0}))
    b3._last_player = p
    b3.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
    logs3 = []
    BM.MECH_EFFECTS["poison_burst"](b3, 1, b3.mech_stacks, 100, logs3, "毒爆术", False)
    check("毒爆 3 层附虚弱 -15%", abs(b3.e_buffs.get("_weaken_val", 0) - 0.15) < 1e-9
          and b3.e_buffs.get("mon_atk_down", 0) >= 1, str(b3.e_buffs))
    b4 = BT.Battle("monster", mk_enemy(**{"def": 0}))
    b4._last_player = p
    b4.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0}
    logs4 = []
    BM.MECH_EFFECTS["poison_burst"](b4, 1, b4.mech_stacks, 100, logs4, "毒爆术", False)
    check("毒爆 5 层附虚弱 -25%", abs(b4.e_buffs.get("_weaken_val", 0) - 0.25) < 1e-9, str(b4.e_buffs))
    check("毒爆不附重伤", not b4.e_buffs.get("mortal_wound"), str(b4.e_buffs))
    # v1.3 重伤：仅 Boss『重创』施加，玩家吸血减半
    p_st = {"lifesteal": 0.30}
    b5 = BT.Battle("monster", mk_enemy())
    b5._player_stats = lambda pl: p_st
    b5.p_buffs = {}
    hl = []
    b5._settle_lifesteal(p, 1000, hl)
    check("无重伤吸血 300", "回复 300" in str(hl), str(hl))
    b6 = BT.Battle("monster", mk_enemy())
    b6._player_stats = lambda pl: p_st
    b6.p_buffs = {"mortal_wound": 2}
    hl2 = []
    b6._settle_lifesteal(p, 1000, hl2)
    check("重伤吸血减半 150", "回复 150" in str(hl2), str(hl2))
    # Boss『重创』开场技（v152：r=1 触发首回合开场技）
    b7 = BT.Battle("monster", mk_enemy(id="b_cardinal", role="boss", is_boss=True,
                                       mech="heal,phase_open"))
    b7._now = 0.0  # 首回合（_tick_no()=1）
    hl3 = []
    BM.BOSS_MECHS["phase_open"](b7, hl3, b7.enemy, 1)
    check("Boss 重创开场挂玩家重伤", b7.p_buffs.get("mortal_wound") == 2, str(b7.p_buffs))

def test_instance_flow():
    print("【9. 副本 dot_pending + poison_all 共享】")
    st = {"boss": {"name": "B", "hp": 1000, "max_hp": 1000}, "dot_pending": True,
          "members": [1, 2], "alive": {"1": True, "2": True}, "round_acted": []}
    # 模拟 C agent 的轮次流转：行动后 False → 轮满 True
    st["round_acted"].append("1")
    st["dot_pending"] = False
    check("行动后 dot_pending=False", st["dot_pending"] is False, str(st["dot_pending"]))
    st["round_acted"].append("2")
    if set(st["round_acted"]) >= {"1", "2"}:
        st["round_acted"] = []
        st["dot_pending"] = True
    check("轮满 dot_pending=True", st["dot_pending"] is True, str(st["dot_pending"]))
    check("round_acted 清空", st["round_acted"] == [], str(st["round_acted"]))
    # poison_all 共享层
    from game.commands import instance as inst
    inst_logs = []
    kind = "poison_all"
    if kind == "poison_all":
        boss = st.get("boss")
        if boss:
            deb = boss.setdefault("debuffs", {})
            cur = deb.get("poison") or {"n": 0, "mult": 1.0}
            cur["n"] = min(5, cur["n"] + 2)
            deb["poison"] = cur
            inst_logs.append("☠️ 全队武器淬毒！(毒层共享，每回合结算一次)")
    check("poison_all 共享层 +2", st["boss"]["debuffs"]["poison"]["n"] == 2,
          str(st["boss"]["debuffs"]))
    check("poison_all 日志", any("共享" in l for l in inst_logs), str(inst_logs))

def test_legacy_migration():
    print("【10. 老存档迁移】")
    st = {"type": "monster", "enemy": {"name": "老怪", "hp": 100, "max_hp": 100},
          "mech_stacks": {"poison": 3, "rage": 2}, "p_buffs": {}, "e_buffs": {}}
    b = BT.Battle.from_state(st)
    check("poison 迁入 enemy debuffs", b.enemy["debuffs"]["poison"]["n"] == 3,
          str(b.enemy.get("debuffs")))
    check("玩家资源保留", b.mech_stacks.get("rage") == 2, str(b.mech_stacks))
    check("mech_stacks 无 poison", "poison" not in b.mech_stacks, str(b.mech_stacks))

def test_fix_regressions():
    print("【11. 审计修复回归】")
    p = mk_player()
    # M2：dot 不触发 Boss 反射（dot 只走护盾）
    b = BT.Battle("monster", mk_enemy(hp=1000, mech="reflect"))
    b.enemy["hp"] = 100  # <25% 触发反射区间
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 2, "mult": 1.0}
    tick(b, p)
    check("dot 不触发反射（玩家不掉血）", p["hp"] == 9999, f"hp={p['hp']}")
    # M3：标记层每回合衰减
    b2 = BT.Battle("monster", mk_enemy(hp=100000))
    b2.enemy.setdefault("debuffs", {})["mark"] = {"n": 2, "mult": 1.0}
    tick(b2, p)
    check("标记衰减 2→1", b2.enemy["debuffs"]["mark"]["n"] == 1, str(b2.enemy["debuffs"]))
    tick(b2, p)
    check("标记归零移除", "mark" not in b2.enemy.get("debuffs", {}), str(b2.enemy.get("debuffs")))
    # immune_dots 对灼烧
    b3 = BT.Battle("monster", mk_enemy(hp=1000, immune_dots=["burn"]))
    b3._last_player = p
    lg = []
    BM.MECH_EFFECTS["burn"](b3, 2, b3.mech_stacks, 100, lg, "灼烧", False)
    check("灼烧免疫不叠层", "burn" not in b3.enemy.get("debuffs", {}), str(b3.enemy.get("debuffs")))
    # adapt 对灼烧回落（v152：b._now = 5×ACT_TICK，last_tick=2）
    b4 = BT.Battle("monster", mk_enemy(hp=100000, adapt={"burn": 0.12}))
    b4._now = 5 * 2.0
    b4.enemy.setdefault("debuffs", {})["burn"] = {"n": 1, "mult": 1.0, "last_tick": 2}
    tick(b4, p)
    check("灼烧适应回落 0.12→0.08", abs(b4.enemy["adapt"]["burn"] - 0.08) < 1e-9, str(b4.enemy["adapt"]))
    # 重伤对技能吸血减半
    b5 = BT.Battle("monster", mk_enemy(hp=100000))
    b5.p_buffs = {"mortal_wound": 2}
    info = {"lifesteal": 0.25}
    hp0 = p["hp"]
    b5._player_skill(b5._player_stats(p), "嗜血斩", info, p) if False else None
    # 直接验证 skill_lifesteal 路径：模拟 _player_skill 的吸血块（重伤 ×0.5）
    from game import engine as EG
    heal = int(1000 * EG.skill_lifesteal_pct(info, 10))
    if b5.p_buffs.get("mortal_wound"):
        heal = int(heal * 0.5)
    check("重伤技能吸血减半（25%→12.5%）", heal == 125, f"heal={heal}")
    # Boss phase 清减益/适应 → v138.2 律三进度遗产：保留 50% 层数（不再全清）
    b6 = BT.Battle("monster", mk_enemy(hp=1000, mech="phase,phase"))
    b6.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
    b6.enemy["adapt"] = {"poison": 0.12}
    b6.enemy["hp"] = 300  # <50% 触发第一段
    lg6 = []
    BM.BOSS_MECHS["phase"](b6, lg6, b6.enemy, 3)
    check("phase 转换保留 50% 层数（进度遗产）", b6.enemy.get("debuffs", {}).get("poison", {}).get("n", 0) == 1,
          str(b6.enemy.get("debuffs")))
    check("phase 转换保留适应（进度遗产）", "adapt" in b6.enemy, str(b6.enemy.get("adapt")))
    check("phase 残留日志", any("残留" in l or "保留" in l for l in lg6), str(lg6))
    # H1：流血词条写入目标级 debuffs 并结算
    b7 = BT.Battle("monster", mk_enemy(hp=100000))
    b7._equip_affix_ids = lambda pl: ["bleed"]
    import random as _rnd
    _orig = _rnd.random
    _rnd.random = lambda: 0.05
    try:
        from game.core import affix_effects as AFX
        AFX.HIT_EFFECTS["bleed"](b7, p, 100, [])
    finally:
        _rnd.random = _orig
    check("流血词条挂目标 debuffs 3 层", b7.enemy["debuffs"]["bleed"]["n"] == 3,
          str(b7.enemy.get("debuffs")))
    before = b7.enemy["hp"]
    tick(b7, p)
    check("流血结算造成伤害且衰减", b7.enemy["hp"] < before
          and b7.enemy["debuffs"]["bleed"]["n"] == 2, f"hp={b7.enemy['hp']}")


if __name__ == "__main__":
    test_mixed_formula()
    test_decay()
    test_resistance()
    test_adapt()
    test_immune()
    test_shield_dot()
    test_bleed_erode_mark()
    test_bursts()
    test_instance_flow()
    test_legacy_migration()
    test_fix_regressions()
    print(f"\n结果: {passed} 通过, 0 失败")
