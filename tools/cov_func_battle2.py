# -*- coding: utf-8 -*-
"""函数级覆盖检测：跑全部 battle2 测试，记录哪些顶层函数从未被调用。

比行覆盖更严格——函数没被 enter 过 = 该能力完全没验证。
用 sys.setprofile 记录函数调用（仅统计 battle2 包顶层/嵌套函数）。
"""
import os
import sys
import glob

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DIR = os.path.join(PLUGIN_DIR, "tests")
os.chdir(PLUGIN_DIR)

_called = set()      # 被调用过的函数名（qualname）
_all_defs = {}       # qualname -> 文件（预扫 battle2 包所有函数）

# 预扫 battle2 所有 def
import ast
for fn in glob.glob(os.path.join(PLUGIN_DIR, "framework", "battle2", "*.py")):
    try:
        tree = ast.parse(open(fn, encoding="utf-8").read())
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _all_defs[node.name] = os.path.basename(fn)

def _prof(frame, event, arg):
    if event == "call":
        try:
            name = frame.f_code.co_name
            if name in _all_defs:
                _called.add(name)
        except Exception:
            pass
    return None

sys.setprofile(_prof)

test_files = sorted(glob.glob(os.path.join(TEST_DIR, "test_battle2_*.py")))
for tf in test_files:
    try:
        code = compile(open(tf, encoding="utf-8").read(), tf, "exec")
        _ns = {"__name__": "__main__", "__file__": tf}
        exec(code, _ns, _ns)
    except SystemExit:
        pass
    except Exception as e:
        print(f"⚠️ {os.path.basename(tf)}: {e}")

sys.setprofile(None)

print("\n=== 函数级覆盖 ===")
uncalled = []
for name, fn in sorted(_all_defs.items(), key=lambda x: x[1]):
    hit = name in _called
    if not hit:
        uncalled.append(f"{fn}:{name}")
    print(f"  {'✅' if hit else '❌'} {fn} :: {name}")
print(f"\n未调用函数 {len(uncalled)} 个")
for u in uncalled:
    print(f"  - {u}")
