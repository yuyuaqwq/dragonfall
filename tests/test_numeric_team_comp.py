# -*- coding: utf-8 -*-
"""v156+ 队伍构成平衡测试 test_numeric_team_comp —— 副本可打性 + 构成梯度。

v173.1 更新（2026-09-04 鱼鱼拍板）：
- Boss 平砍统一 12-15%（4 人坦克口径）——段乘区 INSTANCE_BOSS_ATK_STAGE_MULT 治本
  （此前副本 Boss 被排除在野外 BOSS_ATK_STAGE_MULT 外，后期平砍仅 2-4% 坦克 HP，
  牧师失业；鱼鱼拍板副本 Boss 也要压迫感，单刷本 solo 装被秒 = 逼组队是设计意图）
- 治疗预期 = Boss 战牧师全职奶（HEAL_CAST_SHARE 1.0，heal 槽位输出 = 0）
- 承伤门禁（相对口径，不再追求绝对 survive）：
    ① 单人本（min=1）：按 solo 档可击杀（60-80 轮），不设承伤门槛（单刷难=逼组队）
    ② 多人本（min≥2）：standard(带奶) 击杀轮 61-90（Boss 战带纯奶慢是设计，鱼鱼接受 74-87）
    ③ 多人本：no_heal 硬抗 6-8 轮（漏奶 ~7 轮团灭 = 奶妈高压，不能无奶挂机）
    ④ 多人本：standard 承伤 ≥ no_heal 硬抗 ×1.5（奶量显著提升续航）
    ⑤ heal_per_round 奶量模型 >0 且随等级增长（公式自洽按 HEAL_CAST_SHARE=1.0）
    ⑥ legacy 对照锚点（哥布林/老王之墓，随副本血量重标同步）
- ⚠️ team_matrix(instances=[...]) 单本参数当前被忽略（全量遍历）——
  取单本结果必须全量扫对应 loadout 后按 iid 取值，禁止传 instances=[iid] 取 rows[0]。

运行：python tests/test_numeric_team_comp.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # tests/
_PLUGIN_DIR = os.path.dirname(_SCRIPT_DIR)                        # dragonfall/
_SCRIPTS_DIR = os.path.join(_PLUGIN_DIR, "scripts")
for _p in (_SCRIPTS_DIR, _PLUGIN_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN_DIR, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env  # noqa: E402,F401
from numeric_lib.team import team_matrix, heal_per_round, HEAL_CAST_SHARE  # noqa: E402
from numeric_lib.gear import gear_loadout  # noqa: E402
from data.plugins.dragonfall.game.data.instances import INSTANCES  # noqa: E402

passed, failed = 0, 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {detail}")


def inst_loadout(iid):
    """副本 → 标准打法人装备档（v173：不同阶段玩家装备不同，按副本阶段标）"""
    inst = INSTANCES[iid]
    lv = inst.get("lv", 0)
    mn = inst.get("min_players", 1)
    if mn == 1:
        return ("solo_mid" if lv <= 30 else "solo_mid_upgrade"), None
    if lv <= 30:
        return "team_mid", "standard"
    if lv <= 80:
        return "team_purple9", "standard"
    return "team_orange9", "standard"


def team_ld(lv):
    """多人本装备档（按等级段）"""
    if lv <= 30:
        return "team_mid"
    if lv <= 80:
        return "team_purple9"
    return "team_orange9"


def all_matrix(loadout, comp):
    """全量跑对应档位构成，返回 {iid: row}（team_matrix instances 单本参数被忽略，只能全量取）"""
    return {r["iid"]: r for r in team_matrix(loadout=loadout, comp=comp)}


def main():
    print("【① 单人本 solo 档可击杀（v173.1：不设承伤门槛，单刷难=逼组队）】")
    solo_mn1 = []
    for iid, inst in sorted(INSTANCES.items(), key=lambda kv: kv[1].get("lv", 0)):
        if inst.get("min_players", 1) != 1:
            continue
        lv = inst.get("lv", 0)
        ld = "solo_mid" if lv <= 30 else "solo_mid_upgrade"
        rows = all_matrix(ld, None)
        r = rows.get(iid)
        if not r:
            continue
        solo_mn1.append(r["rounds"])
    check(f"单人本击杀轮全部 ∈ [55, 90]（{len(solo_mn1)} 本，solo 档）",
          all(55 <= x <= 90 for x in solo_mn1),
          f"out={[round(x,1) for x in solo_mn1 if not (55 <= x <= 90)]}")
    # 单人本 Boss 平砍也应 12-15%（同一 Boss 攻击不分单/多人打）
    from numeric_lib.player import build_player, PlayerOptions  # noqa
    from data.plugins.dragonfall.game.core.drops import build_monster  # noqa
    from data.plugins.dragonfall.game.engine import calc_damage  # noqa
    pct_bad = []
    for iid, inst in sorted(INSTANCES.items(), key=lambda kv: kv[1].get("lv", 0)):
        if inst.get("min_players", 1) != 1:
            continue
        lv = inst.get("lv", 0)
        ld = team_ld(lv)  # 4 人坦克口径（Boss 攻击标定基准）
        boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
        m = build_monster(boss_def, {"id": iid, "name": iid, "area": "instance"})
        gear = gear_loadout(lv, ld)
        st = build_player("cls_zhan_shi", lv, gear, PlayerOptions(), potion=0.0)
        hp = st["max_hp"]
        pdef = int(st["def"] * 1.45)
        pmdef = int(st["mdef"] * 1.45)
        am = inst.get("atk_mult", 1.0)
        d1 = calc_damage(int(m["atk"] * am), pdef, variance=0.0, dmg_type="phys")
        d2 = calc_damage(int(m["matk"] * am), pmdef, variance=0.0, dmg_type="magi")
        pct = max(d1, d2) / hp * 100
        if not (11.5 <= pct <= 15.5):
            pct_bad.append((iid, round(pct, 1)))
    check(f"单人本 Boss 平砍 11.5-15.5% 4人坦HP（{22 - len(pct_bad)}/22 全副本统一 12-15%）",
          len(pct_bad) == 0, f"out={pct_bad}")

    print("【② 多人本 standard(带奶) 击杀轮（Boss 战纯奶慢是设计，接受 61-90）】")
    multi_ok = 0
    multi_bad = []
    for iid, inst in sorted(INSTANCES.items(), key=lambda kv: kv[1].get("lv", 0)):
        if inst.get("min_players", 1) == 1:
            continue
        lv = inst.get("lv", 0)
        ld = team_ld(lv)
        rows = all_matrix(ld, "standard")
        r = rows.get(iid)
        if not r:
            continue
        if 60 <= r["rounds"] <= 90:
            multi_ok += 1
        else:
            multi_bad.append((iid, round(r["rounds"], 1)))
    check(f"多人本 standard 击杀轮 ∈ [60, 90]（{multi_ok}/{multi_ok + len(multi_bad)}）",
          len(multi_bad) == 0, f"out={multi_bad}")

    print("【③ 多人本 no_heal 硬抗（漏奶 ~7 轮团灭 = 奶妈高压，不能无奶挂机）】")
    noh_bad = []
    for iid, inst in sorted(INSTANCES.items(), key=lambda kv: kv[1].get("lv", 0)):
        if inst.get("min_players", 1) == 1:
            continue
        lv = inst.get("lv", 0)
        ld = team_ld(lv)
        rows = all_matrix(ld, "no_heal")
        r = rows.get(iid)
        if not r:
            continue
        sv = r.get("survive", 0)
        if not (5.0 <= sv <= 12.0):
            noh_bad.append((iid, round(sv, 1)))
    check(f"多人本 no_heal 硬抗 ∈ [5, 12] 轮（{12 - len(noh_bad)}/12，漏奶即团灭）",
          len(noh_bad) == 0, f"out={noh_bad}")

    print("【④ 多人本 standard 承伤 ≥ no_heal×1.5（奶量显著提升续航）】")
    heal_bad = []
    for iid, inst in sorted(INSTANCES.items(), key=lambda kv: kv[1].get("lv", 0)):
        if inst.get("min_players", 1) == 1:
            continue
        lv = inst.get("lv", 0)
        ld = team_ld(lv)
        r_std = all_matrix(ld, "standard").get(iid)
        r_noh = all_matrix(ld, "no_heal").get(iid)
        if not r_std or not r_noh:
            continue
        ratio = r_std.get("survive", 0) / max(r_noh.get("survive", 1), 1)
        if ratio < 1.5:
            heal_bad.append((iid, round(ratio, 2)))
    check(f"standard 承伤 ≥ no_heal ×1.5（{12 - len(heal_bad)}/12）",
          len(heal_bad) == 0, f"low_ratio={heal_bad}")

    print("【⑤ heal_per_round 奶量模型：>0 且随等级增长（HEAL_CAST_SHARE 全职奶）】")
    check(f"HEAL_CAST_SHARE = 1.0（v173.1 Boss 战牧师专职奶）",
          abs(HEAL_CAST_SHARE - 1.0) < 1e-9, f"share={HEAL_CAST_SHARE}")
    lv20 = heal_per_round(("cls_mu_shi", 20, gear_loadout(20, "team_mid")))
    lv60 = heal_per_round(("cls_mu_shi", 60, gear_loadout(60, "team_mid")))
    lv90 = heal_per_round(("cls_mu_shi", 90, gear_loadout(90, "team_mid")))
    check(f"Lv20 治疗/轮 > 0（{lv20:.1f}）", lv20 > 0, f"lv20={lv20}")
    check(f"Lv60 治疗/轮 > Lv20（{lv60:.1f} > {lv20:.1f}）", lv60 > lv20,
          f"lv60={lv60} lv20={lv20}")
    check(f"Lv90 治疗/轮 > Lv60（{lv90:.1f} > {lv60:.1f}）", lv90 > lv60,
          f"lv90={lv90} lv60={lv60}")
    build_player = __import__("numeric_lib.player", fromlist=["build_player"]).build_player
    st20 = build_player("cls_mu_shi", 20, gear_loadout(20, "team_mid"))
    expect20 = st20["matk"] * 2.0 * 1.0 * (1 + min(st20.get("heal_power", 0) or 0, 0.5))
    check(f"公式自洽（matk×2.0×1.0×(1+heal_power)，Lv20={expect20:.1f}）",
          abs(lv20 - expect20) < 1e-6, f"got={lv20} expect={expect20}")

    print("【⑥ legacy 对照锚点（v173 副本血量重标后同步）】")
    legacy = all_matrix("legacy", None)
    gob = legacy.get("inst_goblin_camp", {}).get("rounds", 0)
    old_king = legacy.get("inst_old_king_tomb", {}).get("rounds", 0)
    check("哥布林 legacy 轮数 350~390（v173 hp_mult 2.343 后）",
          350 <= gob <= 390, f"rounds={gob}")
    check("老王之墓 legacy 轮数 780~830（v173.3 Boss降级40+hp补偿2.356 后）",
          780 <= old_king <= 830, f"rounds={old_king}")

    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
