# -*- coding: utf-8 -*-
"""v138.2 异常体系五律测试（docs/COMBAT_ENRICH_v138.md §二）

覆盖：
1. 律一 阈值递增：触发后 threshold ×1.3（封顶 ×3.0），防无限复读
2. 律二 每场上限+饱和：trigger_count 达 DOT_MAX_TRIGGER[k] 置饱和；
   饱和后控制类不再结算、伤害类照常结算
3. 律三 跨阶段保留：_preserve_debuffs 保留一半层数 + 阈值 +15%
4. 律四 异常直伤独立结算：corros 真伤绕过 _enemy_mitigate 的 def 削减（仍走免疫检查）
5. 律五 饱和阈值收敛：饱和后 saturate_mult 逐次 ×0.8
6. 兼容：旧 debuffs 无 threshold/trigger_count/saturate_mult 字段 → 默认不崩
7. 常量导出：core/__init__ 与 data/battle_config 可导入

随机种子固定（本测试无随机依赖，仍固定以防未来引入）。
"""
import sys, os, random
random.seed(20260829)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.data.battle_config import DOT_DEFS
from game.core.constants import (
    DOT_THRESHOLD_MULT, DOT_THRESHOLD_CAP, DOT_MAX_TRIGGER,
    DOT_PRESERVE_PCT, DOT_PRESERVE_THRESHOLD_BONUS, DOT_SATURATE_MULT,
)
from game.core import constants as CORE

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def mk_player(atk=100, matk=80):
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": {}, "skills": [], "skill_levels": {}, "learned_skills": []}

def mk_enemy(hp=1000, **kw):
    e = {"name": "靶子", "lv": 10, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}}
    e.update(kw)
    return e

def tick(b, player, force=True):
    b._player_stats = lambda pl: {"atk": 100, "matk": 80, "def": 50, "mdef": 50,
                                  "spd": 10, "crit": 0.05, "max_hp": 9999, "max_mp": 999}
    b._dot_pending = True
    logs = []
    b._tick_dots(player, logs, force=force)
    return logs

def test_constants():
    print("【0. 常量与导出】")
    check("DOT_THRESHOLD_MULT=1.3", abs(DOT_THRESHOLD_MULT - 1.3) < 1e-9)
    check("DOT_THRESHOLD_CAP=3.0", abs(DOT_THRESHOLD_CAP - 3.0) < 1e-9)
    check("DOT_MAX_TRIGGER 伤害类 5 次", DOT_MAX_TRIGGER["poison"] == 5
          and DOT_MAX_TRIGGER["burn"] == 5 and DOT_MAX_TRIGGER["bleed"] == 5
          and DOT_MAX_TRIGGER["corros"] == 5, str(DOT_MAX_TRIGGER))
    check("DOT_MAX_TRIGGER 控制类 2 次", DOT_MAX_TRIGGER["freeze"] == 2
          and DOT_MAX_TRIGGER["stun"] == 2 and DOT_MAX_TRIGGER["sleep"] == 2,
          str(DOT_MAX_TRIGGER))
    check("DOT_PRESERVE_PCT=0.5", abs(DOT_PRESERVE_PCT - 0.5) < 1e-9)
    check("DOT_SATURATE_MULT=0.8", abs(DOT_SATURATE_MULT - 0.8) < 1e-9)
    check("core/__init__ 导出（v103.3 教训）", hasattr(CORE, "DOT_MAX_TRIGGER")
          and CORE.DOT_MAX_TRIGGER is DOT_MAX_TRIGGER)
    check("DOT_DEFS 新增 corros true_dmg", DOT_DEFS["corros"].get("true_dmg") is True,
          str(DOT_DEFS.get("corros")))
    check("旧三系无 true_dmg（默认 False）", all(not v.get("true_dmg", False)
          for k, v in DOT_DEFS.items() if k != "corros"), str(DOT_DEFS))

def test_threshold():
    print("【1. 律一 阈值递增】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=100000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
    tick(b, p)
    d = b.enemy["debuffs"]["poison"]
    check("首触后 threshold = 1.3", abs(d.get("threshold", 0) - 1.3) < 1e-9, str(d))
    tick(b, p)
    d = b.enemy["debuffs"]["poison"]
    check("二触后 threshold = 1.69", abs(d.get("threshold", 0) - 1.69) < 1e-9, str(d))
    # 连续触发：3 层每次只触发一次；第 2 次 tick 后 n=1，第 3 次 tick 后消散。
    # 用大层数续命到封顶：1.3/1.69/2.197/2.8561/3.0（封顶）——9 层可触发 5 次
    b2 = BT.Battle("monster", mk_enemy(hp=100000))
    b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 9, "mult": 1.0}
    for _ in range(5):
        tick(b2, p)
    d2 = b2.enemy["debuffs"]["poison"]
    check("多触封顶 3.0（9 层连触发 5 次）", d2.get("n", 0) > 0
          and abs(d2.get("threshold", 0) - 3.0) < 1e-9, str(d2))

def test_max_trigger_and_saturation():
    print("【2. 律二 每场上限+饱和】")
    p = mk_player()
    # 伤害类：达上限后照常结算（Boss 不被锁输出）
    b = BT.Battle("monster", mk_enemy(hp=100000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 10, "mult": 1.0}
    for i in range(6):
        tick(b, p)
        d = b.enemy["debuffs"]["poison"]
        if i < 5:
            check(f"poison 第 {i+1} 次触发 count={i+1}", d.get("trigger_count") == i + 1, str(d))
        else:
            check("第 6 次仍结算（伤害类饱和不清除）", d.get("saturated") is True, str(d))
    check("伤害类饱和后 trigger_count 达上限", b.enemy["debuffs"]["poison"]["trigger_count"] >= 5,
          str(b.enemy["debuffs"]["poison"]))
    # 控制类：饱和后不再结算（冻结/眩晕/睡眠），但伤害类照常
    # 控制效果存于 e.buffs（eb），由 _enemy_turn 消费；_tick_dots 按 eb 的
    # {k}_trigger_count 做饱和判定（达上限的控制在 eb 中直接移除，从根源不再生效）
    b2 = BT.Battle("monster", mk_enemy(hp=100000))
    b2.enemy.setdefault("buffs", {})["stun"] = 1
    b2.enemy["buffs"]["stun_trigger_count"] = 1  # 已触发 1 次（<上限 2）
    tick(b2, p)
    check("stun 未饱和时 eb 保留（第 1 次）", b2.enemy["buffs"].get("stun") == 1,
          str(b2.enemy["buffs"]))
    b2.enemy["buffs"]["stun_trigger_count"] = 2  # 达上限 2
    tick(b2, p)
    check("stun 饱和后 eb 控制被移除（不再生效）", "stun" not in b2.enemy["buffs"],
          str(b2.enemy["buffs"]))
    # freeze/sleep 饱和
    for k in ("freeze", "sleep"):
        b3 = BT.Battle("monster", mk_enemy(hp=100000))
        b3.enemy.setdefault("buffs", {})[k] = 1
        b3.enemy["buffs"][f"{k}_trigger_count"] = 2  # 达上限
        tick(b3, p)
        check(f"{k} 饱和后 eb 控制被移除", k not in b3.enemy["buffs"],
              str(b3.enemy["buffs"]))

def test_preserve():
    print("【3. 律三 跨阶段保留】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=100000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 5, "mult": 1.0, "threshold": 1.69}
    b.enemy["debuffs"]["burn"] = {"n": 3, "mult": 1.0, "threshold": 0.0}
    b.enemy["debuffs"]["mark"] = {"n": 2, "mult": 1.0}  # 标记不保留
    logs = []
    b._preserve_debuffs(logs)
    deb = b.enemy["debuffs"]
    check("poison 5 层 → 保留 2 层（50% 向下取整）", deb["poison"]["n"] == 2, str(deb["poison"]))
    check("burn 3 层 → 保留 1 层（max(1, int(1.5))）", deb["burn"]["n"] == 1, str(deb["burn"]))
    check("阈值 +15%：1.69→1.9435", abs(deb["poison"].get("threshold", 0) - 1.9435) < 1e-9,
          str(deb["poison"]))
    check("无阈值字段不崩（默认 0 保留）", "threshold" not in deb["burn"] or deb["burn"].get("threshold", 0) == 0.0,
          str(deb["burn"]))
    check("标记不保留（mark 非异常积蓄，跨阶段清除）", "mark" not in deb,
          str(deb.keys()))
    check("保留日志", any("保留一半层数" in l for l in logs), str(logs))
    # 阈值封顶
    b2 = BT.Battle("monster", mk_enemy(hp=100000))
    b2.enemy.setdefault("debuffs", {})["bleed"] = {"n": 4, "mult": 1.0, "threshold": 2.9}
    b2._preserve_debuffs([])
    check("阈值 +15% 封顶 3.0", abs(b2.enemy["debuffs"]["bleed"]["threshold"] - 3.0) < 1e-9,
          str(b2.enemy["debuffs"]["bleed"]))

def test_true_dmg():
    print("【4. 律四 异常直伤独立结算】")
    p = mk_player(atk=100, matk=80)
    # 腐蚀 1 层（v156 分类重构后）：atk×0.3 + matk×0.2 + max_hp×1% = 30+16+10 = 56
    # 真伤只豁免防御削减（def/mdef），不豁免目标异常抗性（dot_res 0.9 仍生效 → 56×0.1=5.6→5）
    # 注：def/mdef 是保留字，用 **{"def": ...} 解包传参（同 test_dot_refactor.py 口径）
    b = BT.Battle("monster", mk_enemy(hp=1000, **{"def": 1000000, "mdef": 1000000, "dot_res": 0.9}))
    b.enemy.setdefault("debuffs", {})["corros"] = {"n": 1, "mult": 1.0}
    tick(b, p)
    check("腐蚀真伤绕过 def/mdef：56×0.1=5", 1000 - b.enemy["hp"] == 5,
          f"dmg={1000 - b.enemy['hp']}")
    # 对照：同配置毒被 0.9 总抗削到 6 点（毒还额外吃 def/mdef？不，毒是 magi 段走 _enemy_mitigate）——
    # 关键差异：腐蚀不吃 def/mdef（真伤），毒吃 mdef（_enemy_mitigate 削减）
    b2 = BT.Battle("monster", mk_enemy(hp=1000, **{"def": 1000000, "mdef": 1000000, "dot_res": 0.9}))
    b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 1, "mult": 1.0}
    tick(b2, p)
    check("同配置毒被防御+抗性双重压制（对照）", 1000 - b2.enemy["hp"] < 56,
          f"dmg={1000 - b2.enemy['hp']}")
    # 无 dot_res 时腐蚀全额 56（真伤不吃 def）
    b5 = BT.Battle("monster", mk_enemy(hp=1000, **{"def": 1000000, "mdef": 1000000}))
    b5.enemy.setdefault("debuffs", {})["corros"] = {"n": 1, "mult": 1.0}
    tick(b5, p)
    check("无抗性时腐蚀全额 56（真伤豁免 def）", 1000 - b5.enemy["hp"] == 56,
          f"dmg={1000 - b5.enemy['hp']}")
    # 免疫仍生效
    b3 = BT.Battle("monster", mk_enemy(hp=1000, immune_dots=["corros"]))
    b3.enemy.setdefault("debuffs", {})["corros"] = {"n": 3, "mult": 1.0}
    tick(b3, p)
    check("腐蚀仍走免疫检查", "corros" not in b3.enemy.get("debuffs", {}),
          str(b3.enemy.get("debuffs")))
    # 真伤护盾层仍吸收（不 -50%，护盾层吸收）——v110 真伤口径：
    # 真伤不被打折（dmg 全额），护盾层仅消耗盾值（500→444），hp 仍掉全额 56
    b4 = BT.Battle("monster", mk_enemy(hp=1000, mech="shield", boss_shield=500))
    b4.enemy.setdefault("debuffs", {})["corros"] = {"n": 1, "mult": 1.0}
    tick(b4, p)
    check("真伤护盾层消耗盾值且伤害全额穿透", 1000 - b4.enemy["hp"] == 56
          and b4.enemy["boss_shield"] == 444,
          f"hp={b4.enemy['hp']} shield={b4.enemy.get('boss_shield')}")

def test_saturate_conv():
    print("【5. 律五 饱和阈值收敛】")
    p = mk_player()
    # poison 每层（v156 分类重构后 flat 型）：100×0.8 = 80（不吃目标血）
    # 层数每回合 -1（DOT 固有机制），同层数下对比饱和收敛：
    # 饱和后 saturate_mult 乘区 = 0.8^t，同层数伤害 = 80×n×(0.8^t)
    b = BT.Battle("monster", mk_enemy(hp=100000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 8, "mult": 1.0}
    # 触发 5 次至饱和（trigger_count 1→5，第 5 次置位）
    for _ in range(4):
        tick(b, p)
    d = b.enemy["debuffs"]["poison"]
    check("第 4 次触发未饱和", not d.get("saturated"), str(d))
    hp0 = b.enemy["hp"]
    tick(b, p)  # 第 5 次：饱和置位，当次满伤（饱和前已结算）
    d = b.enemy["debuffs"]["poison"]
    check("饱和置位当次满伤（n=4×80=320）", hp0 - b.enemy["hp"] == 320,
          f"dmg={hp0 - b.enemy['hp']} n={d.get('n')}")
    check("置位后 saturate_mult=0.8（下次起收敛）", abs(d.get("saturate_mult", 0) - 0.8) < 1e-9,
          str(d))
    # 第 6 次：n=3，×0.8 → 80×3×0.8 = 192
    hp0 = b.enemy["hp"]
    tick(b, p)
    d = b.enemy["debuffs"]["poison"]
    check("饱和后同层伤害 ×0.8：80×3×0.8=192", hp0 - b.enemy["hp"] == 192,
          f"dmg={hp0 - b.enemy['hp']} n={d.get('n')}")
    check("saturate_mult 继续收敛 0.64", abs(d.get("saturate_mult", 0) - 0.64) < 1e-9, str(d))
    # 第 7 次：n=2，×0.64 → 80×2×0.64 = 102.4→102
    hp0 = b.enemy["hp"]
    tick(b, p)
    check("二次收敛 ×0.64：80×2×0.64=102", hp0 - b.enemy["hp"] == 102,
          f"dmg={hp0 - b.enemy['hp']}")
    # 对照：未饱和同层数（n=4）满伤 320（无收敛乘区）
    b2 = BT.Battle("monster", mk_enemy(hp=100000))
    b2.enemy.setdefault("debuffs", {})["poison"] = {"n": 4, "mult": 1.0}
    hp0 = b2.enemy["hp"]
    tick(b2, p)
    check("未饱和同层对照：n=4 满伤 320", hp0 - b2.enemy["hp"] == 320,
          f"dmg={hp0 - b2.enemy['hp']}")

def test_legacy_compat():
    print("【6. 兼容：旧字段缺省】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(hp=100000))
    b.enemy.setdefault("debuffs", {})["poison"] = {"n": 3, "mult": 1.0}
    tick(b, p)
    d = b.enemy["debuffs"]["poison"]
    check("旧结构自动补 threshold/trigger_count", d.get("threshold") == 1.3
          and d.get("trigger_count") == 1, str(d))
    check("saturate_mult 缺省不崩", d.get("saturate_mult", 1.0) == 1.0, str(d))
    # 旧字段不显式给 saturate_mult 时默认 1.0
    b2 = BT.Battle("monster", mk_enemy(hp=100000))
    b2.enemy.setdefault("debuffs", {})["burn"] = {"n": 3, "mult": 1.0}
    tick(b2, p)
    check("burn 旧结构兼容", b2.enemy["debuffs"]["burn"].get("trigger_count") == 1,
          str(b2.enemy["debuffs"]["burn"]))

if __name__ == "__main__":
    test_constants()
    test_threshold()
    test_max_trigger_and_saturation()
    test_preserve()
    test_true_dmg()
    test_saturate_conv()
    test_legacy_compat()
    print(f"\n结果: {passed} 通过, 0 失败")
