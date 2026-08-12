# -*- coding: utf-8 -*-
"""全量回归：逐个直接执行 tests/test_*.py（旧式脚本 + pytest 风格均可独立运行）。

用法：
  python scripts/run_all_tests.py [--file tests/test_xxx.py] [--fail-fast]

注意：
  - 必须用 AstrBot 的 uv python（带 pypinyin）：C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe
  - 所有测试共用 test_game_data.db，顺序执行没问题；但全量跑完前不要并行跑单测（会互相 clean_db 污染）
  - 跑全量期间不要改动任何源文件（避免中间态误判）
"""
import os
import subprocess
import sys
import time

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(PLUGIN_DIR, "tests")
PYTHON = r"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"

def main():
    fail_fast = "--fail-fast" in sys.argv
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--file="):
            only = a.split("=", 1)[1]

    if only:
        files = [only] if only.endswith(".py") else [only + ".py"]
        # 兼容两种传法：--file=test_xxx.py 或 --file=tests/test_xxx.py（避免重复 join）
        files = [os.path.join(TESTS_DIR, os.path.basename(f)) if not os.path.isabs(f) else f for f in files]
    else:
        files = sorted(
            f for f in os.listdir(TESTS_DIR)
            if f.startswith("test_") and f.endswith(".py")
        )
        files = [os.path.join(TESTS_DIR, f) for f in files]

    results = []
    t0 = time.time()
    for f in files:
        name = os.path.basename(f)
        ts = time.time()
        proc = subprocess.run(
            [PYTHON, f], capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        dt = time.time() - ts
        ok = proc.returncode == 0
        results.append((name, ok, proc, dt))
        flag = "✅" if ok else "❌"
        print(f"{flag} {name} ({dt:.1f}s, exit={proc.returncode})", flush=True)
        if not ok:
            # 只打印最后 30 行失败输出，避免刷屏
            lines = (proc.stdout or "").strip().splitlines()
            tail = lines[-30:] if lines else []
            print("\n".join(tail), flush=True)
            print("-" * 60, flush=True)
            if fail_fast:
                break

    # 汇总
    print("\n" + "=" * 60)
    passed = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    print(f"文件: {len(results)} 个，通过 {len(passed)}，失败 {len(failed)}，总耗时 {time.time()-t0:.0f}s")
    if failed:
        print("失败文件:")
        for name, _, _, _ in failed:
            print(f"  ❌ {name}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
