# -*- coding: utf-8 -*-
"""v161 技能表合并：skills_v153.py 内容并入 skills.py，删 update 覆盖层 + 旧职业表。

方案（鱼鱼拍板）：
1. skills.py 的 PLAYER_SKILLS（旧 v151 表）→ 替换为 _V153_PLAYER_SKILLS 内容
2. skills.py 的 BRANCH_SKILLS（旧 v151 表）→ 替换为 _V153_BRANCH_SKILLS 内容
3. 删 update 覆盖层（v153 override import）
4. 保留 TUTOR_SKILLS
5. 删 skills_v153.py
6. 全量回归验证

用法：python scripts/merge_skills_v153.py
"""
import ast
import os
import re
import sys

ROOT = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall"
SKILLS_FILE = os.path.join(ROOT, "game", "data", "skills.py")
V153_FILE = os.path.join(ROOT, "game", "data", "skills_v153.py")


def extract_assign(src: str, var: str) -> str:
    """提取顶层赋值 var = {...} 的完整文本（含缩进后的 dict 字面量）。"""
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == var:
                    start = node.lineno - 1
                    end = node.end_lineno
                    lines = src.split("\n")
                    return "\n".join(lines[start:end])
    raise ValueError(f"{var} not found")


def main():
    v153_src = open(V153_FILE, encoding="utf-8").read()
    skills_src = open(SKILLS_FILE, encoding="utf-8").read()

    # 提取 v153 两表
    player_v153 = extract_assign(v153_src, "_V153_PLAYER_SKILLS")
    branch_v153 = extract_assign(v153_src, "_V153_BRANCH_SKILLS")

    # 定位 skills.py 各段
    lines = skills_src.split("\n")
    # PLAYER_SKILLS 起始（line 3 → index 2）
    ps_start = next(i for i, ln in enumerate(lines) if ln.startswith("PLAYER_SKILLS = {"))
    # BRANCH_SKILLS 起始
    bs_start = next(i for i, ln in enumerate(lines) if ln.startswith("BRANCH_SKILLS = {"))
    # TUTOR_SKILLS 起始
    ts_start = next(i for i, ln in enumerate(lines) if ln.startswith("TUTOR_SKILLS = {"))
    # v153 override 块起始（"# ===== v153" 注释）
    v153_comment = next(i for i, ln in enumerate(lines) if "v153 职业体系重做" in ln)

    print(f"ps_start={ps_start} bs_start={bs_start} ts_start={ts_start} v153_comment={v153_comment}")

    # 新文件：头部注释 + PLAYER_SKILLS(v153) + BRANCH_SKILLS(v153) + TUTOR_SKILLS(原样)
    header = "\n".join(lines[:ps_start])
    tutor_part = "\n".join(lines[ts_start:])

    # v153 表去掉顶层变量名，变成 PLAYER_SKILLS = ...
    player_body = player_v153.split("=", 1)[1].strip()
    branch_body = branch_v153.split("=", 1)[1].strip()

    new_src = (
        header.rstrip("\n") + "\n\n"
        + "# ===== v153 职业体系重做（2026-09-01 合并入主表，原 skills_v153.py 已删除）=====\n"
        + "PLAYER_SKILLS = " + player_body + "\n\n\n"
        + "BRANCH_SKILLS = " + branch_body + "\n\n\n"
        + tutor_part
    )

    open(SKILLS_FILE, "w", encoding="utf-8").write(new_src)
    print(f"已写回 {SKILLS_FILE}（{len(new_src)} 字符）")
    print("验证语法...")
    ast.parse(open(SKILLS_FILE, encoding="utf-8").read())
    print("语法 OK")
    print("删除 skills_v153.py...")
    os.remove(V153_FILE)
    print("完成")


if __name__ == "__main__":
    main()
