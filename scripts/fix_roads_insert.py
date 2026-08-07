# -*- coding: utf-8 -*-
"""修复 apply_roads 插入错误（按行号操作，最稳）"""
import os

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(PLUGIN_DIR, "game", "data", "maps.py")
lines = open(path, encoding="utf-8").read().split("\n")

# 1. 找 MAPS 闭合：第一个 ']' 行（前面是 '    },'）
close_idx = None
for i, ln in enumerate(lines):
    if ln.strip() == "]" and i > 100:
        # 前面几行应有 '    },' 表示 MAPS 结束
        prev = lines[i-1]
        if prev.strip() == "}," or prev.strip() == "}":
            close_idx = i
            break
print(f"MAPS 闭合行: {close_idx + 1} -> {repr(lines[close_idx])}")

# 2. 找 road 块开始（'    [' 后跟 '      {' 含 road_）
road_start = None
for i in range(close_idx + 1, len(lines)):
    if lines[i].strip() == "[" and i + 2 < len(lines) and 'road_' in lines[i + 2]:
        road_start = i
        break
print(f"road 块开始行: {road_start + 1}")

# road 块结束 = 下一个 ']'（在 road 块内，缩进 4 空格）
road_end = None
for i in range(road_start + 1, len(lines)):
    if lines[i].strip() == "]":
        road_end = i
        break
print(f"road 块结束行: {road_end + 1}")

# 3. 提取 road 元素（从 road_start+1 到 road_end-1，即 dict 们）
road_elems = lines[road_start + 1:road_end]
# 去掉首尾空白元素
while road_elems and not road_elems[0].strip():
    road_elems.pop(0)
while road_elems and not road_elems[-1].strip():
    road_elems.pop()
# 调整缩进：6空格 → 4空格
fixed = []
for ln in road_elems:
    if ln.startswith("      "):
        ln = "    " + ln[6:]
    fixed.append(ln)
# 最后一个元素结尾无逗号则补逗号（在元素内部处理：'}' 行变成 '},' 除了最后一个）
# road 元素以 '      }' 或 '      },' 结束；这里 fixed 里每个 dict 的最后一行是 '    }'
# 找出每个 dict 结束行，除最后一个外补逗号
last_line_idx = len(fixed) - 1
for i, ln in enumerate(fixed):
    if ln.strip() == "}" and i != last_line_idx:
        # 确认这是 dict 结束（后一行是 '    }' 或 '    {'）
        if i + 1 < len(fixed) and (fixed[i+1].strip().startswith("{") or fixed[i+1].strip() == "}"):
            fixed[i] = "    },"
# 但如果最后元素本身就是 '}'，改成 '},' 不要——直接保持

# 4. 重建
new_lines = lines[:close_idx]  # 到 MAPS 闭合 ] 之前（不含 ]）
new_lines.append("    },")  # 原最后元素补逗号（原 '    },' 已在 close_idx 前？不，close_idx 前一行是 '    },'）
# 检查：lines[close_idx-1] 应该是 '    },'，直接保留它，然后在 ] 前插入 road 元素
new_lines = lines[:close_idx]  # 包含 '    },' 和前面的所有
new_lines += fixed
new_lines += ["]"]
# 跳过原 road 块 + 多余 ]，接 MAP_BY_ID
# 找 MAP_BY_ID 行
mbi = None
for i in range(road_end + 1, len(lines)):
    if lines[i].startswith("MAP_BY_ID"):
        mbi = i
        break
print(f"MAP_BY_ID 行: {mbi + 1}")
new_lines += lines[mbi:]

open(path, "w", encoding="utf-8").write("\n".join(new_lines))
print(f"✅ 完成：road 元素 {len(fixed)} 个已移入 MAPS")
