# -*- coding: utf-8 -*-
"""通用数值实验 CLI numtool —— 任意 职业/等级/加点/装备/怪 role/等级/种子数 的胜率+面板实验。

纯工具：不锁死任何断言（数值门禁请用 scripts/run_numeric_tests.py + tests/test_numeric_*.py），
本工具只负责快速、可复现地输出 面板 → 胜率 → 建议，供人工标定/对比/调参参考。

用法示例：
  python scripts/numtool.py --cls 战士 --lv 11 --attr auto --mlv 22 --role dps
  python scripts/numtool.py --cls 刺客,拳师 --lv 11 --attr agi:39 --mlv 11 --role dps --seeds 8 --vs
  python scripts/numtool.py --cls 法师 --lv 11 --attr auto --mlv 11 --role dps --equip full --skill auto --seeds 16
  python scripts/numtool.py --cls 战士 --lv 11 --attr auto --mlv 22 --role dps --json
  python scripts/numtool.py --cls 战士 --lv 11 --attr auto --mlv 11 --role elite --equip full,weapon:海风长弓

实现口径（与 tests/numeric_sim.py 完全一致）：
  - import numeric_sim 复用其 面板/怪/战斗 构造（core 公式零 mock，GWEN_GAME_DB 同 test_game_data.db）
  - BT.Battle 直连模拟；固定种子序列 seed 0..N-1（每场先 random.seed(seed)，可复现；装备生成用固定种子）
  - ⚠️ 玩家 dict 必须传【同一个 dict】给 BT.Battle：战斗内 hp 修改保留在该 dict
    （历史教训 v130.10：每次 dict() 新副本 → 玩家永不掉血、假胜率）。本工具战后自动校验：
    defeat 时玩家 hp 仍满 → 输出 Fake hp 警告（dict 未同步）。

参数：
  --cls      职业名（中文或 ID，逗号分隔多个）         必填，如 战士 / cls_zhan_shi / 战士,法师
  --lv       玩家等级                                 必填
  --attr     加点 dict（如 agi:39,str:0；'auto'=职业推荐加点）  默认 auto
  --mlv      怪等级                                   必填
  --role     怪类型 dps/tank/elite/boss/caster/speedster      默认 dps
  --seeds    场数（固定种子 0..N-1）                   默认 8
  --equip    none=裸装 / full=按等级自动配满装（名册每槽最高 ≤lv 件；槽位无 ≤lv 件时取最低档）
             高级：逗号组合 'slot:名册名/rid' 覆盖（如 full,weapon:海风长弓）    默认 none
  --skill    none=纯普攻 / auto=职业代表性技能循环     默认 none
  --vs       对比模式：多职业时末尾输出对比表
  --json     只输出 JSON（管道友好，供脚本消费）
"""
import argparse
import json
import os
import random
import sys

# ---- UTF-8 控制台兜底（GBK 下 ✅/中文会 UnicodeEncodeError）----
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---- 路径与运行环境（与 numeric_sim 同口径）----
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PLUGIN_DIR = os.path.dirname(_SCRIPT_DIR)                                   # dragonfall/
_TESTS_DIR = os.path.join(_PLUGIN_DIR, "tests")
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))  # qqbot/
for _p in (_QQBOT_DIR, _PLUGIN_DIR, _TESTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS_DIR, "test_game_data.db"))

import numeric_sim as NS  # noqa: E402  辅助库：口径与数值测试完全一致

C, E, BT = NS.C, NS.E, NS.BT

ROLES = ("dps", "tank", "elite", "boss", "caster", "speedster")
SLOTS = ("weapon", "helm", "armor", "legs", "boots", "ring", "necklace")
QUAL_RANK = {"white": 0, "green": 1, "blue": 2, "purple": 3, "orange": 4}
_MAX_TURNS = 500  # 单场回合护栏（与 numeric_sim 一致）


# ---------------------------------------------------------------- 解析
def resolve_classes(spec: str) -> list:
    """'战士,cls_fa_shi' → [cls_zhan_shi, cls_fa_shi]（正则化 ID 列表）。"""
    out = []
    for raw in spec.split(","):
        raw = raw.strip()
        if not raw:
            continue
        cid = C.resolve("classes", raw)
        if not cid or cid not in C.CLASSES:
            raise ValueError("未知职业: %r（支持 6 基础职业：%s）" % (raw, "、".join(NS.REP_SKILL)))
        cn = cls_cn(cid)
        if cn not in NS.REP_SKILL:
            raise ValueError("职业 %r 不在数值实验支持集（%s）" % (cn, "、".join(NS.REP_SKILL)))
        if cid not in out:
            out.append(cid)
    if not out:
        raise ValueError("--cls 为空")
    return out


def cls_cn(cid: str) -> str:
    return C.CLASSES[cid].get("name", cid)


def parse_attr(spec: str):
    """'agi:39,str:0' → {'agi': 39}；'auto' → None（按职业 STD_ATTR）。0 值项剔除（等价于不加）。"""
    if spec == "auto":
        return None
    d = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        k, _, v = part.partition(":")
        k = k.strip()
        if not k:
            raise ValueError("加点键为空: %r" % part)
        try:
            val = int(v.strip())
        except ValueError:
            raise ValueError("加点值需为整数: %r" % part)
        d[k] = val
    d = {k: v for k, v in d.items() if v}
    if not d:
        print("⚠️ --attr %r 解析后为空 dict（0 点加点实验）" % spec)
    return d


def auto_full_equip(lv: int) -> dict:
    """按等级自动配满装：每槽取 lv≤玩家等级 的最高等级/品质名册件（槽位无 ≤lv 件时退取最低档）。

    装备词条随机 → 每槽固定 random.seed(1000+slot_idx) 生成，可复现（与测试锁种子思路一致）。
    """
    equip = {}
    for i, slot in enumerate(SLOTS):
        cands = [(rid, r) for rid, r in C.EQUIP_ROSTER.items() if r.get("slot") == slot]
        if not cands:
            continue
        pool = [(rid, r) for rid, r in cands if r.get("lv", 0) <= lv] or cands
        rid, _ = max(pool, key=lambda t: (t[1].get("lv", 0), QUAL_RANK.get(t[1].get("quality", "white"), 0)))
        random.seed(1000 + i)
        equip[slot] = C.generate_roster_equip(rid)
    return equip


def parse_equip(spec: str, lv: int) -> dict:
    """'none' → {}；'full' → auto_full_equip(lv)；
    高级：逗号组合，'none'/'full' 定底 + 'slot:名册名或rid' 逐个覆盖（如 full,weapon:海风长弓）。"""
    base, over = {}, {}
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if tok in ("none", "full"):
            base = {} if tok == "none" else auto_full_equip(lv)
            continue
        slot, _, ident = tok.partition(":")
        slot, ident = slot.strip().lower(), ident.strip()
        if slot not in SLOTS:
            raise ValueError("未知装备槽位: %r（可取 %s）" % (slot, "/".join(SLOTS)))
        rids = C.EQUIP_ROSTER_BY_NAME.get(ident) or []
        if not rids and ident in C.EQUIP_ROSTER:
            rids = [ident]
        if not rids:
            raise ValueError("装备名册无此件: %r" % ident)
        random.seed(2000 + SLOTS.index(slot))
        over[slot] = C.generate_roster_equip(rids[0])
    equip = dict(base)
    equip.update(over)
    return equip


# ---------------------------------------------------------------- 实验
def run_experiment(cid: str, lv: int, attr, equip: dict, role: str, mlv: int,
                   seeds: int, use_skill: bool) -> dict:
    """单职业单怪实验：面板 + 固定种子序列胜率 + 战后存活 + Fake-hp 校验。"""
    cn = cls_cn(cid)
    attr = attr if attr is not None else NS.STD_ATTR[cn]
    m = NS.monster_of(role, mlv)  # 怪只建一次（与 numeric_sim 同口径）

    wins, rounds_sum = 0, 0
    survive_sum, fake_hp, zero_dmg = 0.0, 0, 0
    for seed in range(seeds):
        random.seed(seed)  # 固定种子序列 seed 0..N-1 → 可复现
        st = E.player_final_stats(cid, lv, equip, 0, attr)
        learned = [NS.REP_SKILL[cn]] if use_skill else []
        player = {
            "class_name": cid, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": dict(equip), "attributes": dict(attr), "learned_skills": learned,
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None,
        }
        # ⚠️ 同一 dict 传入战斗（战斗内 hp 修改保留）——dict 拆新副本会假胜率（v130.10 教训）
        b = BT.Battle(btype="monster", enemy=dict(m), player=player)
        skill_name = NS.REP_SKILL[cn] if use_skill else None
        turns = 0
        while b.result is None and turns < _MAX_TURNS:
            prev_round = b.round
            b.actor_turn("skill" if use_skill else "attack", skill_name, player)
            # 技能施放被拦截（蓝/资源/CD 未就绪）→ 当回合转普攻
            if use_skill and b.round == prev_round and b.result is None:
                b.actor_turn("attack", None, player)
            turns += 1
        if b.result == "victory":
            wins += 1
        rounds_sum += b.round
        hp_left = max(0.0, player.get("hp", 0)) / max(1, player["max_hp"])
        survive_sum += hp_left
        # 战后校验 dict 同步：defeat 必掉血；若掉血为 0 → dict 未同步（假胜率红灯）
        if b.result == "defeat" and player.get("hp", 0) >= player["max_hp"]:
            fake_hp += 1
        elif b.result == "victory" and b.round >= 3 and hp_left >= 0.999:
            zero_dmg += 1  # 多回合零伤胜利：纯闪避脸可以，但连续出现需留意

    warnings = []
    if fake_hp:
        warnings.append("疑似 Fake hp（defeat 但血量仍满 ×%d）——玩家 dict 未同步，胜率不可信！" % fake_hp)
    if zero_dmg:
        warnings.append("零伤胜利 ≥3 回合 ×%d（纯闪避脸或异常）" % zero_dmg)

    return {
        "class": cn, "class_id": cid,
        "attr": dict(attr),
        "equip": {s: {"name": it.get("name", ""), "lv": it.get("lv", 0),
                      "quality": it.get("quality", "")} for s, it in equip.items()},
        "player_panel": st,
        "monster": {k: m.get(k) for k in
                    ("name", "max_hp", "atk", "matk", "def", "mdef", "spd", "crit", "dodge") if k in m},
        "wins": wins, "seeds": seeds, "win_rate": round(wins / seeds, 4),
        "avg_round": round(rounds_sum / seeds, 2),
        "avg_survive_hp": round(survive_sum / seeds, 4),
        "advice": advice(mlv, lv, wins, seeds),
        "warnings": warnings,
    }


# ---------------------------------------------------------------- 建议区间（N01 跨级预期参考）
def advice(mlv: int, lv: int, wins: int, seeds: int) -> dict:
    """按等级差给目标区间参考（N01 任务卡口径，按 seeds 等比缩放）：
    +11 级应 ≤2/8；+5~10 级应 ≤6/8；同级 ±4 应在 3/8~7/8；低 ≥5 级应 ≥5/8。"""
    diff = mlv - lv
    if diff >= 11:
        lo, hi, label = None, int(seeds * 0.25), "怪高 ≥+11 级（跨级应打不过）"
    elif diff >= 5:
        lo, hi, label = None, int(seeds * 0.75), "怪高 +5~10 级（不应无脑赢）"
    elif diff >= 0:
        lo, hi, label = int(seeds * 0.375), int(seeds * 0.875), "怪高 ≤4 级/同级（正常对抗）"
    else:
        lo, hi, label = int(seeds * 0.625), None, "怪低 1 级以上（应稳赢）"
    if lo is None:
        ok, target = wins <= hi, "胜率 ≤ %d/%d" % (hi, seeds)
    elif hi is None:
        ok, target = wins >= lo, "胜率 ≥ %d/%d" % (lo, seeds)
    else:
        ok, target = lo <= wins <= hi, "胜率 %d/%d ~ %d/%d" % (lo, seeds, hi, seeds)
    note = ""
    if not ok:
        note = ("偏离目标区间；可能是已知失衡基线（如刺客 11v22 5-6/8 ⚠️CTB 待修），"
                "或加点/装备/怪档差异所致——纯工具不锁断言，仅提示人工核对")
    return {"level_diff": diff, "label": label, "target": target, "ok": ok, "note": note}


# ---------------------------------------------------------------- 输出
def _w(s) -> int:
    """终端显示宽：CJK 计 2 格。"""
    return sum(2 if ord(c) > 0x2E7F else 1 for c in str(s))


def _pad(s, width: int) -> str:
    s = str(s)
    return s + " " * max(1, width - _w(s))


def _pct(v) -> str:
    return "%.1f%%" % (v * 100) if isinstance(v, (int, float)) else str(v)


def panel_line(st: dict) -> str:
    keys = (("max_hp", "HP"), ("atk", "攻击"), ("matk", "魔攻"), ("def", "防御"),
            ("mdef", "魔防"), ("spd", "速度"), ("crit", "暴击"), ("dodge", "闪避"))
    return " | ".join("%s %s" % (cn, _pct(st.get(k, 0)) if k in ("crit", "dodge")
                                 else str(int(st.get(k, 0)))) for k, cn in keys)


def monster_line(m: dict) -> str:
    keys = (("max_hp", "HP"), ("atk", "攻击"), ("matk", "魔攻"), ("def", "防御"),
            ("mdef", "魔防"), ("spd", "速度"), ("crit", "暴击"), ("dodge", "闪避"))
    return " | ".join("%s %s" % (cn, _pct(m.get(k, 0)) if k in ("crit", "dodge")
                                 else str(int(m.get(k, 0)))) for k, cn in keys if k in m)


def equip_summary(equip: dict) -> str:
    if not equip:
        return "裸装（none）"
    return "满装 %d 槽: %s" % (len(equip), ", ".join(
        "%s=%s(Lv.%d%s)" % (s, it.get("name", ""), it.get("lv", 0), it.get("quality", "")) for s, it in equip.items()))


def pct_pair(wins: int, seeds: int) -> str:
    return "%d/%d (%.0f%%)" % (wins, seeds, 100.0 * wins / seeds)


def print_experiment(r: dict, lv: int, mlv: int, role: str, skill_label: str) -> None:
    a = r["advice"]
    print("\n────────── %s（%s） Lv.%d vs %s Lv.%d ──────────" % (
        r["class"], r["class_id"], lv, role, mlv))
    print("加点: %s　装备: %s　技能: %s" % (
        ",".join("%s:%d" % kv for kv in sorted(r["attr"].items())) or "0 点",
        equip_summary(r["equip"]), skill_label))
    print("[面板] %s" % panel_line(r["player_panel"]))
    print("[怪物] %s" % monster_line(r["monster"]))
    print("[战果] 胜率 %s | 平均 %.2f 回合 | 战后存活均值 %.1f%%" % (
        pct_pair(r["wins"], r["seeds"]), r["avg_round"], r["avg_survive_hp"] * 100))
    flag = "✅" if a["ok"] else "⚠️"
    print("[建议] 等级差 %+d：%s → 目标 %s → %s %s" % (a["level_diff"], a["label"], a["target"], flag, a["note"]))
    for w in r["warnings"]:
        print("🚨 %s" % w)


def print_vs_table(results: list) -> None:
    print("\n════════════ 对比表（--vs）════════════")
    heads = ("职业", "HP", "攻击", "防御", "速度", "暴击", "闪避", "胜率", "平均回合", "判定")
    widths = [8, 7, 7, 7, 7, 8, 8, 10, 9, 2]
    print(" ".join(_pad(h, w) for h, w in zip(heads, widths)))
    for r in results:
        st = r["player_panel"]
        row = (r["class"], int(st.get("max_hp", 0)), int(st.get("atk", 0)), int(st.get("def", 0)),
               int(st.get("spd", 0)), _pct(st.get("crit", 0)), _pct(st.get("dodge", 0)),
               pct_pair(r["wins"], r["seeds"]), "%.2f" % r["avg_round"], "✅" if r["advice"]["ok"] else "⚠️")
        print(" ".join(_pad(v, w) for v, w in zip(row, widths)))
    print("══════════════════════════════════════")


def build_json(params: dict, results: list) -> str:
    payload = {"tool": "numtool", "params": params, "results": results}
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="numtool", description="通用数值实验 CLI：面板 + 胜率 + 建议（纯工具，不锁断言）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("参数：")[0])
    ap.add_argument("--cls", required=True, help="职业名（中文/ID，逗号分隔多个，如 战士,法师）")
    ap.add_argument("--lv", required=True, type=int, help="玩家等级")
    ap.add_argument("--attr", default="auto", help="加点（如 agi:39,str:0；auto=职业推荐加点）")
    ap.add_argument("--mlv", required=True, type=int, help="怪等级")
    ap.add_argument("--role", default="dps", choices=ROLES, help="怪类型（默认 dps）")
    ap.add_argument("--seeds", default=8, type=int, help="场数（默认 8，固定种子 0..N-1）")
    ap.add_argument("--equip", default="none", help="none/full 或 slot:名册名组合（默认 none）")
    ap.add_argument("--skill", default="none", choices=("none", "auto"), help="none=普攻 / auto=代表技能（默认 none）")
    ap.add_argument("--vs", action="store_true", help="对比模式：多职业末尾输出对比表")
    ap.add_argument("--json", action="store_true", help="只输出 JSON")
    args = ap.parse_args(argv)

    if args.seeds < 1:
        ap.error("--seeds 必须 ≥1")
    if not os.path.exists(os.path.join(_TESTS_DIR, "test_game_data.db")):
        print("❌ 缺少 numeric_sim 依赖的测试库: %s" % os.path.join(_TESTS_DIR, "test_game_data.db"))
        return 1

    try:
        cids = resolve_classes(args.cls)
        attr = parse_attr(args.attr)
        equip = parse_equip(args.equip, args.lv)
    except ValueError as e:
        print("❌ 参数错误: %s（--help 查看用法）" % e)
        return 2
    use_skill = args.skill == "auto"
    skill_label = "代表技能循环" if use_skill else "纯普攻"

    if not args.json:
        print("===== numtool 数值实验 =====")
        print("实验: %s | 玩家 Lv.%d 加点 %s | 装备 %s | 技能 %s" % (
            ",".join(cls_cn(c) for c in cids), args.lv,
            ",".join("%s:%d" % kv for kv in sorted(attr.items())) if attr else "auto(职业推荐)",
            equip_summary(equip), skill_label))
        print("对象: %s 怪 Lv.%d | %d 场（固定种子 0..%d）%s" % (
            args.role, args.mlv, args.seeds, args.seeds - 1, " | 对比模式 --vs" if args.vs else ""))

    results = []
    for cid in cids:
        r = run_experiment(cid, args.lv, attr, equip, args.role, args.mlv, args.seeds, use_skill)
        results.append(r)
        if not args.json:
            print_experiment(r, args.lv, args.mlv, args.role, skill_label)

    if args.json:
        print(build_json({"cls": [cls_cn(c) for c in cids], "lv": args.lv, "attr": (
            ",".join("%s:%d" % kv for kv in sorted(attr.items())) if attr else "auto"),
            "mlv": args.mlv, "role": args.role, "seeds": args.seeds,
            "equip": args.equip, "skill": args.skill, "vs": args.vs}, results))
    elif args.vs and len(results) > 1:
        print_vs_table(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())