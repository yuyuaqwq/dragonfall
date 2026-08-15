# -*- coding: utf-8 -*-
"""⚠️ 一次性迁移已内化，勿重跑：全库无差别全角↔半角替换会破坏合法文案。
v95.3d 排版规范（tokenize 精确版 v2）：
- 普通字符串：全角圆括号（）→ 半角 ()；"+数字/{x" → "＋数字"；"-数字" → "－数字"
- f-string：只处理 {expr} 之外的常量文本区；表达式区一律不动
- 跨行字符串：跳过（量少，人工处理）
"""
import io, os, re, tokenize, sys

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

print("🗑 本脚本已归档（scripts/_archive/）：全库无差别全角↔半角替换会破坏合法文案，禁止重跑。", file=sys.stderr)
sys.exit(1)

def fix_text(s: str):
    nb = s.count("（") + s.count("）")
    s = s.replace("（", "(").replace("）", ")")
    s2, np_ = re.subn(r'[ \t]*\+[ \t]*(?=[\d{])', '＋', s)
    s2, nm = re.subn(r'[ \t]*\-[ \t]*(?=[\d{])', '－', s2)
    return s2, nb, np_, nm

def split_fstring(body: str):
    """把 f-string 内容切成 [常量段, (expr, 原文本), 常量段...]。
    返回 segments: list of (kind, text) kind in ('lit','expr')"""
    segs = []
    i = 0
    n = len(body)
    while i < n:
        c = body[i]
        if c == "{":
            # 表达式：跳过 { }（含嵌套）
            depth = 1
            j = i + 1
            while j < n and depth:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            segs.append(("expr", body[i:j]))
            i = j
        else:
            j = i
            while j < n and body[j] != "{":
                j += 1
            segs.append(("lit", body[i:j]))
            i = j
    return segs

def process_body(body: str, is_f: bool) -> str:
    """处理字符串体（已去前缀引号）：普通字符串整体处理；f-string 只处理常量段。"""
    if not is_f:
        return fix_text(body)[0]
    out = []
    for kind, seg in split_fstring(body):
        if kind == "lit":
            out.append(fix_text(seg)[0])
        else:
            out.append(seg)  # 表达式不动
    return "".join(out)

tot = [0, 0, 0]
for dirpath, _d, files in os.walk(ROOT):
    for fn in sorted(files):
        if not fn.endswith(".py"):
            continue
        p = os.path.join(dirpath, fn)
        with open(p, encoding="utf-8") as f:
            src = f.read()
        try:
            toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
        except Exception as e:
            print("SKIP", p, e)
            continue
        edits = []
        for tok in toks:
            if tok.type != tokenize.STRING:
                continue
            raw = tok.string
            # 前缀
            idx = 0
            while idx < len(raw) and raw[idx] in "fFrRbBuU":
                idx += 1
            if idx >= len(raw):
                continue
            quote = raw[idx]
            if quote not in "\"'":
                continue
            body = raw[idx:]  # 含引号
            is_f = idx > 0 and raw[0] in "fF"
            if "\n" in body:
                continue
            # 去掉外层引号
            inner = body[1:-1]
            if not inner:
                continue
            new_inner = process_body(inner, is_f)
            if new_inner != inner:
                start = tok.start[1] + idx + 1
                edits.append((tok.start[0] - 1, start, start + len(inner), new_inner))
        if not edits:
            continue
        lines = src.split("\n")
        for ln, sc, ec, new in sorted(edits, reverse=True):
            lines[ln] = lines[ln][:sc] + new + lines[ln][ec:]
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  {os.path.relpath(p, ROOT)}: edits {len(edits)}")

print(f"完成")
