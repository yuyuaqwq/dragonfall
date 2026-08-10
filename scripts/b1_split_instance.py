# -*- coding: utf-8 -*-
"""v103.7 B1-3 _instance_start 拆分：stages/state 构建段提取为 _instance_build_state（纯搬代码）"""
import io, shutil

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\commands\instance.py"
shutil.copy(PATH, PATH + ".bak_v103")
lines = io.open(PATH, encoding="utf-8").read().splitlines()

def find(pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    return None

fn_start = find(lambda l: l.startswith("    async def _instance_start("))
assert fn_start is not None

# 提取边界：641 行（now = int(time.time()) 之后）到 st 构建结束
# 定位 "now = int(time.time())" 行（1-indexed 640）
now_i = find(lambda l: "now = int(time.time())" in l, fn_start)
# 定位 stages 构建开始（now 后第一个 "stages = inst.get"）
stages_i = find(lambda l: 'stages = inst.get("stages") or []' in l, now_i)
# 定位 st 构建结束：752 行（0-indexed 751）是 st dict 的 "}" 行
# 找 "over": False, 后下一个缩进 8 空格的 "for m in members:"
over_i = find(lambda l: '"over": False' in l, stages_i)
next_stmt = find(lambda l: l.startswith("        for m in members:"), over_i)
end = next_stmt - 1  # st dict 结束行（752）

print(f"_instance_start: {fn_start+1} | now={now_i+1} stages={stages_i+1} st_end={end+1}")

# 提取 642-752（0-indexed stages_i..end），缩进不变（8 空格方法体 → 8 空格方法体）
body = lines[stages_i:end + 1]
method = [
    "    def _instance_build_state(self, kid, inst, members, boss, now):",
    '        """v103.7 B1-3：副本状态构建（stages 分层/地图模式判定/st 初始 dict），原 _instance_start 中段拆出"""',
]
for ln in body:
    if ln.startswith("        "):
        method.append(ln)  # 8 空格保留
    elif ln.strip() == "":
        method.append("")
    else:
        method.append("        " + ln)  # 保险：顶格行补缩进
method.append("        return st")
m_text = "\n".join(method)

# 主函数替换：stages 构建段 → 一行调用
new_lines = lines[:stages_i] + [
    "        st = self._instance_build_state(kid, inst, members, boss, now)",
] + lines[end + 1:]

# 新方法插入 _instance_start 之前
insert_at = fn_start
new_src = "\n".join(new_lines[:insert_at]) + "\n\n" + m_text + "\n\n\n" + "\n".join(new_lines[insert_at:]) + "\n"

io.open(PATH, "w", encoding="utf-8", newline="").write(new_src)
print("已写回 instance.py")
