# -*- coding: utf-8 -*-
"""临时审计回归运行器：用系统 Python 3.12 逐个直跑 tests/test_*.py（镜像 run_all_tests.py）。
仅审计 Agent 2 临时使用，跑完全量后删除。"""
import os
import sys
import subprocess
import time
import json

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("GWEN_GAME_DB", os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_game_data.db"))

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(PLUGIN_DIR, "tests")
PYTHON = r"C:/Users/yuyu/AppData/Local/Programs/Python/Python312/python.exe"
OUT = os.path.join(PLUGIN_DIR, "scripts", "_audit_regression_result.json")

def main():
    files = sorted(
        f for f in os.listdir(TESTS_DIR)
        if f.startswith("test_") and f.endswith(".py")
    )
    results = []
    t0 = time.time()
    for f in files:
        path = os.path.join(TESTS_DIR, f)
        ts = time.time()
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        try:
            proc = subprocess.run([PYTHON, path], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env, timeout=300)
            timed_out = False
        except subprocess.TimeoutExpired as _te:
            timed_out = True
            proc = _te
        dt = time.time() - ts
        ok = False if timed_out else (proc.returncode == 0)
        results.append({"name": f, "ok": ok, "timed_out": timed_out,
                        "exit": None if timed_out else proc.returncode,
                        "dt": round(dt, 1),
                        "tail": None if ok else ((proc.stdout or "")[-2000:] + "\n---STDERR---\n" + (proc.stderr or "")[-1500:])})
        print(("PASS" if ok else "FAIL") + f" {f} ({dt:.1f}s)", flush=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)
    passed = sum(1 for r in results if r["ok"])
    print(f"\n==== 文件 {len(results)} 通过 {passed} 失败 {len(results)-passed} 耗时 {time.time()-t0:.0f}s ====", flush=True)
    for r in results:
        if not r["ok"]:
            print(f"FAIL {r['name']} exit={r['exit']} {r['dt']}s", flush=True)

if __name__ == "__main__":
    main()
