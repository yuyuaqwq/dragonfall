# -*- coding: utf-8 -*-
"""数值门禁：CLASS_MECHANICS_v153 设计文档自动校验（`scripts/audit_v153.py` 固化进门槛）。

来源：v153 §待办 原句「`audit_v153.py` 固化进 CI，作为数值变更准入门槛」——本文件即该门槛
（2026-09-11 落地）。脚本本身只在报告里打印告警、**不设退出码**，本门禁补上退出码与逐段断言。

防退化基线（任意一条变红 = 技能表 / 文档被改坏）：
  1. `audit_v153.py` 退出码 0，报告可读
  2. 报告「【总告警】N 条」中 N = 0
  3. 16 段逐段 ✅：A eps 天花板/观感帽 · B 记法唯一性 · C 多段 ≤ 同档单体 ×1.10 ·
     D 分档数量+等级升序 · E 不重名 · F 真伤 ≤2/线 · G mp=0 白名单 · G2 规则逃逸 ·
     H 伤害技必有 CD 或代价 · I 孤儿机制 · J 机制重复 · K 控制倒挂 · L cast 节奏 vs §0.3 ·
     M 唯一技能数 · N 回合残留（刻） · O 与引擎常量一致性
  4. 技能条目数不下降（≥294）——条目变少说明技能被误删（也是 §待办 C-14「cast 字段落库」的基线）

跑法：python tests/test_numeric_v153_audit.py（exit=0 全绿）
"""
import os
import re
import subprocess
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 与 scripts/run_numeric_tests.py 同一个项目解释器（带依赖）
PYTHON = r"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"

SEGS = ["A", "B", "C", "D", "E", "F", "G", "G2", "H", "I", "J", "K", "L", "M", "N", "O"]
MIN_SKILLS = 294          # v153 技能条目基线（2026-09-11 实测 294）

PASS = 0
FAIL = 0
FAILURES = []


from _check import bind_check  # noqa: E402  P0-1 断言助手单源：tests/_check.py

check = bind_check(globals(), "PASS", "FAIL", "FAILURES")


def run_audit():
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run(
        [PYTHON, os.path.join(PLUGIN_DIR, "scripts", "audit_v153.py")],
        cwd=PLUGIN_DIR, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env, timeout=300)


def main():
    print("== v153 设计文档校验门禁（audit_v153.py 固化进门槛）==")
    p = run_audit()
    out = (p.stdout or "") + (p.stderr or "")

    check("audit_v153.py 退出码 = 0", p.returncode == 0,
          f"rc={p.returncode} tail={out[-400:]!r}")
    check("报告含『总告警』汇总行", "总告警" in out, f"tail={out[-200:]!r}")

    m = re.search(r"【总告警】(\d+) 条", out)
    check("总告警 = 0 条", bool(m) and m.group(1) == "0",
          m.group(0) if m else "未匹配到【总告警】行")

    missing = [s for s in SEGS if f"── {s}. " not in out]
    check(f"16 段报告齐全（实测缺 {len(missing)} 段：{missing}）", not missing, f"missing={missing}")

    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("── ") and "✅ 通过" not in l]
    check("所有段 ✅ 通过（无 ⚠ 段）", not bad, " | ".join(bad[:5]))

    m2 = re.search(r"【技能条目】(\d+)", out)
    n = int(m2.group(1)) if m2 else 0
    check(f"技能条目数 ≥ {MIN_SKILLS}（实测 {n}）", n >= MIN_SKILLS, f"n={n}（技能被误删？）")

    print(f"\n== 结果：通过 {PASS} / 共 {PASS + FAIL} ==")
    if FAILURES:
        for f in FAILURES:
            print("  FAIL:", f)
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
