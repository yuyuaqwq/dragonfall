# -*- coding: utf-8 -*-
"""
⚠️ 一次性迁移已内化，勿重跑：

【一次性手术，勿重跑】本次改动已于 v112 内化进 game/data/skills.py。
本脚本仅通过 py_compile 做语法校验，无语义校验；若重复运行，可能因
marker 已不存在或内容已改变而删错区域，造成数据损坏。请勿再次执行。
"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import io
import py_compile

path = 'game/data/skills.py'
src = io.open(path, encoding='utf-8').read()


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
    print(f'removed {label}: chars {i}..{e} ({e - i} chars)')
    return src[:i] + src[e:]


for marker, label in [
    ('    "cls_bard": {', 'cls_bard'),
    ('    "cls_spellblade": {', 'cls_spellblade'),
    ('                "秘法法师": {', '秘法法师'),
    ('                "秘法术士": {', '秘法术士'),
    ('                "秘法贤者": {', '秘法贤者'),
]:
    src = remove_block(src, marker, label)

for old, new in [('                "拳斗士": {', '                "格斗士": {'),
                 ('                "武斗师": {', '                "拳术师": {')]:
    if old in src:
        src = src.replace(old, new)
        print(f'renamed {old.strip()} -> {new.strip()}')
    else:
        print(f'!! rename marker not found: {old.strip()}')

i = src.find('_ADD_HIDDEN_SKILLS = {')
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
if e < len(src) and src[e] == '\n':
    e += 1
src = src[:i] + '_ADD_HIDDEN_SKILLS = {}\n' + src[e:]
print('replaced _ADD_HIDDEN_SKILLS with placeholder')

io.open(path, 'w', encoding='utf-8').write(src)
print('written')
py_compile.compile(path, doraise=True)
print('py_compile OK')
