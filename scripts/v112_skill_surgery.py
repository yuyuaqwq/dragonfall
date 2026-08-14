# -*- coding: utf-8 -*-
"""v112 skills.py 手术脚本：删除旧隐藏职业块/秘法守线，改名拳师分支，_ADD_HIDDEN_SKILLS 置空"""
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
