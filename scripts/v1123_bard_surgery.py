# -*- coding: utf-8 -*-
"""v112.3 skills.py 手术：牧师攻线换诗人路线（圣武士/审判骑士/裁决骑士 → 吟游诗人/灵魂歌者/黎明颂者）
- 诗人 12 技能入牧师攻线（等级对齐 30/60/90 档位：t1 32-45 / t2 60-68 / t3 90-98）
- 旧圣光攻线技能删除（与守线神谕系重叠，鱼鱼拍板无包袱）
- 删除独立 cls_bard（PLAYER_SKILLS + BRANCH_SKILLS）"""
import io
import py_compile

path = 'game/data/skills.py'
src = io.open(path, encoding='utf-8').read()


def replace_block(src, marker, new_block, label):
    i = src.find(marker)
    if i < 0:
        print(f'!! marker not found: {label}')
        return src
    j = src.find('{', i)
    depth = 0
    k = j
    while k < len(src):
        if src[k] == '{':
            depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    e = k + 1
    while e < len(src) and src[e] in ' \t':
        e += 1
    if e < len(src) and src[e] == ',':
        e += 1
    if e < len(src) and src[e] == '\n':
        e += 1
    print(f'replaced {label}: chars {i}..{e}')
    return src[:i] + new_block + src[e:]


def remove_block(src, marker, label):
    i = src.find(marker)
    if i < 0:
        print(f'!! marker not found: {label}')
        return src
    j = src.find('{', i)
    depth = 0
    k = j
    while k < len(src):
        if src[k] == '{':
            depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    e = k + 1
    while e < len(src) and src[e] in ' \t':
        e += 1
    if e < len(src) and src[e] == ',':
        e += 1
    if e < len(src) and src[e] == '\n':
        e += 1
    print(f'removed {label}: chars {i}..{e}')
    return src[:i] + src[e:]


# 牧师攻线 T1 圣武士 → 吟游诗人（诗人起手/增益技能，等级对齐 t1 档）
t1 = '''                "吟游诗人": {
                    "即兴弹唱": {"lv": 32, "mp": 3, "power": 1.0, "kind": "物理",
                                 "mech": "poison", "mech_val": 1,
                                 "desc": "即兴弹唱！100% 物理伤害，15% 概率使目标中毒(琴弦如刃)",
                                 "name": "即兴弹唱"},
                    "轻快拨弦": {"lv": 35, "mp": 3, "power": 1.1, "kind": "物理",
                                 "res_gain": 1, "mech": "poison", "mech_chance": 0.1,
                                 "desc": "轻快拨弦，110% 物理伤害，10% 附加中毒。吟游诗人的热身曲。",
                                 "name": "轻快拨弦"},
                    "战歌": {"lv": 38, "mp": 10, "power": 0, "kind": "增益",
                             "effect": "atk_up", "team": "atk_all", "cd": 2,
                             "desc": "激昂战歌！全队攻＋30% 3 回合(副本广播，团队技能)",
                             "name": "战歌"},
                    "安眠曲": {"lv": 45, "mp": 10, "power": 0, "kind": "增益",
                               "effect": "sleep", "cd": 3,
                               "desc": "安眠曲！使敌人陷入沉睡 2 回合（受击解除，对首领只持续 1 回合）",
                               "name": "安眠曲"},
                },'''
src = replace_block(src, '                "圣武士": {', t1, 't1 圣武士→吟游诗人')

# 牧师攻线 T2 审判骑士 → 灵魂歌者
t2 = '''                "灵魂歌者": {
                    "鼓舞": {"lv": 60, "mp": 10, "power": 0, "kind": "增益",
                             "effect": "crit_up", "team": "crit_all", "cd": 2,
                             "desc": "鼓舞士气！全队暴击＋20% 3 回合(副本广播，团队技能)",
                             "name": "鼓舞"},
                    "哀歌": {"lv": 62, "mp": 15, "power": 1.6, "kind": "魔法",
                             "cc": "silence", "cd": 3,
                             "desc": "哀歌！160% 魔法伤害，50% 概率沉默目标 2 回合",
                             "name": "哀歌"},
                    "伴奏": {"lv": 65, "mp": 0, "power": 0, "kind": "被动",
                             "passive": {"stat": "crit", "add": 0.08},
                             "desc": "属性被动：伴奏之魂，暴击＋8%",
                             "name": "伴奏"},
                    "轻风咏叹": {"lv": 68, "mp": 15, "power": 0, "kind": "增益",
                                 "effect": "spd_up", "team": "spd_all", "cd": 2,
                                 "desc": "轻快旋律！全队速度＋40% 3 回合(副本广播，团队技能)",
                                 "name": "轻风咏叹"},
                },'''
src = replace_block(src, '                "审判骑士": {', t2, 't2 审判骑士→灵魂歌者')

# 牧师攻线 T3 裁决骑士 → 黎明颂者
t3 = '''                "黎明颂者": {
                    "英雄叙事诗": {"lv": 90, "mp": 20, "power": 1.5, "kind": "治疗",
                                   "cd": 2, "team": "heal_all",
                                   "desc": "英雄叙事诗！治疗全队 150% 生命(副本广播，团队技能)",
                                   "name": "英雄叙事诗"},
                    "奥术咏叹调": {"lv": 92, "mp": 20, "power": 0, "kind": "增益",
                                   "effect": "matk_up", "team": "matk_all", "cd": 2,
                                   "desc": "奥术咏叹调！魔攻＋50% 3 回合，组队时全队魔攻强化(副本广播，团队技能)",
                                   "name": "奥术咏叹调"},
                    "快板节奏": {"lv": 95, "mp": 0, "power": 0, "kind": "被动",
                                 "passive": {"stat": "cdr", "add": 0.08},
                                 "desc": "属性被动：快板节奏，冷却缩减＋8%",
                                 "name": "快板节奏"},
                    "终章·黎明颂歌": {"lv": 98, "mp": 35, "power": 0, "kind": "增益",
                                       "effect": "atk_up_strong", "team": "atk_all", "cd": 5,
                                       "desc": "终章·黎明颂歌！全队攻＋75% 3 回合(副本广播，团队技能)",
                                       "name": "终章·黎明颂歌"},
                },'''
src = replace_block(src, '                "裁决骑士": {', t3, 't3 裁决骑士→黎明颂者')

# 删除独立 cls_bard（BRANCH_SKILLS 条目）
src = remove_block(src, '    "cls_bard": {', 'BRANCH cls_bard')

# 删除 _ADD_HIDDEN_SKILLS cls_bard（4 个基础技能已入牧师攻线）
src = remove_block(src, '    "cls_bard": {', '_ADD_HIDDEN_SKILLS cls_bard')

io.open(path, 'w', encoding='utf-8').write(src)
print('written')
py_compile.compile(path, doraise=True)
print('py_compile OK')
