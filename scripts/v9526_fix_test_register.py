# -*- coding: utf-8 -*-
"""v95.26 性别强制：批量给 tests/*.py 的无性别注册调用补『 男』。
规则：注册字符串不含性别 token（男/女/male/female/♂/♀）→ 末尾追加 男。
跳过 test_v95_24_gender.py（手工改，它是性别专项测试）。
"""
import io, os, re, glob

BASE = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\tests"
GENDER_TOKENS = ("男", "女", "male", "female", "♂", "♀", "m\"", "f\"", "m ", "f ")

changed = 0
for path in glob.glob(os.path.join(BASE, "test_*.py")):
    if "test_v95_24_gender" in path:
        continue
    text = io.open(path, encoding="utf-8").read()
    orig = text

    def fix(m):
        global changed
        full = m.group(0)
        # 去掉首尾引号
        inner = full[1:-1]
        toks = inner.split()
        if len(toks) < 2:
            return full  # 单 token 也补（如 "注册 见习二号"）
        if any(t in GENDER_TOKENS for t in toks):
            return full  # 已带性别
        # 末尾补 男
        changed += 1
        return full[:-1] + " 男\""

    text = re.sub(r'"注册 [^"]+"', fix, text)
    if text != orig:
        io.open(path, "w", encoding="utf-8").write(text)
        print(f"  {os.path.basename(path)}")

print(f"补性别注册调用: {changed} 处")
