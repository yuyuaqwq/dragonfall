# -*- coding: utf-8 -*-
"""合并 6 个对话树分片进 game/data/dialogues.py

流程：
1. 解析每个 scripts/_dlg_parts/part_*.py 的 DIALOGUES_PART（ast.literal_eval，纯字面量校验）
2. 结构校验：start 存在、next 引用有效、need/action 键在注册表内、npc_id 无重复
3. 文本拼接进 dialogues.py 收尾大括号前（保持原文件字节不变，只追加）
4. py_compile + import 冒烟
"""
import ast
import os
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PLUGIN = os.path.dirname(os.path.abspath(__file__))  # scripts/
ROOT = os.path.dirname(PLUGIN)                        # dragonfall/
QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(ROOT)))  # qqbot/
PARTS_DIR = os.path.join(PLUGIN, '_dlg_parts')
TARGET = os.path.join(ROOT, 'game', 'data', 'dialogues.py')

os.environ.setdefault('GWEN_GAME_DB', os.path.join(ROOT, 'test_game_data.db'))
os.environ.setdefault('GWEN_TEST_MODE', '1')
sys.path.insert(0, QQBOT)

# 必须先导入 content 完成包初始化（core.index ↔ data._assembly 存在循环导入，
# 首个导入为 core 时会炸；content 先行则正常）
from data.plugins.dragonfall.game import content as C0            # noqa: E402
from data.plugins.dragonfall.game.core.dialogue_conds import CONDITIONS   # noqa: E402

# talk_actions 依赖 astrbot 框架（系统 python 不可导入），动作键用规范稳定清单硬编码
ACTIONS = {'set_flag', 'give_gold', 'give_exp', 'give_item', 'open_shop', 'hint',
           'quest_take', 'side_take', 'side_offer', 'consume_item', 'unlock_prof',
           'unlock_class', 'tutor_skill', 'evolve_class', 'hidden_evolve'}

RESULT = []


def log(msg):
    RESULT.append(msg)
    print(msg)


def load_part(path):
    """解析分片文件 → (npc_id 前缀注释, dict)"""
    text = open(path, encoding='utf-8').read()
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == 'DIALOGUES_PART':
                    return ast.literal_eval(node.value)
    raise ValueError('未找到 DIALOGUES_PART 赋值: %s' % path)


def check_tree(npc_id, dlg, errors):
    nodes = dlg.get('nodes') or {}
    start = dlg.get('start')
    if start not in nodes:
        errors.append('%s: start %r 不在 nodes 中' % (npc_id, start))
    # 选项引用与键合法性
    for nid, node in nodes.items():
        for opt in node.get('options') or []:
            nxt = opt.get('next')
            if nxt not in nodes and nxt != '__end__':
                errors.append('%s.%s: next %r 无效' % (npc_id, nid, nxt))
            for k in (opt.get('need') or {}):
                if k not in CONDITIONS:
                    errors.append('%s.%s: need 键 %r 未注册' % (npc_id, nid, k))
            for k in (opt.get('action') or {}):
                if k not in ACTIONS:
                    errors.append('%s.%s: action 键 %r 未注册' % (npc_id, nid, k))
    # 可达性（忽略 need 的图可达）
    seen = set()
    stack = [start] if start in nodes else []
    while stack:
        nid = stack.pop()
        if nid in seen:
            continue
        seen.add(nid)
        for opt in (nodes[nid].get('options') or []):
            nxt = opt.get('next')
            if nxt in nodes and nxt not in seen:
                stack.append(nxt)
    unreachable = [n for n in nodes if n not in seen]
    if unreachable:
        errors.append('%s: 不可达节点 %s' % (npc_id, ','.join(sorted(unreachable))))


def main():
    if not os.path.isdir(PARTS_DIR):
        log('[错误] 分片目录不存在: %s' % PARTS_DIR)
        return 1
    part_files = sorted(f for f in os.listdir(PARTS_DIR) if f.startswith('part_') and f.endswith('.py'))
    if not part_files:
        log('[错误] 没有分片文件')
        return 1
    log('发现分片: %s' % ', '.join(part_files))

    all_entries = {}
    errors = []
    for f in part_files:
        try:
            d = load_part(os.path.join(PARTS_DIR, f))
        except Exception as e:
            errors.append('%s: 解析失败 %s' % (f, e))
            continue
        for npc_id, dlg in d.items():
            if npc_id in all_entries:
                errors.append('npc_id 重复: %s（%s 与 %s）' % (npc_id, all_entries[npc_id], f))
            all_entries[npc_id] = (dlg, f)
            check_tree(npc_id, dlg, errors)
    if errors:
        log('--- 校验失败 ---')
        for e in errors:
            log('  ❌ ' + e)
        return 1

    # 与现有 DIALOGUES 查重
    text = open(TARGET, encoding='utf-8').read()
    for npc_id in all_entries:
        m = re.search(r'^\s{4}"%s":\s*\{' % re.escape(npc_id), text, re.M)
        if m:
            log('❌ %s 已存在于 dialogues.py' % npc_id)
            return 1

    # 文本拼接：取每份分片 DIALOGUES_PART 花括号内正文
    parts_body = []
    for f in part_files:
        t = open(os.path.join(PARTS_DIR, f), encoding='utf-8').read()
        m = re.search(r'DIALOGUES_PART\s*=\s*\{', t)
        inner = t[m.end():].rstrip()
        if inner.endswith('}'):
            inner = inner[:-1].rstrip()
        parts_body.append(inner)
    if not text.rstrip().endswith('}'):
        log('❌ dialogues.py 不以 } 结尾，中止拼接')
        return 1
    merged = text.rstrip()[:-1].rstrip() + '\n' + '\n'.join(parts_body) + '\n}\n'
    open(TARGET, 'w', encoding='utf-8').write(merged)
    log('已合并 %d 个 NPC 对话树进 dialogues.py' % len(all_entries))

    # 冒烟：py_compile + import
    import py_compile
    py_compile.compile(TARGET, doraise=True)
    log('py_compile 通过')
    sys.path.insert(0, ROOT)
    from data.plugins.dragonfall.game import content as C2  # noqa: F401
    log('import content 通过，DIALOGUES 总数: %d' % len(C2.DIALOGUES))
    return 0


if __name__ == '__main__':
    sys.exit(main())
