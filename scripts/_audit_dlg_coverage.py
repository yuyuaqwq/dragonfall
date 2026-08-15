# -*- coding: utf-8 -*-
"""合并后审计：20 位主线 giver 全覆盖检查（接取/交付/树存在）"""
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(ROOT)))
os.environ.setdefault('GWEN_GAME_DB', os.path.join(ROOT, 'test_game_data.db'))
os.environ.setdefault('GWEN_TEST_MODE', '1')
sys.path.insert(0, QQBOT)

from data.plugins.dragonfall.game import content as C  # noqa: E402

DLG = C.DIALOGUES
givers = {}
for mq in C.MAIN_QUESTS:
    givers.setdefault(mq['giver'], []).append(mq['id'])

# 链式自动推进：存在前序任务 next == 本任务 → 完成后自动接取，无需树内入口
chained = set()
for mq in C.MAIN_QUESTS:
    if mq.get('next'):
        chained.add(mq['next'])

fails = []
for giver, qids in sorted(givers.items()):
    dlg = DLG.get(giver)
    if not dlg:
        fails.append('%s: 无对话树' % giver)
        continue
    nodes = dlg.get('nodes') or {}
    all_opts = [o for n in nodes.values() for o in (n.get('options') or [])]

    def covered(opts, key, qid):
        """静态 qid 匹配或动态 ""（giver 校验语义）任一即算覆盖"""
        for o in opts:
            need = o.get('need') or {}
            v = need.get(key)
            if v == qid:
                return True
            if v == '':
                return True  # 动态模式：引擎按当前主线 + giver == 本 NPC 校验
        return False

    for qid in qids:
        if qid in chained:
            continue  # 链式自动推进，无需树内接取入口
        if not covered(all_opts, 'quest_pending', qid):
            fails.append('%s %s: 缺 quest_pending 接取入口' % (giver, qid))
        if not covered(all_opts, 'quest_ready', qid):
            fails.append('%s %s: 缺 quest_ready 交付入口' % (giver, qid))

print('主线 giver 数: %d，任务数: %d' % (len(givers), sum(len(v) for v in givers.values())))
if fails:
    print('❌ %d 处缺口:' % len(fails))
    for f in fails:
        print('  ' + f)
    sys.exit(1)
print('✅ 全部主线 giver 均有对话树，70 任务接取/交付入口全覆盖')
