#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文案表（消息模板）门禁 —— `game/data/text_specs.json` + `game/core/texts.py`。

**这一层要防的四件事**（每件都由断言钉死）：
  ① 声明与调用脱节：表里有、代码不用（死文案）｜代码用、表里没有（运行时缺 key）
  ② 槽位对不上：模板写 `{foo}`，调用点传 `name` ⇒ 玩家会看到 `{foo}` 原样露出来
  ③ 静默降级：缺 key 时悄悄退回旧串/空串 —— 本层刻意**不静默**（ERROR 日志 + 返回 key 本身）
  ④ 声明文件坏了没人知道：语法错/空值/params 与模板不一致（引擎 `validate()` 只报告不抛 → 这里必须查）

**逐字一致**（"迁移没改玩家看到的字"）由两层证据扛：
  · 副本域：`tests/test_v185_instance_admission.py` 的 **805 格逐格冻结比对**（对照物 = 旧实现冻结体）
  · 周常 / 签到 / 补给箱域：本文件 `WEEKLY_FROZEN` / `SIGNIN_FROZEN` / `SUPPLY_FROZEN` —— **迁移前真跑各分支存下来的完整输出**，
    每次跑测试复跑比对（签到分支用 random 打桩保证可复现）

跑法：python tests/test_texts_table.py（exit=0 通过）
"""
import ast
import asyncio
import datetime
import io
import json
import os
import random
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from conftest import C, db, clean_db, FakeEvent, run, Main  # noqa: E402
from data.plugins.dragonfall.game.core import texts as T  # noqa: E402
from data.plugins.dragonfall.game.services.weekly_progress import (  # noqa: E402
    _week_state, _save_week_state,
)

_PD = os.path.dirname(_HERE)
WEEKLY_SRC = os.path.join(_PD, "game", "commands", "weekly.py")
MISC_SRC = os.path.join(_PD, "game", "commands", "misc.py")
EVENT_SRC = os.path.join(_PD, "game", "commands", "event_menu.py")
GATE_SRC = os.path.join(_PD, "game", "core", "instance_gate.py")
SPEC = T.SPEC_PATH
# 已迁移的域 → 该域文案由哪个文件接线（新增一个域时在这里加一行）
WIRED = {"副本准入": GATE_SRC, "周常": WEEKLY_SRC, "签到": MISC_SRC,
         "补给箱": EVENT_SRC}

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, str(detail)[:400]))


# ══════════════════════════════════════════════════════════════════════════
# 迁移前行为快照（真跑『周常』『周常列表』6 个分支，逐字冻结）
# ══════════════════════════════════════════════════════════════════════════
WEEKLY_FROZEN = {
    "A_locked": "🏮 悬赏板还蒙着布——上面的委托要 Lv.50 的冒险者才接得动。\n💡 先完成『每日』任务和主线提升等级，到了 Lv.50 再来看看～",
    "B_first": "🏮 【本周悬赏】已发布！\n━━━━━━━━━━━━\n1. 『边境肃清令』击败 30 只任意怪物\n    目标：讨伐任意怪物 30 只｜赏金：经验 +155000 金币 +38000\n2. 『深林猎手悬赏』击败 40 只任意怪物\n    目标：讨伐任意怪物 40 只｜赏金：经验 +175000 金币 +44000\n3. 『剿灭魔裔』击败 5 只精英怪物\n    目标：讨伐精英怪物 5 只｜赏金：经验 +190000 金币 +48000\n\n💡 击杀自动计数，达标立即发奖！『周常』随时查进度，『周常列表』看全池悬赏",
    "C_progress": "🏮 【本周悬赏】1/3 已完成\n━━━━━━━━━━━━\n1. 『边境肃清令』 ✅ 已完成\n2. 『深林猎手悬赏』 ⏳ 0/40\n    目标：讨伐任意怪物 40 只｜赏金：经验 +175000 金币 +44000\n3. 『剿灭魔裔』 ⏳ 0/5\n    目标：讨伐精英怪物 5 只｜赏金：经验 +190000 金币 +48000\n\n💡 击杀自动计数，达标立即发奖——悬赏每周一刷新",
    "D_pool_p1": "🏮 【周常悬赏池】第 1/3 页（每周自动发布 3 条）\n━━━━━━━━━━━━\n· 『边境肃清令』(Lv.50+) 击败 30 只任意怪物\n    经验 +155000 金币 +38000\n· 『深林猎手悬赏』(Lv.50+) 击败 40 只任意怪物\n    经验 +175000 金币 +44000\n· 『剿灭魔裔』(Lv.50+) 击败 5 只精英怪物\n    经验 +190000 金币 +48000\n· 『破阵斩将』(Lv.50+) 击败 6 只精英怪物\n    经验 +210000 金币 +53000\n\n💡 每周一刷新自动抽取适合你等级的悬赏；『周常』查看本周任务\n📄 『周常列表 2』翻页",
    "E_pool_p2": "🏮 【周常悬赏池】第 2/3 页（每周自动发布 3 条）\n━━━━━━━━━━━━\n· 『讨伐区域首领』(Lv.50+) 击败 2 个区域 Boss\n    经验 +230000 金币 +58000\n· 『诛灭祸乱之源』(Lv.50+) 击败 3 个区域 Boss\n    经验 +250000 金币 +64000\n· 『龙脊清扫令』(Lv.70+ 🔒) 击败 35 只任意怪物\n    经验 +400000 金币 +100000\n· 『深渊行者试炼』(Lv.70+ 🔒) 击败 45 只任意怪物\n    经验 +450000 金币 +115000\n\n💡 每周一刷新自动抽取适合你等级的悬赏；『周常』查看本周任务\n📄 『周常列表 3』翻页",
    "F_all_done": "🏮 【本周悬赏】3/3 已完成\n━━━━━━━━━━━━\n1. 『边境肃清令』 ✅ 已完成\n2. 『深林猎手悬赏』 ✅ 已完成\n3. 『剿灭魔裔』 ✅ 已完成"
}   # 迁移前快照（2026-09-12 真跑存下，勿手改）

# 迁移前行为快照（真跑『签到』5 个分支，逐字冻结；random 打桩保证可复现）
SIGNIN_FROZEN = {
    "A_first_bad": "📅 【签到成功】第 1 次签到！连续 1 天！\n💰 获得 25 金币\n🌧️ 今日运势：小凶(今日金币－10%)\n💡 今日小凶金币收益 -10%……别灰心！用『使用 幸运符』可消解，或明日签到重roll运势～",
    "B_first_big": "📅 【签到成功】第 1 次签到！连续 1 天！\n💰 获得 25 金币\n🌟 今日运势：大吉(今日经验＋10%)",
    "C_dup": "今天已经签过到啦！明天再来～",
    "D_streak7": "📅 【签到成功】第 7 次签到！连续 7 天！\n💰 获得 55 金币\n🌟 今日运势：大吉(今日经验＋10%)\n🎁 连续 7 天奖励：🟣【龙鳞战甲】！",
    "E_festival": "📅 【签到成功】第 1 次签到！连续 1 天！\n💰 获得 50 金币\n🌟 今日运势：大吉(今日经验＋10%)\n🎉 节日庆典：签到奖励翻倍！"
}   # 迁移前快照（2026-09-12 真跑存下，勿手改）

SUPPLY_FROZEN = {
    "A_first": "📦 【每日补给箱】\n━━━━━━━━━━━━\n  🎁 每日材料箱：图纸残页、淬火石、烤肉串！\n  🎁 每日道具箱：强化石、双倍金币符、炖菜！\n  🎁 每日豪华箱：白银箱、精炼强化石、幸运符！\n\n💡 补给箱内容：图纸残页/淬火石/强化石/幸运符等（每日 0 点重置）",
    "B_second": "📦 【每日补给箱】\n━━━━━━━━━━━━\n  ⏳ 每日材料箱：今日已领取～\n  ⏳ 每日道具箱：今日已领取～\n  🎁 每日豪华箱：白银箱、精炼强化石、幸运符！\n\n💡 补给箱内容：图纸残页/淬火石/强化石/幸运符等（每日 0 点重置）",
    "C_third": "📦 【每日补给箱】\n━━━━━━━━━━━━\n  ⏳ 每日材料箱：今日已领取～\n  ⏳ 每日道具箱：今日已领取～\n  ⏳ 每日豪华箱：本周已领 2/2～\n  今天/本周的补给箱都已领过啦，明天再来吧～\n\n💡 补给箱内容：图纸残页/淬火石/强化石/幸运符等（每日 0 点重置）"
}   # 迁移前快照（2026-09-12 真跑存下，勿手改）

_GID, _QID = "g_txt", "q_txt"
_SID = "g_si"


async def _inv(m, name, msg):
    ev = FakeEvent(_GID, _QID, msg)
    res = await run(getattr(m, name), ev)
    return res[-1] if res else ""


async def _weekly_scenarios() -> dict:
    """复跑迁移前的 6 个分支（步骤与快照脚本逐行一致）。"""
    clean_db()
    m = Main(None)
    out = {}
    db.create_player(_GID, _QID, "文案", C.resolve("classes", "战士"), {}, 100, 100)
    db.update_player(_GID, _QID, level=49, stamina=100)
    out["A_locked"] = await _inv(m, "weekly_cmd", "周常")
    db.update_player(_GID, _QID, level=50, stamina=100)
    out["B_first"] = await _inv(m, "weekly_cmd", "周常")
    st = dict(_week_state(_QID) or {})
    tasks = st.get("tasks") or {}
    for i, (tn, t) in enumerate(tasks.items()):
        t["prog"] = 1 if i == 0 else 0
        t["done"] = (i == 0)
    st["done_n"] = 1 if tasks else 0
    _save_week_state(_QID, st)
    out["C_progress"] = await _inv(m, "weekly_cmd", "周常")
    out["D_pool_p1"] = await _inv(m, "weekly_list", "周常列表")
    out["E_pool_p2"] = await _inv(m, "weekly_list", "周常列表 2")
    st2 = dict(_week_state(_QID) or {})
    for t in (st2.get("tasks") or {}).values():
        t["done"] = True
        t["prog"] = int(t.get("need") or 1)
    st2["done_n"] = len(st2.get("tasks") or {})
    _save_week_state(_QID, st2)
    out["F_all_done"] = await _inv(m, "weekly_cmd", "周常")
    clean_db()
    return out


async def _signin_scenarios() -> dict:
    """复跑『签到』迁移前的 5 个分支（步骤与快照脚本逐行一致；random 打桩保证可复现）。"""
    clean_db()
    m = Main(None)
    out = {}
    _rnd = random.random

    def _mk(qid):
        db.create_player(_SID, qid, "签到", C.resolve("classes", "战士"), {}, 100, 100)
        db.update_player(_SID, qid, level=10, gold=1000)

    async def _sign(qid):
        ev = FakeEvent(_SID, qid, "签到")
        res = await run(m.signin, ev)
        return res[-1] if res else ""

    def _pre(qid, days):
        today = datetime.date.today()
        for i in range(days, 0, -1):
            d = today - datetime.timedelta(days=i)
            db.signin_claim(_SID, qid, d.isoformat(),
                            (d - datetime.timedelta(days=1)).isoformat())

    try:
        _mk("q_a")
        random.seed(42)
        random.random = lambda: 0.05          # < fortune_bad_th 0.15 → 小凶
        out["A_first_bad"] = await _sign("q_a")
        _mk("q_b")
        random.seed(42)
        random.random = lambda: 0.9           # ≥ 0.55 → 大吉
        out["B_first_big"] = await _sign("q_b")
        out["C_dup"] = await _sign("q_b")     # 同人再签 → 已签分支
        _mk("q_d")
        _pre("q_d", 6)                        # 昨天刚签 + 连续 6 天 → 本次第 7 天
        random.seed(7)
        random.random = lambda: 0.9
        out["D_streak7"] = await _sign("q_d")
        _mk("q_e")
        db.save_world_event("festival", int(time.time()) + 86400, {"name": "测试庆典"})
        random.seed(42)
        random.random = lambda: 0.9
        out["E_festival"] = await _sign("q_e")
        db.clear_world_event()
    finally:
        random.random = _rnd
        clean_db()
    return out


async def _supply_scenarios() -> dict:
    """复跑『领取补给箱』迁移前的 3 个分支（步骤与快照脚本逐行一致）。"""
    clean_db()
    m = Main(None)
    db.create_player("g_sp", "q_sp", "补给", C.resolve("classes", "战士"), {}, 100, 100)
    out = {}
    for k in ("A_first", "B_second", "C_third"):
        ev = FakeEvent("g_sp", "q_sp", "领取补给箱")
        res = await run(m.event_menu, ev)
        out[k] = res[-1] if res else ""
    clean_db()
    return out


# ══════════════════════════════════════════════════════════════════════════
def _scan_calls(path):
    """AST 扫模块：

    ① `T.text("k", **kw)` / `T.static("k")` → (key, frozenset(kwarg 名), kind)（直接调用点）
    ② 模块里出现过的字符串字面量集合 → 「键在映射表里」这类用法（如运势键 → 文案键的 dict）
       也算被引用，否则会被当成死文案误报。

    ②只用于「有没有引用」，槽位对账仍只认①的直接调用实参。
    """
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    calls, lits = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lits.add(node.value)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("text", "static")
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "T"):
            k = node.args[0].value if (node.args and isinstance(node.args[0], ast.Constant)) else None
            if k is None:
                continue          # 动态键（如 T.static(_FORTUNE_TEXT.get(fortune))）静态扫不出：
                                  # 交给②「字面量也算引用」兜，避免误报成「调用了未声明的 None」
            calls.append((k, frozenset(kw.arg for kw in node.keywords if kw.arg), node.func.attr))
    return calls, lits


def t1_table_selfcheck():
    print("\n[1] 装载与自检（引擎 validate/audit）")
    tb = T.reload()
    check("声明文件存在且路径正确", os.path.exists(SPEC) and SPEC.endswith("text_specs.json"), SPEC)
    check("装载无错（load_error 为空）", T.load_error() == "", T.load_error())
    check("表非空（61 条：副本准入 26 + 签到 10 + 周常 18 + 补给箱 7）", len(tb) >= 40, len(tb))
    check("★ validate() 干净（无空值/语法错/params 与模板不一致）",
          tb.audit()["problems"] == [], tb.audit()["problems"][:5])
    check("元信息键（_ 开头）不入表", not [k for k in tb.keys() if k.startswith("_")], tb.keys()[:3])
    check("每条都有 category（编辑器分组用）",
          not [s.key for s in tb if not s.category], [s.key for s in tb if not s.category][:5])
    check("key 无重复", len(tb.keys()) == len(set(tb.keys())))
    cats = sorted({s.category for s in tb})
    check("category 取值符合预期（副本准入 / 签到 / 周常 / 补给箱）",
          set(cats) == {"副本准入", "签到", "周常", "补给箱"}, cats)


def t2_key_and_params_accounting():
    print("\n[2] 声明 ↔ 调用点对账（双向；AST 扫真实调用）")
    declared = set(T.table().keys())
    used, mismatch, lits = set(), [], set()
    for name, path in WIRED.items():
        calls, l = _scan_calls(path)
        lits |= (l & declared)
        for key, kwargs, kind in calls:
            used.add(key)
            spec = T.table().spec(key)
            if spec is None:
                mismatch.append("%s: 调用了未声明的 %s" % (os.path.basename(path), key))
                continue
            slots = set(spec.slots)                       # 声明优先，缺省自动抽取
            if kind == "static" and kwargs:
                mismatch.append("%s: T.static(%s) 不该带槽位" % (os.path.basename(path), key))
            if set(kwargs) != slots:
                mismatch.append("%s: %s 槽位不符（调用 %s / 声明 %s）"
                                % (os.path.basename(path), key, sorted(kwargs), sorted(slots)))
    used |= lits                                          # 映射表里的键也算被引用
    check("★ 代码里每一处调用都能在表里找到（否则运行时缺 key）", not mismatch, mismatch[:5])
    dead = sorted(declared - used)
    check("★ 表里没有死文案（每条声明都被真实调用）", not dead, dead)
    check("★ 槽位名与调用实参逐条对得上（防模板写出 {foo} 露给玩家）", not mismatch)
    doms = {k.split(".")[0] for k in used}
    check("调用点覆盖全部已迁移域（副本准入 + 周常 + 签到 + 补给箱）",
          {"instance", "weekly", "signin", "supply"} <= doms, sorted(doms))


def t3_no_silent_fallback():
    print("\n[3] 缺 key 不静默（不打回旧串、不吞成空串）")
    tb = T.table()
    got = tb.render("nope.not_declared")
    check("★ 未声明的 key → 返回 key 本身（玩家/日志双可见）", got == "nope.not_declared", repr(got))
    check("★ 记账：missing() 记下了这个缺 key", "nope.not_declared" in tb.missing(), tb.missing())
    tb.reset_stats()

    # 坏声明文件：不抛、不静默，空表 + 错误可见
    bad = os.path.join(os.environ.get("LOCALAPPDATA", _HERE), "Temp", "_bad_text_specs.json")
    with io.open(bad, "w", encoding="utf-8") as fh:
        fh.write("{ this is not json ")
    real = T.SPEC_PATH
    try:
        T.SPEC_PATH = bad
        T.reload()
        check("★ 声明文件语法坏 → 不抛异常，且 load_error 有原因",
              bool(T.load_error()), T.load_error())
        check("★ 坏文件下渲染不静默（返回 key，不是空串）",
              T.text("instance.leader_only") == "instance.leader_only")
    finally:
        T.SPEC_PATH = real
        T.reload()
    os.remove(bad)
    check("恢复正常声明后表重建（61 条）", len(T.table()) >= 40, len(T.table()))


def t4_weekly_frozen():
    print("\n[4] 周常域逐字冻结：迁移前 6 分支行为快照复跑比对")
    check("冻结基准已内嵌（6 场景）", len(WEEKLY_FROZEN) == 6, len(WEEKLY_FROZEN))
    now = asyncio.run(_weekly_scenarios())
    bad = [k for k in WEEKLY_FROZEN if WEEKLY_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, now.get(k, "")[:120]))
    check("★ 周常『周常』『周常列表』6 分支输出与迁移前**逐字一致**", not bad, bad)
    check("冻结基准非空且含换行结构（防基准写空）",
          all(v and "\n" in v for v in WEEKLY_FROZEN.values()))


def t5_signin_frozen():
    print("\n[5] 签到域逐字冻结：迁移前 5 分支行为快照复跑比对")
    check("冻结基准已内嵌（5 场景）", len(SIGNIN_FROZEN) == 5, len(SIGNIN_FROZEN))
    now = asyncio.run(_signin_scenarios())
    bad = [k for k in SIGNIN_FROZEN if SIGNIN_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, now.get(k, "")[:120]))
    check("★『签到』5 分支输出与迁移前**逐字一致**", not bad, bad)


def t6_supply_frozen():
    print("\n[6] 补给箱域逐字冻结：迁移前 3 分支（首发/日限/周限）复跑比对")
    check("冻结基准已内嵌（3 场景）", len(SUPPLY_FROZEN) == 3, len(SUPPLY_FROZEN))
    now = asyncio.run(_supply_scenarios())
    bad = [k for k in SUPPLY_FROZEN if SUPPLY_FROZEN[k] != now.get(k)]
    for k in bad:
        print("     · %s 现=%r" % (k, now.get(k, "")[:120]))
    check("★『领取补给箱』3 分支输出与迁移前**逐字一致**", not bad, bad)


def main():
    print("=" * 74)
    print("文案表门禁：game/data/text_specs.json + game/core/texts.py")
    print("=" * 74)
    t1_table_selfcheck()
    t2_key_and_params_accounting()
    t3_no_silent_fallback()
    t4_weekly_frozen()
    t5_signin_frozen()
    t6_supply_frozen()
    print("\n" + "=" * 74)
    print("结果：通过 %d / %d" % (passed, passed + failed))
    print("=" * 74)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
