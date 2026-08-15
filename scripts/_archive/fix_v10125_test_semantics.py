# -*- coding: utf-8 -*-
"""⚠️ 一次性迁移已内化，勿重跑： v101.25 #320 语义适配：有会话时菜单选项选择用裸数字（『对话 N』=找 NPC）"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import io, re

def fix(path, pairs, note):
    with io.open(path, 'r', encoding='utf-8') as f:
        txt = f.read()
    total = 0
    for old, new in pairs:
        n = txt.count(old)
        txt = txt.replace(old, new)
        total += n
        print(f"  {old!r} -> {new!r}: {n} 处")
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print(f"{path}: 共替换 {total} 处 [{note}]")

# 1) test_v95_23_job_system.py：全部『对话 N』都是 find_npc 后选选项
fix("tests/test_v95_23_job_system.py",
    [('"对话 1"', '"1"'), ('"对话 3"', '"3"')],
    "有会话选选项改裸数字")

# 2) test_stage7_evolve.py：同上（3 参数 await_cmd）
fix("tests/test_stage7_evolve.py",
    [('"对话 3"', '"3"'), ('"对话 1"', '"1"')],
    "有会话选选项改裸数字")

# 3) test_v101_16_dialog_quick.py：第7步『对话 2』找第2个NPC——oak_town_1 酱油NPC随机
#    （roam/appear 深夜不在场）→ 移到 oak_town_2（镇长+文书墨点，墨点无随机配置=稳定）
p3 = "tests/test_v101_16_dialog_quick.py"
with io.open(p3, 'r', encoding='utf-8') as f:
    t3 = f.read()
old7 = '''    # ---- 7. 『对话 <序号>』无状态 → 找第 N 个 NPC ----
    ev7 = FakeEvent("g1", "1001", "对话 2")'''
new7 = '''    # ---- 7. 『对话 <序号>』无状态 → 找第 N 个 NPC ----
    # v101.25 测试确定性：oak_town_1 酱油 NPC（卖糖人/新手/老人/顽童）有 roam/appear
    # 随机性，深夜跑全量可能只剩小艾 → 移到 oak_town_2（镇长+文书墨点，墨点无随机配置）
    db.update_player("g1", "1001", cur_map="oak_town", cur_subarea="oak_town_2")
    ev7 = FakeEvent("g1", "1001", "对话 2")'''
assert old7 in t3, "test_v101_16 第7步锚点未找到"
t3 = t3.replace(old7, new7)
old7b = '''    check("『对话 2』命中第 2 个 NPC", "卖糖人" in r7 or "蜜嘴" in r7, r7[:100])'''
new7b = '''    check("『对话 2』命中第 2 个 NPC", "墨点" in r7, r7[:100])'''
assert old7b in t3, "test_v101_16 断言锚点未找到"
t3 = t3.replace(old7b, new7b)
with io.open(p3, 'w', encoding='utf-8', newline='') as f:
    f.write(t3)
print(f"{p3}: 第7步改为 oak_town_2 稳定场景")
print("DONE")
