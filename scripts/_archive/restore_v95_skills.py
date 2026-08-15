# -*- coding: utf-8 -*-
"""
⚠️ 一次性迁移已内化，勿重跑：
锚点 = 每个职业块内第一个技能 dict 的结束（配对大括号），在其后插入新块。从后往前插。"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import re, json

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"

def S(*parts):
    return "".join(parts)

def find_dict_end(text, open_idx):
    """从 { 位置找配对 } 的 index。"""
    depth = 0
    in_str = False
    for i in range(open_idx, len(text)):
        c = text[i]
        if in_str:
            if c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1

NEW_SKILLS = [
    ("cls_bard", "吟游诗人", {
        S("sk_", "qin", "_xian"): {"lv": 2, "mp": 0, "power": 1.1, "kind": "物理", "res_gain": 1,
            "mech": "poison", "mech_chance": 0.10,
            "desc": "轻快拨弦，110% 物理伤害，10% 附加中毒。吟游诗人的热身曲。", "name": "轻快拨弦"},
    }),
    ("cls_zhan_shi", "战士", {
        S("sk_", "meng", "_ji"): {"lv": 2, "mp": 0, "power": 1.2, "kind": "物理", "res_gain": 1,
            "desc": "猛力一击，120% 物理伤害，怒气＋1。", "name": "猛击"},
    }),
    ("cls_fa_shi", "法师", {
        S("sk_", "bing", "_jing"): {"lv": 2, "mp": 8, "power": 1.05, "kind": "魔法", "element": "ice",
            "desc": "凝结冰晶掷向敌人，冰系 105% 魔法伤害。元素流转的前奏。", "name": "冰晶术"},
    }),
    ("cls_you_xia", "游侠", {
        S("sk_", "miao", "_zhun"): {"lv": 2, "mp": 0, "energy": 10, "power": 1.4, "kind": "物理",
            "desc": "屏息瞄准，140% 物理伤害，消耗 10 精力。", "name": "瞄准射击"},
    }),
    ("cls_mu_shi", "牧师", {
        S("sk_", "sheng", "_guang"): {"lv": 2, "mp": 8, "power": 1.15, "kind": "魔法", "res_gain": 1,
            "desc": "圣光凝聚成束，115% 圣光伤害，信仰＋1。", "name": "圣光术"},
    }),
    ("cls_ci_ke", "刺客", {
        S("sk_", "ge_lie"): {"lv": 2, "mp": 0, "power": 1.15, "kind": "物理", "res_gain": 1,
            "desc": "利刃撕裂，115% 物理伤害，连击点＋1。", "name": "割裂"},
    }),
    ("cls_wu_seng", "拳师", {
        S("sk_", "chong_quan"): {"lv": 2, "mp": 0, "power": 1.1, "kind": "物理", "res_gain": 1,
            "combo": {"tag": "拳"},
            "desc": "沉肩冲拳，110% 物理伤害，气＋1，连招【拳】。", "name": "冲拳"},
    }),
]

with open(PATH, encoding="utf-8") as f:
    src = f.read()

positions = []
for cls_id, cname, skill in NEW_SKILLS:
    pat = re.compile(r'"' + cls_id + r'": \{\s*"name": "' + cname + r'",\s*"skills": \{')
    m = pat.search(src)
    if not m:
        print(f"!! 找不到 {cls_id} {cname}")
        continue
    skills_open = src.index("{", m.end() - 1)  # skills: { 的 {
    # 第一个技能 dict 开始（skills { 后第一个 {）
    sk1 = src.index("{", skills_open + 1)
    end1 = find_dict_end(src, sk1)
    if end1 < 0:
        print(f"!! 解析失败 {cls_id}")
        continue
    # 插入点 = 第一个技能 } 之后（保留原 ,\n）
    insert_at = end1 + 1
    positions.append((insert_at, cls_id, cname, skill))
    # 校验插入点后应该是 ,\n
    print(f"  {cls_id}: 技能1结束@{end1} 后={repr(src[end1:end1+4])}")

# 从后往前插入（跳过首个位置以避免索引漂移影响后续——从大到小天然安全）
for insert_at, cls_id, cname, skill in sorted(positions, reverse=True):
    parts = []
    for skey, sinfo in skill.items():
        inner = ",\n".join(f"                {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}"
                           for k, v in sinfo.items())
        parts.append(f"    {json.dumps(skey, ensure_ascii=False)}: {{\n{inner},\n            }},")
    block = "\n" + "\n".join(parts)
    src = src[:insert_at] + block + src[insert_at:]
    print(f"  ✓ 插入 {cls_id} {cname}")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(src)

# 验证
import importlib.util
spec = importlib.util.spec_from_file_location("skills_v", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ok = True
for cls_id, cname, skill in NEW_SKILLS:
    table = m.PLAYER_SKILLS[cls_id]
    sk = table["skills"] if isinstance(table, dict) and "skills" in table else table
    lvs = sorted(s["lv"] for s in sk.values())
    has2 = 2 in lvs
    ok = ok and has2
    print(f"  verify {cls_id}: Lv序列 {lvs} | Lv.2={'有' if has2 else '无!'}")
print("全部通过" if ok else "有失败!")
