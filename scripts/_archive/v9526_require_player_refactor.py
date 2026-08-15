# -*- coding: utf-8 -*-
"""
⚠️ 一次性迁移已内化，勿重跑：

对 game/commands/*.py：
1. 删除标准 if 块（112 处标准文案 + player.py shortcut 变体）
2. 在被删块所在 handler 的 @filter.regex 后插入 @require_player()
3. import 行补 require_player
"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import io, os, re, sys

BASE = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
CMDS = os.path.join(BASE, "game", "commands")

FILES = ["combat.py", "economy.py", "gm.py", "instance.py", "misc.py", "player.py", "social.py", "world.py"]

STD_YIELD = 'yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")'
SHORT_YIELD = 'yield event.plain_result("❌ 还没注册角色哦，先发『注册 <名字> <职业>』～")'

total_blocks = 0
total_deco = 0

for fn in FILES:
    path = os.path.join(CMDS, fn)
    lines = io.open(path, encoding="utf-8").read().split("\n")

    # 1) 找标准 if 块（缩进 8 空格）
    to_delete = []      # (行号, 函数定义行号)
    removed_here = 0
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s+)if not player:\s*$", lines[i])
        if m:
            indent = m.group(1)
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip() in (STD_YIELD, SHORT_YIELD) and lines[j].startswith(indent + " "):
                k = j + 1
                while k < len(lines) and lines[k].strip() == "":
                    k += 1
                if k < len(lines) and lines[k].strip() == "return" and lines[k].startswith(indent):
                    # 找到函数定义行（向上找 async def）
                    fn_def = None
                    for t in range(i - 1, -1, -1):
                        if re.match(r"^\s+async def ", lines[t]):
                            fn_def = t
                            break
                        if lines[t].strip().startswith("async def ") and not lines[t].startswith((" ", "\t")):
                            fn_def = t
                            break
                        if t < i - 30:
                            break
                    to_delete.extend([i, j, k])
                    removed_here += 1
                    i = k + 1
                    continue
        i += 1
    if not to_delete:
        print(f"{fn}: 无标准块")
        continue
    total_blocks += removed_here

    # 2) 被删块所属函数名（删除前定位，防行号漂移）
    func_names = set()
    for d in to_delete:
        for t in range(d - 1, -1, -1):
            m = re.match(r"^\s+async def (\w+)\(", lines[t])
            if m:
                func_names.add(m.group(1))
                break
            if t < d - 30:
                break
    # 3) 删除 if 块行（从后往前删）
    for d in sorted(to_delete, reverse=True):
        del lines[d]

    # 4) 插入 @require_player()：按函数名重新定位（删除后行号），向上找 @filter.regex 行
    inserts = []  # (插入位置, 文本)
    for name in func_names:
        t = None
        for idx, l in enumerate(lines):
            if re.match(rf"^\s+async def {name}\(", l):
                t = idx
                break
        if t is None:
            print(f"  !! 找不到函数 {name}")
            continue
        # 向上找 @filter.regex
        deco_line = None
        for u in range(t - 1, -1, -1):
            if lines[u].lstrip().startswith("@filter.regex"):
                deco_line = u
                break
            if re.match(r"^\s+async def ", lines[u]):
                break  # 越过上一个函数
            if u < t - 15:
                break
        if deco_line is None:
            print(f"  !! {fn}::{name} 找不到 @filter.regex")
            continue
        inserts.append((deco_line + 1, "    @require_player()"))

    # 5) import 补 require_player
    new_text = "\n".join(lines)
    if "from ..commands.base import" in new_text:
        new_text = re.sub(
            r"from \.\.commands\.base import ([^\n]+)",
            lambda m: m.group(0) if "require_player" in m.group(1) else f"from ..commands.base import {m.group(1).rstrip()}, require_player",
            new_text,
        )
    elif "from .base import" in new_text:
        new_text = re.sub(
            r"from \.base import ([^\n]+)",
            lambda m: m.group(0) if "require_player" in m.group(1) else f"from .base import {m.group(1).rstrip()}, require_player",
            new_text,
        )

    # 6) 插入装饰器（按位置倒序插入到行列表）
    lines2 = new_text.split("\n")
    for pos, text in sorted(inserts, reverse=True):
        # pos 是按 lines2 行号——但 import 替换不影响行数，装饰器插入互不影响（倒序）
        lines2.insert(pos, text)
    total_deco += len(inserts)

    io.open(path, "w", encoding="utf-8").write("\n".join(lines2))
    print(f"{fn}: 删 {removed_here} 块, 插 {len(inserts)} 装饰器")

print(f"\n总计: 删块 {total_blocks}, 装饰器 {total_deco}")
