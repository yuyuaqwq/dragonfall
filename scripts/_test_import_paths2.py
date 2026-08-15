# -*- coding: utf-8 -*-
"""临时：测试 content 之后导入 talk_actions 是否可行"""
import sys, os
QQBOT = r'C:\Users\yuyu\qqbot'
ROOT = r'C:\Users\yuyu\qqbot\data\plugins\dragonfall'
os.environ.setdefault('GWEN_GAME_DB', os.path.join(ROOT, 'test_game_data.db'))
os.environ.setdefault('GWEN_TEST_MODE', '1')
sys.path.insert(0, QQBOT)

try:
    from data.plugins.dragonfall.game import content as C
    print('content OK, DIALOGUES =', len(C.DIALOGUES))
    from data.plugins.dragonfall.game.core.dialogue_conds import CONDITIONS
    print('CONDITIONS OK,', len(CONDITIONS))
    from data.plugins.dragonfall.game.commands.talk_actions import ACTIONS
    print('ACTIONS OK,', len(ACTIONS))
except Exception as e:
    import traceback
    traceback.print_exc()
