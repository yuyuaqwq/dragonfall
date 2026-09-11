# -*- coding: utf-8 -*-
"""v175 期望 vs 真引擎抽验 —— 校准期望模型可信度（门禁仲裁依据）。

抽验格：各职业推荐流派 × 对应当前阶段真实 Boss。
期望模型 = build_matrix.build_vs_boss（击杀轮预估）
真引擎   = numeric_lib.saintess_engine.battle_rotation（真实 BT.Battle 多技能循环）

输出每格：期望击杀轮 / 真引擎胜率+实际击杀轮 / 偏差 / 结论
"""
from __future__ import annotations
import os, sys, json

_BM_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.dirname(_BM_DIR)
_PLUGIN = os.path.dirname(_SCRIPTS)
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
_TESTS = os.path.join(_PLUGIN, "tests")
for _p in (_QQBOT, _PLUGIN, _TESTS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS, "test_game_data.db"))

from build_matrix.build_matrix import build_vs_boss, resolve_attr, build_panel
from build_matrix.boss_matrix import boss_def_of, boss_panel
from numeric_lib.saintess_engine import battle_rotation, attr_pts_total
from data.plugins.dragonfall.game.data import instances as I


def load_cls(cid: str) -> dict:
    with open(os.path.join(_BM_DIR, "..", "balance_data", f"{cid}.json"), encoding="utf-8") as f:
        return json.load(f)


# 抽验格： (职业, 等级/阶段档, 流派, Boss实例, 加点名)
PROBES = [
    # 战士 P1 打哥布林
    ("cls_zhan_shi", 20, "solo_low", "狂战流", "inst_goblin_camp", "full_str"),
    ("cls_zhan_shi", 20, "solo_low", "血怒流", "inst_goblin_camp", "offtank"),
    # 法师 P2 打海蚀（需跨级，实际用海蚀22级boss但玩家24）
    ("cls_fa_shi", 24, "solo_mid", "元素爆发流", "inst_sea_cave", "full_int"),
    # 游侠 P1 打哥布林
    ("cls_you_xia", 20, "solo_low", "疾风连射流", "inst_goblin_camp", "full_agi"),
    # 刺客 P2 打海蚀
    ("cls_ci_ke", 24, "solo_mid", "影舞连段流", "inst_sea_cave", "full_agi"),
    # 拳师 P2
    ("cls_wu_seng", 24, "solo_mid", "破绽连打流", "inst_sea_cave", "full_str"),
    # 牧师 P1（治疗流应该打不死——验证期望"杀不死"与真引擎一致）
    ("cls_mu_shi", 20, "solo_low", "神谕治疗流", "inst_goblin_camp", "full_int"),
    # 诗人 P2（期望废，验证真引擎）
    ("cls_shi_ren", 24, "solo_mid", "咏叹鼓舞流", "inst_sea_cave", "full_int"),
]


def run_probe(cid, lv, loadout, bname, iid, attr_name, seeds=6):
    jd = load_cls(cid)
    if bname not in jd["builds"]:
        return {"error": f"build {bname} not in {cid}"}
    bdef = jd["builds"][bname]
    rotation_dict = bdef["rotation"]           # [{"skill","cond","prio"}...]
    rotation_names = [s["skill"] for s in rotation_dict]  # ["挥砍",...]
    apreset = jd["attr_presets"].get(attr_name, jd["builds"][bname].get("attr_preset", {"str": "all"}))
    # attr_preset 可能是名字（字符串）或 dict
    if isinstance(apreset, str):
        apreset = jd["attr_presets"][apreset]
    attr = resolve_attr(apreset, lv)
    boss_def = boss_def_of(iid)
    if not boss_def:
        return {"error": f"no boss for {iid}"}
    # 期望（rotation_dps 吃 dict 列表；iid 让 Boss 叠 hp_mult，与真引擎同口径）
    try:
        exp = build_vs_boss(cid, lv, loadout, attr, rotation_dict, boss_def,
                            int(boss_def[3]), iid=iid, n_players=1)
    except Exception as ex:
        exp = {"error": str(ex)}
    # 真引擎（battle_rotation 吃名字列表；iid 叠 hp_mult）
    try:
        real = battle_rotation(cid, lv, loadout, attr, rotation_names, boss_def,
                               seeds=seeds, iid=iid, n_players=1)
    except Exception as ex:
        real = {"error": str(ex)}
    return {"exp": exp, "real": real, "rotation": rotation_names, "boss": boss_def[1], "boss_lv": boss_def[3]}


if __name__ == "__main__":
    print("== 期望 vs 真引擎抽验 ==")
    for p in PROBES:
        cid, lv, loadout, bname, iid, attr_name = p
        jd = load_cls(cid)
        cname = jd.get("class_name", cid)
        r = run_probe(*p)
        print(f"\n--- {cname} {bname} Lv{lv} ({loadout}) vs {r.get('boss','?')} Lv{r.get('boss_lv','?')} ---")
        exp = r.get("exp", {})
        real = r.get("real", {})
        exp_kill = exp.get("kill_rounds", "err")
        exp_verdict = exp.get("verdict", "")
        real_wins = real.get("wins", "err")
        real_rounds = real.get("avg_rounds", 0)
        real_survive = real.get("avg_survive", 0)
        print(f"  期望: 击杀{exp_kill}轮 {exp_verdict} | 生存{exp.get('survive_rounds','?')}轮")
        print(f"  真引擎: {real_wins}/{real.get('seeds','?')}胜 击杀{real_rounds}轮 存活{real_survive}轮")
        if isinstance(exp_kill, (int, float)) and isinstance(real_rounds, (int, float)) and real_wins and real_wins > 0:
            delta = exp_kill - real_rounds
            flag = "✅" if abs(delta) <= 15 else ("🟡" if abs(delta) <= 30 else "🔴")
            print(f"  偏差: {flag} 期望-实际 = {delta:+.0f}轮")
        elif isinstance(exp_kill, str) and real_wins == 0:
            print(f"  ✅ 一致：期望{exp_kill} + 真引擎打不死")
        else:
            print("  ⚠️ 需要看（期望 vs 实际不一致或数据缺失）")
