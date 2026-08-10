# -*- coding: utf-8 -*-
import io
lines = io.open(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\battle.py",
                encoding="utf-8").read().splitlines()
for i in range(968, 986):
    print(i + 1, repr(lines[i][:80]))
