# -*- coding: utf-8 -*-
"""v103.3 B3 魔法数字抽常量：精确字符串替换 + 每处替换计数验证"""
import io, os, sys

GAME = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

# (文件, 旧串, 新串, 期望次数)
REPLACES = [
    # player.py
    (r"commands\player.py", "need_lv = {1: 30, 2: 60, 3: 90}.get(next_tier)",
     "need_lv = C.EVOLVE_LEVELS.get(next_tier)", 1),
    (r"commands\player.py", "lv = t * 30", "lv = C.EVOLVE_LEVELS[t]", 1),
    (r"commands\player.py", "owner[0]*30", "C.EVOLVE_LEVELS[owner[0]]", 1),
    (r"commands\player.py", "cost = {1: 500, 2: 2000, 3: 5000}.get(tier, 500)",
     "cost = C.EVOLVE_FEES.get(tier, 500)", 1),
    (r"commands\player.py", "cost = 500", "cost = C.RESET_SKILL_COST", 2),
    # world.py
    (r"commands\world.py", "need_lv = {1: 30, 2: 60, 3: 90}.get(next_tier)",
     "need_lv = C.EVOLVE_LEVELS.get(next_tier)", 1),
    # engine.py
    (r"engine.py", 'if player["level"] in (30,):',
     'if player["level"] == C.EVOLVE_LEVELS[1]:', 1),
    # battle.py
    (r"battle.py", 'player.get("max_mp", 50)', 'player.get("max_mp", C.DEFAULT_MAX_MP)', 2),
    # combat.py (commands)
    (r"commands\combat.py", 'player.get("max_mp", 50)', 'player.get("max_mp", C.DEFAULT_MAX_MP)', 1),
    (r"commands\combat.py", "time.time() - battle.get(\"updated_at\", 0) > 300",
     "time.time() - battle.get(\"updated_at\", 0) > C.PVP_TIMEOUT_SEC", 1),
    # instance.py (commands)
    (r"commands\instance.py", 'p.get("max_mp", 50)', 'p.get("max_mp", C.DEFAULT_MAX_MP)', 2),
    # social.py (commands)
    (r"commands\social.py", 'g["level"] * 300', 'g["level"] * C.GUILD_EXP_BASE', 1),
    # store/social.py
    (r"store\social.py", 'g["level"] * 300', 'g["level"] * C.GUILD_EXP_BASE', 2),
    # store/professions.py
    (r"store\professions.py", "lv * 20", "lv * C.PROF_EXP_BASE", 2),
    # economy.py (commands)
    (r"commands\economy.py", 'need = p["lv"] * 20', 'need = p["lv"] * C.PROF_EXP_BASE', 1),
]

ok = True
for rel, old, new, expect in REPLACES:
    path = os.path.join(GAME, rel)
    src = io.open(path, encoding="utf-8").read()
    n = src.count(old)
    if n != expect:
        print(f"❌ {rel}: 期望 {expect} 处，实际 {n} 处 —— 跳过")
        ok = False
        continue
    io.open(path, "w", encoding="utf-8", newline="").write(src.replace(old, new))
    print(f"✅ {rel}: 替换 {n} 处")

# store 层补 import C（players.py 先例：from .. import content as C）
for rel, anchor in [(r"store\social.py", "from .connection import _connect, _lock"),
                    (r"store\professions.py", "from .connection import _connect, _lock")]:
    path = os.path.join(GAME, rel)
    src = io.open(path, encoding="utf-8").read()
    if "import content as C" in src:
        print(f"⏭️  {rel}: 已有 C import")
        continue
    if src.count(anchor) == 1:
        src = src.replace(anchor, anchor + "\nfrom .. import content as C")
        io.open(path, "w", encoding="utf-8", newline="").write(src)
        print(f"✅ {rel}: 补 import C")
    else:
        print(f"❌ {rel}: 锚点不唯一（{src.count(anchor)} 处）")
        ok = False

sys.exit(0 if ok else 1)
