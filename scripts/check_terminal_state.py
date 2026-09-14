#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TERMGATE · 终态验收门禁 —— 把「宿主外壳化终态」的四条判据（计划 §6 六项）做成一条命令。

为什么需要它
------------
「宿主外壳化终态」的判据此前**每次都要人手数**（2026-09-14 晚手工数过：宿主 12,524 行 /
`orlandia|from content\\.` 101 处 / 渲染调用点 0 处）。做成可跑门禁后，P6/B21 验收与每批搬迁后
复核都变成一条命令。

两种模式（都要）
----------------
    python scripts/check_terminal_state.py             # **差距报告**：逐条打印 当前值/目标/差额/状态
                                                       #   退出码 **恒为 0**（现在还没达标，报差距是正常的）
    python scripts/check_terminal_state.py --check     # **断言达标**：任一条不满足 → 退出码非零（P6/B21 用这个）

常用开关
--------
    --repo PATH      宿主插件仓根（默认：本脚本上级目录，即 <repo>/scripts/..）
    --engine PATH    引擎仓根（默认 $GWEN_FRAMEWORK_DIR > C:/Users/yuyu/framework-engine > <repo>/framework）
    --python PATH    跑引擎门禁的解释器（默认 sys.executable）
    --py-path DIR    追加到子进程 PYTHONPATH（沙箱下传 `<自己目录>/_env` 用，见下「沙箱坑」）
    --timeout SEC    单条外部门禁超时（默认 600）
    --skip-external  只算本地判据 ①②③⑥，不跑引擎侧 ④⑤（快速冒烟用；--check 下 skip 视为未达标，fail-closed）
    --json-out PATH  另存机器可读结果（`-` = 打到 stdout）

六条判据（逐条打印 当前值 / 目标 / 状态，并给可复核命令）
--------------------------------------------------------
    ① 宿主规模   game/**/*.py + main.py 的 .py 行数                目标 ≤ 2,000
    ② 零包知识   `orlandia|from content\\.` 命中数（另收严口径，见下） 目标 0
    ③ 命令层不渲染  命令层里 T.text / T.static 的**调用点**             目标 0
    ④ 换包能跑   同宿主跑 orlandia + minimal-game 各一场（转调引擎门禁/骨架 demo）
    ⑤ host 契约  saintess_engine 侧 26 项 + 骨架 5 项（转调，不复制实现）
    ⑥ 包内覆盖   scripts/verify_package_coverage.py --check 0 失败

口径（★ 写进输出，可人手复核）
------------------------------
① 行数：`os.walk(<repo>/game)` 收 `*.py`，跳过 `__pycache__`，**排除路径段 tests/ scripts/ tools/**
   （排除项是否命中会打印）；再 `+ <repo>/main.py`。等价于「game/**/*.py + main.py」。
② 命中：按**行**计（`grep -rn` 语义），范围 `game/` 全树 + `main.py`：
   · 口径A = 计划 §6 原文 `orlandia|from content\\.`（今晚实测线 101 处，本脚本原样复现）
   · 口径B = 门禁用（fail-closed）= 口径A ∪ `from content import ...` ∪ 行首 `import content...`
     ★ 为什么按 B：作业书 §3② 的反证就是「在副本里塞一行 `from content import x` → 对应判据变红」；
       口径A 的 `from content\\.` **抓不到** `from content import x`（没有点）→ 无牙。故状态按 B 判。
③ 渲染调用点：对 `game/commands/**/*.py` 做 **AST** 扫描，数「`T.text(...)` / `T.static(...)` 调用表达式」。
   注释/文档串里提到 `T.text/T.static` **不算调用点**（这个口径差会一并打印，见「口径A(原始 grep)」）。
   `event.plain_result(...)` = 宿主适配器的**回话出口**（B18_TERMINAL_SHAPE §1.3 明写保留），
   不计入渲染；其条数也会打印出来，不做隐藏。
④⑤ 引擎门禁**转调**（不复制实现），退出码 + 汇总行双证据：
   `tests/test_host_contract.py`（26 项）· `tests/test_host_skeleton.py`（5 项）
   · `examples/minimal-game/tests/test_smoke.py`（minimal-game 包自身冒烟）。
⑥ 原样转调宿主仓既有门禁 `scripts/verify_package_coverage.py --check`，解析其「失败 N」。

沙箱坑（Windows dsh 沙箱，见 overnight/B18-QUEUE-gwen.md 落地姿势第 0 条）
--------------------------------------------------------------------------
沙箱下 `tempfile.mkdtemp` 用 `os.mkdir(path, 0o700)` → 拿不到写 ACE → 走临时目录的引擎门禁**假红**。
本脚本**不改仓内文件**；沙箱下请加 `--py-path <自己目录>/_env`（内含只换 `mkdtemp` 的 sitecustomize），
真仓 / CI 不需要、也不该带。本脚本对子进程设 `PYTHONDONTWRITEBYTECODE=1`，不往真仓写 `__pycache__`。

真仓只读：本脚本自分只读文件；⑥ 转调的门禁自述「自始只读」；④⑤ 只写系统临时目录。
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------- 常量 / 口径

DEFAULT_ENGINE = "C:/Users/yuyu/framework-engine"        # 与 verify_package_coverage.py 同默认
SKIP_SEGMENTS = ("__pycache__", "tests", "scripts", "tools")   # 口径① 的排除段
LAX_RE = re.compile(r"orlandia|from content\.")
STRICT_RE = re.compile(r"orlandia|from\s+content(?:\.|\s+import\b)|^\s*import\s+content(?:\.|\s|$)")
RENDER_ATTRS = ("text", "static")                        # 口径③：T.text / T.static
PLAIN_RESULT_RE = re.compile(r"\.plain_result\s*\(")
TARGET_HOST_LINES = 2000
TARGET_CONTRACT_ITEMS = 26
TARGET_SKELETON_ITEMS = 5

PASS, FAIL, SKIP = "pass", "fail", "skip"
MARK = {PASS: "✅", FAIL: "❌", SKIP: "⚠️"}


def _u8(stream) -> None:
    try:                                                 # 控制台编码（GBK 控制台打印 ✅/中文会炸）
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                    # noqa: BLE001
        pass


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _py_files(base: str, skip: tuple = ()) -> list:
    """收 `base` 下所有 .py（跳过 `skip` 里的路径段与 __pycache__）。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in skip and d != "__pycache__"]
        for name in filenames:
            if name.endswith(".py"):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


def _lines(path: str) -> int:
    return sum(1 for _ in open(path, "r", encoding="utf-8", errors="replace"))


def _fmt(n) -> str:
    return "{:,}".format(n) if isinstance(n, int) else str(n)


# ---------------------------------------------------------------- 外部门禁转调

class GateRunner:
    """在子进程里转调引擎/宿主门禁，缓存结果（④⑤ 共用一次骨架跑）。"""

    def __init__(self, python: str, timeout: int, py_path: str | None = None):
        self.python = python
        self.timeout = timeout
        self.py_path = py_path
        self.cache: dict = {}

    def run(self, script: str, cwd: str, extra_env: dict | None = None) -> dict:
        key = (os.path.abspath(script), os.path.abspath(cwd), json.dumps(extra_env or {}, sort_keys=True))
        if key in self.cache:
            return self.cache[key]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"              # 不往真仓写 __pycache__
        if self.py_path:
            old = env.get("PYTHONPATH") or ""
            env["PYTHONPATH"] = self.py_path + (os.pathsep + old if old else "")
        for k, v in (extra_env or {}).items():
            env[k] = str(v)
        res = {"script": script, "cwd": cwd, "exit": None, "out": "", "error": None, "ok": False}
        if not os.path.isfile(script):
            res["error"] = "脚本不存在：%s" % script
        else:
            try:
                pr = subprocess.run([self.python, script], cwd=cwd, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    env=env, timeout=self.timeout)
                res["exit"] = pr.returncode
                res["out"] = (pr.stdout or "") + (pr.stderr or "")
                res["ok"] = pr.returncode == 0
            except subprocess.TimeoutExpired:
                res["error"] = "超时 >%ss" % self.timeout
            except OSError as exc:                         # noqa: BLE001
                res["error"] = "启动失败：%s" % exc
        self.cache[key] = res
        return res


def _last_summary(out: str) -> str:
    for line in reversed((out or "").splitlines()):
        if line.strip():
            return line.strip()
    return "(无输出)"


def _grep(out: str, pattern: str):
    return [ln for ln in (out or "").splitlines() if re.search(pattern, ln)]


# ---------------------------------------------------------------- 判据 ①

def crit_host_size(repo: str) -> dict:
    game_dir = os.path.join(repo, "game")
    main_py = os.path.join(repo, "main.py")
    all_game = _py_files(game_dir) if os.path.isdir(game_dir) else []
    kept = [p for p in all_game
            if not any(seg in os.path.relpath(p, game_dir).replace("\\", "/").split("/")
                       for seg in ("tests", "scripts", "tools"))]
    dropped = [p for p in all_game if p not in kept]
    per_dir: dict = {}
    for p in kept:
        rel = os.path.relpath(os.path.dirname(p), game_dir).replace("\\", "/")
        per_dir[rel if rel != "." else "game 根"] = per_dir.get(rel if rel != "." else "game 根", 0) + _lines(p)
    game_lines = sum(per_dir.values())
    main_lines = _lines(main_py) if os.path.isfile(main_py) else 0
    total = game_lines + main_lines
    status = PASS if total <= TARGET_HOST_LINES else FAIL
    evidence = [
        "game/ %s 行 / %d 文件 ＋ main.py %s 行 → 合计 %s 行"
        % (_fmt(game_lines), len(kept), _fmt(main_lines), _fmt(total)),
        "分层：" + " · ".join("%s %s" % (k, _fmt(v)) for k, v in sorted(per_dir.items(), key=lambda kv: -kv[1])),
        "排除项本次命中：tests/scripts/tools 路径段 %d 个文件%s"
        % (len(dropped), ("（" + ", ".join(os.path.relpath(p, repo) for p in dropped[:5]) + "）") if dropped else "（本仓 game/ 下无这些目录）"),
    ]
    return {
        "id": "①", "title": "宿主规模（game/**/*.py + main.py ≤ 2,000 行）",
        "caliber": "os.walk(<repo>/game) 收 *.py，跳 __pycache__，排除路径段 tests|scripts|tools；再 + <repo>/main.py",
        "current": "%s 行" % _fmt(total), "target": "≤ %s 行" % _fmt(TARGET_HOST_LINES),
        "gap": "+%s 行" % _fmt(total - TARGET_HOST_LINES) if total > TARGET_HOST_LINES else "0（达标）",
        "status": status, "evidence": evidence,
        "num": {"game_lines": game_lines, "game_files": len(kept), "main_lines": main_lines, "total": total,
                "target": TARGET_HOST_LINES, "excluded_files": len(dropped)},
        "commands": [
            "python scripts/check_terminal_state.py --json-out termgate.json   # 取 criteria[0].num.total",
            "bash: find game -name '*.py' -not -path '*/__pycache__/*' -not -path '*/tests/*' "
            "-not -path '*/scripts/*' -not -path '*/tools/*' -print0 | xargs -0 wc -l ; wc -l main.py",
        ],
    }


# ---------------------------------------------------------------- 判据 ②

def crit_zero_knowledge(repo: str) -> dict:
    files = _py_files(os.path.join(repo, "game"))
    main_py = os.path.join(repo, "main.py")
    if os.path.isfile(main_py):
        files.append(main_py)
    lax_lines = lax_files = strict_lines = strict_files = 0
    lax_set, strict_set = set(), set()
    for path in files:
        for line in open(path, "r", encoding="utf-8", errors="replace"):
            if LAX_RE.search(line):
                lax_lines += 1
                lax_set.add(path)
            if STRICT_RE.search(line):
                strict_lines += 1
                strict_set.add(path)
    lax_files, strict_files = len(lax_set), len(strict_set)
    status = PASS if strict_lines == 0 else FAIL
    return {
        "id": "②", "title": "零包知识（包知识命中数 = 0）",
        "caliber": "按行计（grep -rn 语义），范围 game/ 全树 + main.py。"
                   "口径A=计划§6原文 `orlandia|from content\\.`；"
                   "口径B=门禁口径（fail-closed）=A ∪ `from content import` ∪ 行首 `import content`",
        "current": "口径B %s 处 / %d 文件（口径A %s 处 / %d 文件）"
                   % (_fmt(strict_lines), strict_files, _fmt(lax_lines), lax_files),
        "target": "0 处", "gap": "+%s 处（口径B）" % _fmt(strict_lines) if strict_lines else "0（达标）",
        "status": status,
        "evidence": [
            "口径A（计划 §6 原文，今晚实测线 101 处）：%s 处 / %d 文件" % (_fmt(lax_lines), lax_files),
            "口径B（本门禁判定口径）：%s 处 / %d 文件（比 A 多 %s 处 = `from content import ...` 之类）"
            % (_fmt(strict_lines), strict_files, _fmt(strict_lines - lax_lines)),
            "★ 按 B 判的理由：§3② 反证塞的是 `from content import x`（无点），口径A 抓不到 → 无牙",
        ],
        "num": {"lax_lines": lax_lines, "lax_files": lax_files,
                "strict_lines": strict_lines, "strict_files": strict_files},
        "commands": [
            'grep -rEn "orlandia|from content\\." game/ main.py | wc -l        # 口径A（今晚实测 101）',
            "grep -rEn \"orlandia|from content\\.|from content import|^import content\" game/ main.py | wc -l   # 口径B",
            "python scripts/check_terminal_state.py --json-out -   # criteria[1].num",
        ],
    }


# ---------------------------------------------------------------- 判据 ③

def crit_no_render(repo: str) -> dict:
    cmd_dir = os.path.join(repo, "game", "commands")
    files = _py_files(cmd_dir)
    calls: dict = {}
    raw_lines = 0
    raw_re = re.compile(r"T\.(?:%s)\b" % "|".join(RENDER_ATTRS))
    plain_lines = 0
    plain_files = set()
    for path in files:
        src = _read_text(path)
        raw_lines += sum(1 for ln in src.splitlines() if raw_re.search(ln))
        for ln in src.splitlines():
            if PLAIN_RESULT_RE.search(ln):
                plain_lines += 1
                plain_files.add(path)
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in RENDER_ATTRS
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "T"):
                rel = os.path.relpath(path, repo).replace("\\", "/")
                calls[rel] = calls.get(rel, 0) + 1
    total = sum(calls.values())
    status = PASS if total == 0 else FAIL
    return {
        "id": "③", "title": "命令层不渲染（game/commands 里 T.text/T.static 调用点 = 0）",
        "caliber": "AST 扫描 game/commands/**/*.py，数调用表达式 T.text(...) / T.static(...)；"
                   "注释与文档串里的同名字样不算调用点",
        "current": "%d 处调用点" % total, "target": "0 处",
        "gap": "+%d 处" % total if total else "0（达标）", "status": status,
        "evidence": [
            "AST 调用点：%d 处%s" % (total, ("（" + ", ".join("%s×%d" % kv for kv in sorted(calls.items())) + "）") if calls else ""),
            "参考·口径A(原始 grep，含注释/文档串提及)：%d 行 — 所以 `grep -c` 不为 0 不等于有渲染调用点" % raw_lines,
            "参考·event.plain_result(...)（宿主适配器回话出口，B18_TERMINAL_SHAPE §1.3 明写保留，不计渲染）：%d 行 / %d 文件"
            % (plain_lines, len(plain_files)),
        ],
        "num": {"ast_calls": total, "raw_grep_lines": raw_lines,
                "plain_result_lines": plain_lines, "plain_result_files": len(plain_files),
                "cmd_files": len(files)},
        "commands": [
            "grep -rEn 'T\\.text|T\\.static' game/commands/ | wc -l        # 口径A（含注释，%d）" % raw_lines,
            "grep -rEn '\\.plain_result\\(' game/commands/ | wc -l          # 回话出口（%d）" % plain_lines,
            "python scripts/check_terminal_state.py --json-out -   # criteria[2].num.ast_calls",
        ],
    }


# ---------------------------------------------------------------- 判据 ④

def crit_swap_packages(engine: str, runner: GateRunner) -> dict:
    runs = []
    if not os.path.isdir(engine):
        return {
            "id": "④", "title": "换包能跑（同宿主跑 orlandia + minimal-game 各一场）",
            "caliber": "转调引擎门禁/骨架 demo（不复制实现）", "current": "引擎仓不存在", "target": "2/2 场通过",
            "gap": "无法判定", "status": SKIP, "evidence": ["引擎仓目录不存在：%s" % engine],
            "num": {"passed": 0, "total": 2}, "commands": [],
        }
    # ④.1 orlandia 包走通用骨架宿主
    skel = os.path.join(engine, "tests", "test_host_skeleton.py")
    r1 = runner.run(skel, engine)
    ok1 = bool(r1["ok"]) and "全绿" in r1["out"]
    runs.append(("orlandia 包 × 通用骨架宿主（tests/test_host_skeleton.py）", ok1, r1))
    # ④.2 minimal-game 包自身冒烟
    smoke = os.path.join(engine, "examples", "minimal-game", "tests", "test_smoke.py")
    r2 = runner.run(smoke, os.path.dirname(os.path.dirname(smoke)))
    m = re.search(r"通过\s*(\d+)\s*/\s*(\d+)", r2["out"] or "")
    ok2 = bool(r2["ok"]) and bool(m)
    runs.append(("minimal-game 包（examples/minimal-game/tests/test_smoke.py）", ok2, r2))
    passed = sum(1 for _, ok, _ in runs if ok)
    status = PASS if passed == len(runs) else FAIL
    evidence = []
    for label, ok, res in runs:
        if res["error"]:
            evidence.append("%s → ❌ %s" % (label, res["error"]))
        else:
            evidence.append("%s → %s exit=%s；%s" % (label, MARK[PASS] if ok else MARK[FAIL], res["exit"],
                                                      _last_summary(res["out"])))
    if m:
        evidence.append("minimal-game 冒烟计数：通过 %s / %s" % (m.group(1), m.group(2)))
    return {
        "id": "④", "title": "换包能跑（同宿主跑 orlandia + minimal-game 各一场）",
        "caliber": "转调引擎门禁/骨架 demo：host-skeleton 宿主跑 orlandia 包 + minimal-game 包自冒烟",
        "current": "%d/%d 场通过" % (passed, len(runs)), "target": "2/2 场通过",
        "gap": "0（达标）" if status == PASS else "%d 场未过" % (len(runs) - passed), "status": status,
        "evidence": evidence,
        "num": {"passed": passed, "total": len(runs),
                "orlandia_ok": ok1, "minimal_ok": ok2},
        "commands": [
            "python %s" % os.path.join(engine, "tests", "test_host_skeleton.py"),
            "python %s" % os.path.join(engine, "examples", "minimal-game", "tests", "test_smoke.py"),
        ],
    }


# ---------------------------------------------------------------- 判据 ⑤

def crit_host_contract(engine: str, runner: GateRunner) -> dict:
    if not os.path.isdir(engine):
        return {
            "id": "⑤", "title": "host 契约（引擎侧 26 项 + 骨架 5 项）",
            "caliber": "转调引擎门禁，退出码 + 汇总行双证据", "current": "引擎仓不存在",
            "target": "26 项 + 5 项 全绿", "gap": "无法判定", "status": SKIP,
            "evidence": ["引擎仓目录不存在：%s" % engine], "num": {},
            "commands": [],
        }
    contract = os.path.join(engine, "tests", "test_host_contract.py")
    skeleton = os.path.join(engine, "tests", "test_host_skeleton.py")
    rc = runner.run(contract, engine)
    rs = runner.run(skeleton, engine)
    mc = re.search(r"全绿（(\d+)\s*项）", rc["out"] or "")
    ms = re.search(r"全绿（(\d+)\s*项）", rs["out"] or "")
    c_items = int(mc.group(1)) if mc else None
    s_items = int(ms.group(1)) if ms else None
    ok = (bool(rc["ok"]) and c_items == TARGET_CONTRACT_ITEMS
          and bool(rs["ok"]) and s_items == TARGET_SKELETON_ITEMS)
    summary_c = next((ln.strip() for ln in (rc["out"] or "").splitlines() if "全绿" in ln), _last_summary(rc["out"]))
    summary_s = next((ln.strip() for ln in (rs["out"] or "").splitlines() if "全绿" in ln), _last_summary(rs["out"]))
    evidence = [
        "tests/test_host_contract.py → %s exit=%s 项=%s；%s"
        % (MARK[PASS] if (rc["ok"] and c_items == TARGET_CONTRACT_ITEMS) else MARK[FAIL],
           rc["exit"], c_items if c_items is not None else "?", summary_c),
        "tests/test_host_skeleton.py → %s exit=%s 项=%s；%s"
        % (MARK[PASS] if (rs["ok"] and s_items == TARGET_SKELETON_ITEMS) else MARK[FAIL],
           rs["exit"], s_items if s_items is not None else "?", summary_s),
    ]
    if rc["error"]:
        evidence.append("contract 执行问题：%s" % rc["error"])
    if rs["error"]:
        evidence.append("skeleton 执行问题：%s" % rs["error"])
    return {
        "id": "⑤", "title": "host 契约（引擎侧 26 项 + 骨架 5 项）",
        "caliber": "转调引擎仓 tests/test_host_contract.py（26 项）与 tests/test_host_skeleton.py（5 项）；"
                   "引擎仓路径 = --engine > $GWEN_FRAMEWORK_DIR > 默认",
        "current": "%s 项 + %s 项" % (c_items if c_items is not None else "?", s_items if s_items is not None else "?"),
        "target": "%d 项 + %d 项 全绿" % (TARGET_CONTRACT_ITEMS, TARGET_SKELETON_ITEMS),
        "gap": "0（达标）" if ok else "未达标", "status": PASS if ok else FAIL, "evidence": evidence,
        "num": {"contract_items": c_items, "skeleton_items": s_items,
                "contract_exit": rc["exit"], "skeleton_exit": rs["exit"]},
        "commands": ["python %s" % contract, "python %s" % skeleton],
    }


# ---------------------------------------------------------------- 判据 ⑥

def crit_package_coverage(repo: str, engine: str, runner: GateRunner) -> dict:
    script = os.path.join(repo, "scripts", "verify_package_coverage.py")
    res = runner.run(script, repo, extra_env={"GWEN_FRAMEWORK_DIR": engine})
    fails = None
    for m in re.finditer(r"失败\s*(\d+)", res["out"] or ""):
        fails = int(m.group(1))
    bad = _grep(res["out"] or "", r"❌")
    ok = bool(res["ok"]) and fails == 0
    evidence = ["scripts/verify_package_coverage.py --check → %s exit=%s 失败=%s；%s"
                % (MARK[PASS] if ok else MARK[FAIL], res["exit"], fails if fails is not None else "?",
                   _last_summary(res["out"]))]
    if res["error"]:
        evidence.append("执行问题：%s" % res["error"])
    if bad:
        evidence.append("失败项：%s" % "；".join(ln.strip() for ln in bad[:5]))
    return {
        "id": "⑥", "title": "包内覆盖（scripts/verify_package_coverage.py --check 0 失败）",
        "caliber": "原样转调宿主仓既有门禁；引擎仓经 GWEN_FRAMEWORK_DIR 传入（与 ⑤ 同一路径）",
        "current": "%s 失败" % (fails if fails is not None else "?"), "target": "0 失败",
        "gap": "0（达标）" if ok else "%s 项失败" % (fails if fails is not None else "?"),
        "status": PASS if ok else FAIL, "evidence": evidence,
        "num": {"fails": fails, "exit": res["exit"], "fail_lines": len(bad)},
        "commands": ["GWEN_FRAMEWORK_DIR=%s python scripts/verify_package_coverage.py --check" % engine],
    }


# ---------------------------------------------------------------- 渲染 / 汇总

def render(results: list, meta: dict, mode: str) -> None:
    print("=" * 78)
    print("TERMGATE · 终态验收门禁 —— 宿主外壳化终态 · 六条判据")
    print("模式：%s" % ("差距报告（默认；退出码恒为 0）" if mode == "report"
                       else "断言达标 --check（任一条不满足 → 退出码非零）"))
    print("宿主仓：%s" % meta["repo"])
    print("引擎仓：%s   （来源：%s）" % (meta["engine"], meta["engine_source"]))
    print("时间：%s · 解释器：%s" % (meta["time"], meta["python"]))
    print("=" * 78)
    for r in results:
        print("\n%s %s" % (r["id"], r["title"]))
        print("   口径：%s" % r["caliber"])
        print("   当前：%s" % r["current"])
        print("   目标：%s      差额：%s      状态：%s" % (r["target"], r["gap"], MARK[r["status"]]))
        for ev in r["evidence"]:
            print("   · %s" % ev)
        for cmd in r["commands"]:
            print("   复核：%s" % cmd)
    n_pass = sum(1 for r in results if r["status"] == PASS)
    n_fail = sum(1 for r in results if r["status"] == FAIL)
    n_skip = sum(1 for r in results if r["status"] == SKIP)
    print("\n" + "=" * 78)
    print("== 汇总（逐条 当前 / 目标 / 状态）==")
    for r in results:
        print("  %s %s  %s / %s  %s" % (MARK[r["status"]], r["id"], r["current"], r["target"], r["gap"]))
    print("  ── 达标 %d 条 / 未达标 %d 条 / 未判定 %d 条" % (n_pass, n_fail, n_skip))
    if mode == "report":
        print("  [差距报告] 退出码 0（默认模式：现在还没达标，报差距是正常的）")
    else:
        bad = [r["id"] for r in results if r["status"] != PASS]
        print("  [断言达标] %s" % ("❌ 未达标：%s → 退出码 1" % " ".join(bad) if bad else "✅ 六条全绿 → 退出码 0"))
    print("=" * 78)


def main(argv=None) -> int:
    _u8(sys.stdout)
    _u8(sys.stderr)
    ap = argparse.ArgumentParser(
        description="终态验收门禁（默认=差距报告退 0；--check=断言达标退非零）",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=None, help="宿主插件仓根（默认：本脚本上级目录）")
    ap.add_argument("--engine", default=None, help="引擎仓根（默认 $GWEN_FRAMEWORK_DIR > 内置默认 > <repo>/framework）")
    ap.add_argument("--python", default=sys.executable, help="跑引擎门禁的解释器（默认 sys.executable）")
    ap.add_argument("--py-path", default=None, help="追加到子进程 PYTHONPATH（沙箱下传 <自己目录>/_env）")
    ap.add_argument("--timeout", type=int, default=600, help="单条外部门禁超时秒（默认 600）")
    ap.add_argument("--skip-external", action="store_true", help="只算 ①②③⑥（跳过 ④⑤ 的引擎门禁）")
    ap.add_argument("--check", action="store_true", help="断言达标：任一条不满足 → 退出码非零")
    ap.add_argument("--json-out", default=None, help="另存 JSON 结果（`-` = stdout）")
    args = ap.parse_args(argv)

    repo = os.path.abspath(args.repo or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    if args.engine:
        engine, engine_source = os.path.abspath(args.engine), "--engine"
    elif os.environ.get("GWEN_FRAMEWORK_DIR"):
        engine, engine_source = os.path.abspath(os.environ["GWEN_FRAMEWORK_DIR"]), "$GWEN_FRAMEWORK_DIR"
    elif os.path.isdir(DEFAULT_ENGINE):
        engine, engine_source = os.path.abspath(DEFAULT_ENGINE), "默认内置路径"
    else:
        engine, engine_source = os.path.abspath(os.path.join(repo, "framework")), "<repo>/framework 回退"

    runner = GateRunner(args.python, args.timeout, args.py_path)

    results = [crit_host_size(repo), crit_zero_knowledge(repo), crit_no_render(repo)]
    if args.skip_external:
        for cid, title in (("④", "换包能跑（同宿主跑 orlandia + minimal-game 各一场）"),
                           ("⑤", "host 契约（引擎侧 26 项 + 骨架 5 项）")):
            results.append({"id": cid, "title": title, "caliber": "本次 --skip-external 未执行（不隐藏：不判定）",
                            "current": "未执行", "target": "—", "gap": "未判定", "status": SKIP,
                            "evidence": ["按 --skip-external 跳过；断言模式下 skip 视为未达标（fail-closed）"],
                            "num": {}, "commands": []})
    else:
        results.append(crit_swap_packages(engine, runner))
        results.append(crit_host_contract(engine, runner))
    results.append(crit_package_coverage(repo, engine, runner))

    meta = {"repo": repo, "engine": engine, "engine_source": engine_source,
            "time": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "python": args.python, "mode": "check" if args.check else "report"}
    render(results, meta, meta["mode"])

    payload = {"meta": meta, "criteria": results,
               "summary": {"pass": sum(1 for r in results if r["status"] == PASS),
                           "fail": sum(1 for r in results if r["status"] == FAIL),
                           "skip": sum(1 for r in results if r["status"] == SKIP),
                           "ok": all(r["status"] == PASS for r in results)}}
    if args.json_out:
        blob = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json_out == "-":
            print(blob)
        else:
            with open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(blob + "\n")
            print("JSON → %s" % os.path.abspath(args.json_out))

    if not args.check:
        return 0
    return 0 if payload["summary"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
