# -*- coding: utf-8 -*-
"""批量跑 saintess_engine 测试并统计 framework/saintess_engine 覆盖率（stdlib trace，零依赖）。

跑法：python tools/cov_battle2.py
输出：每个 saintess_engine 模块的 executed/total 行数 + 未覆盖行号。
"""
import os
import sys
import trace
import glob

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))  # 引擎框架包（S8 物理分离：framework/ 为引擎 submodule）
TEST_DIR = os.path.join(PLUGIN_DIR, "tests")

os.chdir(PLUGIN_DIR)

test_files = sorted(glob.glob(os.path.join(TEST_DIR, "test_battle2_*.py")))
print(f"跑 {len(test_files)} 个测试文件")

# 单 tracer 跨文件累积（runctx 每次执行累积 counts）
tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.prefix])

for tf in test_files:
    try:
        code = compile(open(tf, encoding="utf-8").read(), tf, "exec")
        _ns = {"__name__": "__main__", "__file__": tf}
        tracer.runctx(code, _ns, _ns)  # globals=locals 同一 dict，函数定义可被 main 找到
    except SystemExit:
        pass  # 测试文件 sys.exit(0/1) 正常
    except Exception as e:
        print(f"  ⚠️ {os.path.basename(tf)} 异常: {type(e).__name__} {e}")

# 汇总 saintess_engine 目录覆盖率
from collections import defaultdict
file_lines = defaultdict(set)
file_exec = defaultdict(set)
for (fn, ln), cnt in (tracer.counts or {}).items():
    fn = fn.replace("\\", "/")
    if "/framework/saintess_engine/" not in fn:
        continue
    file_lines[fn].add(ln)
    if cnt > 0:
        file_exec[fn].add(ln)

total = exe = 0
print("\n=== saintess_engine 覆盖率（行级） ===")
for fn in sorted(file_lines):
    t = len(file_lines[fn])
    e = len(file_exec[fn])
    total += t
    exe += e
    name = fn.split("/saintess_engine/")[-1]
    missing = sorted(file_lines[fn] - file_exec[fn])
    pct = 100.0 * e / t if t else 0
    print(f"  {name}: {e}/{t} ({pct:.1f}%)")
    if missing:
        # 压缩显示未覆盖行号
        ranges = []
        s = missing[0]
        prev = missing[0]
        for x in missing[1:]:
            if x == prev + 1:
                prev = x
            else:
                ranges.append(f"{s}" if s == prev else f"{s}-{prev}")
                s = prev = x
        ranges.append(f"{s}" if s == prev else f"{s}-{prev}")
        print(f"    未覆盖: {', '.join(str(r) for r in ranges[:12])}{'...' if len(ranges)>12 else ''}")
if total:
    print(f"\n  合计: {exe}/{total} ({100.0*exe/total:.1f}%)")
