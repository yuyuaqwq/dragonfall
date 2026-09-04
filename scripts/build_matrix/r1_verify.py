# -*- coding: utf-8 -*-
"""v175 R1 病根真引擎复核：0CD 基础技 vs CD 高阶技循环，谁快？

实验设计（真引擎最终裁决）：
  同一职业同等级同装备，rotation A = 只 0CD 基础技 spam；
  rotation B = 正常连招（基础技 + CD 高阶技）。
  打同一 Boss（叠 hp_mult），seeds 固定比胜率/击杀轮。

若 A 明显优于 B（甚至 B 不如纯普攻）→ R1 实证：CD 高阶技是负收益 = 必须修。
"""
from __future__ import annotations
import os, sys, json

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_PLUGIN, "scripts")
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
for _p in (_QQBOT, _PLUGIN, _HERE, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_HERE, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from numeric_lib.battle2 import battle_rotation, attr_pts_total
from build_matrix.boss_matrix import boss_def_of
from data.plugins.dragonfall.game.data import skills as SK


def skill_names_of(cid: str, max_lv: int, only_0cd: bool = False) -> list:
    """该职业 ≤max_lv 的技能名（0CD 过滤可选）。"""
    out = []
    cdef = SK.PLAYER_SKILLS.get(cid, {})
    for info in cdef.get("skills", {}).values():
        if int(info.get("lv", 99) or 99) <= max_lv:
            cd = info.get("cd")
            if only_0cd and cd not in (None, 0):
                continue
            out.append(info["name"])
    br = SK.BRANCH_SKILLS.get(cid, {}).get("branches", {})
    for tier, tdef in br.items():
        if not isinstance(tdef, dict):
            continue
        for line, skills in tdef.items():
            if not isinstance(skills, dict):
                continue
            for info in skills.values():
                if not isinstance(info, dict):
                    continue
                if int(info.get("lv", 99) or 99) <= max_lv and info["name"] not in out:
                    cd = info.get("cd")
                    if only_0cd and cd not in (None, 0):
                        continue
                    out.append(info["name"])
    return out


def main():
    print("== v175 R1 病根真引擎复核：0CD spam vs 含 CD 连招 ==")
    # 用打不死的观察口径也行——改用"伤害竞速"不可行，真引擎只有胜负。
    # 所以选玩家能赢的弱 Boss：哥布林(min=1 且可单刷)，玩家 Lv30 满装
    # 玩家必须能打赢才能比击杀轮。用高等级碾压低 Boss：
    # Lv40 满装 solo_mid 打哥布林 Lv20 → 稳赢，击杀轮反映输出
    PROBES = [
        ("cls_zhan_shi", 40, "solo_mid", "inst_goblin_camp", {"str": 0}),
        ("cls_ci_ke", 40, "solo_mid", "inst_goblin_camp", {"agi": 0}),
        ("cls_fa_shi", 40, "solo_mid", "inst_goblin_camp", {"int": 0}),
        ("cls_you_xia", 40, "solo_mid", "inst_goblin_camp", {"agi": 0}),
        ("cls_wu_seng", 40, "solo_mid", "inst_goblin_camp", {"str": 0}),
    ]
    seeds = 6
    for cid, lv, loadout, iid, attr_tpl in PROBES:
        pts = attr_pts_total(lv)
        attr = {k: pts for k in attr_tpl}
        boss_def = boss_def_of(iid)
        if not boss_def:
            continue
        boss_name = boss_def[1]
        # rotation A: 只有 0CD 基础技（按 lv 排序取前 3）
        all_0cd = skill_names_of(cid, lv, only_0cd=True)
        rot_a = all_0cd[:4]  # 最多 4 个 0CD
        # rotation B: 完整技能池（含 CD 高阶，按学习 lv 排序取前 6）
        all_sk = skill_names_of(cid, lv, only_0cd=False)
        rot_b = all_sk[:6]
        cname = SK.PLAYER_SKILLS.get(cid, {}).get("name", cid)
        print(f"\n--- {cname} Lv{lv} vs {boss_name}（seeds={seeds}）---")
        print(f"  A 纯0CD: {rot_a}")
        print(f"  B 含CD: {rot_b}")
        ra = battle_rotation(cid, lv, loadout, attr, rot_a, boss_def,
                             seeds=seeds, iid=iid, n_players=1, max_turns=800)
        rb = battle_rotation(cid, lv, loadout, attr, rot_b, boss_def,
                             seeds=seeds, iid=iid, n_players=1, max_turns=800)
        wa, wb = ra["wins"], rb["wins"]
        ar_a = f"{ra['avg_rounds']}轮" if wa else f"存活{ra['avg_survive']}轮"
        ar_b = f"{rb['avg_rounds']}轮" if wb else f"存活{rb['avg_survive']}轮"
        verdict = ""
        if wa == 0 and wb == 0:
            verdict = "🟡 都打不过（无法比输出）"
        elif wa > wb:
            verdict = "🔴 R1实证：纯0CD更强（CD高阶技负收益）"
        elif wb > wa:
            verdict = "🟢 含CD连招更强（高阶技有正收益）"
        elif wa > 0:
            # 都能赢：比击杀轮
            if ra["avg_rounds"] < rb["avg_rounds"]:
                verdict = "🔴 R1实证：纯0CD击杀更快（CD高阶技负收益）"
            elif rb["avg_rounds"] < ra["avg_rounds"]:
                verdict = "🟢 含CD击杀更快（高阶技有正收益）"
            else:
                verdict = "🟡 击杀轮相同"
        else:
            verdict = "🟡 胜率相同"
        print(f"  A纯0CD: {wa}/{seeds}胜 {ar_a}")
        print(f"  B含CD:  {wb}/{seeds}胜 {ar_b}")
        print(f"  → {verdict}")


if __name__ == "__main__":
    main()
