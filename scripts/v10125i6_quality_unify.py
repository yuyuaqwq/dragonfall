# -*- coding: utf-8 -*-
"""v101.25i6 品质体系收口：垂钓/符文统一走 QUALITY（鱼鱼：加品质要全服生效）
A. 垂钓: FISH_QUALITY_ORDER = QUALITY_ORDER 别名; 删 FISH_QUALITY_CN(改用 QUALITY.name, 优良→优秀)
B. 符文: quality 字段 稀有/史诗/传说 → blue/purple/orange; RUNE_DROP key 同步; 显示/名字走 QUALITY
"""
import io

def rd(p):
    return io.open(p, 'r', encoding='utf-8').read()

def wr(p, t):
    io.open(p, 'w', encoding='utf-8', newline='').write(t)

base = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

# ===== A1. fishing.py: 删两份独立定义 =====
p = base + r"\data\fishing.py"
t = rd(p)
old_order = '# 品质档位顺序（与 FISH_QUALITY_WEIGHTS 行对应）\nFISH_QUALITY_ORDER = ["white", "green", "blue", "purple", "orange"]\n\n'
assert old_order in t, "FISH_QUALITY_ORDER 定义未找到"
t = t.replace(old_order, '# 品质档位顺序：v101.25i6 统一引用 QUALITY_ORDER（见 data/__init__.py 别名）\n')
old_cn = '# 品质中文名（白档不显示 ✦ 标记）\nFISH_QUALITY_CN = {\n    "white": "普通", "green": "优良", "blue": "稀有",\n    "purple": "史诗", "orange": "传说",\n}\n\n'
assert old_cn in t, "FISH_QUALITY_CN 定义未找到"
t = t.replace(old_cn, '# 品质中文名：v101.25i6 统一走 QUALITY[q]["name"]（白档不显示 ✦ 标记）\n')
wr(p, t)
print("fishing.py: FISH_QUALITY_ORDER/CN 定义已移除 ✓")

# ===== A2. data/__init__.py: 别名 + 删导出 =====
p = base + r"\data\__init__.py"
t = rd(p)
old_imp = 'from .fishing import (  # noqa: F401\n    FISHING_SPOTS, FISH_POOL, FISH_QUALITY_WEIGHTS,\n    FISH_QUALITY_ORDER, FISH_QUALITY_CN, FISH_EXP, FISH_COLLECT,\n)\n'
assert old_imp in t, "__init__ fishing import 未找到"
t = t.replace(old_imp, 'from .fishing import (  # noqa: F401\n    FISHING_SPOTS, FISH_POOL, FISH_QUALITY_WEIGHTS,\n    FISH_QUALITY_ORDER, FISH_EXP, FISH_COLLECT,\n)\n')
# 别名行（紧跟 equipment import 后，找 QUALITY_ORDER 导入块）
alias = '# v101.25i6 品质统一：垂钓档位 = 装备 QUALITY_ORDER（加品质全服生效）\nFISH_QUALITY_ORDER = QUALITY_ORDER  # noqa: F401\n'
if alias not in t:
    anchor = 'from .equipment import (  # noqa: F401\n    EQUIP_SLOTS, QUALITY, QUALITY_ORDER, WEAPON_TYPES, WEAPON_NAME_SUFFIX,'
    assert anchor in t, "equipment import 锚点未找到"
    # 在 equipment import 块结束后插入——找该块结尾（下一个 from . 开头）
    idx = t.index(anchor)
    nxt = t.index('\nfrom .', idx + len(anchor))
    t = t[:nxt] + '\n' + alias.rstrip('\n') + t[nxt:]
wr(p, t)
print("data/__init__.py: 别名+删导出 ✓")

# ===== B1. runes.py: quality 字段 + RUNE_DROP key =====
p = base + r"\data\runes.py"
t = rd(p)
for cn, key in [("史诗", "purple"), ("稀有", "blue"), ("传说", "orange")]:
    t = t.replace(f'"quality": "{cn}"', f'"quality": "{key}"')
    t = t.replace(f'"{cn}": 0.', f'"{key}": 0.')
assert '"quality": "史诗"' not in t and '"稀有": 0.' not in t, "runes.py 替换不彻底"
wr(p, t)
print("runes.py: quality 字段+RUNE_DROP key 已转 key ✓")

# ===== B2. core/runes.py: 名字拼 QUALITY name =====
p = base + r"\core\runes.py"
t = rd(p)
t = t.replace('from ..data import RUNES, RUNE_CONFLICTS, RUNE_LEVEL_ROMAN\n',
              'from ..data import RUNES, RUNE_CONFLICTS, RUNE_LEVEL_ROMAN, QUALITY\n')
old_name = '"name": f"{r[\'quality\']}符文·{r.get(\'name\', name)} {roman}",'
new_name = '"name": f"{QUALITY[r[\'quality\']][\'name\']}符文·{r.get(\'name\', name)} {roman}",'
assert old_name in t, "rune_item name 未找到"
t = t.replace(old_name, new_name)
wr(p, t)
print("core/runes.py: 名字走 QUALITY.name ✓")

# ===== B3. combat.py: 掉落判定 key =====
p = base + r"\commands\combat.py"
t = rd(p)
pairs = [
    ('C.RUNE_DROP["稀有"]', 'C.RUNE_DROP["blue"]'),
    ('rune_quality = "稀有"', 'rune_quality = "blue"'),
    ('if rune_quality == "稀有":', 'if rune_quality == "blue":'),
    ('elif rune_quality == "史诗":', 'elif rune_quality == "purple":'),
]
for a, b in pairs:
    assert a in t, f"combat.py 未找到 {a}"
    t = t.replace(a, b)
wr(p, t)
print("combat.py: 符文掉落判定 key ✓")

# ===== B4. economy.py: 垂钓品质显示 + 百科符文显示 =====
p = base + r"\commands\economy.py"
t = rd(p)
pairs = [
    ('f"✦{C.FISH_QUALITY_CN.get(fq, fq)}"', 'f"✦{C.QUALITY.get(fq, {}).get(\'name\', fq)}"'),
    ('f"💎 【{st[\'quality\']}符文·{stone_name}】"', 'f"💎 【{C.QUALITY[st[\'quality\']][\'name\']}符文·{stone_name}】"'),
    ('f"品质：{st[\'quality\']}"', 'f"品质：{C.QUALITY[st[\'quality\']][\'name\']}"'),
    ('f"使用：『附魔 <装备名> {st[\'quality\']}符文·{stone_name}』"', 'f"使用：『附魔 <装备名> {C.QUALITY[st[\'quality\']][\'name\']}符文·{stone_name}』"'),
    ('f"  💎 {s[\'quality\']}符文·{nm}({s[\'desc\']})"', 'f"  💎 {C.QUALITY[s[\'quality\']][\'name\']}符文·{nm}({s[\'desc\']})"'),
]
for a, b in pairs:
    assert a in t, f"economy.py 未找到 {a}"
    t = t.replace(a, b)
wr(p, t)
print("economy.py: 垂钓标记+百科符文显示走 QUALITY ✓")
print("全部完成")
