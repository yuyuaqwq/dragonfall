# -*- coding: utf-8 -*-
"""命令解析域：正则互斥 / 免空格 / 序号 / 分页 / 命令矩阵（源自 test_regex/test_nospace/test_move_num/v81/v84/v86/v87/v91）

验证：
  1. 命令矩阵互斥性：任意两个 handler 不得同时命中不同命令（防双触发）
  2. 免空格触发：『背包材料』『宠物改名小黑』『公会签到5』等
  3. 序号分流：『物品详情1』只走物品详情，『背包2』只走背包
  4. 翻页：『列表2』等
  5. 移动序号：『移动 2』按邻居列表
"""
import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


# ---------- 从 commands/*.py 提取 @filter.regex ----------
SRC_ALL = []
for _p in glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game", "commands", "*.py")):
    if _p.endswith("__init__.py"):
        continue
    with open(_p, encoding="utf-8") as _f:
        SRC_ALL.append(_f.read())
src = "\n".join(SRC_ALL)
handler_pat = re.compile(r'@filter\.regex\(r"([^"]+)"\)\s*\n\s*async def (\w+)')
handlers = [(m.group(1), m.group(2)) for m in handler_pat.finditer(src)]
comps = [re.compile(p) for p, _ in handlers]
CMD_PREFIX = r"^(?:\[At:\d+\]\s*)?"


def body(pat):
    p = pat
    if p.startswith("^"):
        p = p[1:]
    if p.startswith("(?:\\[At:\\d+\\]\\s*)?"):
        p = p[len("(?:\\[At:\\d+\\]\\s*)?"):]
    elif p.startswith(r"(?:\[At:\d+\]\s*)?"):
        p = p[len(r"(?:\[At:\d+\]\s*)?"):]
    return p


def tokens(pat):
    b = body(pat)
    out = []
    head = re.match(r"[\u4e00-\u9fff]+|[A-Za-z]{3,}", b)
    if head:
        out.append(head.group(0))
    for m in re.finditer(r"\(\?:([^()]*)\)", b):
        for part in m.group(1).split("|"):
            part = part.strip()
            # 过滤正则语法噪声（\s* 空匹配、.* 通配、[\s\S]* 换行通配、纯符号）
            if not part or part in (r"\s*", r"\s+", r".*", r".+", r"$", r"[\s\S]*", r"\S*"):
                continue
            if re.fullmatch(r"[\s.*+?$^|()\\\[\]]+", part):
                continue
            if len(part) >= 2:
                out.append(part)
    return out


async def main():
    print("【命令矩阵：互斥性】")    # 提取所有命令词
    all_tokens = {}
    for pat, name in handlers:
        for t in tokens(pat):
            all_tokens.setdefault(t, set()).add(name)
    # 检查：同一命令词命中多个 handler 且不是同一 handler 的别名
    conflicts = []
    for t, names in all_tokens.items():
        if len(names) > 1:
            conflicts.append((t, sorted(names)))
    check("命令词无跨 handler 冲突", not conflicts, str(conflicts[:5]))

    print("【命令矩阵：历史 bug 回归】")
    # 物品详情1 只走物品详情（不抢背包）
    cases = [
        ("物品详情1", "item_detail"),
        ("技能详情1", "skill_detail"),
        ("背包2", "inventory"),
        ("宠物改名小黑", "pet_rename"),
        ("公会签到5", "guild_sign"),
        ("公会任务", "guild_task"),
        ("技能学习怒吼", "skill_learn"),
        ("背包材料", "inventory"),      # v42：无空格筛选走 inventory（内部解析类型）
        ("背包 材料", "inventory"),
        ("背包筛选 材料", "bag_filter"),  # 独立筛选指令
        ("筛选", "bag_filter"),
        ("背包", "inventory"),
    ]
    for text, expect in cases:
        hit = []
        for (pat, name), c in zip(handlers, comps):
            if c.search(text):
                hit.append(name)
        check(f"『{text}』→ {expect}（命中 {hit}）", expect in hit and len(hit) == 1, str(hit))

    print("【命令矩阵：随机 fuzz】")
    random.seed(42)
    fuzz_hits = 0
    for i in range(200):
        # 随机中文命令词组合
        w = random.choice(["背包", "技能", "物品", "锻造", "公会", "攻击", "探索", "移动", "宠物", "属性", "任务", "地图", "垂钓"])
        n = random.choice(["", "1", "2", "材料", "详情", "学习", "升级", " 2", "5"])
        text = w + n
        hit = [name for (_, name), c in zip(handlers, comps) if c.search(text)]
        if len(hit) > 1:
            fuzz_hits += 1
    check("200 次 fuzz 无双触发", fuzz_hits == 0, f"{fuzz_hits} 次多命中")

    print("【免空格：移动序号】")
    # 移动 2：从 vila_square 的邻居（vila_street, ...）取第 2 个
    from conftest import db as _db, Main as _Main
    _db.init_db()
    m = _Main(None)
    ev = FakeEvent("g1", "m1", "注册 战士 移动者")
    await run(m.register, ev)
    _db.update_player("g1", "m1", cur_map="vila_square")
    ev = FakeEvent("g1", "m1", "移动 2")
    results = await run(m.move, ev)
    out = results[-1] if results else ""
    check("移动序号有返回", len(out) > 5, out[:100])

    print("【分页：列表序号】")
    # 背包翻页（无物品时提示空）
    out = ""
    results = await run(m.inventory, FakeEvent("g1", "m1", "背包 2"))
    out = results[-1] if results else ""
    check("背包翻页有返回", len(out) > 3, out[:100])

    print("【正则：At 前缀】")
    hit = [name for (_, name), c in zip(handlers, comps) if c.search("[At:123] 背包")]
    check("At+背包 → inventory", "inventory" in hit, str(hit))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio, random
    sys.exit(0 if asyncio.run(main()) else 1)
