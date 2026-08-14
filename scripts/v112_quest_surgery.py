# -*- coding: utf-8 -*-
"""v112 quests.py 手术：隐藏解锁链 12+ → 6（每线 1 条），unlock_class 改新线 ID"""
import io
import py_compile

path = 'game/data/quests.py'
src = io.open(path, encoding='utf-8').read()

# 删除的解锁任务（按 id 起止标记删除整个 dict 块）
delete_ids = ["s_spellblade_trial", "s_void_walker_trial", "s_jungle_hunter_trial",
              "s_templar_trial", "s_blood_mage_trial", "s_beast_king_trial"]

for qid in delete_ids:
    marker = f'"id": "{qid}"'
    i = src.find(marker)
    if i < 0:
        print(f'!! quest marker not found: {qid}')
        continue
    # 找到该 dict 的起始 '{'（"id" 前应有 "{\n" 或 "{ "）——向前找本 dict 开括号
    start = src.rfind('{', 0, i)
    # 向后括号配对
    depth = 0
    k = start
    while k < len(src):
        if src[k] == '{':
            depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    e = k + 1
    # 消费 dict 结尾的逗号与换行（保留下一项）
    while e < len(src) and src[e] in ' \t':
        e += 1
    if e < len(src) and src[e] == ',':
        e += 1
        if e < len(src) and src[e] == '\n':
            e += 1
    print(f'deleted quest {qid}: chars {start}..{e}')
    src = src[:start] + src[e:]

# 6 条保留解锁链改 unlock_class
repoint = {
    '"unlock_class": "cls_spellblade"': None,  # 已删
    '"unlock_class": "cls_arcanist"': '"unlock_class": "cls_arcanum"',
    '"unlock_class": "cls_shadow_blade"': None,  # 不变
    '"unlock_class": "cls_dragon_warrior"': '"unlock_class": "cls_dragon_oath"',
    '"unlock_class": "cls_void_walker"': None,  # 已删
    '"unlock_class": "cls_astrologer"': '"unlock_class": "cls_wild_hunter"',
    '"unlock_class": "cls_jungle_hunter"': None,  # 已删
    '"unlock_class": "cls_templar"': None,  # 已删
    '"unlock_class": "cls_wu_sheng"': None,  # 不变
    '"unlock_class": "cls_blood_mage"': None,  # 已删
    '"unlock_class": "cls_necromancer"': '"unlock_class": "cls_hymn"',
    '"unlock_class": "cls_beast_king"': None,  # 已删
}
for old, new in repoint.items():
    cnt = src.count(old)
    if cnt == 0 and new is not None:
        print(f'!! unlock_class not found: {old}')
    elif new is not None:
        src = src.replace(old, new)
        print(f'repointed {old} -> {new} (x{cnt})')
    else:
        if cnt:
            print(f'!! leftover unlock_class {old} x{cnt}')

io.open(path, 'w', encoding='utf-8').write(src)
print('written')
py_compile.compile(path, doraise=True)
print('py_compile OK')
