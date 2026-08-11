# -*- coding: utf-8 -*-
"""v101.21h 战士/刺客/拳师技能补蓝耗（特色+平衡）：
起手式免费（挥砍/刺击/直拳=普攻替代）、普通技能低蓝、终结技资源+蓝双耗、被动0。
按 sk_key 精确定位（铁壁等重名技能安全）。"""
import io, re, sys
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
from game import content as C

# 数值表：cls -> {技能名: mp}
PLAN = {
    "cls_zhan_shi": {
        "挥砍": 0, "猛击": 4, "破甲斩": 6, "旋风斩": 10, "裂地斩": 8,
        "战吼": 5, "铁壁": 5, "蓄势": 3, "盾击": 6, "战争践踏": 12, "无畏冲击": 15,
    },
    "cls_ci_ke": {
        "刺击": 0, "割裂": 4, "双刃乱舞": 8, "淬毒": 6, "暗杀": 12,
        "潜行": 5, "疾影": 3, "影袭": 6, "死亡标记": 6, "毒雾": 10, "暗影处刑": 18,
    },
    "cls_wu_seng": {
        "直拳": 0, "冲拳": 3, "崩拳": 6, "回旋踢": 6, "震地击": 8,
        "侧踢": 4, "铁掌": 5, "气息调息": 5, "铁壁": 5, "连招三连": 10, "破晓之拳": 15,
    },
}

p = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
with io.open(p, encoding="utf-8") as f:
    s = f.read()

changed = 0
for cls, plan in PLAN.items():
    table = C.PLAYER_SKILLS[cls]["skills"]
    for sk_key, info in table.items():
        name = info.get("name")
        if name not in plan:
            continue
        new_mp = plan[name]
        old_mp = info.get("mp", 0)
        if old_mp == new_mp:
            continue
        # 定位 "sk_key": { 块内的 "mp": N,（该 dict 的 mp 字段）
        pat = re.compile(r'("' + re.escape(sk_key) + r'"\s*:\s*\{.*?"mp":\s*)\d+', re.S)
        m = pat.search(s)
        if not m:
            print(f"!! 未找到 {sk_key}({name}) 的 mp 字段")
            continue
        def repl(mm):
            return mm.group(1) + str(new_mp)
        s2, n = pat.subn(repl, s)
        if n == 0:
            print(f"!! 未找到 {sk_key}({name}) 的 mp 字段")
            continue
        if n > 1:
            print(f"  ⚠️ {sk_key}({name}) 出现 {n} 处同名块，全部替换（数值一致）")
        s = s2
        changed += 1
        print(f"  {cls} {name}: mp {old_mp} -> {new_mp} (x{n})")

with io.open(p, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print(f"共修改 {changed} 处")
