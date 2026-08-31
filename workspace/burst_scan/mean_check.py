# -*- coding: utf-8 -*-
"""v133 均值轮次复验：收敛后 裸装同级 是否保住 v131 的 4~6 轮（数值门禁配套）"""
import sys
sys.path.insert(0, 'C:/Users/yuyu/qqbot/data/plugins')
from dragonfall.scripts.numeric_lib.player import per_action_dmg, PlayerOptions
from dragonfall.scripts.numeric_lib.monster import panel

CLS = [('cls_ci_ke', '刺客'), ('cls_zhan_shi', '战士'), ('cls_you_xia', '游侠'),
       ('cls_fa_shi', '法师'), ('cls_mu_shi', '牧师'), ('cls_wu_seng', '武僧')]

rows = []
for lv in (10, 20, 40, 60, 80):
    p = panel('dps', lv)
    hp, df = p['hp'], p['def']
    for cls, cn in CLS:
        d = per_action_dmg(cls, lv, {}, df, df,
                           PlayerOptions(attr_points=True, tier=True, evolve=False))
        r = hp / max(d, 1)
        rows.append((lv, cn, d, r, hp))

for lv, cn, d, r, hp in rows:
    flag = 'OK' if 3.5 <= r <= 8.5 else ('FAST' if r < 3.5 else 'SLOW')
    print(f'L{lv:>3} {cn} 均伤{d:6.0f} 轮次{r:5.1f} [{flag}] 怪血{hp}')