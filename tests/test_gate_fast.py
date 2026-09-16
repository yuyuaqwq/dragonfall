# -*- coding: utf-8 -*-
"""门禁：`scripts/gate_fast.py`（门禁快速档）的**映射正确性 + 有牙 + 不许静默少跑**。

跑法（与全仓其它测试同一姿势，独立可跑、也可被 `scripts/run_all_tests.py` 收编）：
```
python tests/test_gate_fast.py
```
本文件**只读**、不写仓内任何文件、不跑长门禁（全部走 `--plan` 纯计算路径），秒级完成。

红线（作业书 §2）
-----------------
① 映射准确性：用**三个真实历史事件**回放，断言选中的集合**包含**当时真正抓到问题的门禁，
   并把当时的**原文**（红在哪一行、报的什么）一起打印出来。
② 有牙：在内存里挖掉一条映射 → `--self-check` 与回放断言**必须报红** → 还原复绿。
③ 不许静默少跑：只改 docs 的场景，输出必须明示「跳过了全部行为门禁」。
④ `--full` 与手工那套（7 道）等价：清单并排对照 + 差异逐条解释；断言手工 7 道 ⊂ --full。
⑤ `scripts/run_all_tests.py` 不受影响（md5 冻结 + gate_fast 只原样转调它）。
"""
from __future__ import annotations

import hashlib
import io
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_REPO, "scripts")
for _p in (_HERE, _REPO, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_fast as GF  # noqa: E402

DEFAULT_FRAMEWORK_DIR = "C:/Users/yuyu/framework-engine"
FW_ROOT = os.path.abspath(os.environ.get("GWEN_FRAMEWORK_DIR") or DEFAULT_FRAMEWORK_DIR)

#: `scripts/run_all_tests.py` 的冻结 md5（**本工具不改它**的机器证据；全量入口）
#: ★ P5F 前置⑥（2026-09-15）：`run_all_tests.py` 因**去壳前置**被有意改动（`_TPL_INIT`
#:   从内嵌 `game.store.init_db` 改走宿主工厂 `host/store_factory` + 引擎 `load_package`，
#:   并新增 `_find_package_dir()`）⇒ 冻结值随这次**有意**改动更新：
#:   旧 `EF5528C8EFE079C5AD15433B55899E42` → 新 `D56C15B22A5A4526080A032A79F8B20C`。
#: ★ T8 测试单源化（2026-09-16）：`run_all_tests.py` 被**有意重写** —— 枚举面从
#:   「宿主 tests/ 一份」改成「**宿主自留件 + 包仓那份 tests**」（`framework/games/*/tests`，
#:   不写死包名），并新增「两侧同名 ⇒ 醒目报错」「包仓 tests 缺失 ⇒ 醒目报错」两条硬判据；
#:   `QQBOT_DIR` 死算路径改成发现式（本工作副本布局），`_TPL_INIT` 改走 `host.store_factory`。
#:   ⇒ 冻结值随这次**有意**改动更新：
#:   `D56C15B22A5A4526080A032A79F8B20C` → `47A2B007D4B65BC8769F23D2484D8163`。
#:   判据本身（「跑门禁不得改全量 runner」+ 无反向依赖 + 语法可编译 + 原样转调）一条未减。
RUN_ALL_TESTS_MD5 = "47A2B007D4B65BC8769F23D2484D8163"

_passed = 0
_failed = []


def check(title, cond, detail=""):
    global _passed
    if cond:
        _passed += 1
        print("  \u2705 %s" % title)
    else:
        _failed.append(title)
        print("  \u274c %s%s" % (title, ("  <- %s" % detail) if detail else ""))
    return bool(cond)


def section(t):
    print("")
    print("=" * 74)
    print(t)
    print("=" * 74)


def capture_plan(argv):
    """跑 gate_fast 的 `--plan` 并抓 stdout（不执行任何门禁）。"""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = GF.main(["--host", _REPO, "--framework", FW_ROOT] + argv + ["--plan"])
    finally:
        sys.stdout = old
    return rc, buf.getvalue()


def selected_ids(out):
    """从 `--plan` 输出里抠出「选中集合」段的门禁 id（顺序保留）。"""
    ids, in_sec = [], False
    for ln in out.splitlines():
        if not in_sec:
            if ln.startswith("选中集合"):
                in_sec = True
            continue
        # 段尾 = 两段打印的分隔线 / 「已跑」标题
        if ln.startswith("-" * 10) or ln.startswith("\u2705 已跑") or ln.startswith("\u23ed"):
            break
        s = ln.strip()
        if s.startswith("\u00b7 "):
            ids.append(s[2:].split()[0])
    return ids


def skipped_ids(out):
    """从「已跳过」段里抠出门禁 id（只认「第二列是已知门禁 id」的行，避开表头）。"""
    known = set(GF.GATES_BY_ID)
    res = []
    for ln in out.splitlines():
        s = ln.strip()
        if not s.startswith("\u23ed\ufe0f "):
            continue
        parts = s[2:].split()
        if parts and parts[0] in known:
            res.append(parts[0])
    return res


# ======================================================================================
# ① 映射表结构自检（表本身的完整性；不依赖任何仓库状态）
# ======================================================================================

def test_mapping_table_integrity():
    section("①-0 映射表结构自检（每条门禁：覆盖 glob 良构 + 耗时已实测 + 理由非空）")
    bad = []
    for g in GF.GATES:
        if not g.covers:
            bad.append("%s: covers 为空" % g.gid)
        for c in g.covers:
            if c != "*" and (":" not in c or c.split(":", 1)[0] not in ("host", "fw")):
                bad.append("%s: 覆盖 glob 前缀非法 %r" % (g.gid, c))
        if not (g.cost and g.cost > 0):
            bad.append("%s: 耗时未实测（cost=%r）" % (g.gid, g.cost))
        if not g.why:
            bad.append("%s: why 为空" % g.gid)
    check("全部门禁：covers 非空 + glob 前缀合法 + cost>0 + why 非空", not bad, "; ".join(bad[:6]))

    ids = [g.gid for g in GF.GATES]
    check("门禁 id 唯一", len(ids) == len(set(ids)))

    missing = [m for m in GF.MANUAL_CANON if m not in GF.GATES_BY_ID]
    check("手工那套 7 道都在映射表里", not missing, ",".join(missing))

    extras = [g.gid for g in GF.GATES if g.gid not in GF.MANUAL_CANON]
    no_reason = [e for e in extras if e not in GF.FULL_EXTRA_REASONS]
    check("--full 的每一道「多出来的」门禁都有逐条解释", not no_reason, ",".join(no_reason))

    full_gates = [g.gid for g in GF.GATES if g.tier == "full"]
    check("全量门禁存在且**不参选** --changed（否则每轮都变全量）",
          full_gates and all(not GF.GATES_BY_ID[g].selectable for g in full_gates),
          ",".join(full_gates))

    cov_g = [g.gid for g in GF.coverage_gates()]
    check("覆盖判定不含 tier=full / smoke（否则 self-check 无牙）",
          all(GF.GATES_BY_ID[g].tier not in ("full", "smoke") for g in cov_g))

    # glob 语义：`*` 不跨 `/`，`**` 跨层级
    cases = [
        ("fw:games/*/content/**", "fw", "games/orlandia/content/event_templates.py", True),
        ("fw:games/*/**/*.py", "fw", "games/orlandia/content/a/b/c.py", True),
        ("fw:games/*/**/*.py", "fw", "games/orlandia/content/x.py", True),
        ("fw:games/*/content/data/*.json", "fw", "games/orlandia/content/data/a.json", True),
        ("fw:games/*/content/data/*.json", "fw", "games/orlandia/content/data/sub/a.json", False),
        ("host:game/commands/**", "host", "game/commands/combat.py", True),
        ("host:game/commands/**", "fw", "game/commands/combat.py", False),
        ("*", "host", "anything/at/all.md", True),
    ]
    bad = [(p, r, rel, exp) for p, r, rel, exp in cases if GF.path_matches(p, r, rel) != exp]
    check("glob 语义（* 不跨 / · ** 跨层级 · repo 前缀硬约束）", not bad, str(bad[:3]))


# ======================================================================================
# ① 三个真实历史事件回放
# ======================================================================================

#: 事件 ① 原文（IMPGATE logs/12_gate_b3c2fc8_before_overlay.log 逐字）
EV1_VERBATIM = (
    "  GAP content/event_templates.py:144 | from .reward import _host_content | "
    "`_host_content` not found in target module content.reward | target module name count=34"
)
#: 事件 ① 的另一半原文（INTFIX out/W-INTFIX.md §0）
EV1_VERBATIM2 = (
    "现象：tests/test_v83_explore_egg.py 与 tests/test_v97_03_event_templates.py 报 "
    "ImportError: cannot import name '_host_content' from 'content.reward'"
)
#: 事件 ② 原文（INTFIX out/evidence/v97_05_night.txt 逐字）
EV2_VERBATIM = "======== 结果: 77 通过 / 1 失败 ========"
EV2_VERBATIM2 = (
    "[A] after `HOST_RE._is_time = lambda span: span == 'day'`\n"
    "    PKG  _is_time is HOST _is_time : False\n"
    "    PKG  _is_time('deep_night')    : True\n"
    "    fire(...) -> '\U0001f47b 深夜的橡木平原雾气弥漫，一个半透明的老奶奶飘过来问路...'\n"
    "    assertion 't1 == \"\"'          : False"
)
#: 事件 ③ 原文（fixdecl out/raw/01_baseline_coverage.txt 逐字）
EV3_VERBATIM = (
    "=== 3. 孤儿域文件（包内存在但清单未声明）===\n"
    "  \u274c content/data/text_specs.json\n"
    "=== 4. 汇总 ===\n"
    "  域 72 个 / 条目合计 9126 / 失败 1\n"
    "  \u274c 存在未声明的域文件：['content/data/text_specs.json']"
)

EVENTS = [
    {
        "name": "① content/event_templates.py（C2<->C4 接口错位 / _host_content 被打断）",
        "changed": ["fw:games/orlandia/content/event_templates.py"],
        "must_select": ["import_closure"],           # 点名 GAP 的那条
        "also_expected": ["evt97_03", "egg83"],      # 当时当场炸 ImportError 的两条
        "verbatim": [EV1_VERBATIM, EV1_VERBATIM2],
        "cite": "IMPGATE out/W-IMPGATE.md §0 + logs/12_gate_b3c2fc8_before_overlay.log；"
                "INTFIX out/W-INTFIX.md §0",
    },
    {
        "name": "② game/core/rule_engine.py（猴补面失效：宿主壳 _is_time 覆盖不到包内实现）",
        "changed": ["host:game/core/rule_engine.py"],
        "must_select": ["re97_05"],
        "also_expected": [],
        "verbatim": [EV2_VERBATIM, EV2_VERBATIM2],
        "cite": "PATCHAUDIT out/../overnight/PATCHAUDIT_BRIEF.md §0；"
                "INTFIX out/W-INTFIX.md §7-U1 + out/evidence/probe_v97_05_time.txt",
    },
    {
        "name": "③ games/orlandia/editor/domains.json（域声明：text_specs 域漂移）",
        "changed": ["fw:games/orlandia/editor/domains.json"],
        "must_select": ["pkg_coverage", "domain_owner", "editor_domains"],
        "also_expected": [],
        "verbatim": [EV3_VERBATIM],
        "cite": "FIXDECL out/W-FIXDECL.md §0/§4.1 + out/raw/01_baseline_coverage.txt",
    },
]


def test_historical_replays():
    section("① 三个真实历史事件回放（断言：选中集合包含当时真正抓到问题的门禁）")
    for ev in EVENTS:
        print("")
        print("── 回放 %s" % ev["name"])
        print("   改动文件：%s" % ", ".join(ev["changed"]))
        print("   当时原文（逐字留档）：")
        for v in ev["verbatim"]:
            for ln in v.splitlines():
                print("      | %s" % ln)
        print("   出处：%s" % ev["cite"])
        rc, out = capture_plan(["--changed"] + ev["changed"])
        sel = selected_ids(out)
        print("   本次选中：%s" % ", ".join(g for g in sel
                                          if g not in ("smoke_engine", "smoke_pkg_import")))
        check("回放 [%s]：rc=0 且选中集合非空" % ev["name"].split("（")[0],
              rc == 0 and bool(sel), "rc=%s sel=%s" % (rc, sel))
        for gid in ev["must_select"]:
            check("回放必须选中 `%s`（当时就是它报的红）" % gid, gid in sel,
                  "实际选中=%s" % ",".join(sel))
        for gid in ev.get("also_expected", []):
            check("回放同时命中 `%s`（当时当场炸的定点门禁）" % gid, gid in sel,
                  "实际选中=%s" % ",".join(sel))
        # 反向：不该把整仓所有门禁都选上（否则等于每轮全量）
        check("回放没有把映射表里的门禁全选上（仍然只跑相关面）",
              len(sel) < len(GF.GATES) - 2, "选中 %d / 共 %d" % (len(sel), len(GF.GATES)))


def test_replay_verbatim_kept():
    section("①-2 回放原文留档自检（原文不许被后来的改动悄悄改掉）")
    for i, ev in enumerate(EVENTS, 1):
        joined = "\n".join(ev["verbatim"])
        check("事件 %d 的原文非空且含关键红字" % i,
              bool(joined.strip()) and ("\u274c" in joined or "失败" in joined or "GAP" in joined),
              joined[:60])
    check("事件①原文点名了 content/event_templates.py 与 _host_content",
          "_host_content" in EV1_VERBATIM and "event_templates.py" in EV1_VERBATIM)
    check("事件②原文是「夜红 77/1」那份", "77 通过 / 1 失败" in EV2_VERBATIM)
    check("事件③原文是「未声明的域文件 text_specs.json」那份",
          "text_specs.json" in EV3_VERBATIM and "失败 1" in EV3_VERBATIM)


# ======================================================================================
# ② 有牙：挖掉一条映射 -> self-check / 回放必须报红 -> 还原复绿
# ======================================================================================

def test_teeth_remove_mapping():
    section("② 有牙反证：挖掉一条映射 -> 回放与 self-check 必须报红 -> 还原复绿")

    # 基线：当前树上 self-check 全绿 + 事件①回放含 import_closure
    rc0, out0 = capture_plan(["--changed", "fw:games/orlandia/content/event_templates.py"])
    sel0 = selected_ids(out0)
    check("[基线] 事件①回放含 import_closure", "import_closure" in sel0, ",".join(sel0))
    sc_rc0 = GF.main(["--host", _REPO, "--framework", FW_ROOT, "--self-check"]) \
        if os.path.isdir(FW_ROOT) else None
    check("[基线] --self-check 返回 0（无盲区）", sc_rc0 == 0, "rc=%s" % sc_rc0)

    victim = GF.GATES_BY_ID["import_closure"]
    saved = list(victim.covers)
    try:
        victim.covers = []                                     # 挖掉这条映射
        rc1, out1 = capture_plan(["--changed", "fw:games/orlandia/content/event_templates.py"])
        sel1 = selected_ids(out1)
        check("[有牙·回放] 挖掉 import_closure 后，事件①回放**选不中**它（回放断言会红）",
              "import_closure" not in sel1, ",".join(sel1))
        sc_rc1 = GF.main(["--host", _REPO, "--framework", FW_ROOT, "--self-check"]) \
            if os.path.isdir(FW_ROOT) else None
        check("[有牙·self-check] 挖掉映射后 --self-check 返回非零（3=有盲区）",
              sc_rc1 == 3, "rc=%s" % sc_rc1)
    finally:
        victim.covers = saved                                  # 还原

    rc2, out2 = capture_plan(["--changed", "fw:games/orlandia/content/event_templates.py"])
    sel2 = selected_ids(out2)
    check("[还原] 事件①回放又含 import_closure", "import_closure" in sel2, ",".join(sel2))
    sc_rc2 = GF.main(["--host", _REPO, "--framework", FW_ROOT, "--self-check"]) \
        if os.path.isdir(FW_ROOT) else None
    check("[还原] --self-check 复绿（返回 0）", sc_rc2 == 0, "rc=%s" % sc_rc2)


def test_teeth_remove_no_gate_annotation():
    section("②-2 有牙反证：把 NO_GATE 整表撤掉 -> self-check 必须报出盲区 -> 还原复绿")
    if not os.path.isdir(FW_ROOT):
        check("[SKIP] 引擎仓不存在，跳过本条", True)
        return
    saved = list(GF.NO_GATE)
    try:
        GF.NO_GATE[:] = []
        rc = GF.main(["--host", _REPO, "--framework", FW_ROOT, "--self-check"])
        check("[有牙] 撤掉无覆盖标注后 --self-check 报红（3）", rc == 3, "rc=%s" % rc)
    finally:
        GF.NO_GATE[:] = saved
    rc2 = GF.main(["--host", _REPO, "--framework", FW_ROOT, "--self-check"])
    check("[还原] 标注还原后 --self-check 复绿（0）", rc2 == 0, "rc=%s" % rc2)


# ======================================================================================
# ③ 不许静默少跑
# ======================================================================================

def test_no_silent_skip():
    section("③ 不许静默少跑：只改 docs 的场景必须明示「跳过了全部行为门禁」")

    rc, out = capture_plan(["--changed", "fw:docs/engine-wiki/reference/package-format.md"])
    check("docs-only 场景 rc=0", rc == 0, "rc=%s" % rc)
    check("输出里出现「跳过了全部行为门禁」（醒目提示）",
          "跳过了全部行为门禁" in out, out[-300:])
    sel = [g for g in selected_ids(out) if g not in ("smoke_engine", "smoke_pkg_import")]
    check("docs-only 场景**没有**任何行为门禁被选中（wiki_refs 属文档层）",
          all(GF.GATES_BY_ID[g].tier == "docs" for g in sel), ",".join(sel))
    check("docs-only 场景仍然跑了 cheap 冒烟",
          "smoke_engine" in selected_ids(out) and "smoke_pkg_import" in selected_ids(out))

    rc2, out2 = capture_plan(["--changed", "host:docs/whatever.md"])
    check("完全不可判定的 docs 路径：同样明示「跳过了全部行为门禁」+ 只剩冒烟",
          "跳过了全部行为门禁" in out2
          and all(g in ("smoke_engine", "smoke_pkg_import") for g in selected_ids(out2)),
          ",".join(selected_ids(out2)))

    # 每一个「已跳过」都必须逐条带原因；且都要指到 --full
    check("「已跳过」段逐条带原因", out.count("\u23ed\ufe0f ") >= 1 and "跳过原因" in out)
    check("「已跳过」段落指向批收口 --full", "--full" in out)

    # 跳过的门禁不影响退出码：--plan 全跳过时 rc 仍为 0
    check("跳过不影响退出码（全跳过时 --plan rc=0）", rc == 0)


def test_skip_list_is_complete():
    section("③-2 跳过清单完备性：每一道没跑的门禁都必须在「已跳过」里出现")
    rc, out = capture_plan(["--changed", "host:game/commands/combat.py"])
    sel = set(selected_ids(out))
    listed = set(skipped_ids(out))
    not_listed = sorted(set(GF.GATES_BY_ID) - sel - listed)
    check("选中 ∪ 已跳过 == 映射表全集（没有门禁被静默吞掉）",
          not not_listed, "未出现在任何清单里：%s" % ",".join(not_listed))
    skip_lines = [l for l in out.splitlines()
                  if l.strip().startswith("\u23ed\ufe0f ")
                  and l.strip()[2:].split()[:1] and l.strip()[2:].split()[0] in GF.GATES_BY_ID]
    check("已跳过清单里每一条都带 tier 标签与原因",
          bool(skip_lines) and all("[" in l and "]" in l for l in skip_lines), skip_lines[:1])


# ======================================================================================
# ④ --full 与手工那套等价（清单并排对照 + 差异逐条解释）
# ======================================================================================

def test_full_equivalence():
    section("④ --full 与手工那套（7 道）等价：并排对照 + 差异逐条解释")
    rc, out = capture_plan(["--full"])
    check("--full --plan rc=0", rc == 0, "rc=%s" % rc)
    sel = selected_ids(out)
    missing = [m for m in GF.MANUAL_CANON if m not in sel]
    check("手工那套 7 道全部在 --full 清单里（手工那套 ⊂ --full）", not missing,
          "缺：%s" % ",".join(missing))
    check("--full 清单 = 映射表全集（一道不漏）",
          len([g for g in sel]) >= len(GF.GATES), "%d < %d" % (len(sel), len(GF.GATES)))

    check("打印了并排对照表（表头 `#   手工那套`）", "#" in out and "手工那套" in out)
    check("并排对照里每一条手工门禁都标了「同一条」",
          out.count("同一条") >= len(GF.MANUAL_CANON), "同一条 x%d" % out.count("同一条"))
    extras = [g.gid for g in GF.GATES if g.gid not in GF.MANUAL_CANON]
    explained = sum(1 for e in extras
                    if ("\u2795 %-18s" % e) in out or ("\u2795 " + e) in out)
    check("--full 多出来的 %d 道**逐条**给了多跑的理由" % len(extras),
          explained == len(extras), "解释了 %d 条" % explained)
    check("对照段里给了手工那套的证据出处（p4pf gates_final.log）",
          "gates_final.log" in out)


# ======================================================================================
# ⑤ run_all_tests.py 不受影响
# ======================================================================================

def test_run_all_untouched():
    section("⑤ scripts/run_all_tests.py（278 文件全量：宿主自留件 6 + 包仓那份 272）不受影响")
    p = os.path.join(_SCRIPTS, "run_all_tests.py")
    check("run_all_tests.py 存在（可单独跑）", os.path.exists(p))
    if os.path.exists(p):
        with io.open(p, "rb") as fh:
            data = fh.read()
        md5 = hashlib.md5(data).hexdigest().upper()
        check("run_all_tests.py md5 与冻结值一致（本工具零改动）",
              md5 == RUN_ALL_TESTS_MD5, "实际 %s" % md5)
        text = data.decode("utf-8", "replace")
        check("run_all_tests.py 里不出现 gate_fast（没有反向依赖/没有绕过它）",
              "gate_fast" not in text)
        check("run_all_tests.py 语法可编译（仍能单独跑）",
              bool(compile(text, p, "exec")))
        check("仍保留 --file= / --skip= / --serial 三个既有开关",
              all(k in text for k in ("--file=", "--skip=", "--serial")))
    host_runall = GF.GATES_BY_ID.get("host_runall")
    check("gate_fast 对全量是**原样转调**（argv 就是 run_all_tests.py）",
          host_runall is not None and host_runall.argv == ["scripts/run_all_tests.py"])
    check("全量门禁只在 --full 跑（不进 --changed）",
          host_runall is not None and host_runall.selectable is False)

    src_path = os.path.join(_SCRIPTS, "gate_fast.py")
    with io.open(src_path, encoding="utf-8") as fh:
        src = fh.read()
    check("gate_fast 只写 --json 指定的那一个文件（源码里 write-mode open 恰好 1 处）",
          src.count('io.open(args.json, "w"') == 1 and src.count(', "w", encoding') == 1,
          "write-open=%d" % src.count(', "w", encoding'))
    check("gate_fast 里没有 shutil / rmtree / 任何删改仓内文件的动作",
          "shutil" not in src and "rmtree" not in src and "os.remove" not in src)


# ======================================================================================
# ⑥ 退出码口径
# ======================================================================================

def test_exit_code_semantics():
    section("⑥ 退出码口径：已跑的门禁有红 -> 非零；跳过不影响退出码")
    # --plan 是纯计算，永远 0（它不跑门禁）
    rc, out = capture_plan(["--changed", "fw:games/orlandia/content/event_templates.py"])
    check("--plan 不因「选中了可能变红的门禁」而改变退出码（rc=0）", rc == 0)
    check("输出里写明了退出码口径",
          "退出码口径" in out and "已跳过" in out)
    # 未给模式 -> 用法错（2）
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc2 = GF.main(["--host", _REPO, "--framework", FW_ROOT])
    finally:
        sys.stdout = old
    check("不给 --changed/--full/--self-check -> 用法错 rc=2", rc2 == 2, "rc=%s" % rc2)
    # --gates 未知 id -> 2
    sys.stdout = buf = io.StringIO()
    try:
        rc3 = GF.main(["--host", _REPO, "--framework", FW_ROOT, "--gates", "no_such_gate"])
    finally:
        sys.stdout = old
    check("--gates 给未知门禁 -> 用法错 rc=2", rc3 == 2, "rc=%s" % rc3)


def test_auto_and_normalize():
    section("⑥-2 --changed 的路径归一（各写法都落到同一个门禁集合）")
    variants = [
        ["fw:games/orlandia/content/event_templates.py"],
        ["framework/games/orlandia/content/event_templates.py"],
        [os.path.join(FW_ROOT, "games", "orlandia", "content", "event_templates.py")],
        [os.path.join(_REPO, "framework", "games", "orlandia", "content", "event_templates.py")],
    ]
    sets = []
    for v in variants:
        rc, out = capture_plan(["--changed"] + v)
        sets.append(set(selected_ids(out)))
    check("四种写法（fw: 前缀 / framework/ 前缀 / 引擎仓绝对路径 / 宿主仓 framework 绝对路径）选出同一集合",
          len(set(frozenset(s) for s in sets)) == 1,
          str([sorted(s) for s in sets]))
    check("宿主仓里的 framework/<rel> 与引擎仓 <rel> 等价（子模块镜像口径）",
          sets[0] == sets[1] == sets[2] == sets[3])


def main():
    print("门禁：gate_fast（门禁快速档）映射正确性 / 有牙 / 不许静默少跑")
    print("宿主插件仓 : %s" % _REPO)
    print("引擎仓     : %s%s" % (FW_ROOT, "" if os.path.isdir(FW_ROOT) else "   <-- 不存在！"))
    test_mapping_table_integrity()
    test_historical_replays()
    test_replay_verbatim_kept()
    test_teeth_remove_mapping()
    test_teeth_remove_no_gate_annotation()
    test_no_silent_skip()
    test_skip_list_is_complete()
    test_full_equivalence()
    test_run_all_untouched()
    test_exit_code_semantics()
    test_auto_and_normalize()

    section("汇总")
    print("  通过 %d / 失败 %d" % (_passed, len(_failed)))
    if _failed:
        print("  失败项：")
        for f in _failed:
            print("    \u274c %s" % f)
        return 1
    print("  全绿 \u2705")
    return 0


if __name__ == "__main__":
    sys.exit(main())
