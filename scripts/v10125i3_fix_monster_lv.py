# -*- coding: utf-8 -*-
"""v101.25i3 数据修正：野外(非副本)普通怪等级与 sa_lv 偏差 ≤-3 的拉到 sa_lv-2
（生成器时代系统性偏差：深处子区域怪比标注低 3-6 级，玩家感知"区域等级虚高"）
副本房/精英/Boss 不碰（Boss 房高等级是设计）。
"""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\subareas.py"
lines = io.open(PATH, 'r', encoding='utf-8').read().split('\n')

# 状态机：找 sa_id / type / monsters 块内的 [id, name, role, lv]
sa_id, sa_type = None, None
in_monsters = False          # 在 "monsters": [ 块内
in_m_block = False           # 在单个怪物 [ 块内
m_buf = []                   # 当前怪物块的原始行 idx 记录
fixes = []                   # (行号, 旧lv, 新lv, sa_id, 怪名)

MON_ID_RE = re.compile(r'^\s*"m_[a-z0-9_]+",\s*$')
ROLE_SET = {"tank", "speedster", "dps", "caster", "healer", "support", "normal",
            "elite", "boss", "wild", "ranged", "brute"}

i = 0
while i < len(lines):
    line = lines[i]
    # 子区域 id（缩进 12 空格的在 subarea dict 里）
    m = re.match(r'^\s+"id": "([a-z0-9_]+)",\s*$', line)
    if m and not in_monsters:
        sa_id = m.group(1)
    m = re.match(r'^\s+"type": "([^"]+)",\s*$', line)
    if m and not in_monsters:
        sa_type = m.group(1)
    # monsters 块开始
    if re.search(r'"monsters": \[', line):
        in_monsters = True
        in_m_block = False
    elif in_monsters and re.match(r'^\s+\[\s*$', line):
        in_m_block = True
        m_buf = []
    elif in_m_block and MON_ID_RE.match(line):
        m_buf = [i]
    elif in_m_block and m_buf:
        m_buf.append(i)
        # 依次期待 name / role / lv
        if len(m_buf) == 4:
            mid_line = lines[m_buf[0]].strip().strip(',').strip('"')
            name_line = lines[m_buf[1]].strip().strip(',').strip('"')
            role_line = lines[m_buf[2]].strip().strip(',').strip('"')
            lv_line = m_buf[3]
            lv_txt = lines[lv_line].strip().strip(',').strip()
            try:
                old_lv = int(lv_txt)
            except ValueError:
                m_buf = []
                in_m_block = False
                continue
            role = role_line.strip('"')
            if (sa_type != "副本" and role not in ("elite", "boss")
                    and sa_id and old_lv <= (sa_id_lv := 0)):  # placeholder
                pass
            if sa_type != "副本" and role not in ("elite", "boss") and old_lv <= 0:
                pass
            # 需要 sa_lv：从子区域 lv 行拿——这里直接比较时用容错：记录候选，后续统一判定
            fixes.append((sa_id, sa_type, name_line, role, old_lv, lv_line))
            m_buf = []
            in_m_block = False
    # monsters 块结束
    if in_monsters and re.match(r'^\s+\],\s*$', line):
        in_monsters = False
        in_m_block = False
    i += 1

# 第二遍：拿每个 sa 的 lv（"lv": N 在 subarea dict 内）
sa_lv_map = {}
i = 0
cur_id = None
in_sub = False
while i < len(lines):
    line = lines[i]
    m = re.match(r'^\s+"id": "([a-z0-9_]+)",\s*$', line)
    if m:
        cur_id = m.group(1)
    m = re.match(r'^\s+"lv": (\d+),\s*$', line)
    if m and cur_id:
        sa_lv_map[cur_id] = int(m.group(1))
    i += 1

# 判定 + 收集修改
to_change = []
for sa_id, sa_type, name, role, old_lv, lv_line in fixes:
    sa_lv = sa_lv_map.get(sa_id)
    if sa_lv is None:
        continue
    diff = old_lv - sa_lv
    if diff <= -3:
        new_lv = sa_lv - 2
        to_change.append((lv_line, old_lv, new_lv, sa_id, name))

print(f"扫描到怪物块 {len(fixes)} 个, 需修正 {len(to_change)} 个 (diff≤-3)")
# 从后往前替换（行号不漂移）
for lv_line, old_lv, new_lv, sa_id, name in sorted(to_change, reverse=True):
    lines[lv_line] = lines[lv_line].replace(str(old_lv), str(new_lv), 1)
    print(f"  {sa_id} [{name}] {old_lv} → {new_lv}")

io.open(PATH, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
print("写入完成")
