# -*- coding: utf-8 -*-
"""对比指定函数在 pyc 与当前 py 中的反汇编"""
import marshal, types, os, sys, dis, datetime

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
os.chdir(ROOT)

def load_pyc_code(path):
    with open(path, 'rb') as f:
        return marshal.loads(f.read()[16:])

def find_func(co, name, path=""):
    if isinstance(co, types.CodeType):
        if co.co_name == name and path:
            return co, path
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                r = find_func(c, name, path + "." + c.co_name if path else c.co_name)
                if r:
                    return r
    return None

def pyc_func(pyc_path, name):
    code = load_pyc_code(pyc_path)
    # 顶层找
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            r = find_func(c, name, c.co_name)
            if r:
                return r[0]
    return None

def py_func(py_path, name):
    with open(py_path, encoding='utf-8', errors='replace') as f:
        src = f.read()
    code = compile(src, py_path, 'exec')
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            r = find_func(c, name, c.co_name)
            if r:
                return r[0]
    return None

if __name__ == '__main__':
    mod = sys.argv[1]
    name = sys.argv[2]
    pyc_path = os.path.join('game', mod + '.py')
    # 找 pyc
    import glob
    cands = glob.glob(os.path.join('game', '**', f'{mod}.cpython-311.pyc'), recursive=True)
    pyc_path = None
    for c in cands:
        if os.path.getmtime(c) < datetime.datetime(2026, 8, 9, 11, 8, 0).timestamp():
            pyc_path = c
            break
    if not pyc_path:
        print("no pyc"); sys.exit(1)
    parts = pyc_path.replace('\\', '/').split('/')
    i = parts.index('__pycache__')
    py_src = os.path.join(*parts[:i], parts[i + 1].replace('.cpython-311.pyc', '.py'))
    pf = pyc_func(pyc_path, name)
    cf = py_func(py_src, name)
    print(f"### {mod}.py :: {name}  (pyc vs py)")
    print("=" * 90)
    if pf is None:
        print("!! pyc 无此函数")
    if cf is None:
        print("!! py 无此函数")
    if pf and cf:
        # 行号偏移校正：分别从 co_firstlineno 开始
        d1 = list(dis.get_instructions(pf))
        d2 = list(dis.get_instructions(cf))
        # 简化对比：打印两个版本
        print(f"--- pyc 版 (L{pf.co_firstlineno}, {len(d1)} 指令) ---")
        for ins in d1:
            print(f"  {ins.positions.lineno or '?':>5} {ins.opname:<28} {ins.argrepr}")
        print()
        print(f"--- py 版 (L{cf.co_firstlineno}, {len(d2)} 指令) ---")
        for ins in d2:
            print(f"  {ins.positions.lineno or '?':>5} {ins.opname:<28} {ins.argrepr}")
