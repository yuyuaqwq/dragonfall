# -*- coding: utf-8 -*-
"""⚠️ 一次性迁移已内化，勿重跑：全库无差别全角↔半角替换会破坏合法文案。
v95.3c 排版规范（tokenize 精确版）：
- 字符串字面量内：全角圆括号（）→ 半角 ()
- 字符串字面量内："+数字/{x" → "＋数字/{x"（去空格，全角加号）
- 字符串字面量内："-数字/{x" → "－数字/{x"
只动 STRING token，绝不碰代码。f-string 前缀的字符串按整体处理。
"""
import io, os, re, tokenize, ast, sys

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

print("🗑 本脚本已归档（scripts/_archive/）：全库无差别全角↔半角替换会破坏合法文案，禁止重跑。", file=sys.stderr)
sys.exit(1)

def fix_text(s: str):
    nb = s.count("（") + s.count("）")
    s = s.replace("（", "(").replace("）", ")")
    s2, np_ = re.subn(r'[ \t]*\+[ \t]*(?=[\d{])', '＋', s)
    s2, nm = re.subn(r'[ \t]*\-[ \t]*(?=[\d{])', '－', s2)
    return s2, nb, np_, nm

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
        # 收集 STRING token 的绝对区间
        edits = []
        for tok in toks:
            if tok.type != tokenize.STRING:
                continue
            raw = tok.string
            # 去掉前缀 f/r/b
            body = raw
            while body[:1] in "fFrRbBuU":
                body = body[1:]
            quote = body[0]
            if quote not in "\"'":
                continue
            # 简单单行字符串（多行/转义复杂情况跳过，量少）
            if "\n" in body:
                continue
            # 用 tokenize 的 str 再解码（处理转义）
            try:
                val = ast.literal_eval(body)
            except Exception:
                val = None
            new_body, nb, np_, nm = fix_text(body)
            if new_body != body:
                start = tok.start[1] + (len(raw) - len(body))
                edits.append((tok.start[0] - 1, start, start + len(body), new_body))
                tot[0] += nb; tot[1] += np_; tot[2] += nm
        if not edits:
            continue
        lines = src.split("\n")
        for ln, sc, ec, new in sorted(edits, reverse=True):
            lines[ln] = lines[ln][:sc] + new + lines[ln][ec:]
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  {os.path.relpath(p, ROOT)}: edits {len(edits)}")

print(f"总计：括号 {tot[0]}，加号 {tot[1]}，减号 {tot[2]}")
