# -*- coding: utf-8 -*-
"""临时：测试不同导入路径是否触发循环导入"""
import sys, os
QQBOT = r'C:\Users\yuyu\qqbot'
ROOT = r'C:\Users\yuyu\qqbot\data\plugins\dragonfall'
os.environ.setdefault('GWEN_GAME_DB', os.path.join(ROOT, 'test_game_data.db'))
os.environ.setdefault('GWEN_TEST_MODE', '1')
sys.path.insert(0, QQBOT)

print('方式1: from data.plugins.dragonfall.game import content as C')
try:
    from data.plugins.dragonfall.game import content as C
    print('  OK, DIALOGUES =', len(C.DIALOGUES))
except Exception as e:
    print('  FAIL:', type(e).__name__, e)

print('方式2: 先 import game 包')
try:
    import data.plugins.dragonfall.game as G
    print('  OK')
except Exception as e:
    print('  FAIL:', type(e).__name__, e)

print('方式3: from data.plugins.dragonfall.game.core import dialogue_conds')
try:
    from data.plugins.dragonfall.game.core import dialogue_conds as DC
    print('  OK, CONDITIONS =', len(DC.CONDITIONS))
except Exception as e:
    print('  FAIL:', type(e).__name__, e)
