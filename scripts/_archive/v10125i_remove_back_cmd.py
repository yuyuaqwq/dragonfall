# -*- coding: utf-8 -*-
"""
⚠️ 一次性迁移已内化，勿重跑：
- world.py: 删 move_back 函数(992-1070 行, 含装饰器); 交付路径空行条件化
- combat.py: 战斗胜利升级/任务横幅空行条件化
- _registry.py: 删 move_back 条目（必须用 str.replace 防反斜杠转义）
"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import io

def read(p):
    with io.open(p, 'r', encoding='utf-8') as f:
        return f.readlines()

def write(p, lines):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.writelines(lines)

base = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

# ========== 1. world.py 删 move_back (992-1070, 1-indexed) ==========
p = base + r"\commands\world.py"
lines = read(p)
# 验证边界
assert '返回' in lines[991], f"992行异常: {lines[991]!r}"
assert lines[989].strip().startswith('return'), f"990行异常: {lines[989]!r}"
assert '祭坛|方碑' in lines[1071], f"1072行异常: {lines[1071]!r}"
del lines[991:1070]  # 0-indexed: 992-1070 行 = idx 991..1069
write(p, lines)
print(f"world.py: 已删 move_back ({len(lines)} 行剩余)")

# ========== 2. world.py 交付路径空行条件化 ==========
lines = read(p)
src = '            if lv_logs:\n                lines.append("")\n                lines += lv_logs\n'
dst = '            if lv_logs:\n                if lines:\n                    lines.append("")\n                lines += lv_logs\n'
assert src in "".join(lines), "world.py 交付路径空行锚点未找到"
write(p, "".join(lines).replace(src, dst))
print("world.py: 交付路径升级空行条件化 ✓")

# ========== 3. combat.py 两处空行条件化 ==========
p2 = base + r"\commands\combat.py"
txt = io.open(p2, 'r', encoding='utf-8').read()
s1 = '        if lv_logs:\n            lines += [""] + lv_logs\n'
d1 = '        if lv_logs:\n            if lines:\n                lines.append("")\n            lines += lv_logs\n'
assert s1 in txt, "combat.py lv_logs 锚点未找到"
txt = txt.replace(s1, d1)
s2 = '        if quest_lines:\n            lines += [""] + quest_lines\n'
d2 = '        if quest_lines:\n            if lines:\n                lines.append("")\n            lines += quest_lines\n'
assert s2 in txt, "combat.py quest_lines 锚点未找到"
txt = txt.replace(s2, d2)
io.open(p2, 'w', encoding='utf-8', newline='').write(txt)
print("combat.py: 战斗胜利升级/任务横幅空行条件化 ✓")

# ========== 4. _registry.py 删 move_back ==========
p3 = base + r"\commands\_registry.py"
txt3 = io.open(p3, 'r', encoding='utf-8').read()
s3 = '    "move_back": r\'^(?:\\[At:\\d+\\]\\s*)?返回(?:\\s*|$)\',\n'
assert s3 in txt3, "_registry.py move_back 条目未找到"
txt3 = txt3.replace(s3, '')
io.open(p3, 'w', encoding='utf-8', newline='').write(txt3)
print("_registry.py: move_back 条目已删 ✓")
print("全部完成")
