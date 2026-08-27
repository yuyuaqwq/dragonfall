# -*- coding: utf-8 -*-
"""全量数值评估矩阵生成器（v131）—— 所有职业 × 档位 × 小怪/精英/Boss/副本 Boss。

输出（真实模型，可复跑）：
  矩阵一：野外战斗 4 档(裸/蓝+5/紫+9/橙+9) × 6 职业 × 4 场景
          (11v11 小怪 / 11v16 越5级小怪 / 11v11 精英 / 11v20 野外Boss)
  矩阵二：副本 Boss 3 档(4人蓝+5/紫+9/橙+9) × 22 副本 × 6 职业（击杀轮+判定）

判定符号：✅=15-30轮且扛得住 / 🟡=30-60偏慢 / 🔴=扛不住(先死)或>60 / ⚠️=<15过速
用法：C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe scripts/gen_numeric_matrix.py
产物：终端打印 markdown + 落盘 docs/NUMERIC_MATRIX_v131.md
"""
import os
import sys

_PD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
_SD = os.path.join(_PD, "scripts")
sys.path.insert(0, _SD)
sys.path.insert(0, _PD)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env  # noqa: E402,F401
from numeric_lib.player import PlayerOptions, build_player, per_action_dmg  # noqa: E402
from numeric_lib.gear import gear_loadout  # noqa: E402
from numeric_lib.constants import CLASSES, LOADOUTS, TEAM_BUFF  # noqa: E402
from numeric_lib.report import md_table  # noqa: E402

# 11 级标准加点（与 tests/numeric_sim STD_ATTR 一致；20 级同样比例）
ATTR = {
    "战士": {"str": 39}, "游侠": {"agi": 39}, "法师": {"int": 39},
    "牧师": {"int": 39}, "刺客": {"agi": 39}, "拳师": {"str": 39},
}
ATTR20 = {k: {a: int(v * 20 / 11) for a, v in d.items()} for k, d in ATTR.items()}


def verdict(kill, survive, n=1):
    if survive < kill * 0.9:
        return "🔴"          # 先死
    if kill > 60:
        return "🔴"
    if kill < 15 and n > 1:
        return "⚠️"
    if kill > 30:
        return "🟡"
    return "✅"


def eval_fight(cls_cn, plv, gear, role, mlv, n=1, team_buff=1.0,
               hp_mult=1.0, min_players=1, monster: dict | None = None):
    """(击杀轮, 承伤轮, 判定)。承伤：仅 elite/boss 吃攻强乘区 ×1.35（enrage 等），普通怪 ×1.0。
    hp_mult>1（副本 Boss）：Boss 有效 HP = 模板 × [hp_mult + 0.65×(n-min_players)]（32 章三）。
    monster：真实怪 dict（副本 Boss 必须传——个体 mod 会让通用模板失真，如老王 30753 vs 通用 22780）。"""
    cid = [c[1] for c in CLASSES if c[0] == cls_cn][0]
    from data.plugins.dragonfall.game import content as C
    from data.plugins.dragonfall.game import engine as E
    if monster is None:
        monster = C.build_monster(("m_eval", "评估怪", role, mlv, [], []),
                                  {"id": "eval", "name": "eval", "area": "eval"})
    m = monster
    ehp = m.get("max_hp", 1)
    if hp_mult > 1.0:
        ehp = int(ehp * (hp_mult + 0.65 * max(0, n - min_players)))
    edef, emdef = m.get("def", 0), m.get("mdef", 0)
    st = build_player(cid, plv, gear, PlayerOptions(), potion=0.0)
    d = per_action_dmg(cid, plv, gear, edef, emdef, PlayerOptions(), potion_on=True)
    kill = ehp / max(d * n * team_buff, 0.01)
    # 承伤
    boss_mult = 1.35 if role in ("elite", "boss") else 1.0
    d_ph = E.calc_damage(int(m.get("atk", 0) * boss_mult), int(st.get("def", 0)),
                         variance=0.0, dmg_type="phys")
    d_mg = E.calc_damage(int(m.get("matk", 0) * boss_mult), int(st.get("mdef", 0)),
                         variance=0.0, dmg_type="magi")
    hit = max(d_ph, d_mg, 1)
    survive = st.get("max_hp", 1000) * n / hit
    return round(kill, 1), round(survive, 1), verdict(kill, survive, n)


def main():
    out = []
    out.append("# 全量数值评估矩阵 v131（2026-08-27，真实玩家模型）")
    out.append("")
    out.append("> 生成：scripts/gen_numeric_matrix.py（可复跑）；判定：✅15-30轮且扛得住 / 🟡偏慢 / "
               "🔴扛不住或>60轮 / ⚠️<15轮过速；承伤=HP池/怪单发（elite/boss 攻强 ×1.35）")

    # ---------- 矩阵一：野外 ----------
    out.append("\n## 矩阵一：野外战斗（单刷，各档位全乘区）")
    out.append("\n### 1.1 同级小怪 11v11 dps：击杀轮")
    rows = []
    gear_cache = {}
    for lo in ("naked", "solo_mid", "team_purple9", "team_orange9"):
        g = gear_loadout(11, lo)
        for cn, *_ in CLASSES:
            k, s, v = eval_fight(cn, 11, g, "dps", 11)
            rows.append({"档位": LOADOUTS[lo]["label"], "职业": cn, "击杀轮": k, "承伤轮": s, "判定": v})
    out.append(md_table(rows, ["档位", "职业", "击杀轮", "承伤轮", "判定"]))

    out.append("\n### 1.2 越 5 级小怪 11v16 dps：击杀轮 / 承伤轮 / 判定（跨级全胜问题核心）")
    rows = []
    for lo in ("naked", "solo_mid", "team_purple9", "team_orange9"):
        g = gear_loadout(11, lo)
        for cn, *_ in CLASSES:
            k, s, v = eval_fight(cn, 11, g, "dps", 16)
            rows.append({"档位": LOADOUTS[lo]["label"], "职业": cn, "击杀轮": k, "承伤轮": s, "判定": v})
    out.append(md_table(rows, ["档位", "职业", "击杀轮", "承伤轮", "判定"]))

    out.append("\n### 1.3 同级精英 11v11 elite：击杀轮 / 承伤轮 / 判定")
    rows = []
    for lo in ("naked", "solo_mid", "team_purple9", "team_orange9"):
        g = gear_loadout(11, lo)
        for cn, *_ in CLASSES:
            k, s, v = eval_fight(cn, 11, g, "elite", 11)
            rows.append({"档位": LOADOUTS[lo]["label"], "职业": cn, "击杀轮": k, "承伤轮": s, "判定": v})
    out.append(md_table(rows, ["档位", "职业", "击杀轮", "承伤轮", "判定"]))

    out.append("\n### 1.4 野外 Boss（20 级玩家打 20 级 Boss，模拟真实最低野外 Boss 哥布林酋长档）：")
    rows = []
    for lo in ("naked", "solo_mid", "team_purple9", "team_orange9"):
        g = gear_loadout(20, lo)
        for cn, *_ in CLASSES:
            k, s, v = eval_fight(cn, 20, g, "boss", 20)
            rows.append({"档位": LOADOUTS[lo]["label"], "职业": cn, "击杀轮": k, "承伤轮": s, "判定": v})
    out.append(md_table(rows, ["档位", "职业", "击杀轮", "承伤轮", "判定"]))

    # ---------- 矩阵二：副本 Boss ----------
    from numeric_lib.team import team_matrix
    from data.plugins.dragonfall.game import content as C
    out.append("\n## 矩阵二：副本 Boss（每副本 × 档位 × 6 职业；人数=档位人数，BossHP 按 hp_mult 公式）")
    # 手动构造：对每个 (iid, loadout, cls) 用 eval_fight 打副本 Boss（4 人池承伤）
    insts = sorted(C.INSTANCES.items(), key=lambda x: x[1].get("lv", 0))
    for lo in ("team_mid", "team_purple9", "team_orange9"):
        n = LOADOUTS[lo]["players"]
        out.append(f"\n### 档位：{LOADOUTS[lo]['label']}（{n} 人）")
        rows = []
        for iid, inst in insts:
            lv = inst.get("lv", 0)
            boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
            if not boss_def:
                continue
            mn = inst.get("min_players", 1)
            row = {"副本": iid[:18], "Lv": lv}
            # 真 Boss（含个体 mod）：矩阵必须用实例 Boss 构建，通用模板会失真
            real_boss = C.build_monster(boss_def, {"id": iid, "name": iid, "area": "instance"})
            for cn, *_ in CLASSES:
                # 副本 Boss：有效 HP = 模板 × [hp_mult + 0.65×(n-min_players)]（32 章三）
                g = gear_loadout(lv, lo)
                k, s, v = eval_fight(cn, lv, g, "boss", boss_def[3], n=n, team_buff=TEAM_BUFF,
                                     hp_mult=inst.get("hp_mult", 1.0), min_players=mn,
                                     monster=real_boss)
                row[cn] = f"{k:.0f}{v}"
            rows.append(row)
        out.append(md_table(rows, ["副本", "Lv"] + [cn for cn, *_ in CLASSES]))

    text = "\n".join(out)
    print(text)
    with open(os.path.join(_PD, "docs", "NUMERIC_MATRIX_v131.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("\n（已落盘 docs/NUMERIC_MATRIX_v131.md）")
    return 0


if __name__ == "__main__":
    sys.exit(main())