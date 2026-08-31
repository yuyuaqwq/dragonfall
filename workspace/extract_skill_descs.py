# -*- coding: utf-8 -*-
"""提取 skills.py 全部技能 desc 现状 → JSON，供子 agent 重写 desc 用。
用法: python extract_skill_descs.py <输出json>
输出: {"cls_zhan_shi": {"sk_hui_kan": {"name": "挥砍", "desc": "旧desc", "kind": "物理", ...}}}
"""
import json, re, sys

SRC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\skills.py"
src = open(SRC, encoding="utf-8").read()

# 解析 PLAYER_SKILLS 结构：职业块 → 技能块
# 用 ast 太麻烦（文件里有动态结构），用缩进解析
result = {}

# 按行扫描，跟踪当前职业 / 当前技能
cur_cls = None
cur_skill = None
skill_start = None

lines = src.splitlines()
i = 0
# 顶层 key 缩进 4 空格（"cls_xxx": {）
# 技能 key 缩进 8 空格（"sk_xxx": {）
# 字段缩进 12 空格（"desc": "..."）

def parse_skill_block(lines, start_idx):
    """从技能块起始行解析出 dict，返回 (dict, 结束行idx)。"""
    d = {}
    depth = 0
    j = start_idx
    while j < len(lines):
        line = lines[j]
        stripped = line.strip()
        if stripped.startswith("}"):
            if depth == 0:
                return d, j
            depth -= 1
        elif stripped.endswith("{"):
            depth += 1
        else:
            m = re.match(r'"([^"]+)"\s*:\s*("(?:[^"\\]|\\.)*"|\[.*\]|\{.*\}|[^,}]+),?$', stripped)
            if m:
                key = m.group(1)
                val = m.group(2)
                # 简单解析值
                try:
                    d[key] = json.loads(val)
                except Exception:
                    d[key] = val
        j += 1
    return d, j

j = 0
while j < len(lines):
    line = lines[j]
    m = re.match(r'^    "cls_([a-z0-9_]+)"\s*:\s*\{', line)
    if m:
        cls_id = "cls_" + m.group(1)
        # 跳过 {"name": ..., "skills": { 头
        k = j + 1
        cls_name = None
        while k < len(lines):
            mm = re.match(r'^\s+"name"\s*:\s*"([^"]+)"', lines[k])
            if mm:
                cls_name = mm.group(1)
                break
            k += 1
        result[cls_id] = {"name": cls_name, "skills": {}}
        cur_cls = cls_id
        # 找 skills: { 之后
        k = j
        while k < len(lines) and '"skills"' not in lines[k]:
            k += 1
        k += 1  # 跳到 skills: { 下一行
        # 解析技能块
        while k < len(lines):
            sm = re.match(r'^\s{8}"(sk_[a-z0-9_]+)"\s*:\s*\{', lines[k])
            if sm:
                sid = sm.group(1)
                d, k2 = parse_skill_block(lines, k)
                result[cls_id]["skills"][sid] = d
                k = k2 + 1
            elif re.match(r'^\s{4}"[a-z_]+"\s*:', lines[k]) or lines[k].strip() == "}":
                break
            else:
                k += 1
        j = k
        continue
    j += 1

print(json.dumps(result, ensure_ascii=False, indent=1))
