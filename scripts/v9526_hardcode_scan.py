# -*- coding: utf-8 -*-
"""v95.26 硬编码提示扫描：找玩家可见提示的重复/不一致。
输出：
1. 高频重复字符串（同一完整提示出现 ≥4 次 → 候选常量）
2. 『命令示例』按命令词分组，找同一命令的不同写法（格式不一致）
3. 引导类提示模式（"你还没有"/"输入『"）分布
"""
import io, os, re, glob
from collections import Counter, defaultdict

BASE = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

files = [p for p in glob.glob(os.path.join(BASE, "**", "*.py"), recursive=True)]
strs = []  # (字符串, 文件, 行号)
for p in files:
    lines = io.open(p, encoding="utf-8").read().split("\n")
    for i, l in enumerate(lines, 1):
        # 双引号字符串（含三引号内的行也算，粗扫）
        for m in re.finditer(r'"([^"\n]{6,})"', l):
            s = m.group(1)
            if s.strip() and not s.startswith(("from ", "import ", ":", "#")):
                strs.append((s, os.path.relpath(p, BASE), i))

# ---- 1. 高频重复字符串 ----
cnt = Counter(s for s, _, _ in strs)
print("=" * 60)
print("【1. 高频重复提示（≥4 次，候选常量）】")
for s, c in cnt.most_common(40):
    if c >= 4:
        print(f"  {c:3d}× {s[:80]}")

# ---- 2. 命令示例不一致 ----
print("=" * 60)
print("【2. 『』命令示例按命令词分组（同一命令不同写法）】")
cmd_examples = defaultdict(set)
for s, f, ln in strs:
    for m in re.finditer(r"『([^』]{1,40})』", s):
        ex = m.group(1)
        # 命令词 = 第一个 token（中文）
        head = re.match(r"[\u4e00-\u9fff]+", ex)
        if head:
            cmd_examples[head.group(0)].add(ex)
for cmd, exs in sorted(cmd_examples.items()):
    if len(exs) > 1:
        print(f"\n  【{cmd}】{len(exs)} 种写法:")
        for e in sorted(exs):
            print(f"    『{e}』")

# ---- 3. 引导提示模式 ----
print("=" * 60)
print("【3. 引导类提示（'你还没有X' / 未注册变体）】")
pat = re.compile(r"你还没有[^\"，。！]{0,12}")
guides = Counter()
for s, f, ln in strs:
    for m in pat.finditer(s):
        guides[m.group(0)] += 1
for g, c in guides.most_common(20):
    print(f"  {c:3d}× {g}")

print("=" * 60)
print(f"扫描完成：{len(files)} 文件, {len(strs)} 字符串")
