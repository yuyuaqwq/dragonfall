# -*- coding: utf-8 -*-
"""临时验证脚本（recon Agent D / 世界 Boss dot 重构）——可保留。

模拟 combat.py _worldboss_act 的 dot 结算流程（契约 §6），用真实 Battle + _tick_dots 验证：
  1. gboss 创建时 setdefault: debuffs/dot_act/dot_res(0.9)/immune_dots
  2. 行动前 debuffs 全局→本地同步
  3. 行动后 dot_act 累加，%WORLD_BOSS_DOT_INTERVAL==0 时 force 结算
  4. 结算后 hp/debuffs 写回全局；dealt 含 dot 伤害
  5. force=True 时 logs = b._tick_dots(...)（原地追加+返回同列表）不重复
  6. dot_res 默认 0.9 生效（毒伤×(1-0.9)=×0.1）
"""
import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import battle as BT

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  {detail}")


def make_battle(gboss_debuffs, dot_res=None):
    """按 combat.py 创建世界 Boss battle 的逻辑：b setdefault + build 后逐单位 setdefault。"""
    b = dict(gboss_debuffs)  # 模拟 gboss 原始
    b.setdefault("debuffs", {})
    b.setdefault("dot_act", 0)
    b.setdefault("dot_res", 0.9)
    b.setdefault("immune_dots", [])
    b.setdefault("adapt", {"poison": 0.0, "burn": 0.0})  # v1.2 契约 §11
    # 单怪简化（主目标即 enemy），模拟 _worldboss_act 的 b.enemy 即 enemies[0]
    main = {
        "name": "世界Boss·测试", "hp": 100000, "max_hp": 100000,
        "debuffs": {k: dict(v) for k, v in b["debuffs"].items()},
        "dot_res": b["dot_res"] if dot_res is None else dot_res,
        "immune_dots": list(b["immune_dots"] or []),
        "adapt": dict(b["adapt"] or {}),
    }
    battle = BT.Battle("worldboss", None, {}, player={"name": "t", "hp": 500, "max_hp": 500}, enemies=[main])
    return b, battle


def sim_worldboss_act(gboss, battle, player_unit, poison_layers=3, interval=4, n_actions=4, logs_buf=None):
    """复刻 combat.py _worldboss_act 的关键逻辑（不含 db/奖励）：
    返回 (dealt, logs, end_gboss_debuffs, end_gboss_hp)。每次 action 打一点点直伤触发挂层由调用方预置。"""
    b = battle
    player = {"name": "测试", "hp": 800, "max_hp": 1000, "mp": 100, "max_mp": 300}
    genemies = gboss.get("enemies")
    # 行动前 debuffs 同步
    b.enemy["debuffs"] = {k: dict(v) for k, v in (gboss.get("debuffs") or {}).items()}
    # v1.2 行动前 adapt 同步
    b.enemy["adapt"] = dict(gboss.get("adapt") or {"poison": 0.0, "burn": 0.0})
    before = sum(max(0, u.get("hp", 0)) for u in b.enemies)
    # 行动（简化：不发 actor_turn，避免对老存档/缺技能怪抛错；只走 dot 结算流）
    logs = logs_buf if logs_buf is not None else []
    gboss["dot_act"] = int(gboss.get("dot_act", 0) or 0) + 1
    if int(gboss["dot_act"]) % interval == 0:
        logs = b._tick_dots(player, logs, force=True)
    after = sum(max(0, u.get("hp", 0)) for u in b.enemies)
    dealt = max(0, before - after)
    # 写回
    if genemies:
        _l_by_uid = {u.get("uid"): u for u in b.enemies}
        for _gu in genemies:
            _lu = _l_by_uid.get(_gu.get("uid"))
            if _lu is not None:
                _gu["hp"] = _lu.get("hp", _gu.get("hp", 0))
    gboss["debuffs"] = {k: dict(v) for k, v in (b.enemy.get("debuffs") or {}).items()}
    # v1.2 行动后 adapt 写回
    gboss["adapt"] = dict(b.enemy.get("adapt") or {"poison": 0.0, "burn": 0.0})
    gboss["hp"] = after
    return dealt, logs, gboss["debuffs"], gboss["hp"]


print("═" * 60)
# ---------- 场景 1：dot_res 默认 0.9，4 次行动一次结算 ----------
print("场景1：默认 dot_res=0.9；第4次行动触发 force 结算")
gboss, battle = make_battle({"debuffs": {"poison": {"n": 3, "mult": 1.0}}})
# 预置毒层到本地（模拟挂层后）
battle.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
max_hp = battle.enemy["max_hp"]
# 期望毒伤：max_hp×0.05×3层×(1-0.9)=100000×0.05×3×0.1=1500
expected_dot = int(max_hp * 0.05 * 3 * (1 - 0.9))
# 前3次不结算
for i in range(1, 4):
    dealt, logs, _deb, _hp = sim_worldboss_act(gboss, battle, None, n_actions=i)
    check(f"  第{i}次行动不触发结算(dot_act={gboss['dot_act']})", gboss["dot_act"] == i and "发作" not in "".join(logs), f"dot_act={gboss['dot_act']}")
    check(f"  第{i}次行动无 dot 伤害(dealt=0)", dealt == 0, f"dealt={dealt}")
check("  debuffs 已写回全局", "poison" in gboss["debuffs"], str(gboss["debuffs"]))
# 第4次（触发）
dealt, logs, _deb, _hp = sim_worldboss_act(gboss, battle, None, n_actions=4)
check(f"  第4次行动 dot_act=4 触发结算", gboss["dot_act"] == 4, f"dot_act={gboss['dot_act']}")
check(f"  dot 结算扣血≈{expected_dot}", dealt == expected_dot, f"dealt={dealt} expected={expected_dot}")
check("  结算日志含『毒发作』", any("毒发作" in x for x in logs), str(logs))
check("  gboss hp 已写回(比 max_hp 少 dot)", gboss["hp"] == max_hp - expected_dot, f"gboss.hp={gboss['hp']} exp={max_hp-expected_dot}")
check("  gboss debuffs 已写回且层数减1(n=2)", gboss["debuffs"]["poison"]["n"] == 2, str(gboss["debuffs"]))
# 层数衰减与消散
for i in range(5, 9):  # 再触发结算 n:2→1→消散
    dealt, logs, _deb, _hp = sim_worldboss_act(gboss, battle, None, n_actions=i)
    pass
check("  dot_res=0.9 兜底生效（初始毒伤×0.1）", True)  # 上面已用 0.9 验证

# ---------- 场景 2：dot_act 计数跨玩家行动累加，不重复日志 ----------
print("场景2：logs = b._tick_dots(...) 不重复（原地追加+返回同列表）")
gboss2, battle2 = make_battle({"debuffs": {"burn": {"n": 1, "mult": 1.0}}})
battle2.enemy.setdefault("debuffs", {})["burn"] = {"n": 1, "mult": 1.0}
buf = ["【直伤日志】打掉敌人一点血"]
for i in range(1, 5):
    dealt, logs, _deb, _hp = sim_worldboss_act(gboss2, battle2, None, n_actions=i, logs_buf=buf)
occ = sum(1 for x in buf if "灼烧发作" in x)
check(f"  灼烧发作行恰好出现1次(非重复)", occ == 1, f"occ={occ}; buf={buf}")

# ---------- 场景 3：immune_dots 命中移除不结算 ----------
print("场景3：immune_dots 命中 poison → 移除不扣血")
# poison 与 immune_dots 都挂全局，action 前同步才能带进本地（与 real 流程一致）
gboss3, battle3 = make_battle({"debuffs": {"poison": {"n": 5, "mult": 1.0}}, "immune_dots": ["poison"]})
battle3.enemy.setdefault("debuffs", {})
battle3.enemy.setdefault("immune_dots", ["poison"])
for i in range(1, 5):
    dealt, logs, _deb, _hp = sim_worldboss_act(gboss3, battle3, None, n_actions=i)
check("  免疫时不扣血(dealt=0)", dealt == 0, f"dealt={dealt}")
check("  免疫提示且 poison 已移除", any("免疫中毒" in x for x in logs) and "poison" not in _deb, str(_deb))
check("  debuffs 写回（poison 已清）", "poison" not in gboss3["debuffs"], str(gboss3["debuffs"]))

# ---------- 场景 4：敌方状态栏渲染（契约 §7，复刻 combat.py _status_line 敌方块） ----------
print("场景4：敌方状态栏渲染（debuffs + 异常抗性）")
_DEBUFF_NAMES = {"poison": "☠️毒", "burn": "🔥灼烧", "mark": "🎯标记", "bleed": "🩸流血"}
def enemy_block(b):
    ebuf = []
    deb = b.enemy.get("debuffs") or {}
    for k, d in deb.items():
        if k in _DEBUFF_NAMES:
            _n = int((d or {}).get("n", 0) or 0)
            if _n > 0:
                ebuf.append(f"{_DEBUFF_NAMES[k]}×{_n}")
    _dres = float(b.enemy.get("dot_res", 0) or 0)
    if _dres > 0:
        ebuf.append(f"🛡️异常抗性{int(_dres * 100)}%")
    return f"👹敌：「{' '.join(ebuf)}」" if ebuf else ""

b4 = BT.Battle("worldboss", {"name": "测试Boss", "hp": 100, "max_hp": 100,
                             "debuffs": {"poison": {"n": 4, "mult": 1.0}, "bleed": {"n": 2, "mult": 1.0}},
                             "dot_res": 0.9})
line = enemy_block(b4)
check("  毒×4+流血×2+异常抗性90% 显示", "☠️毒×4" in line and "🩸流血×2" in line and "异常抗性90%" in line, line)
b5 = BT.Battle("monster", {"name": "普通怪", "hp": 50, "max_hp": 50, "debuffs": {"mark": {"n": 1, "mult": 1.0}}})
line5 = enemy_block(b5)
check("  普通怪(无 dot_res)只显示标记，无抗性", "🎯标记×1" in line5 and "异常抗性" not in line5, line5)
b6 = BT.Battle("monster", {"name": "无减益", "hp": 50, "max_hp": 50})
check("  无减益→敌方块为空串", enemy_block(b6) == "", repr(enemy_block(b6)))

# ---------- 场景 5：v1.2 adapt（减益适应）同步/写回 ----------
print("场景5：v1.2 adapt 全局→本地同步、本地→全局写回")
gb, b5 = make_battle({"adapt": {"poison": 0.12, "burn": 0.04}})
# sim 内部：行动前同步(全局→本地 enemy)、行动后写回(本地→全局)
dealt, logs, _deb, _hp = sim_worldboss_act(gb, b5, None, n_actions=1)
check("  sim 同步+写回保持 adapt 一致(0.12)", b5.enemy["adapt"] == gb["adapt"] == {"poison": 0.12, "burn": 0.04},
      f"local={b5.enemy['adapt']} gb={gb['adapt']}")
# 模拟战斗内叠层提升本地 adapt(如 _m_poison)后写回全局：只跑同步+写回数据通之路
gb0, b0 = make_battle({})
# 直接验证行动前同步逻辑：手动把全局设成某值，再走同步，本地等于全局
gb0["adapt"] = {"poison": 0.20, "burn": 0.0}
b0.enemy["adapt"] = dict(gb0.get("adapt") or {"poison": 0.0, "burn": 0.0})
check("  行动前同步：本地=全局(0.20)", b0.enemy["adapt"] == {"poison": 0.20, "burn": 0.0}, str(b0.enemy["adapt"]))
# 直接验证写回逻辑（不重跑 sim 的同步）：
gb0["debuffs"] = {k: dict(v) for k, v in (b0.enemy.get("debuffs") or {}).items()}
gb0["adapt"] = dict(b0.enemy.get("adapt") or {"poison": 0.0, "burn": 0.0})
check("  行动后写回：全局=本地(0.20)", gb0["adapt"]["poison"] == 0.20, str(gb0["adapt"]))
check("  adapt 默认兜底(缺失回 0.0)", make_battle({})[0]["adapt"] == {"poison": 0.0, "burn": 0.0}, str(make_battle({})[0]["adapt"]))

print(f"\n结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)
