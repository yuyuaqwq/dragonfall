# -*- coding: utf-8 -*-
"""数值重设计 方案v4 预演：三档难度（鱼鱼 2026-08-27 拍板）
  精英 ≥20轮（蓝+5单刷）｜野外 Boss ≥60轮（4人组队）｜副本 Boss ≥100轮（4人组队）
管道分离（零引擎改动，纯数据）：
  A. 精英   → MONSTER_MODS hp_mult 分档（role 模板 growth 不动）
  B. 野外Boss → MONSTER_MODS hp_mult 分档（inst 无关）
  C. 副本Boss → 实例 inst.hp_mult 逐副本上调（boss role growth 不动，避免牵动野外）
  D. 承伤模型升级：4人队默认 1奶（牧师治愈 200%×50% 轮次占用 ≈ matk/轮），净承伤 = hit - 奶
"""
import os, sys
_PD = os.getcwd()
sys.path.insert(0, os.path.join(_PD, "tests")); sys.path.insert(0, os.path.join(_PD, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_PD))))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env
from numeric_lib.monster import curve_override
from numeric_lib.player import PlayerOptions, build_player, per_action_dmg
from numeric_lib.gear import gear_loadout
from numeric_lib.constants import CLASSES, TEAM_BUFF
from numeric_lib.team import boss_hp
from data.plugins.dragonfall.game import content as C
from saintess_engine.formulas import calc_damage
from data.plugins.dragonfall.game.data import monster_mods as MM

GROWTH = {
    "tank":      {"hp": 36, "atk": 3.5, "def": 4.0, "matk": 1.2, "mdef": 2.8, "spd": 0.3},
    "dps":       {"hp": 30, "atk": 5.0, "def": 5.0, "matk": 1.5, "mdef": 2.4, "spd": 1.0},
    "caster":    {"hp": 22, "atk": 1.8, "def": 3.5, "matk": 5.0, "mdef": 4.0, "spd": 0.9},
    "speedster": {"hp": 22, "atk": 3.5, "def": 4.5, "matk": 1.5, "mdef": 2.0, "spd": 1.8},
    "healer":    {"hp": 20, "atk": 1.5, "def": 3.0, "matk": 4.0, "mdef": 3.0, "spd": 0.8},
    "elite":     {"hp": 70, "atk": 6.5, "def": 5.5, "matk": 5.0, "mdef": 4.5, "spd": 1.5},
    "boss":      {"hp": 145, "atk": 7.5, "def": 3.8, "matk": 6.0, "mdef": 3.4, "spd": 1.8},
}
HP_STAGE = [(15, 1.0), (30, 1.75), (60, 2.65), (999, 3.45)]

def player_dmg(cls, lv, loadout, edef, emdef):
    return per_action_dmg(cls, lv, gear_loadout(lv, loadout), edef, emdef,
                          PlayerOptions(), potion_on=True)

def hit_of(m, pdef, pmdef, mult=1.35):
    return max(calc_damage(int(m.get("atk", 0) * mult), int(pdef), variance=0.0),
               calc_damage(int(m.get("matk", 0) * mult), int(pmdef), variance=0.0), 1)

def survive_with_heal(pool, hit, heal_per_round, rounds):
    """带奶续航：净承伤 = hit - 奶量；奶不足时兜底 hit×20%。"""
    net = max(hit - heal_per_round, hit * 0.2)
    return pool / net

with curve_override(growth=GROWTH, hp_stage=HP_STAGE):
    # ---------- A. 精英：分档 hp_mult 候选扫描（11 级蓝+5 单刷目标 18~30 轮） ----------
    print("【A. 精英分档扫描（11级 蓝+5 战士单刷）】")
    for em in (4.0, 5.0, 6.0, 8.0, 10.0):
        m = C.build_monster(("m_e", "精英", "elite", 11, [], []), {"id": "e", "name": "e", "area": "f"})
        m["max_hp"] = m["hp"] = int(m["max_hp"] * em / 1.0)  # 用 mods 语义改血量
        saved = MM.MONSTER_MODS.get("m_e", {})
        MM.MONSTER_MODS["m_e"] = dict(saved, hp_mult=em)
        m = C.build_monster(("m_e", "精英", "elite", 11, [], []), {"id": "e", "name": "e", "area": "f"})
        d = player_dmg("cls_zhan_shi", 11, "solo_mid", m["def"], m["mdef"])
        k = m["max_hp"] / d
        st = build_player("cls_zhan_shi", 11, gear_loadout(11, "solo_mid"), PlayerOptions())
        surv = st["max_hp"] / hit_of(m, st["def"], st["mdef"])
        print(f"  elite mult={em}: HP={m['max_hp']:,} 击杀 {k:.1f} 轮 裸装承伤(参考) {surv:.1f}")
    MM.MONSTER_MODS.pop("m_e", None)

    # 30/60 级抽查（mult 分档在哪个值达标 18~30）
    print("  高等级抽查（elite mult 分档候选）:")
    for lv, em in ((30, 3.0), (30, 4.0), (60, 2.0), (60, 2.5)):
        saved = MM.MONSTER_MODS.get("m_e2", {})
        MM.MONSTER_MODS["m_e2"] = dict(saved, hp_mult=em)
        m = C.build_monster(("m_e2", "精英", "elite", lv, [], []), {"id": "e", "name": "e", "area": "f"})
        d = player_dmg("cls_zhan_shi", lv, "solo_mid", m["def"], m["mdef"])
        print(f"  Lv{lv} mult={em}: HP={m['max_hp']:,} 蓝+5击杀 {m['max_hp']/d:.1f} 轮")
    MM.MONSTER_MODS.pop("m_e2", None)

    # ---------- B. 野外 Boss 分档扫描（4人组队蓝+5 目标 60~100） ----------
    print("\n【B. 野外 Boss 分档扫描（4人 蓝+5 战士）】")
    FIELDS = [
        ("b_goblin_chief", 20), ("b_pirate_king", 28), ("b_ghost_ghoul", 24), ("b_old_king", 45),
        ("b_marcus", 52), ("b_elven_king", 66), ("b_sea_queen", 60), ("b_abyss_lord", 98),
    ]
    for mid, lv in FIELDS:
        for fm in (10.0, 12.0, 14.0):
            saved = MM.MONSTER_MODS.get(mid, {})
            MM.MONSTER_MODS[mid] = dict(saved, hp_mult=fm)
            m = C.build_monster((mid, mid, "boss", lv, [], []), {"id": mid, "name": mid, "area": "f"})
            d = player_dmg("cls_zhan_shi", lv, "solo_mid", m["def"], m["mdef"])
            k = m["max_hp"] / (d * 4 * TEAM_BUFF)
            st = build_player("cls_zhan_shi", lv, gear_loadout(lv, "solo_mid"), PlayerOptions())
            hit = hit_of(m, st["def"], st["mdef"])
            surv = survive_with_heal(st["max_hp"] * 4, hit, st["matk"] * 2.0 * 0.5, k)
            mark = "✅" if 60 <= k <= 100 and surv >= k else "🟡" if 45 <= k <= 110 else "❌"
            print(f"  {mid} Lv{lv} mult={fm}: 杀 {k:.1f} 轮 带奶承伤 {surv:.1f} {mark}")
        # 还原
        if saved:
            MM.MONSTER_MODS[mid] = saved
        else:
            MM.MONSTER_MODS.pop(mid, None)

    # ---------- C. 副本 Boss：实例 hp_mult 扫描（4人蓝+5 目标 100~150） ----------
    print("\n【C. 副本 Boss 逐副本 hp_mult 扫描（4人 蓝+5 战士，目标 100~150 轮）】")
    for iid, inst in sorted(C.INSTANCES.items(), key=lambda x: x[1].get("lv", 0)):
        lv = inst.get("lv", 0)
        boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
        if not boss_def:
            continue
        mn = inst.get("min_players", 1)
        n = 4
        m = C.build_monster(boss_def, {"id": iid, "name": iid, "area": "instance"})
        d = player_dmg("cls_zhan_shi", lv, "solo_mid", m["def"], m["mdef"])
        base = m["max_hp"]
        # 找目标 hpm：轮数 = base×(hpm+0.65×(n-mn)) / (d×n×1.1) ∈ [100,150]
        best = None
        for hpm in [x / 2 for x in range(2, 41)]:  # 1.0 ~ 20.0
            hp_tot = int(base * (hpm + 0.65 * (n - mn)))
            k = hp_tot / (d * n * TEAM_BUFF)
            if 100 <= k <= 150:
                best = (hpm, hp_tot, k)
                break
        if best:
            hpm, hp_tot, k = best
            st = build_player("cls_zhan_shi", lv, gear_loadout(lv, "solo_mid"), PlayerOptions())
            hit = hit_of(m, st["def"], st["mdef"])
            surv = survive_with_heal(st["max_hp"] * 4, hit, st["matk"] * 2.0 * 0.5, k)
            print(f"  {iid[:20]:22s} Lv{lv:>3} 现hpm={inst.get('hp_mult')} → 建议 {hpm:>4.1f}  HP={hp_tot:>10,}  杀{k:>5.1f}轮 承伤{surv:>5.1f} {'✅' if surv >= k else '🔴奶不够'}")
        else:
            print(f"  {iid[:20]:22s} Lv{lv:>3} ⚠️ 目标区间找不到（20.0 范围内）")