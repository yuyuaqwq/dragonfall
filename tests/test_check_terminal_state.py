#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""门禁自测：`scripts/check_terminal_state.py` 的**判据与口径**正确 + **有牙**（反证会变红）。

跑法（与宿主仓其它 tests 一致，可独立执行，也可被 pytest / scripts/run_all_tests.py 收走）：
    python tests/test_check_terminal_state.py          # exit 0 = 全绿

它在验什么（对应作业书 §3「脚本自己也得有牙」）
------------------------------------------------
  ① 口径正确 —— 在**合成夹具仓**里验证三条本地判据的口径：①的行数含 game/**/*.py + main.py
     且排除 tests|scripts|tools；②按**行**计并复现计划 §6 原文口径（口径A）与 fail-closed 口径（口径B）；
     ③按 **AST 调用点**计（注释/文档串提及不算）。
  ② 有牙（反证）—— 在夹具**临时副本**里故意塞 `from content import x` / 真 `T.text(...)` 调用 /
     把文件撑过行数阈值 → 对应判据变红（`--check` 退非零）；**还原 → 复绿**（`--check` 退 0）。
     另加反向反证：只塞**注释**里的 `T.text` 不许变红（防假红）。
  ③ 零假绿 —— 输出里每条 ✅ 都必须带命中数证据（current 与 evidence 都含数字）。
  ④ 真仓标定 —— 对真宿主仓（若在）复核 ③=0 调用点、①/② 与独立重算一致，并做一次真仓副本反证
     （+1 行 `from content import x` → 口径B 恰 +1 → 还原回原值）。
  ⑤ 模式语义 —— 默认=差距报告恒退 0；`--check`=断言达标退非零；`--skip-external` 在 `--check` 下
     fail-closed（skip ≠ pass）。

沙箱坑（Windows dsh 沙箱，见 overnight/B18-QUEUE-gwen.md 落地姿势第 0 条）
--------------------------------------------------------------------------
本测试**不调用 `tempfile.mkdtemp`**（沙箱下 0o700 目录会假红），改用 `os.makedirs` + uuid 自建可写临时目录
→ 沙箱与真仓/CI 行为一致，不需要 `_env` 猴补。测试只写系统临时目录，绝不写真仓。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from _check import bind_check


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                                   # 宿主仓根（本文件在 <repo>/tests/）
CHECKER = os.path.join(REPO, "scripts", "check_terminal_state.py")
# 真仓标定的对象仓：落地后 = REPO；在「只读真仓 + 产物放 out/」的沙箱作业里可用该 env 指到真宿主仓
REAL_REPO = os.path.abspath(os.environ.get("TERMGATE_REAL_REPO") or REPO)
REAL_ENGINE = os.environ.get("GWEN_FRAMEWORK_DIR") or "C:/Users/yuyu/framework-engine"

FAILS: list = []
CHECKS = 0


# ---------------------------------------------------------------- 极小测试脚手架（独立执行 + pytest 双模）

# ★ 审计 P0-1 单源化：断言助手唯一实现 = tests/_check.py
#   （原先本文件手抄一份 def check；差异项已作为 bind_check 参数写出）
check = bind_check(globals(), total="CHECKS", failures="FAILS", strict=True)


# ---------------------------------------------------------------- 临时目录（沙箱安全：不用 mkdtemp）

def _sandbox_safe_tmp(prefix: str) -> str:
    """`os.makedirs` 默认 mode（受 umask）→ 沙箱下也可写；刻意避开 `tempfile.mkdtemp` 的 0o700。"""
    base = tempfile.gettempdir()
    for _ in range(50):
        path = os.path.join(base, "%s%s" % (prefix, uuid.uuid4().hex[:10]))
        try:
            os.makedirs(path)                                  # 默认 mode，不传 0o700
            return path
        except FileExistsError:
            continue
    raise RuntimeError("建临时目录连续撞名")


def _write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _write_lines(path: str, n: int) -> None:
    _write(path, "".join("X%d = %d\n" % (i, i) for i in range(n)))


# ---------------------------------------------------------------- 合成夹具：宿主仓 + 引擎仓

CLEAN_MOD = "# -*- coding: utf-8 -*-\nVALUE = 1\n"
CLEAN_PANEL = "# -*- coding: utf-8 -*-\ndef build(env):\n    return [\"ok\"]\n"

COVERAGE_STUB_FAIL = '''# -*- coding: utf-8 -*-
"""夹具：冒充 scripts/verify_package_coverage.py —— 报 %(n)d 失败、退 1。"""
print("=== 4. 汇总 ===")
print("  域 1 个 / 条目合计 2 / 失败 %(n)d")
raise SystemExit(1)
'''

CONTRACT_STUB = '''# -*- coding: utf-8 -*-
"""夹具：冒充引擎 tests/test_host_contract.py（复现「全绿（N 项）+ 退出码」契约）。"""
import sys
N = int(sys.argv[1]) if len(sys.argv) > 1 else 26
print("✅ 宿主契约全绿（%d 项）：stub" % N)
sys.exit(0 if N == 26 else 1)
'''

SKELETON_STUB = '''# -*- coding: utf-8 -*-
"""夹具：冒充引擎 tests/test_host_skeleton.py（复现「全绿（N 项）+ 退出码」契约）。"""
import sys
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
print("✅ 宿主骨架冒烟全绿（%d 项）：stub" % N)
sys.exit(0 if N == 5 else 1)
'''

SMOKE_STUB = '''# -*- coding: utf-8 -*-
"""夹具：冒充引擎 examples/minimal-game/tests/test_smoke.py（复现冒烟计数契约）。"""
print("===== 结果：通过 20 / 20 =====")
'''

FIXTURE_COVERAGE = '''# -*- coding: utf-8 -*-
"""夹具仓自带门禁（冒充）：0 失败 → 退 0。"""
print("=== 4. 汇总 ===")
print("  域 1 个 / 条目合计 2 / 失败 0")
'''


def build_fixture_repo(root: str, *, coverage_fails: int = 0) -> str:
    """合规夹具仓：①小 ②零包知识 ③零渲染调用点 ⑥0 失败（coverage_fails>0 时夹具门禁报红）。"""
    _write(os.path.join(root, "game", "mod.py"), CLEAN_MOD)
    _write(os.path.join(root, "game", "commands", "panel.py"), CLEAN_PANEL)
    _write(os.path.join(root, "main.py"), "# -*- coding: utf-8 -*-\nprint('host')\n")
    stub = FIXTURE_COVERAGE if not coverage_fails else (COVERAGE_STUB_FAIL % {"n": coverage_fails})
    _write(os.path.join(root, "scripts", "verify_package_coverage.py"), stub)
    return root


def build_fixture_engine(root: str, *, contract_n: int = 26, skeleton_n: int = 5) -> str:
    _write(os.path.join(root, "tests", "test_host_contract.py"), CONTRACT_STUB)
    _write(os.path.join(root, "tests", "test_host_skeleton.py"), SKELETON_STUB)
    _write(os.path.join(root, "examples", "minimal-game", "tests", "test_smoke.py"), SMOKE_STUB)
    return root


# ---------------------------------------------------------------- 跑门禁

def run_checker(repo: str, engine: str, *, check_mode: bool = False, skip_external: bool = False,
                json_out: str | None = None, timeout: int = 300) -> dict:
    cmd = [sys.executable, CHECKER, "--repo", repo, "--engine", engine, "--python", sys.executable,
           "--timeout", str(timeout)]
    if check_mode:
        cmd.append("--check")
    if skip_external:
        cmd.append("--skip-external")
    if json_out is None:
        json_out = os.path.join(_sandbox_safe_tmp("tg_json_"), "out.json")
    cmd += ["--json-out", json_out]
    env = dict(os.environ)
    env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    pr = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                        env=env, timeout=timeout, cwd=repo)
    payload = None
    if os.path.isfile(json_out):
        with open(json_out, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    out = (pr.stdout or "") + (pr.stderr or "")
    return {"exit": pr.returncode, "out": out, "json": payload,
            "crit": ({c["id"]: c for c in payload["criteria"]} if payload else {})}


def _num(res: dict, cid: str, key: str):
    return res["crit"][cid]["num"][key]


def _fresh_pair(**kw) -> tuple:
    repo = build_fixture_repo(_sandbox_safe_tmp("tg_repo_"), **kw)
    engine = build_fixture_engine(_sandbox_safe_tmp("tg_engine_"))
    return repo, engine


def _rm(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


# ================================================================ 测试
# ① 口径正确

def test_clean_fixture_is_all_green_in_check_mode():
    repo, engine = _fresh_pair()
    try:
        res = run_checker(repo, engine, check_mode=True)
        check("--check 在合规夹具仓上退 0", res["exit"] == 0, "exit=%s" % res["exit"])
        check("JSON summary.ok = true", res["json"] and res["json"]["summary"]["ok"] is True)
        for cid in ("①", "②", "③", "④", "⑤", "⑥"):
            check("判据 %s 合规夹具上为 pass" % cid, res["crit"][cid]["status"] == "pass",
                  res["crit"][cid]["current"])
    finally:
        _rm(repo)
        _rm(engine)


def test_default_mode_exits_zero_even_when_failing():
    repo, engine = _fresh_pair()
    try:
        _write(os.path.join(repo, "game", "mod.py"), CLEAN_MOD + "from content import x\n")
        res = run_checker(repo, engine)                       # 默认模式：差距报告
        check("默认模式即使有未达标项也退 0", res["exit"] == 0, "exit=%s" % res["exit"])
        check("输出标注「差距报告」", "差距报告" in res["out"])
        check("JSON 如实记下未达标条数", res["json"]["summary"]["fail"] >= 1,
              str(res["json"]["summary"]))
    finally:
        _rm(repo)
        _rm(engine)


def test_caliber_one_counts_and_excludes():
    repo, engine = _fresh_pair()
    try:
        _write_lines(os.path.join(repo, "game", "big_extra.py"), 10)
        _write(os.path.join(repo, "main.py"), "".join("M%d = %d\n" % (i, i) for i in range(7)))
        res = run_checker(repo, engine, skip_external=True)
        # game/mod.py 2 行 + game/commands/panel.py 3 行 + big_extra.py 10 行 = 15；main.py 7 行
        check("① game/ 行数 = 15", _num(res, "①", "game_lines") == 15, str(_num(res, "①", "game_lines")))
        check("① main.py 行数 = 7", _num(res, "①", "main_lines") == 7, str(_num(res, "①", "main_lines")))
        check("① 合计 = 22", _num(res, "①", "total") == 22, str(_num(res, "①", "total")))
        # 排除口径：game/tests|scripts|tools 下的 .py 不计入
        _write_lines(os.path.join(repo, "game", "tests", "ignored.py"), 500)
        _write_lines(os.path.join(repo, "game", "scripts", "ignored.py"), 500)
        res2 = run_checker(repo, engine, skip_external=True)
        check("① 排除 tests|scripts|tools 后合计不变", _num(res2, "①", "total") == 22,
              str(_num(res2, "①", "total")))
        check("① 报告被排除文件数 = 2", _num(res2, "①", "excluded_files") == 2,
              str(_num(res2, "①", "excluded_files")))
    finally:
        _rm(repo)
        _rm(engine)


def test_caliber_two_counts_lines_and_both_scopes():
    repo, engine = _fresh_pair()
    try:
        # 口径A 命中 3 行 / 2 文件；其中 1 行是无点的 `from content import`（口径B 才算）
        _write(os.path.join(repo, "game", "mod.py"),
               "from content.catalog import A\n"        # A: 有点 → A、B 都算
               "from content import B\n"                # 无点 → 只有 B 算
               "X = 'orlandia'\n")                      # orlandia → A、B 都算
        _write(os.path.join(repo, "game", "commands", "panel.py"),
               "import content.persistence as P\n")     # 行首 import content → 只有 B 算
        res = run_checker(repo, engine, skip_external=True)
        check("② 口径A 行数 = 2（点式 + orlandia）", _num(res, "②", "lax_lines") == 2,
              str(_num(res, "②", "lax_lines")))
        check("② 口径B 行数 = 4（多收 `from content import` 与 `import content.`）", _num(res, "②", "strict_lines") == 4,
              str(_num(res, "②", "strict_lines")))
        check("② 命中 > 0 → fail", res["crit"]["②"]["status"] == "fail")
    finally:
        _rm(repo)
        _rm(engine)


def test_caliber_three_is_ast_call_sites_not_text_mentions():
    repo, engine = _fresh_pair()
    try:
        _write(os.path.join(repo, "game", "commands", "panel.py"),
               CLEAN_PANEL + "# 注释里提到 T.text / T.static 不算调用点\n")
        res = run_checker(repo, engine, skip_external=True)
        check("③ 只有注释提及 → 调用点 0", _num(res, "③", "ast_calls") == 0,
              str(_num(res, "③", "ast_calls")))
        check("③ 同时如实报出原始 grep 命中行数 = 1", _num(res, "③", "raw_grep_lines") == 1,
              str(_num(res, "③", "raw_grep_lines")))
        check("③ 注释提及不判红（防假红）", res["crit"]["③"]["status"] == "pass")
    finally:
        _rm(repo)
        _rm(engine)


def test_caliber_six_plumbing_reports_real_failure():
    repo = build_fixture_repo(_sandbox_safe_tmp("tg_repo_"), coverage_fails=1)
    engine = build_fixture_engine(_sandbox_safe_tmp("tg_engine_"))
    try:
        res = run_checker(repo, engine, check_mode=True)
        check("⑥ 门禁报 1 失败 → --check 退非零", res["exit"] != 0, "exit=%s" % res["exit"])
        check("⑥ 解析出失败数 = 1", _num(res, "⑥", "fails") == 1, str(_num(res, "⑥", "fails")))
    finally:
        _rm(repo)
        _rm(engine)


# ② 有牙：反证

def test_tooth_content_import_goes_red_then_restore_green():
    """★ 作业书点名的反证：副本里塞一行 `from content import x` → 判据②变红；还原 → 复绿。"""
    repo, engine = _fresh_pair()
    target = os.path.join(repo, "game", "mod.py")
    try:
        base = run_checker(repo, engine, check_mode=True)
        check("基线：合规夹具 --check 退 0", base["exit"] == 0)
        before = _num(base, "②", "strict_lines")
        check("基线：② 口径B = 0", before == 0, str(before))

        original = open(target, encoding="utf-8").read()
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("from content import x  # TOOTH\n")
        red = run_checker(repo, engine, check_mode=True)
        check("塞入后 ② 口径B 恰 +1", _num(red, "②", "strict_lines") == before + 1,
              "%s → %s" % (before, _num(red, "②", "strict_lines")))
        check("塞入后 ② 变红", red["crit"]["②"]["status"] == "fail")
        check("--check 退非零（有牙）", red["exit"] != 0, "exit=%s" % red["exit"])

        with open(target, "w", encoding="utf-8", newline="\n") as fh:   # 逐字还原
            fh.write(original)
        green = run_checker(repo, engine, check_mode=True)
        check("还原后 ② 回到原值", _num(green, "②", "strict_lines") == before,
              str(_num(green, "②", "strict_lines")))
        check("还原后 --check 复绿退 0", green["exit"] == 0, "exit=%s" % green["exit"])
    finally:
        _rm(repo)
        _rm(engine)


def test_tooth_orlandia_and_dotted_import_go_red():
    repo, engine = _fresh_pair()
    target = os.path.join(repo, "game", "mod.py")
    try:
        base = run_checker(repo, engine, skip_external=True)
        original = open(target, encoding="utf-8").read()
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("from content.catalog_rules import K  # TOOTH\nX2 = 'orlandia'\n")
        res = run_checker(repo, engine, skip_external=True)
        check("口径A 对 `from content.` 与 `orlandia` 各 +1",
              _num(res, "②", "lax_lines") == _num(base, "②", "lax_lines") + 2,
              "%s → %s" % (_num(base, "②", "lax_lines"), _num(res, "②", "lax_lines")))
        check("② 变红", res["crit"]["②"]["status"] == "fail")
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(original)
        check("还原后 ② 复绿",
              run_checker(repo, engine, skip_external=True)["crit"]["②"]["status"] == "pass")
    finally:
        _rm(repo)
        _rm(engine)


def test_tooth_real_render_call_goes_red_but_comment_does_not():
    repo, engine = _fresh_pair()
    target = os.path.join(repo, "game", "commands", "panel.py")
    try:
        original = open(target, encoding="utf-8").read()
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n\ndef _tooth(env):\n    return T.text('some.key')\n")
        red = run_checker(repo, engine, check_mode=True)
        check("真调用 T.text(...) → ③ 调用点 = 1", _num(red, "③", "ast_calls") == 1,
              str(_num(red, "③", "ast_calls")))
        check("③ 变红且 --check 退非零", red["crit"]["③"]["status"] == "fail" and red["exit"] != 0)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(original)
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n# 只在注释里提 T.static，不许判红\n")
        soft = run_checker(repo, engine, check_mode=True)
        check("只加注释提及 → ③ 仍绿、--check 仍退 0（反向反证）",
              _num(soft, "③", "ast_calls") == 0 and soft["exit"] == 0,
              "calls=%s exit=%s" % (_num(soft, "③", "ast_calls"), soft["exit"]))
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(original)
        check("还原后 --check 复绿", run_checker(repo, engine, check_mode=True)["exit"] == 0)
    finally:
        _rm(repo)
        _rm(engine)


def test_tooth_over_line_threshold_goes_red():
    repo, engine = _fresh_pair()
    big = os.path.join(repo, "game", "too_big.py")
    try:
        _write_lines(big, 2001)
        red = run_checker(repo, engine, check_mode=True)
        check("撑过阈值后 ① 超 2,000 行", _num(red, "①", "total") > 2000,
              str(_num(red, "①", "total")))
        check("① 变红且 --check 退非零", red["crit"]["①"]["status"] == "fail" and red["exit"] != 0)
        os.remove(big)
        check("移除大文件后 --check 复绿", run_checker(repo, engine, check_mode=True)["exit"] == 0)
    finally:
        _rm(repo)
        _rm(engine)


def test_tooth_broken_gate_contract_goes_red():
    """④⑤ 的牙：夹具引擎门禁项数不对 → 判据红（证明我们真的读了项数，不是只看退出码）。"""
    repo = build_fixture_repo(_sandbox_safe_tmp("tg_repo_"))
    engine = build_fixture_engine(_sandbox_safe_tmp("tg_engine_"), contract_n=25)
    try:
        # 夹具 stub 读 argv；这里换成「少一项且退 1」的变体
        _write(os.path.join(engine, "tests", "test_host_contract.py"),
               CONTRACT_STUB.replace("N = int(sys.argv[1]) if len(sys.argv) > 1 else 26", "N = 25"))
        res = run_checker(repo, engine, check_mode=True)
        check("⑤ 读到项数 25（不是只信退出码）", _num(res, "⑤", "contract_items") == 25,
              str(_num(res, "⑤", "contract_items")))
        check("⑤ 变红且 --check 退非零", res["crit"]["⑤"]["status"] == "fail" and res["exit"] != 0)
    finally:
        _rm(repo)
        _rm(engine)


def test_skip_external_is_fail_closed_under_check():
    repo, engine = _fresh_pair()
    try:
        ok = run_checker(repo, engine, check_mode=True)
        check("基线 --check 退 0", ok["exit"] == 0)
        skipped = run_checker(repo, engine, check_mode=True, skip_external=True)
        check("--skip-external 把 ④⑤ 记为 skip", skipped["json"]["summary"]["skip"] == 2,
              str(skipped["json"]["summary"]))
        check("--check 下 skip ≠ pass（fail-closed）", skipped["exit"] != 0, "exit=%s" % skipped["exit"])
    finally:
        _rm(repo)
        _rm(engine)


# ③ 零假绿

def test_no_green_without_numeric_evidence():
    repo, engine = _fresh_pair()
    try:
        res = run_checker(repo, engine, check_mode=True)
        for cid, c in res["crit"].items():
            if c["status"] != "pass":
                continue
            check("零假绿：%s 的 current 带数字证据" % cid,
                  re.search(r"\d", c["current"]) is not None, c["current"])
            check("零假绿：%s 的 evidence 带数字证据" % cid,
                  any(re.search(r"\d", ev) for ev in c["evidence"]))
    finally:
        _rm(repo)
        _rm(engine)


# ④ 真仓标定 + 真仓副本反证

def test_real_repo_calibration_and_counterproof():
    if not os.path.isfile(CHECKER):
        raise AssertionError("找不到主脚本：%s" % CHECKER)
    if not os.path.isfile(os.path.join(REAL_REPO, "main.py")):
        raise AssertionError("真宿主仓里找不到 main.py：%s（可用 TERMGATE_REAL_REPO 指路）" % REAL_REPO)
    res = run_checker(REAL_REPO, REAL_ENGINE, skip_external=True)
    check("真仓：默认模式产出 JSON", res["json"] is not None)
    print("     · 真仓标定：① %s 行 · ② 口径A %s 处/%s 文件 · 口径B %s 处/%s 文件 · ③ %s 调用点"
          % (_num(res, "①", "total"), _num(res, "②", "lax_lines"), _num(res, "②", "lax_files"),
             _num(res, "②", "strict_lines"), _num(res, "②", "strict_files"), _num(res, "③", "ast_calls")))
    # ③ 的「已达标」硬标定：命令层零渲染调用点
    check("真仓 ③ AST 渲染调用点 = 0", _num(res, "③", "ast_calls") == 0)
    # ① 独立重算（另一种写法）必须一致
    # ★ P5F-REPOINT: `game/` 是待删树，终态可能整个不存在 —— `os.walk` 对不存在的目录
    #   产出空序列，与判据①（`crit_host_size()` 的 `os.path.isdir(game_dir)` 守卫）**同口径**：
    #   两边都退化成「只有 main.py」，重算仍逐值相等（无需分支）。
    total = 0
    for dirpath, dirnames, filenames in os.walk(os.path.join(REAL_REPO, "game")):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tests", "scripts", "tools")]
        for name in filenames:
            if name.endswith(".py"):
                total += len(open(os.path.join(dirpath, name), encoding="utf-8", errors="replace").readlines())
    total += len(open(os.path.join(REAL_REPO, "main.py"), encoding="utf-8", errors="replace").readlines())
    check("真仓 ① 与独立重算一致", _num(res, "①", "total") == total,
          "%s vs %s" % (_num(res, "①", "total"), total))
    # ② 独立重算（口径A）必须一致 —— 同时把今晚实测线 101 打出来（不一致会在此暴露）
    lax = 0
    files = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(REAL_REPO, "game")):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        files += [os.path.join(dirpath, n) for n in filenames if n.endswith(".py")]
    files.append(os.path.join(REAL_REPO, "main.py"))
    rx = re.compile(r"orlandia|from content\.")
    for path in files:
        lax += sum(1 for ln in open(path, encoding="utf-8", errors="replace") if rx.search(ln))
    check("真仓 ② 口径A 与独立重算一致", _num(res, "②", "lax_lines") == lax,
          "%s vs %s" % (_num(res, "②", "lax_lines"), lax))

    # 真仓副本反证：+1 行 `from content import x` → 口径B 恰 +1；还原 → 回原值
    copy = _sandbox_safe_tmp("tg_realcopy_")
    try:
        for rel in ("game",):
            src_rel = os.path.join(REAL_REPO, rel)
            # ★ P5F-REPOINT: 终态 `game/`（待删树）可能整个不存在 ⇒ 不 copytree 而是**建空树**，
            #   使下面「塞 1 行到 `game/mod_probe.py`」仍落在判据②的口径范围内（判据不变）。
            if os.path.isdir(src_rel):
                shutil.copytree(src_rel, os.path.join(copy, rel),
                                ignore=shutil.ignore_patterns("__pycache__"))
            else:
                os.makedirs(os.path.join(copy, rel), exist_ok=True)
        shutil.copy2(os.path.join(REAL_REPO, "main.py"), os.path.join(copy, "main.py"))
        _write(os.path.join(copy, "scripts", "verify_package_coverage.py"), FIXTURE_COVERAGE)
        base = run_checker(copy, REAL_ENGINE, skip_external=True)
        target = os.path.join(copy, "game", "mod_probe.py")
        _write(target, "from content import x  # REAL-REPO TOOTH\n")
        after = run_checker(copy, REAL_ENGINE, skip_external=True)
        check("真仓副本：塞 1 行 `from content import x` → 口径B 恰 +1",
              _num(after, "②", "strict_lines") == _num(base, "②", "strict_lines") + 1,
              "%s → %s" % (_num(base, "②", "strict_lines"), _num(after, "②", "strict_lines")))
        check("真仓副本：② 判红（真仓本来就没达标）", after["crit"]["②"]["status"] == "fail")
        os.remove(target)
        back = run_checker(copy, REAL_ENGINE, skip_external=True)
        check("真仓副本：还原后口径B 回原值",
              _num(back, "②", "strict_lines") == _num(base, "②", "strict_lines"),
              "%s → %s" % (_num(after, "②", "strict_lines"), _num(back, "②", "strict_lines")))
    finally:
        _rm(copy)


# ================================================================ 独立执行入口

TESTS = [
    ("clean_fixture_all_green", test_clean_fixture_is_all_green_in_check_mode),
    ("default_mode_exit_zero", test_default_mode_exits_zero_even_when_failing),
    ("caliber_one", test_caliber_one_counts_and_excludes),
    ("caliber_two", test_caliber_two_counts_lines_and_both_scopes),
    ("caliber_three", test_caliber_three_is_ast_call_sites_not_text_mentions),
    ("caliber_six", test_caliber_six_plumbing_reports_real_failure),
    ("tooth_content_import_restore", test_tooth_content_import_goes_red_then_restore_green),
    ("tooth_orlandia_dotted", test_tooth_orlandia_and_dotted_import_go_red),
    ("tooth_render_call_vs_comment", test_tooth_real_render_call_goes_red_but_comment_does_not),
    ("tooth_line_threshold", test_tooth_over_line_threshold_goes_red),
    ("tooth_gate_contract", test_tooth_broken_gate_contract_goes_red),
    ("skip_external_fail_closed", test_skip_external_is_fail_closed_under_check),
    ("no_false_green", test_no_green_without_numeric_evidence),
    ("real_repo_calibration", test_real_repo_calibration_and_counterproof),
]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass
    print("=== 门禁自测：scripts/check_terminal_state.py（口径 + 有牙）===")
    print("被测脚本：%s（仓根 %s）" % (CHECKER, REPO))
    print("真仓标定对象：%s\n引擎仓：%s" % (REAL_REPO, REAL_ENGINE))
    failed_tests = []
    for name, fn in TESTS:
        print("\n--- %s" % name)
        try:
            fn()
        except AssertionError as exc:
            failed_tests.append((name, str(exc)))
            print("  ⛔ 该组未过")
        except Exception as exc:                             # noqa: BLE001
            failed_tests.append((name, "%s: %s" % (type(exc).__name__, exc)))
            print("  ⛔ 该组异常：%s: %s" % (type(exc).__name__, exc))
    print("\n" + "=" * 60)
    print("断言行数：%d · 组数：%d" % (CHECKS, len(TESTS)))
    if failed_tests:
        print("❌ 未过 %d 组：" % len(failed_tests))
        for name, detail in failed_tests:
            print("   · %s  %s" % (name, detail))
        return 1
    print("✅ 门禁自测全绿（%d 组 / %d 条断言）：口径正确 + 有牙 + 零假绿 + 真仓标定" % (len(TESTS), CHECKS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
