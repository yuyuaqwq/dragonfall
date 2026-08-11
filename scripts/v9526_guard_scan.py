# -*- coding: utf-8 -*-
"""v95.26 守卫样板扫描：统计所有"守卫型 if 检查"（if not X: yield...return），
按检查对象分组，找出同类重复（候选提装饰器/函数）vs 业务差异。"""
import io, os, re, glob
from collections import defaultdict, Counter

BASE = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\commands"
files = sorted(glob.glob(os.path.join(BASE, "*.py")))

# 收集每个 handler 内的守卫：if not <var>: <yield 消息> return
guards = defaultdict(list)  # var -> [(文件, 行, handler, 消息, 是否return)]
total = 0
for p in files:
    lines = io.open(p, encoding="utf-8").read().split("\n")
    cur_handler = None
    for i, l in enumerate(lines):
        m = re.match(r"^\s+async def (\w+)\(", l)
        if m:
            cur_handler = m.group(1)
        gm = re.match(r"^\s+if not (\w+):\s*$", l)
        if not gm:
            continue
        var = gm.group(1)
        # 看后面的 yield 内容（跳过空行/注释）
        msg = ""
        is_return = False
        for j in range(i + 1, min(i + 6, len(lines))):
            t = lines[j].strip()
            if not t or t.startswith("#"):
                continue
            ym = re.match(r"yield event\.plain_result\((.*)\)", t)
            if ym:
                msg = ym.group(1)[:90]
                # 检查后面有没有 return
                for k in range(j + 1, min(j + 4, len(lines))):
                    if lines[k].strip() == "return":
                        is_return = True
                        break
                    if lines[k].strip() and not lines[k].strip().startswith("#"):
                        break
            break
        guards[var].append((os.path.basename(p), i + 1, cur_handler, msg, is_return))
        total += 1

print(f"守卫总数: {total}\n")
for var, items in sorted(guards.items(), key=lambda kv: -len(kv[1])):
    msgs = Counter(m for _, _, _, m, _ in items)
    same = len(msgs) == 1 and items[0][3]
    tag = "🔴 同文案重复(候选提函数)" if (len(items) >= 3 and same) else ("🟡 多文案(看语义)" if len(items) >= 3 else "🟢 少量")
    print(f"{tag} if not {var}: ×{len(items)}")
    if len(items) <= 4 or not same:
        for f, ln, h, m, r in items[:6]:
            print(f"    {f}:{ln} [{h}] {m[:60]}{' →return' if r else ''}")
        if len(items) > 6:
            print(f"    ... 共 {len(items)} 处")
    else:
        print(f"    统一文案: {items[0][3][:60]}")
    print()
