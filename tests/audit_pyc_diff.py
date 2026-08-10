# -*- coding: utf-8 -*-
"""系统性对比：回滚前 311 pyc vs 当前 .py —— 找出所有丢失的函数/类/字符串"""
import marshal, types, sys, os, ast, glob, datetime

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
os.chdir(ROOT)
# 2026-08-09 11:08:00 (CST=UTC+8) 回滚提交时刻
CUTOFF = datetime.datetime(2026, 8, 9, 11, 8, 0).timestamp()

def load_pyc_code(path):
    with open(path, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])  # py311 header

def walk(co, funcs, strings, depth=0):
    """递归收集函数名 + 字符串常量"""
    if isinstance(co, types.CodeType):
        if depth <= 30:
            for c in co.co_consts:
                if isinstance(c, types.CodeType):
                    funcs.append(c.co_name)
                    walk(c, funcs, strings, depth + 1)
                elif isinstance(c, str):
                    strings.add(c)

def pyc_analysis(pyc_path):
    code = load_pyc_code(pyc_path)
    funcs, strings = [], set()
    walk(code, funcs, strings)
    # 模块级字符串：顶层 co_consts 里的 str（数据定义用）
    top_strings = {c for c in code.co_consts if isinstance(c, str)}
    return funcs, strings, top_strings

def py_analysis(py_path):
    with open(py_path, encoding='utf-8', errors='replace') as f:
        src = f.read()
    tree = ast.parse(src)
    funcs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            funcs.add(node.name)
    strings = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    # 模块级（顶层）字符串：数据定义用
    top_strings = set()
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            top_strings.add(node.value.value)
    return funcs, strings, top_strings

def mtime_str(path):
    import datetime
    t = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return t.strftime('%m-%d %H:%M:%S')

# 收集 11:08 之前的 311 pyc
pycs = []
for p in glob.glob(os.path.join('game', '**', '__pycache__', '*.cpython-311.pyc'), recursive=True):
    mt = os.path.getmtime(p)
    if mt < CUTOFF:
        pycs.append(p)

print(f"权威 pyc 数: {len(pycs)}")
print("=" * 100)

all_missing = []
for pyc in sorted(pycs):
    # 对应 .py 路径
    parts = pyc.replace('\\', '/').split('/')
    # .../game/xxx/__pycache__/mod.cpython-311.pyc → .../game/xxx/mod.py
    i = parts.index('__pycache__')
    py_path = os.path.join(*parts[:i], parts[i + 1].replace('.cpython-311.pyc', '.py'))
    py_path = '/' + py_path if not py_path.startswith('/') else py_path
    py_path = py_path.replace('C:/', 'C:\\') if os.name == 'nt' else py_path
    py_path = os.path.join(ROOT, *parts[:i], parts[i + 1].replace('.cpython-311.pyc', '.py'))
    if not os.path.exists(py_path):
        print(f"[NO .py] {pyc} -> {py_path}")
        continue
    try:
        pyc_funcs, pyc_strings, pyc_top = pyc_analysis(pyc)
        py_funcs, py_strings, py_top = py_analysis(py_path)
    except Exception as e:
        print(f"[ERR] {pyc}: {e}")
        continue
    missing = sorted(set(pyc_funcs) - py_funcs)
    # 过滤 dunder 和编译器生成名
    missing_real = [f for f in missing if not f.startswith('__') and not f.startswith('<')]
    if missing_real:
        all_missing.append((pyc, missing_real))
        print(f"🔴 {os.path.relpath(py_path, ROOT)}  缺失函数: {missing_real}")
        print(f"    pyc mtime: {mtime_str(pyc)}")
    # 模块级数据字符串差异（pyc 模块级常量 vs py 全量字面量——dict key 也算）
    top_missing = sorted(s for s in pyc_top if s not in py_strings and len(s) >= 2)
    if top_missing:
        print(f"🟠 {os.path.relpath(py_path, ROOT)}  模块级独有字符串({len(top_missing)}):")
        for s in top_missing[:20]:
            print(f"      · {s[:100]!r}")
    # 函数内字符串差异（含 f-string 噪音，供人工判断）
    missing_strs = sorted(s for s in pyc_strings if s not in py_strings and len(s) >= 8 and not s.isdigit() and not s.isascii() and s not in pyc_top)
    if missing_strs:
        print(f"🟡 {os.path.relpath(py_path, ROOT)}  独有文案字符串({len(missing_strs)}): {missing_strs[:12]}")
    # 反向：py 有 pyc 没有（恢复时可能多加了）
    extra = sorted(py_funcs - set(pyc_funcs))
    if extra:
        print(f"🔵 {os.path.relpath(py_path, ROOT)}  当前多出函数: {extra[:10]}")

print("=" * 100)
print(f"共 {len(all_missing)} 个文件有缺失函数")
