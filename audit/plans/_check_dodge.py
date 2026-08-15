# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.getcwd())
os.environ.setdefault('GWEN_GAME_DB', os.path.abspath('test_game_data.db'))
from game import engine as E
for lv in (1, 10, 30, 60):
    st = E.player_final_stats('cls_zhan_shi', lv, {}, 0, None, 0, {}, None)
    print('战士 lv%d: dodge=%s spd=%s' % (lv, st.get('dodge'), st.get('spd')))
