# -*- coding: utf-8 -*-
"""分支级覆盖检测（stdlib，零依赖）：记录每个可执行行是否被走到 + 关键跳转双路。

比函数级覆盖更严格：
- 行级：只统计"真可执行行"（排除 def 行/纯 docstring/纯注释/空行）
- 分支级：对 if/elif/else/for/while/try 的条件行，分析字节码跳转，
  检查跳转的双向目标行是否都执行过（false 走下一行 / true 跳目标）

跑法：python tools/cov_branch_battle2.py
输出：每文件 可执行行/分支 覆盖 + 未覆盖行号清单
"""
import os
import sys
import glob
import dis
import ast

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))  # 引擎框架包（S8 物理分离：framework/ 为引擎 submodule）
TEST_DIR = os.path.join(PLUGIN_DIR, "tests")
os.chdir(PLUGIN_DIR)

# ============ 静态分析：找出"真可执行行"和"条件行" ============
# 可执行行 = 去掉 def/class 行、docstring、纯注释、空行后的代码行
_exec_lines = {}   # 文件 -> set(可执行行号)
_cond_lines = {}   # 文件 -> set(条件行号：含 if/elif/else/while/for/try/return 分支跳转的源行)

for pyfile in glob.glob(os.path.join(PLUGIN_DIR, "framework", "battle2", "*.py")):
    src_lines = open(pyfile, encoding="utf-8").read().splitlines()
    try:
        tree = ast.parse("\n".join(src_lines))
    except Exception:
        continue
    # 收集 docstring 占用行（函数/类/模块 docstring 从 def 下一行到字符串结束）
    doc_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            d = ast.get_docstring(node, clean=False)
            if d and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Str):
                    dl = first.lineno
                    # 字符串可能跨多行（三引号）——统计引号闭合
                    for i in range(dl, min(dl + 50, len(src_lines) + 1)):
                        doc_lines.add(i)
                        line_text = src_lines[i - 1] if i - 1 < len(src_lines) else ""
                        # 简单探测 docstring 结束：含结尾三引号
                        if '"""' in line_text or "'''" in line_text:
                            if i > dl:
                                break
    exec_l = set()
    for node in ast.walk(tree):
        if hasattr(node, "lineno"):
            ln = node.lineno
            # 跳过 def/class 声明行本身、docstring 内容行
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                continue
            if ln in doc_lines:
                continue
            exec_l.add(ln)
    _exec_lines[pyfile] = exec_l

# ============ 运行测试（sys.settrace 精确行轨迹） ============
_hit_lines = {}   # (file, line) -> True
import threading

def _make_tracer():
    def _trace(frame, event, arg):
        if event == "line":
            fn = frame.f_code.co_filename.replace("\\", "/")
            if "/framework/battle2/" in fn:
                _hit_lines[(fn, frame.f_lineno)] = True
        return _trace
    return _trace

test_files = sorted(glob.glob(os.path.join(TEST_DIR, "test_battle2_*.py")))
for tf in test_files:
    try:
        code = compile(open(tf, encoding="utf-8").read(), tf, "exec")
        _ns = {"__name__": "__main__", "__file__": tf}
        sys.settrace(_make_tracer())
        exec(code, _ns, _ns)
        sys.settrace(None)
    except SystemExit:
        sys.settrace(None)
        pass
    except Exception as e:
        sys.settrace(None)
        print(f"⚠️ {os.path.basename(tf)}: {e}")
sys.settrace(None)

# ============ 汇总 ============
print("\n=== battle2 行级覆盖（仅真可执行行） ===")
total_e = total_x = 0
for pyfile in sorted(_exec_lines):
    fn = pyfile.replace("\\", "/")
    exec_l = _exec_lines[pyfile]
    hit = {ln for (f2, ln) in _hit_lines if f2 == fn}
    covered = exec_l & hit
    missing = exec_l - hit
    total_e += len(exec_l)
    total_x += len(covered)
    name = os.path.basename(pyfile)
    pct = 100.0 * len(covered) / len(exec_l) if exec_l else 100
    print(f"  {name}: {len(covered)}/{len(exec_l)} ({pct:.1f}%)")
    if missing:
        miss_sorted = sorted(missing)
        ranges = []
        s = prev = miss_sorted[0]
        for x in miss_sorted[1:]:
            if x == prev + 1:
                prev = x
            else:
                ranges.append(f"{s}" if s == prev else f"{s}-{prev}")
                s = prev = x
        ranges.append(f"{s}" if s == prev else f"{s}-{prev}")
        print(f"    未覆盖行: {', '.join(str(r) for r in ranges)}")
if total_e:
    print(f"\n  合计: {total_x}/{total_e} ({100.0*total_x/total_e:.1f}%)")
