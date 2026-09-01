# -*- coding: utf-8 -*-
"""v153 desc 文案回填脚本：子 agent 精写的 desc JSON → skills_v153.py

用法:
    python scripts/apply_v153_descs.py workspace/v153_desc_outputs/cls_zhan_shi.json

输入格式（子 agent 输出）:
    {"class": "cls_zhan_shi", "descs": {"技能名": "生动描述文案", ...}}

按技能 name 匹配回填到 skills_v153.py（基础 + 分支）。
"""
import json, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SKILLS_FILE = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills_v153.py"

def apply(infile: str):
    data = json.load(open(infile, encoding="utf-8"))
    descs = data.get("descs", {})
    cls = data.get("class", "")
    if not descs:
        print("无 desc 数据")
        return 0

    src = open(SKILLS_FILE, encoding="utf-8").read()

    # 找该职业段（_V153_PLAYER_SKILLS 或 _V153_BRANCH_SKILLS 里）
    # 策略：直接按技能 name 找块，块内替换 desc 行
    replaced = 0
    missing = []
    for name, desc in descs.items():
        # 找 name 字段行（基础技能有 name，分支技能 key=中文名）
        # 先找 'name': 'xxx' 行（基础技能，单引号）
        pat_name = r"'name':\s*'" + re.escape(name) + "'"
        m = re.search(pat_name, src)
        if m:
            # 该技能块内找 desc 行（向后到最近的 'desc': 或块结束）
            block_end = src.find("},", m.end())
            desc_pat = r"'desc':\s*'"
            dm = re.search(desc_pat, src[m.end():block_end])
            if dm:
                # 替换 desc 值（到下一个单引号）
                abs_pos = m.end() + dm.end()
                end_q = src.find("'", abs_pos)
                if end_q > 0:
                    src = src[:abs_pos] + desc.replace("'", "\\'") + src[end_q:]
                    replaced += 1
                    continue
        # 分支技能（key 即中文名）：找 '"name": {' 块
        pat_key = '            "' + re.escape(name) + '": {'
        m2 = re.search(pat_key, src)
        if m2:
            block_end2 = src.find("}", m2.end())
            desc_pat2 = r"('desc':\s*')"
            dm2 = re.search(desc_pat2, src[m2.end():block_end2])
            if dm2:
                abs_pos = m2.end() + dm2.end()
                end_q2 = src.find("'", abs_pos)
                if end_q2 > 0:
                    src = src[:abs_pos] + desc.replace("'", "\\'") + src[end_q2:]
                    replaced += 1
                    continue
        missing.append(name)

    if replaced:
        open(SKILLS_FILE, "w", encoding="utf-8").write(src)
    print(f"{cls}: 替换 {replaced} 条, 未找到 {len(missing)}: {missing[:10]}")
    return replaced

if __name__ == "__main__":
    total = 0
    for infile in sys.argv[1:]:
        total += apply(infile)
    print(f"共替换 {total} 条 desc")
