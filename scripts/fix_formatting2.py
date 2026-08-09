# -*- coding: utf-8 -*-
"""v95.3b 精确排版：先回滚误伤的全角加减号，再用 AST 只处理字符串字面量。
规则：字符串内的 "+数字/{x" / "-数字/{x" → 全角 ＋/－（去空格）；全角圆括号 → 半角。
"""
import ast, os, re

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

def collect_strings(src):
    """返回 [(start, end, text)] 字符串字面量区间（含 f-string 的常量部分）。"""
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((node.lineno, node.col_offset, node.end_lineno, node.end_col_offset))
        elif isinstance(node, ast.JoinedStr):
            # f-string：只处理常量段
            for val in node.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    out.append((val.lineno, val.col_offset, val.end_lineno, val.end_col_offset))
    return out

def fix_text(s: str) -> str:
    """字符串内容排版修复。"""
    n_b = s.count("（") + s.count("）")
    s = s.replace("（", "(").replace("）", ")")
    # 加减号：全角且去空格（只匹配紧贴数字或 { 的）
    s2, n_p = re.subn(r'[ \t]*\+[ \t]*(?=[\d{])', '＋', s)
    s2, n_m = re.subn(r'[ \t]*\-[ \t]*(?=[\d{])', '－', s2)
    return s2, n_b, n_p, n_m

total = [0, 0, 0]
bad = []
for dirpath, _d, files in os.walk(ROOT):
    for fn in sorted(files):
        if not fn.endswith(".py"):
            continue
        p = os.path.join(dirpath, fn)
        with open(p, encoding="utf-8") as f:
            src = f.read()
        try:
            spans = collect_strings(src)
        except SyntaxError as e:
            bad.append((p, str(e)))
            continue
        lines = src.split("\n")
        # 从后往前替换避免 offset 失效
        edits = []
        for (sl, sc, el, ec) in spans:
            if sl == el:
                seg = lines[sl-1][sc:ec]
                new, nb, np_, nm = fix_text(seg)
                if new != seg:
                    edits.append((sl-1, sc, ec, new))
                    total[0] += nb; total[1] += np_; total[2] += nm
            else:
                # 跨行字符串：整段取出（简单处理，先跳过跨行，量少）
                pass
        for ln, sc, ec, new in sorted(edits, reverse=True):
            line = lines[ln]
            lines[ln] = line[:sc] + new + line[ec:]
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

print(f"括号 {total[0]}，加号 {total[1]}，减号 {total[2]}，语法失败 {len(bad)}")
for p, e in bad[:5]:
    print("  FAIL", p, e)
