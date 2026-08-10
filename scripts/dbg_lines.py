# -*- coding: utf-8 -*-
import io
lines = io.open(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\store\connection.py",
                encoding="utf-8").read().splitlines()
for i in range(245, 252):
    print(i + 1, repr(lines[i][:60]))
print("---")
for i, ln in enumerate(lines):
    if '"""' in ln and "executescript" not in ln:
        print("含三引号行:", i + 1, repr(ln[:50]))
