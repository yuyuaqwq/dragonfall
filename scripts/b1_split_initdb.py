# -*- coding: utf-8 -*-
"""v103.5 B1-1 init_db 拆分：巨型 executescript 按域拆常量 + ALTER 段提取 _ensure_legacy_columns"""
import io, re, sys

PATH = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\store\connection.py"
src = io.open(PATH, encoding="utf-8").read()
lines = src.splitlines()

# 1) 定位 executescript 字符串边界（""" 包裹）
start = None
for i, ln in enumerate(lines):
    if 'conn.executescript("""' in ln:
        start = i
        break
assert start is not None, "找不到 executescript 起点"
end = None
for i in range(start + 1, len(lines)):  # 终点必须晚于起点（起点行本身以 """ 结尾）
    if '""")' in lines[i]:  # executescript 结束行：            """)
        end = i
        break
assert end is not None, "找不到 executescript 终点"
print(f"executescript 范围: {start+1}~{end+1} 行")

# 2) 提取 SQL 内容（去掉首行 `conn.executescript("""` 和末行 `"""`）
sql_lines = lines[start+1:end]
sql = "\n".join(sql_lines) + "\n"

# 3) 按 CREATE TABLE 拆分
statements = re.split(r"(?=CREATE TABLE IF NOT EXISTS )", sql)
statements = [s for s in statements if s.strip()]
print(f"共 {len(statements)} 张表")

CORE = ("players", "inventory", "quests", "battle_state", "achievements", "stats",
        "reputation", "signin", "props_use", "fishing", "bestiary", "visited",
        "player_groups")
SOCIAL = ("world_event", "event_state", "market", "party", "guilds",
          "guild_members", "pets", "pet_dex", "feedback")
PROF = ("professions",)

def group(name, members):
    parts = []
    for s in statements:
        m = re.match(r"CREATE TABLE IF NOT EXISTS (\w+)", s)
        if m and m.group(1) in members:
            parts.append(s.rstrip())
    return "".join(parts)

g_core = group("CORE", CORE)
g_social = group("SOCIAL", SOCIAL)
g_prof = group("PROF", PROF)

# 4) 生成常量块（插到 init_db 之前）
const_block = (
    "# ================= v103.5 B1-1 建表 SQL 按域拆分 =================\n"
    "# 原巨型 executescript（317 行 init_db）拆为 3 个常量，init_db 依次执行，行为零变化。\n"
    "# 加新表：按域加入对应常量（或新建常量），并在 init_db 补 executescript。\n"
    "_SQL_CORE_TABLES = \"\"\"\n" + g_core + "\"\"\"\n\n"
    "_SQL_SOCIAL_TABLES = \"\"\"\n" + g_social + "\"\"\"\n\n"
    "_SQL_PROF_TABLES = \"\"\"\n" + g_prof + "\"\"\"\n\n\n"
)

# 5) 新 init_db 头部（替换 executescript 段）
new_head = (
    "def init_db():\n"
    "    \"\"\"建表(全局 qq_id 主键)\"\"\"\n"
    "    with _lock:\n"
    "        conn = _connect()\n"
    "        try:\n"
    "            conn.executescript(_SQL_CORE_TABLES)\n"
    "            conn.executescript(_SQL_SOCIAL_TABLES)\n"
    "            conn.executescript(_SQL_PROF_TABLES)\n"
    "            _ensure_legacy_columns(conn)\n"
    "            conn.commit()\n"
    "        finally:\n"
    "            conn.close()\n"
)

# 6) ALTER 段（end+1 到 conn.commit() 前）提取为 _ensure_legacy_columns
alter_start = end + 1  # 250 行（0-indexed 249）
# 找 "conn.commit()" 行
commit_i = None
for i in range(alter_start, len(lines)):
    if lines[i].strip() == "conn.commit()":
        commit_i = i
        break
assert commit_i is not None
alter_body = lines[alter_start:commit_i]  # 不含 commit 行
# 去掉 12 空格缩进 → 函数体 4 空格（原 init_db 内 try 块是 12 空格，_ensure 函数体 4 空格）
dedented = []
for ln in alter_body:
    if ln.startswith("            "):  # 12 空格
        dedented.append(ln[8:])        # 去 8 留 4
    elif ln.strip() == "":
        dedented.append("")
    else:
        dedented.append(ln[8:] if ln.startswith("        ") else ln)
alter_fn = (
    "\n\ndef _ensure_legacy_columns(conn):\n"
    "    \"\"\"v103.5 B1-1：老库 ALTER 补列自愈（原 init_db 尾部，拆出便于维护）\"\"\"\n"
    + "\n".join(dedented) + "\n"
)

# 7) 组装新文件：头部(到 def init_db 之前) + 常量块 + 新 init_db + 尾部(commit 之后)
def_i = None
for i in range(0, start):
    if lines[i].startswith("def init_db()"):
        def_i = i
        break
assert def_i is not None, "找不到 def init_db"
head = lines[:def_i]  # 不含 def init_db 行（new_head 完整提供新定义）
# 尾部 finally/close 由 new_head 完整提供，丢弃旧收尾行（commit_i+1 之后）
new_src = "\n".join(head) + "\n" + const_block + new_head + alter_fn + "\n"

io.open(PATH + ".new", "w", encoding="utf-8", newline="").write(new_src)
print(f"新文件已生成: {PATH}.new")
print(f"  原 {len(lines)} 行 → 新 {len(new_src.splitlines())} 行")
print("校验: 三常量表数 =", len(re.findall(r"CREATE TABLE", g_core)),
      len(re.findall(r"CREATE TABLE", g_social)), len(re.findall(r"CREATE TABLE", g_prof)))
