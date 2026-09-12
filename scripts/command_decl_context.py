# -*- coding: utf-8 -*-
"""dump 一个命令模块的「迁移上下文」：方法名 / 装饰器链 / 前置注释 / 字面表条目 / docstring。

用法：python scripts/command_decl_context.py social.py [player.py ...]
"""
import ast, importlib.util, os, sys, io

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_DIR = os.path.join(PLUGIN, "game", "commands")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

spec = importlib.util.spec_from_file_location("_reg", os.path.join(CMD_DIR, "_registry.py"))
reg = importlib.util.module_from_spec(spec); spec.loader.exec_module(reg)
literal = dict(reg._LITERAL_REGEX)

# 字面表里的前置注释（按行扫，key -> 上面的注释行）
reg_lines = open(os.path.join(CMD_DIR, "_registry.py"), encoding="utf-8").read().splitlines()
lit_notes = {}
pending = []
for ln in reg_lines:
    s = ln.strip()
    if s.startswith("#"):
        pending.append(s)
    elif s.startswith('"') and ":" in s:
        k = s.split(":", 1)[0].strip().strip('"')
        lit_notes[k] = list(pending); pending = []
    elif s and not s.startswith("#"):
        pending = []

for fn in sys.argv[1:]:
    path = os.path.join(CMD_DIR, fn)
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines()
    tree = ast.parse(src)
    print("=" * 78)
    print("FILE", fn)
    print("=" * 78)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decs = []
        rx = None
        for dec in node.decorator_list:
            seg = ast.get_source_segment(src, dec) or ""
            decs.append(" ".join(seg.split()))
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "regex":
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    rx = dec.args[0].value
        if rx is None:
            print(f"\n--- {node.name} (L{node.lineno})  【已声明或非 @filter.regex】 decs={decs}")
            continue
        lit = literal.get(node.name)
        flag = "✅一致" if lit == rx else ("❌表里没有" if lit is None else "❌不一致")
        print(f"\n### {node.name}  (L{node.lineno})  {flag}")
        print("  decs:", decs)
        print("  literal:", repr(lit))
        # 方法上面的注释块（装饰器之前）
        first_dec_line = min((d.lineno for d in node.decorator_list), default=node.lineno)
        i = first_dec_line - 2
        buf = []
        while i >= 0 and lines[i].strip().startswith("#"):
            buf.insert(0, lines[i].strip()); i -= 1
        if buf:
            print("  code-notes:", buf)
        ds = ast.get_docstring(node)
        if ds:
            print("  docstring:", " ".join(ds.split())[:200])
        note = lit_notes.get(node.name)
        if note:
            print("  table-notes:", note)
