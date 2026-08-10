# -*- coding: utf-8 -*-
"""字节码级对比：回滚前 pyc 函数 vs 当前 py 编译函数 —— 抓函数内部逻辑差异"""
import marshal, types, os, ast, glob, datetime, dis

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
os.chdir(ROOT)
CUTOFF = datetime.datetime(2026, 8, 9, 11, 8, 0).timestamp()

def load_pyc_code(path):
    with open(path, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])

def collect_funcs(co, out, prefix=""):
    """收集 {限定名: code}（类方法带类名前缀）"""
    if isinstance(co, types.CodeType):
        name = co.co_name
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                if c.co_name.startswith('<') or c.co_name in ('<lambda>',):
                    continue
                # 类 body 与函数 body 都递归；类名做前缀
                sub = f"{prefix}.{c.co_name}" if prefix and not c.co_name.startswith('<') else (c.co_name if not prefix else f"{prefix}.{c.co_name}")
                # 简化：只保留两层前缀（模块.类.方法 或 模块.函数）
                out[c.co_name] = c  # 按短名记录
                collect_funcs(c, out, c.co_name if not c.co_name.startswith('<') else prefix)

def sig(code):
    """字节码签名：指令序列 + 名称引用（忽略字符串常量——排版替换会变）"""
    return (code.co_code, tuple(code.co_names), code.co_argcount,
            code.co_nlocals, code.co_stacksize, code.co_flags & ~0x20)

# 收集权威 pyc
pycs = [p for p in glob.glob(os.path.join('game', '**', '__pycache__', '*.cpython-311.pyc'), recursive=True)
        if os.path.getmtime(p) < CUTOFF]

diffs = []
for pyc in sorted(pycs):
    parts = pyc.replace('\\', '/').split('/')
    i = parts.index('__pycache__')
    py_path = os.path.join(*parts[:i], parts[i + 1].replace('.cpython-311.pyc', '.py'))
    if not os.path.exists(py_path):
        continue
    try:
        pyc_code = load_pyc_code(pyc)
        pyc_funcs = {}
        collect_funcs(pyc_code, pyc_funcs)
        with open(py_path, encoding='utf-8', errors='replace') as f:
            src = f.read()
        py_code = compile(src, py_path, 'exec')
        py_funcs = {}
        collect_funcs(py_code, py_funcs)
    except Exception as e:
        print(f"[ERR] {pyc}: {e}")
        continue
    for name, pc in pyc_funcs.items():
        if name.startswith('__') or name.startswith('<'):
            continue
        if name not in py_funcs:
            # 已由函数对比覆盖，跳过
            continue
        ps, cs = sig(pc), sig(py_funcs[name])
        if ps != cs:
            # 只报告指令序列或名称不同的（逻辑差异）
            if ps[0] != cs[0] or ps[1] != cs[1]:
                # 避免重复（一个文件里同名函数多个）
                diffs.append((py_path, name, pc.co_firstlineno, py_funcs[name].co_firstlineno,
                              len(pc.co_code), len(py_funcs[name].co_code)))

seen = set()
print(f"共发现 {len(diffs)} 处函数字节码差异：")
print("=" * 100)
for py_path, name, l1, l2, n1, n2 in diffs:
    key = (py_path, name)
    if key in seen:
        continue
    seen.add(key)
    print(f"🔴 {os.path.relpath(py_path, ROOT)} :: {name}  (pyc L{l1} vs py L{l2}, 字节 {n1} vs {n2})")
print("=" * 100)
print(f"共 {len(seen)} 个函数有字节码差异")
