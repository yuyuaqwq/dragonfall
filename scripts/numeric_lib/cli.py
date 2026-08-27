# -*- coding: utf-8 -*-
"""numeric_lib 统一 CLI —— 多维度数值计算的通用入口。

用法（python scripts/numeric_lib/cli.py <subcommand>）：
  player 战士 60 --gear solo_mid           面板 + 乘区归因表（每项单独倍率）
  dmg    战士 60 solo_mid 16               一次行动伤害 + 击杀回合估算
  calib  --loadout team_mid                全副本 Boss 轮数表（真实玩家模型）
  calib  --loadout legacy                  旧残疾模型（对照，应等于升级前输出）
  team   --inst inst_goblin_camp --n 4     单副本组队矩阵
  matrix --cls 战士,刺客 --lv 11 --mlv 16 --role dps --seeds 8   真实引擎胜率
  diff   --before a.json --after b.json    双 JSON 对比

全局：--json 只输出 JSON（管道友好）；--loadout 档位：
  solo_low(蓝+0单刷) solo_mid(蓝+5单刷) team_mid(4人蓝+5) team_max(4人蓝+9) legacy(旧模型对照)
"""
import argparse
import json
import os
import sys

_SDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scripts/
if _SDIR not in sys.path:
    sys.path.insert(0, _SDIR)

from numeric_lib.env import setup_env  # noqa: E402,F401
from numeric_lib.constants import LOADOUTS, cls_id, cls_name, CLASSES  # noqa: E402
from numeric_lib.player import PlayerOptions, build_player, per_action_dmg, dmg_budget  # noqa: E402
from numeric_lib.gear import gear_loadout  # noqa: E402
from numeric_lib.monster import build as build_monster, curve_override  # noqa: E402
from numeric_lib.team import team_matrix, boss_hp, team_net_mult, team_rounds, instance_details  # noqa: E402
from numeric_lib.battle import win_rate, monster_of  # noqa: E402
from numeric_lib.report import md_table, to_json, diff_tables  # noqa: E402


def _load(args):
    return LOADOUTS.get(args.loadout, LOADOUTS["solo_mid"])


def cmd_player(args):
    cid = cls_id(args.cls)
    gear = {} if args.naked else gear_loadout(args.lv, args.loadout)
    opts = PlayerOptions(attr_points=not args.no_attr, tier=not args.no_tier,
                         evolve=not args.no_evolve, skills=not args.no_skill,
                         affixes=not args.no_affix, enchant=not args.no_enchant,
                         potion=not args.no_potion)
    st = build_player(cid, args.lv, gear, opts, potion=0.0)
    # 取一个同等级 dps 怪做目标
    m = monster_of("dps", args.mlv or args.lv)
    edef, mdef = m.get("def", 0), m.get("mdef", 0)
    dmg = per_action_dmg(cid, args.lv, gear, edef, mdef, opts, potion_on=True)
    budget = dmg_budget(cid, args.lv, gear, edef, mdef, opts)
    rows = [
        {"面板": k, "值": v} for k, v in st.items()
        if k in ("max_hp", "atk", "def", "spd", "matk", "mdef", "crit", "crit_dmg", "pene_phys")
    ]
    rows += [
        {"面板": "对Lv%d dps怪 单发期望" % (args.mlv or args.lv), "值": round(dmg, 1)},
        {"面板": "击杀回合(怪HP%d)" % m.get("max_hp", 0), "值": round(m.get("max_hp", 0) / max(dmg, 1), 1)},
        {"面板": "全乘区累乘", "值": round(budget["total_mult"], 2)},
    ]
    lines = [f"# {cls_name(cid)} Lv{args.lv} ({args.loadout})", md_table(rows, ["面板", "值"])]
    if not args.json:
        lines.append("\n## 乘区归因（每项单独倍率，基准=全关）")
        lines.append(md_table(
            [{"乘区": k, "倍率": round(v, 2)} for k, v in budget["items"].items()],
            ["乘区", "倍率"]))
    if args.json:
        return to_json({"panel": {k: v for k, v in rows}, "budget": budget})
    print("\n".join(lines))
    return ""


def cmd_dmg(args):
    cid = cls_id(args.cls)
    gear = gear_loadout(args.lv, args.loadout)
    m = build_monster(args.role, args.mlv or args.lv)
    edef, mdef = m.get("def", 0), m.get("mdef", 0)
    dmg = per_action_dmg(cid, args.lv, gear, edef, mdef, PlayerOptions(), potion_on=True)
    hp = m.get("max_hp", 0)
    if args.json:
        return to_json({"cls": args.cls, "role": args.role, "mlv": args.mlv or args.lv,
                        "dmg": dmg, "kills": hp / max(dmg, 1), "hp": hp})
    print(f"{cls_name(cid)} Lv{args.lv} 对 {args.role} Lv{args.mlv or args.lv}：单发期望 {dmg:.1f}，"
          f"怪HP {hp:,} → 击杀约 {hp / max(dmg, 1):.1f} 回合")
    return ""


def cmd_calib(args):
    rows = team_matrix(loadout=args.loadout)
    if args.json:
        return to_json(rows)
    head = "全副本 Boss 轮数表（真实玩家模型）— 档位: %s" % LOADOUTS[args.loadout]["label"]
    print(head)
    print(md_table(rows, ["iid", "lv", "boss_lv", "boss_hp", "ratio", "rounds", "survive", "flag"],
                   {"iid": "副本", "lv": "本Lv", "boss_lv": "BossLv", "boss_hp": "BossHP",
                    "ratio": "Boss:普通怪", "rounds": "击杀轮", "survive": "承伤轮", "flag": "判定"}))
    bad = [r for r in rows if r["flag"] == "🔴"]
    print(f"\n异常: {len(bad)}/{len(rows)}"
          f"（🔴=先死打不过或>60轮；⚠️=<15轮过速；承伤轮<击杀轮=扛不住；舒适区=15-30轮）")
    return ""


def cmd_team(args):
    inst, boss_def = instance_details(args.inst)
    m = build_monster(boss_def, {"id": args.inst, "name": args.inst, "area": "instance"})
    mn = inst.get("min_players", 1)
    lv = inst.get("lv", 0)
    gear = gear_loadout(lv, args.loadout)
    from .player import per_action_dmg
    dmg = per_action_dmg("cls_zhan_shi", lv, gear, m.get("def", 0), m.get("mdef", 0),
                         PlayerOptions(), potion_on=True)
    rows = []
    for n in range(mn, 5):
        hpt = boss_hp(m.get("max_hp", 0), n, mn, inst.get("hp_mult"))
        rr = team_rounds(dmg, n, hpt)
        net = team_net_mult(n, mn, inst.get("hp_mult"))
        rows.append({"人数": n, "BossHP": hpt, "轮数": round(rr, 1), "净效率": round(net, 2)})
    if args.json:
        return to_json(rows)
    print(f"# {args.inst} Lv{lv} Boss: {m.get('name', boss_def)} （min={mn}人，战士蓝装档模型）")
    print(md_table(rows, ["人数", "BossHP", "轮数", "净效率"],
                   {"人数": "人数", "BossHP": "BossHP", "轮数": "击杀轮数", "净效率": "组队净效率"}))
    print("净效率>1 = 组队比单刷快（血量涨幅 < DPS增幅）；保守口径见 team.py 文档")
    return ""


def cmd_matrix(args):
    rows = []
    for cls_ in args.cls.split(","):
        for mlv in [int(x) for x in args.mlv.split(",")]:
            wins, rounds = win_rate(cls_, args.lv, None if args.attr == "auto" else args.attr,
                                    {} if args.naked else None, args.role, mlv,
                                    seeds=args.seeds, use_skill=args.skill)
            rows.append({"职业": cls_name(cls_id(cls_)), "vs": f"Lv{mlv} {args.role}",
                         "胜率": f"{wins}/{args.seeds}", "均回合": round(rounds, 1)})
    if args.json:
        return to_json(rows)
    print(md_table(rows, ["职业", "vs", "胜率", "均回合"]))
    return ""


def cmd_diff(args):
    with open(args.before, encoding="utf-8") as f:
        before = json.load(f)
    with open(args.after, encoding="utf-8") as f:
        after = json.load(f)
    print(diff_tables(before, after, key_col=args.key))
    return ""


def main(argv=None):
    p = argparse.ArgumentParser(prog="numeric_lib", description="多维度数值计算工具集")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(pp, default_loadout="solo_mid"):
        pp.add_argument("--loadout", choices=list(LOADOUTS), default=default_loadout)
        pp.add_argument("--json", action="store_true")

    sp = sub.add_parser("player", help="面板 + 乘区归因")
    sp.add_argument("cls"); sp.add_argument("lv", type=int)
    sp.add_argument("--mlv", type=int, default=0, help="目标怪等级（默认同玩家等级）")
    sp.add_argument("--naked", action="store_true", help="裸装")
    for flag in ("attr", "tier", "evolve", "skill", "affix", "enchant", "potion"):
        sp.add_argument(f"--no-{flag}", action="store_true", help=f"关闭乘区 {flag}")
    common(sp)

    sp = sub.add_parser("dmg", help="单发伤害 + 击杀回合")
    sp.add_argument("cls"); sp.add_argument("lv", type=int)
    sp.add_argument("role", default="dps", nargs="?")
    sp.add_argument("--mlv", type=int, default=0)
    common(sp)

    sp = sub.add_parser("calib", help="全副本 Boss 轮数（真实模型）")
    common(sp, default_loadout="team_mid")

    sp = sub.add_parser("team", help="单副本组队矩阵")
    sp.add_argument("--inst", required=True)
    sp.add_argument("--n", type=int, default=0, help="人数（默认扫全部合法人数）")
    common(sp, default_loadout="solo_mid")

    sp = sub.add_parser("matrix", help="真实引擎胜率矩阵")
    sp.add_argument("--cls", required=True, help="职业，逗号分隔")
    sp.add_argument("--lv", type=int, required=True)
    sp.add_argument("--mlv", required=True, help="怪等级，逗号分隔")
    sp.add_argument("--role", default="dps")
    sp.add_argument("--attr", default="auto")
    sp.add_argument("--seeds", type=int, default=8)
    sp.add_argument("--naked", action="store_true")
    sp.add_argument("--skill", action="store_true", help="技能循环（否则纯普攻）")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("diff", help="双 JSON 对比")
    sp.add_argument("--before", required=True)
    sp.add_argument("--after", required=True)
    sp.add_argument("--key", default="iid")

    args = p.parse_args(argv)
    fn = {"player": cmd_player, "dmg": cmd_dmg, "calib": cmd_calib,
          "team": cmd_team, "matrix": cmd_matrix, "diff": cmd_diff}[args.cmd]
    out = fn(args)
    if isinstance(out, str) and out:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())