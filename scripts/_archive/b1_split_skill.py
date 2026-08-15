# -*- coding: utf-8 -*-
"""⚠️ 一次性迁移已内化，勿重跑： v103.6 B1-2 _player_skill 拆分：治疗/增益分支提取为独立方法（纯搬代码，行为零变化）"""
print('已废弃，禁止运行', file=__import__('sys').stderr)
__import__('sys').exit(1)
import io, shutil

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\battle.py"
shutil.copy(PATH, PATH + ".bak_v103")
lines = io.open(PATH, encoding="utf-8").read().splitlines()

def find(pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    return None

# 定位 _player_skill 与分支边界
fn_start = find(lambda l: l.startswith("    def _player_skill("))
assert fn_start is not None
heal_if = find(lambda l: 'if kind == "治疗":' in l, fn_start)
heal_end = find(lambda l: "            return logs" in l and l.index("return") < l.index("logs"), heal_if)  # 治疗分支 return logs
heal_end = heal_if + 1
# 更稳的定位：治疗分支的 return logs 在 922 行（0-indexed 921）
for i in range(heal_if + 1, len(lines)):
    if lines[i].strip() == "return logs":
        heal_end = i
        break
buff_if = find(lambda l: 'if kind == "增益":' in l, heal_end)
for i in range(buff_if + 1, len(lines)):
    if lines[i].strip() == "return logs":
        buff_end = i
        break
taunt_if = find(lambda l: 'if kind == "嘲讽":' in l, buff_end)
for i in range(taunt_if + 1, len(lines)):
    if lines[i].strip() == "return logs":
        taunt_end = i
        break

print(f"_player_skill: {fn_start+1} | 治疗 {heal_if+1}-{heal_end+1} | 增益 {buff_if+1}-{buff_end+1} | 嘲讽 {taunt_if+1}-{taunt_end+1}")

def extract_method(name, doc, start, end):
    """提取分支体（8 空格缩进）→ 方法（4 空格），不含 if 行，**含 return logs**"""
    body = lines[start + 1:end + 1]  # end 是 return logs 行（0-indexed），必须包含
    out = [f"    def {name}(self, st, skill_name, info, player, lv, mech, mval, p_mech, logs):",
           f"        \"\"\"{doc}\"\"\""]
    for ln in body:
        if ln.startswith("        "):
            out.append(ln[4:])
        elif ln.strip() == "":
            out.append("")
        else:
            out.append(ln)  # 理论不会出现
    return "\n".join(out)

m_heal = extract_method("_skill_heal", "治疗分支（v103.6 从 _player_skill 拆出）", heal_if, heal_end)
m_buff = extract_method("_skill_buff", "增益分支（v103.6 从 _player_skill 拆出）", buff_if, buff_end)

# 替换主函数中的分支调用：治疗/增益整块 → 一行调用；嘲讽分支保留原样
new_lines = lines[:heal_if] + [
    '        if kind == "治疗":',
    "            return self._skill_heal(st, skill_name, info, player, lv, mech, mval, p_mech, logs)",
    '        if kind == "增益":',
    "            return self._skill_buff(st, skill_name, info, player, lv, mech, mval, p_mech, logs)",
] + lines[taunt_if:taunt_end + 1] + lines[taunt_end + 1:]

# 新方法插入 _player_skill 定义之前
insert_at = fn_start
new_src = "\n".join(new_lines[:insert_at]) + "\n\n" + m_heal + "\n\n\n" + m_buff + "\n" + "\n".join(new_lines[insert_at:]) + "\n"

io.open(PATH, "w", encoding="utf-8", newline="").write(new_src)
print("已写回 battle.py")
