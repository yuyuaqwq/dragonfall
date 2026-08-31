# -*- coding: utf-8 -*-
"""T4：『背包』页数/翻页提示从标题（顶部）移到列表底部。

玩家意见 #5（zerc）：背包页数建议放底部。done 标注意为已实现，但核实
economy.py:3199 页数仍在标题行 → 未实现，本脚本实施。

改动（仅 game/commands/economy.py，_bag_view 内 2 处，行级替换防 CRLF 噪音）：
  1) 标题行去掉 "(第 X/N 页 · 共 Y 件)" 尾巴 → 纯标题
  2) 底部分隔线后插入 "📄 第 X/N 页 · 共 Y 件｜『…』下一页" 行
     （翻页指令：全背包=『背包 N+1』；筛选视图=『背包筛选 类型 N+1』，
       与炼金/烹饪/锻造/技能列表的底部页数风格统一；末页无翻页提示）

运行：python.exe workspace/feedback_fix/_apply_T4.py
"""
import io

path = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\commands\economy.py"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    src = f.read()

# 1) 标题行：去掉页数/共 N 件（移到底部）
old1 = '        lines = [f"{title}(第 {page}/{pages} 页 · 共 {len(items)} 件)", "━━━━━━━━━━━━"]'
new1 = ('        lines = [title, "━━━━━━━━━━━━"]'
        '  # 玩家意见 #5 zerc：页数/翻页提示移到列表底部（见下方 📄 行）')
assert src.count(old1) == 1, f"old1 命中数 {src.count(old1)}"
src = src.replace(old1, new1)

# 2) 底部分隔线后插入页数/翻页行（保留原注释行不动；文件为 CRLF，行尾用 \\r\\n）
_EOL = "\r\n"
old2 = '        lines.append("━━━━━━━━━━━━")  # v127.2 提示区上方分隔' + _EOL
new2 = (
    '        lines.append("━━━━━━━━━━━━")  # v127.2 提示区上方分隔' + _EOL
    + '        # 玩家意见 #5（zerc）：页数/翻页提示从标题移到底部，' + _EOL
    + '        # 与炼金/烹饪/锻造/技能列表的底部页数风格统一（📄 行）' + _EOL
    + '        _flip = f"｜『背包筛选 {category} {page + 1}』下一页" if (category and page < pages) \\' + _EOL
    + '            else (f"｜『背包 {page + 1}』下一页" if page < pages else "")' + _EOL
    + '        lines.append(f"📄 第 {page}/{pages} 页 · 共 {len(items)} 件{_flip}")' + _EOL
)
assert src.count(old2) == 1, f"old2 命中数 {src.count(old2)}"
src = src.replace(old2, new2)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("T4 patch applied OK")