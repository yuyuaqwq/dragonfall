# -*- coding: utf-8 -*-
"""_tmp_elite_boss_audit.py —— 精英/野外 Boss 数值现状实测（只读审计，不改源码）

输出：
  ① elite/boss 在 Lv 11/16/22/30/45/60 完整面板（build_monster 实测）
  ② 11 级标准加点（39 点，6 职业）裸装/满装 vs elite/boss Lv 11(同级)/16(越5)/22(跨11)
     胜率（seeds=8 固定种子）与平均击杀回合（真实引擎 BT.Battle 纯普攻）
  ③ 怪打玩家承伤回合：期望 dmg=atk²/(atk+def)（E.calc_damage variance=0 实测），
     承伤回合 = ceil(max_hp / 期望单次伤害)（物理 atk vs def、魔法 matk vs mdef）
  ④ 当前区域怪物表（装配后 SUBAREAS + HIDDEN_MONSTERS）elite/boss 等级分布

运行：python scripts/_tmp_elite_boss_audit.py（exit=0）
"""
import math
import os
import random
import sys

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))
for _p in (_QQBOT_DIR, _PLUGIN_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN_DIR, "tests", "test_game_data.db"))

from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.data import SUBAREAS, MAPS, HIDDEN_MONSTERS  # noqa: E402

PLAYER_LV = 11
SEEDS = 8
PANEL_LVS = [11, 16, 22, 30, 45, 60]
FIGHT_LVS = [("同 11", 11), ("越5 16", 16), ("跨11 22", 22)]

# 标准 39 点分配（任务卡 N01 / test_numeric_battle_matrix）
STD_ATTR = {
    "战士": {"str": 39}, "法师": {"int": 39}, "游侠": {"agi": 39},
    "牧师": {"int": 39}, "刺客": {"agi": 39}, "拳师": {"str": 39},
}
# 满装 = N03 固定种子名册 Lv.10-15 蓝装 5 槽（铁港系列，无 ring/necklace 档）
FULL_RIDS = {
    "weapon": "eq_wan_dao", "helm": "eq_chuan_zhang_mao", "armor": "eq_shui_shou_jia_ke",
    "legs": "eq_shui_shou_hu_tui", "boots": "eq_hai_dao_xue",
}
GEN_SEEDS = {s: 100 + i for i, s in enumerate(FULL_RIDS, start=1)}

_MAX_TURNS = 500


def make_full_equip():
    equip = {}
    for slot, rid in FULL_RIDS.items():
        random.seed(GEN_SEEDS[slot])
        equip[slot] = C.generate_roster_equip(rid)
    return equip


def monster_of(role, lv):
    mid = "m_audit_%s_%d" % (role, lv)
    return C.build_monster(
        (mid, "审计%s" % role, role, lv, [], []),
        {"id": mid, "name": "审计%s" % role, "area": "field", "lv": lv},
    )


def player_panel(cls, lv, attr, equip):
    return E.player_final_stats(cls, lv, equip or {}, 0, attr)


def fight(cls, lv, attr, equip, role, mlv, seeds=SEEDS):
    """真实引擎 BT.Battle，固定种子 0..seeds-1，纯普攻。返回 (胜场, 平均回合, 平均击杀回合)。"""
    m = monster_of(role, mlv)
    wins, rounds, wr = 0, 0, 0
    for seed in range(max(1, seeds)):
        random.seed(seed)
        st = player_panel(cls, lv, attr, equip)
        p = {
            "class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": dict(equip or {}), "attributes": dict(attr), "learned_skills": [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None,
        }
        b = BT.Battle(btype="monster", enemy=dict(m), player=p)
        turns = 0
        while b.result is None and turns < _MAX_TURNS:
            b.player_turn("attack", None, p)
            turns += 1
        if b.result == "victory":
            wins += 1
            wr += b.round
        rounds += b.round
    kill_r = round(wr / max(1, wins), 2) if wins else None
    return wins, round(rounds / max(1, seeds), 2), kill_r


def survive_rounds(max_hp, m_atk, p_def):
    """期望单次伤害（variance=0 的 calc_damage 实测公式）+ 承伤回合（ceil）。"""
    dmg = E.calc_damage(m_atk, p_def, variance=0.0)
    return math.ceil(max_hp / max(1, dmg)), dmg


def scan_field_elite_boss():
    """④ 装配后 SUBAREAS 扫描 elite/boss 分布（野外）。返回汇总 dict。"""
    rows = []
    for m in MAPS:
        mid = m["id"]
        for sa in SUBAREAS.get(mid, []):
            sa_name = sa.get("name") or sa.get("id", "")
            if sa.get("elite"):
                (eid, estr, erole, elv, eskl, edrops) = sa["elite"]
                rows.append((m["name"], sa_name, estr, "elite", elv))
            if sa.get("boss"):
                (bid, bstr, brole, blv, bskl, bdrops) = sa["boss"]
                rows.append((m["name"], sa_name, bstr, "boss", blv))
    return rows


def main():
    print("=" * 74)
    print("《奥兰迪亚》精英/野外 Boss 数值现状审计（只读，真实引擎实测）")
    print("=" * 74)

    # ---------- ① 面板 ----------
    print("\n【① elite/boss 面板（build_monster 实测；hp 已含 1+lv×0.04/0.06 上限3.0、"
          "def/mdef ×1.15/1.25、等级段曲线）】")
    print("%-4s | %-32s | %-32s" % ("Lv", "elite hp/atk/def/spd/matk/mdef", "boss hp/atk/def/spd/matk/mdef"))
    print("-" * 74)
    panels = {}
    for lv in PANEL_LVS:
        e = monster_of("elite", lv)
        b = monster_of("boss", lv)
        panels[lv] = (e, b)
        es = "(%d,%d,%d,%d,%d,%d)" % (e["hp"], e["atk"], e["def"], e["spd"], e["matk"], e["mdef"])
        bs = "(%d,%d,%d,%d,%d,%d)" % (b["hp"], b["atk"], b["def"], b["spd"], b["matk"], b["mdef"])
        print("%-4d | %-32s | %-32s" % (lv, es, bs))

    # ---------- ④ 分布 ----------
    print("\n【④ 当前野外怪物表 elite/boss 等级分布（装配后 SUBAREAS 扫描）】")
    rows = scan_field_elite_boss()
    elv_s = sorted(r[4] for r in rows if r[3] == "elite")
    blv_s = sorted(r[4] for r in rows if r[3] == "boss")
    from collections import Counter
    ec, bc = Counter(elv_s), Counter(blv_s)
    print("elite 数量=%d  等级分布: %s" % (len(elv_s), dict(sorted(ec.items()))))
    print("boss  数量=%d  等级分布: %s" % (len(blv_s), dict(sorted(bc.items()))))
    has11e = 11 in ec
    has11b = 11 in bc
    print("11 级野外 elite 存在: %s；11 级野外 boss 存在: %s" % ("是" if has11e else "否", "是" if has11b else "否"))
    if rows:
        print("明细（地图 | 子区域 | 名字 | 类型 | 等级）: 前 30 条")
        for r in rows[:30]:
            print("  %-10s | %-10s | %-8s | %-6s | %d" % (r[0], r[1], r[2], r[3], r[4]))
        if len(rows) > 30:
            print("  ... 共 %d 条（列表截断）" % len(rows))
    else:
        print("  （野外子区域无 elite/boss 定义？）")
    # 隐藏怪（lv_off 相对地图等级）
    hids = [v for v in HIDDEN_MONSTERS.values() if v.get("role") in ("elite", "boss")]
    print("隐藏怪表 elite/boss: %d 条（lv_off 相对值）: %s" % (
        len(hids), sorted(v.get("lv_off", 0) for v in hids)))

    print("\n【模拟说明】11 级野外 elite/boss 存在=打真同级档；不存在则 11 级档为合成同级对照，"
          "16/22 级档模拟 11 级玩家越 5 级/跨 11 级实战档。")
    print("满装 = N03 固定种子名册蓝装 5 槽（Lv.10-15）。战斗=BT.Battle 纯普攻，seeds=%d。" % SEEDS)

    # ---------- ② 玩家 vs elite/boss 胜率 ----------
    print("【② 11 级玩家（39 点）裸装/满装 vs elite/boss 胜率与平均击杀回合】")
    full = make_full_equip()
    agg = {}  # (role, mlv, gear) -> [wins, total, rounds_sum, kill_r_sum]
    print("%-4s %-4s | %s" % ("职业", "装备", " | ".join(
        "%s:e胜/8(k回合) b胜/8(k回合)" % lab for lab, _ in FIGHT_LVS)))
    for cls in STD_ATTR:
        for gear, gname in (({}, "裸装"), (full, "满装")):
            cells = []
            for lab, mlv in FIGHT_LVS:
                we, re_, ke = fight(cls, PLAYER_LV, STD_ATTR[cls], gear, "elite", mlv)
                wb, rb, kb = fight(cls, PLAYER_LV, STD_ATTR[cls], gear, "boss", mlv)
                for role, w, r, k in (("elite", we, re_, ke), ("boss", wb, rb, kb)):
                    a = agg.setdefault((role, mlv, gname), [0, 0, 0.0, 0.0])
                    a[0] += w
                    a[1] += SEEDS
                    a[2] += r * SEEDS
                    if w:
                        a[3] += k * w
                cells.append("%s:e%d/8(k%s) b%d/8(k%s)" % (
                    lab, we, ("%.1f" % ke) if ke else "-", wb, ("%.1f" % kb) if kb else "-"))
            print("%-4s %-4s | %s" % (cls, gname, " | ".join(cells)))
    print("\n六职业合计（%d 场/格）：" % (SEEDS * len(STD_ATTR)))
    for lab, mlv in FIGHT_LVS:
        for role in ("elite", "boss"):
            for gname in ("裸装", "满装"):
                w, n, rs, kr = agg[(role, mlv, gname)]
                ktxt = "  平均击杀 %.1f 回合" % (kr / max(1, w)) if w else ""
                print("  %-6s Lv%-3d %s: %d/%d 胜 (%.1f%%)  平均 %.1f 回合%s" % (
                    role, mlv, gname, w, n, w * 100.0 / n, rs / max(1, n), ktxt))

    # ---------- ③ 怪打玩家承伤回合 ----------
    print("\n【③ elite/boss 打玩家的承伤回合（期望 dmg=atk²/(atk+def)，variance=0 实测）】")
    print("%-4s %-4s | %s" % ("职业", "装备", " | ".join(
        "%s:e物/e魔 b物/b魔" % lab for lab, _ in FIGHT_LVS)))
    for cls in STD_ATTR:
        for gear, gname in (({}, "裸装"), (full, "满装")):
            st = player_panel(cls, PLAYER_LV, STD_ATTR[cls], gear)
            cells = []
            for lab, mlv in FIGHT_LVS:
                e, b = panels.get(mlv) or (monster_of("elite", mlv), monster_of("boss", mlv))
                e_phys = survive_rounds(st["max_hp"], e["atk"], st["def"])
                e_magi = survive_rounds(st["max_hp"], e["matk"], st["mdef"])
                b_phys = survive_rounds(st["max_hp"], b["atk"], st["def"])
                b_magi = survive_rounds(st["max_hp"], b["matk"], st["mdef"])
                cells.append("%s:e%d/%d b%d/%d" % (lab, e_phys[0], e_magi[0], b_phys[0], b_magi[0]))
            print("%-4s %-4s | %s" % (cls, gname, " | ".join(cells)))
    print("注：数值=玩家可承受的期望攻击次数（ceil(max_hp/期望伤害)；物理=atk vs def，魔法=matk vs mdef。")
    print("    实战怪还会放技能（倍率更高）、Boss 战单怪会砍成 0.7× 但带 2 爪牙，承伤更凶。")

    # ---------- 结论 ----------
    print("\n【结论判断】")
    same_e = agg[("elite", 11, "裸装")][0] / agg[("elite", 11, "裸装")][1]
    same_b = agg[("boss", 11, "裸装")][0] / agg[("boss", 11, "裸装")][1]
    same_ef = agg[("elite", 11, "满装")][0] / agg[("elite", 11, "满装")][1]
    same_bf = agg[("boss", 11, "满装")][0] / agg[("boss", 11, "满装")][1]
    x5_e = agg[("elite", 16, "裸装")][0] / agg[("elite", 16, "裸装")][1]
    x5_b = agg[("boss", 16, "裸装")][0] / agg[("boss", 16, "裸装")][1]
    x5_ef = agg[("elite", 16, "满装")][0] / agg[("elite", 16, "满装")][1]
    x5_bf = agg[("boss", 16, "满装")][0] / agg[("boss", 16, "满装")][1]
    x11_e = agg[("elite", 22, "裸装")][0] / agg[("elite", 22, "裸装")][1]
    x11_b = agg[("boss", 22, "裸装")][0] / agg[("boss", 22, "裸装")][1]
    x11_ef = agg[("elite", 22, "满装")][0] / agg[("elite", 22, "满装")][1]
    x11_bf = agg[("boss", 22, "满装")][0] / agg[("boss", 22, "满装")][1]
    print("同级(11) elite 裸装胜率 %.0f%%、满装 %.0f%%；boss 裸装 %.0f%%、满装 %.0f%%" % (
        same_e * 100, same_ef * 100, same_b * 100, same_bf * 100))
    print("越5(16) elite 裸装 %.0f%%、满装 %.0f%%；boss 裸装 %.0f%%、满装 %.0f%%" % (
        x5_e * 100, x5_ef * 100, x5_b * 100, x5_bf * 100))
    print("跨11(22) elite 裸装 %.0f%%、满装 %.0f%%；boss 裸装 %.0f%%、满装 %.0f%%" % (
        x11_e * 100, x11_ef * 100, x11_b * 100, x11_bf * 100))


if __name__ == "__main__":
    main()