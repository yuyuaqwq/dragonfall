# -*- coding: utf-8 -*-
"""v181.P2C-C6 proc_buff + proc_stack 面板段语义门禁（行为零变化单体硬断言）。

在 OLD-NEW 差分探针（test_p2cc6_panel_buff_probe.py）之外，对每个代表场景做数值/副作用
硬断言（不经旧 handler，直接走 NEW proc() 族分发 + battle._player_stats 面板）：
1. gale_step：battle_start → buffs.gale_step=3 / eff.gale_step_pct=0.15；面板 spd 乘 1.15
2. swift_boots/deadman_stride/temple_stride/void_stride：各自 turns/pct 精确值
3. gale 双装备共享键 max：buff=max turns，eff.gale_step_pct=max pct（不叠加）
4. novice_wind_spd：hit → buffs.novice_wind_spd=2；面板 spd 乘 1.05
5. wind_mark：hit 3 层 → 面板 spd 乘 (1+3×0.02)；叠到 max 封顶 4
6. thunder_weave：hit 5 次满层 → stacks 清零 + eff.we_thunder_charge=0.2；4 层不满不 charge
7. thunder_weave 面板：3 层 spd×(1+3×0.02) atk×(1+3×0.01)（各 int 截断语义与旧逐段一致）
8. abyss_barrier：battle_start → max_hp/hp 永久 +8%
9. buff 衰减：buff int=剩余刻 → 时刻推进后 buff 消失 → 面板回基值（无 gale 加成）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import proc as we_proc

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30, class_name="战士", evolve_path=0):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": class_name, "evolve_path": evolve_path, "qq_id": "t1"}

def mk_enemy(hp=100000, max_hp=None, **kw):
    mh = hp if max_hp is None else max_hp
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": mh,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    e.update(kw)
    return e

def battle_for(key, enemy_hp=100000, **pw):
    p = mk_player([key], **pw)
    b = BT.Battle("monster", mk_enemy(hp=enemy_hp), player=p)
    return b, p

def base_player(**pw):
    """同属性无特效玩家（Battle.__init__ 无 battle_start proc → 面板为纯基值）。"""
    p = mk_player([], **pw)
    b = BT.Battle("monster", mk_enemy(), player=p)
    return b, p

def spd_of(b, p):
    return b._player_stats(p).get("spd")

def test_gale_family():
    print("【1. gale_step 家族 5 key（battle_start → buffs/eff/面板）】")
    # ⚠️ Battle.__init__ 末尾自动 proc battle_start——带 gale 特效的 b 构造完 buff 已激活，
    # 基值必须取同属性无特效玩家的面板（不能取同 b 构造后快照，那已是 buff 后值）
    base = spd_of(*base_player())
    cases = [("gale_step", 3, 0.15), ("swift_boots", 3, 0.20),
             ("deadman_stride", 4, 0.15), ("temple_stride", 4, 0.20), ("void_stride", 4, 0.25)]
    for key, turns, pct in cases:
        b, p = battle_for(key)  # 构造即 battle_start proc（buff 已挂）
        check(f"{key} buffs.gale_step={turns}",
              int((p.get("buffs") or {}).get("gale_step", 0)) == turns, str(p.get("buffs")))
        check(f"{key} eff.gale_step_pct={pct}",
              abs(float((p.get("eff") or {}).get("gale_step_pct", 0)) - pct) < 1e-9, str(p.get("eff")))
        check(f"{key} 面板 spd=int(base×{1+pct:.2f})",
              spd_of(b, p) == int(base * (1 + pct)),
              f"base={base} got={spd_of(b, p)} expect={int(base * (1 + pct))}")

def test_shared_max():
    print("【2. gale 双装备共享键 max（不叠加）】")
    b, p = battle_for(None)
    p["equipment"] = {f"s{i}": {"name": f"e{i}", "weapon_effect": k, "slot": "weapon",
                                "quality": "purple", "lv": 30}
                      for i, k in enumerate(["gale_step", "swift_boots"])}
    base = spd_of(b, p)
    we_proc(b, p, "battle_start", {}, [])
    check("双装备 buffs.gale_step=max(3,3)=3", int((p.get("buffs") or {}).get("gale_step", 0)) == 3,
          str(p.get("buffs")))
    check("双装备 eff.gale_step_pct=max(0.15,0.20)=0.20",
          abs(float((p.get("eff") or {}).get("gale_step_pct", 0)) - 0.20) < 1e-9, str(p.get("eff")))
    check("双装备面板 spd=int(base×1.20)", spd_of(b, p) == int(base * 1.20),
          f"base={base} got={spd_of(b, p)} expect={int(base * 1.20)}")

def test_novice_wind_spd():
    print("【3. 翠风 novice_wind_spd（hit → buffs + 面板 spd×1.05）】")
    b, p = battle_for("novice_wind_spd")
    base = spd_of(b, p)
    we_proc(b, p, "hit", {"dmg": 100}, [])
    check("buff novice_wind_spd=2", int((p.get("buffs") or {}).get("novice_wind_spd", 0)) == 2,
          str(p.get("buffs")))
    check("面板 spd=int(base×1.05)", spd_of(b, p) == int(base * 1.05),
          f"base={base} got={spd_of(b, p)} expect={int(base * 1.05)}")
    check("eff 无 gale_step_pct 残留（无 buff_pct_key 不写 eff）",
          "gale_step_pct" not in (p.get("eff") or {}), str(p.get("eff")))

def test_wind_mark():
    print("【4. 风痕 wind_mark（hit 叠层 → 面板 spd×层×0.02）】")
    b, p = battle_for("wind_mark")
    base = spd_of(b, p)
    for _ in range(3):
        we_proc(b, p, "hit", {"dmg": 100}, [])
    check("3 层", int((p.get("stacks") or {}).get("wind_mark", 0)) == 3, str(p.get("stacks")))
    check("面板 spd=int(base×(1+3×0.02))", spd_of(b, p) == int(base * 1.06),
          f"base={base} got={spd_of(b, p)} expect={int(base * 1.06)}")
    for _ in range(5):  # 叠到上限封顶 4
        we_proc(b, p, "hit", {"dmg": 100}, [])
    check("封顶 4 层", int((p.get("stacks") or {}).get("wind_mark", 0)) == 4, str(p.get("stacks")))

def test_thunder_weave():
    print("【5. 雷纹 thunder_weave（叠层/满层 charge/面板双乘）】")
    b, p = battle_for("thunder_weave")
    base_spd, base_atk = spd_of(b, p), b._player_stats(p).get("atk")
    for _ in range(5):
        we_proc(b, p, "hit", {"dmg": 100}, [])
    check("满层后 stacks 清零", int((p.get("stacks") or {}).get("thunder_weave", 0)) == 0,
          str(p.get("stacks")))
    check("eff.we_thunder_charge=0.2",
          abs(float((p.get("eff") or {}).get("we_thunder_charge", 0)) - 0.20) < 1e-9, str(p.get("eff")))
    # 3 层场景（不满层）：面板 spd/atk 各乘
    b2, p2 = battle_for("thunder_weave")
    s0, a0 = spd_of(b2, p2), b2._player_stats(p2).get("atk")
    for _ in range(3):
        we_proc(b2, p2, "hit", {"dmg": 100}, [])
    check("3 层面板 spd=int(s0×(1+3×0.02))", spd_of(b2, p2) == int(s0 * 1.06),
          f"s0={s0} got={spd_of(b2, p2)} expect={int(s0 * 1.06)}")
    check("3 层面板 atk=int(a0×(1+3×0.01))",
          b2._player_stats(p2).get("atk") == int(a0 * 1.03),
          f"a0={a0} got={b2._player_stats(p2).get('atk')} expect={int(a0 * 1.03)}")
    check("3 层无 charge 且 stacks=3",
          int((p2.get("stacks") or {}).get("thunder_weave", 0)) == 3
          and (p2.get("eff") or {}).get("we_thunder_charge") is None,
          f"stacks={p2.get('stacks')} eff={p2.get('eff')}")

def test_abyss_barrier():
    print("【6. 深渊屏障 abyss_barrier（battle_start maxhp 永久 +8%）】")
    b, p = battle_for("abyss_barrier")
    m0, h0 = p["max_hp"], p["hp"]
    we_proc(b, p, "battle_start", {}, [])
    bonus = int(m0 * 0.08)
    check("max_hp 永久 +8%", p["max_hp"] == m0 + bonus, f"{p['max_hp']} vs {m0 + bonus}")
    check("hp 同步 +bonus", p["hp"] == h0 + bonus, f"{p['hp']} vs {h0 + bonus}")

def test_buff_decay_panel():
    print("【7. buff 衰减后面板回基值（gale_step int=剩余刻）】")
    base = spd_of(*base_player())
    b, p = battle_for("gale_step")
    check("激活面板 spd>base", spd_of(b, p) > base, f"base={base} got={spd_of(b, p)}")
    # 时刻推进 buff 到期：buff int 3 刻 → expire_at = 3×ACT_TICK（_advance_time 语义）
    from game.core.constants import ACT_TICK
    b._advance_time(3 * ACT_TICK + 0.1)
    check("buff 衰减消失", "gale_step" not in (p.get("buffs") or {}), str(p.get("buffs")))
    check("面板回基值", spd_of(b, p) == base, f"base={base} got={spd_of(b, p)}")

if __name__ == "__main__":
    test_gale_family()
    test_shared_max()
    test_novice_wind_spd()
    test_wind_mark()
    test_thunder_weave()
    test_abyss_barrier()
    test_buff_decay_panel()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
