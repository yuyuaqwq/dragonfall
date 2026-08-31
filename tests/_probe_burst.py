# -*- coding: utf-8 -*-
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:/Users/yuyu/qqbot/data/plugins")
BUILD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BUILD, "scripts"))
from burst_scan import peak_of

CLS = ["cls_ci_ke", "cls_zhan_shi", "cls_you_xia", "cls_fa_shi", "cls_mu_shi", "cls_wu_seng"]
REDLINE = 42.0
fails = []
for cls in CLS:
    for lv in (30, 50, 70):
        for name, dmg, hp, tlv in peak_of(cls, lv, "naked", 0):
            pct = dmg * 100.0 / max(hp, 1)
            flag = "  <-- OVER" if pct > REDLINE else ""
            print(f"{cls} L{lv} {name}: {pct:.1f}% (dmg={dmg}, hp={hp}){flag}")
            if pct > REDLINE:
                fails.append(f"{cls} L{lv} {name}: {pct:.1f}%")
print("FAILS:", fails)
