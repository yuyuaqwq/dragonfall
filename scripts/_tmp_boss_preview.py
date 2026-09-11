# -*- coding: utf-8 -*-
"""_tmp_boss_preview.py —— 《奥兰迪亚》副本 Boss 数值现状 + 重设计参数预演
（进程内 monkeypatch ONLY：不改任何源文件；游戏本体/测试不受影响）

重设计方案参数（预演）：
  A) 普通怪 role(tank/dps/caster/speedster/healer) 成长：def→4.0/级、atk→6.0/级、hp→25/级；
     其余属性(matk/mdef/spd/dodge)不动；elite/boss 两 role 成长完全不动。
  B) hp_stage_mult：16-30 级段每级 8%→5%（31+ 段按新 30 级锚点 1.75 平滑续接：
     31-60 每级 +0.04、61+ 每级 +0.03，曲线连续无跳变）。

模拟口径（与 scripts/numeric_calibration.py 一致）：
  队伍人数 = min_players；技能轮换 ×1.5；DPS = 战士/游侠伤害均值；
  玩家档位 = 32 章 蓝装 +3~+5（ENHANCE_TABLE: +3=×1.36 / +5=×1.70）；
  Boss HP = build_monster 面板 × hp_mult；Boss ATK = 面板 × atk_mult（真实战斗口径，同 instance.py L448）。
"""
import sys, os

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")

from data.plugins.dragonfall.game import content as C      # noqa: E402
from game.content_rules.panel import player_final_stats
from data.plugins.dragonfall.game.core import stats as ST  # noqa: E402

ROUND_MIN, ROUND_MAX = 15.0, 30.0
RATIO_MIN, RATIO_MAX = 4.0, 8.0
NORMAL_ROLES = ("tank", "dps", "caster", "speedster", "healer")


def make_gear(level, quality, enhance):
    gear = {}
    for slot in C.EQUIP_SLOT_BASE:
        s = ST.equip_stats(slot, level, quality)
        if enhance > 0:
            mult = C.ENHANCE_TABLE.get(enhance, {}).get("mult", 1.0)
            s = {k: int(v * mult) for k, v in s.items()}
        gear[slot] = {"stats": s, "enhance": enhance}
    return gear


def dmg(atk, def_):
    return max(1, atk * atk / (atk + def_))


def player_stats(lv, enhance):
    gear = make_gear(lv, "blue", enhance)
    st_w = player_final_stats("cls_zhan_shi", lv, gear, 0, None, 0, None, None)
    st_r = player_final_stats("cls_you_xia", lv, gear, 0, None, 0, None, None)
    return st_w, st_r


def collect_instances():
    rows = []
    for iid, inst in sorted(C.INSTANCES.items(), key=lambda x: x[1].get("lv", 0)):
        boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
        if not boss_def:
            continue
        stages = inst.get("stages") or []
        elites = []
        norm_defs = []
        for stg in stages:
            if stg.get("elite"):
                elites.append(stg["elite"])
            for m in stg.get("monsters", []):
                if m[2] not in ("elite", "boss"):
                    norm_defs.append(m)
        rows.append({
            "iid": iid, "name": inst.get("name", iid),
            "inst_lv": inst.get("lv", 0), "lv": boss_def[3], "role": boss_def[2],
            "boss_def": boss_def,
            "hp_mult": inst.get("hp_mult", 1.0), "atk_mult": inst.get("atk_mult", 1.0),
            "min_players": inst.get("min_players", 1),
            "elites": elites, "norm_defs": norm_defs,
        })
    return rows


def eval_boss(row, boss_m, enh):
    """按校准口径评估单场 Boss 战：轮数/承伤风险/Boss:普通怪比（工具口径=合成 dps@BossLv，真实口径=副本内最高血普通怪）"""
    lv, role = row["lv"], row["role"]
    if role == "boss":
        bhp = int(boss_m["max_hp"] * row["hp_mult"])
        batk = int(boss_m["atk"] * row["atk_mult"])
    else:
        bhp = boss_m["max_hp"]
        batk = boss_m["atk"]
    st_w, st_r = player_stats(row["inst_lv"], enh)
    avg = (dmg(st_w["atk"], boss_m["def"]) + dmg(st_r["atk"], boss_m["def"])) / 2
    rounds = bhp / max(avg * row["min_players"] * 1.5, 1)
    risk_w = dmg(batk, st_w["def"]) / max(st_w["hp"], 1)
    risk_r = dmg(batk, st_r["def"]) / max(st_r["hp"], 1)
    risk = max(risk_w, risk_r)
    norm_syn = C.build_monster(("m_cal", "普通怪", "dps", lv, [], []),
                               {"id": "cal", "name": "cal", "area": "cal"})
    ratio_syn = bhp / max(norm_syn["max_hp"], 1)
    if row["norm_defs"]:
        norm_real = max((C.build_monster(m, {"id": row["iid"], "name": row["iid"], "area": "instance"})
                         for m in row["norm_defs"]), key=lambda x: x["max_hp"])
        ratio_real = bhp / max(norm_real["max_hp"], 1)
    else:
        norm_real, ratio_real = None, float("nan")
    return {"bhp": bhp, "batk": batk, "bdef": boss_m["def"], "rounds": rounds,
            "risk": risk, "ratio_syn": ratio_syn, "ratio_real": ratio_real,
            "norm_syn_hp": norm_syn["max_hp"],
            "norm_real_hp": norm_real["max_hp"] if norm_real else 0}


def fmt_ratio(r):
    return "-" if r != r else f"{r:.1f}"


def stages_mult_tbl():
    """① 辅助：hp_stage_mult 新旧对照"""
    def old(lv):
        if lv <= 15: return 1.0
        if lv <= 30: return 1.0 + (lv - 15) * 0.08
        if lv <= 60: return 2.2 + (lv - 30) * 0.04
        return 3.4 + (lv - 60) * 0.03
    def new(lv):
        if lv <= 15: return 1.0
        if lv <= 30: return 1.0 + (lv - 15) * 0.05
        if lv <= 60: return 1.75 + (lv - 30) * 0.04
        return 2.95 + (lv - 60) * 0.03
    return old, new


# ========== 第一步：现状实测 ==========
ROWS = collect_instances()
cur = {}   # iid -> {e3: eval, e5: eval}
print("================ 第一步：现状实测（32 章档位 蓝装+3~+5，Boss ATK 已含 atk_mult） ================")
print(f"{'副本':<6}{'BossLv':>5}{'BossHP':>9}{'BossATK':>7} | {'蓝+3轮':>6}{'蓝+5轮':>6} | {'15-30':>5} | {'承伤(战/游)':>10}")
print("-" * 78)
for row in ROWS:
    m = C.build_monster(row["boss_def"], {"id": row["iid"], "name": row["iid"], "area": "instance"})
    e3 = eval_boss(row, m, 3)
    e5 = eval_boss(row, m, 5)
    cur[row["iid"]] = {"m": m, "e3": e3, "e5": e5,
                       "el_old": {ed[3]: C.build_monster(ed, {"id": row["iid"], "name": row["iid"], "area": "instance"})["max_hp"]
                                  for ed in row["elites"]}}
    ok = "✅" if ROUND_MIN <= e5["rounds"] <= ROUND_MAX else ("🔻少" if e5["rounds"] < ROUND_MIN else "🔺超")
    st_w, st_r = player_stats(row["inst_lv"], 5)
    r_w, r_r = dmg(e5["batk"], st_w["def"]) / max(st_w["hp"], 1), dmg(e5["batk"], st_r["def"]) / max(st_r["hp"], 1)
    print(f"{row['name']:<6}{row['lv']:>5}{e5['bhp']:>9,}{e5['batk']:>7,} | {e3['rounds']:>6.0f}{e5['rounds']:>6.0f} | {ok:>5} | {r_w*100:>4.1f}%~{r_r*100:>4.1f}%")
print()

# ========== 第二步预演：monkeypatch 游戏数据表（仅本进程） ==========
# A) 普通怪成长表原地修改（elite/boss 不动）
gr = ST.MONSTER_ROLE_GROWTH
for role in NORMAL_ROLES:
    gr[role]["def"] = 4.0
    gr[role]["atk"] = 6.0
    gr[role]["hp"] = 25.0
# B) hp_stage_mult 16-30 每级 8%→5%（31+ 平滑续接）
_OLD_STAGE, _NEW_STAGE = stages_mult_tbl()


def _hp_stage_new(lv):
    return _NEW_STAGE(lv)


ST.hp_stage_mult = _hp_stage_new
C.hp_stage_mult = _hp_stage_new  # content 若再导出同名函数一并覆盖

# ---- ① boss/elite 面板受影响核算（hp_stage_mult 作用于所有 role，但 elite/boss 成长不变） ----
print("================ ① monkeypatch 后 elite/boss 面板影响（hp_stage_mult 16-30 级段 8%→5%） ================")
print(f"{'等级':>5}{'旧stage':>9}{'新stage':>9}{'HP变化':>8}")
for lv in (15, 16, 20, 22, 28, 30, 31, 36, 45, 52, 58, 60, 66, 82, 90, 94):
    o, n = _OLD_STAGE(lv), _NEW_STAGE(lv)
    print(f"{lv:>5}{o:>9.2f}{n:>9.2f}{n/o-1:>+8.1%}")
print()
print(f"{'副本':<6}{'BossLv':>5}{'BossHP旧':>9}{'BossHP新':>9}{'BossHP变化':>9} | {'精英Lv':>5}{'精英HP旧':>8}{'精英HP新':>8}{'精英变化':>8}")
print("-" * 90)
for row in ROWS:
    m_old = cur[row["iid"]]["m"]
    m_new = C.build_monster(row["boss_def"], {"id": row["iid"], "name": row["iid"], "area": "instance"})
    role = row["role"]
    if role == "boss":
        bhp_old = int(m_old["max_hp"] * row["hp_mult"])
        bhp_new = int(m_new["max_hp"] * row["hp_mult"])
    else:
        bhp_old, bhp_new = m_old["max_hp"], m_new["max_hp"]
    el_old = el_new = el_lv = None
    if row["elites"]:
        el_def = row["elites"][0]
        el_lv = el_def[3]
        el_old = cur[row["iid"]]["el_old"].get(el_lv)
        el_new = C.build_monster(el_def, {"id": row["iid"], "name": row["iid"], "area": "instance"})["max_hp"]
    el_s = f"{el_lv:>5}{el_old:>8,}{el_new:>8,}{el_new/el_old-1:>+8.1%}" if el_old else f"{'-':>5}{'-':>8}{'-':>8}{'-':>8}"
    print(f"{row['name']:<6}{row['lv']:>5}{bhp_old:>9,}{bhp_new:>9,}{bhp_new/bhp_old-1:>+9.1%} | {el_s} | role={role}")
print()

# ---- ②③④ 新参数下全 Boss 战重算 + 对比 ----
print("================ ③④② 全副本对比：现状 vs 新参数（蓝+5 代表档；Boss:普通怪=工具口径 合成dps@BossLv） ================")
print(f"{'副本':<6}{'BossLv':>5}{'role':>7} | {'现状轮':>6}{'新轮':>6} | {'现状比':>7}{'新比':>7} | {'新BossHP':>9} | 结论")
print("-" * 92)
n_ok, n_ratio_ok, n_round_ok = 0, 0, 0
for row in ROWS:
    m_new = C.build_monster(row["boss_def"], {"id": row["iid"], "name": row["iid"], "area": "instance"})
    n5 = eval_boss(row, m_new, 5)
    c5 = cur[row["iid"]]["e5"]
    r_ok = ROUND_MIN <= n5["rounds"] <= ROUND_MAX
    ratio_ok = RATIO_MIN <= n5["ratio_syn"] <= RATIO_MAX
    if r_ok:
        n_round_ok += 1
    if ratio_ok:
        n_ratio_ok += 1
    if r_ok and ratio_ok:
        n_ok += 1
    if r_ok and ratio_ok:
        concl = "✅ 守线"
    else:
        why = []
        if not r_ok:
            why.append("轮数" + ("偏少<15" if n5["rounds"] < ROUND_MIN else "超标>30"))
        if not ratio_ok:
            why.append("比值" + ("偏低<4" if n5["ratio_syn"] < RATIO_MIN else "超标>8"))
        concl = "⚠ 超标(" + "+".join(why) + ")"
    print(f"{row['name']:<6}{row['lv']:>5}{row['role']:>7} | {c5['rounds']:>6.0f}{n5['rounds']:>6.0f} | {c5['ratio_syn']:>6.1f}x{n5['ratio_syn']:>6.1f}x | {n5['bhp']:>9,} | {concl}")
print()
print(f"新参数达标统计：轮数∈[15,30] {n_round_ok}/{len(ROWS)}；比值∈[4,8] {n_ratio_ok}/{len(ROWS)}；双达标 {n_ok}/{len(ROWS)}")
print()

# ---- 补充：真实小怪口径比值（副本内最高血普通怪，含成长变化） ----
print("================ 补充：Boss:真实普通怪（副本内最高血怪）比值 ================")
print(f"{'副本':<6}{'普通怪Lv':>6}{'现比':>7}{'新比':>7} | {'普通HP旧':>8}{'普通HP新':>8}{'普通怪':>6}")
print("-" * 70)
for row in ROWS:
    if not row["norm_defs"]:
        continue
    top = max(row["norm_defs"], key=lambda m: m[3])
    m_real = C.build_monster(top, {"id": row["iid"], "name": row["iid"], "area": "instance"})
    m_new = C.build_monster(row["boss_def"], {"id": row["iid"], "name": row["iid"], "area": "instance"})
    c5 = cur[row["iid"]]["e5"]
    n5 = eval_boss(row, m_new, 5)
    print(f"{row['name']:<6}{m_real['lv']:>6}{c5['ratio_real']:>6.1f}x{n5['ratio_real']:>6.1f}x | {c5['norm_real_hp']:>8,}{m_real['max_hp']:>8,} | {top[1]:>6}")
print()
print("注：新参数下精英/Boss 成长表未动，仅 hp_stage_mult(16-30 段 8%→5%) 生效；普通怪 def/atk/hp 成长改为 4.0/6.0/25 每级。")
print("结论口径：黄金区间 = 击杀轮数 15-30 轮 且 Boss:普通怪 4-8 倍（相对工具口径合成 dps@BossLv）")