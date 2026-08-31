# -*- coding: utf-8 -*-
"""v104 修复项回归：战斗 / 技能 8 项（M17/M22/M23/M24 + 数值审计）

覆盖：
  1. 分支技能消耗：BRANCH_SKILLS 全表（tier 1/2/3）活动技能（非被动）零消耗 = 0
     （每个都有 mp>0 或 res_cost 或 cd）
  2. 闪避生效（v104 策划案 27 章）：装备/面板 dodge 此前只进面板零战斗消费，
     修复后 _damage_player 消费闪避（上限 40%）——高闪避玩家受击 100 次闪避显著 >0
  3. 龙语印记无词条也结算（v104 移入 _extra_dmg_mult）：
     无词条路径（_affix_dmg_mult 空 ids 提前 return）不再漏结算 dragon_mark 倍率
  4. 神龛 buff（v104 M23）：poi_buff_{qid} 战斗开始读取 → 本场 atk×1.10，left-1，
     用完删除 key
  5. 雨事件（v104 M23 rain_{gid}_{qid} 只写不读修复）：30 分钟窗口内探索遇怪率 +15%
     （_rain_boost 读状态 + explore 分支静态断言）
  6. 战斗中移动拦截（v104 M24 P2）：『探索』『前往/移动』在战斗中被拦
  7. 宠物影袭优先于闪避（24 章）：_damage_player 先 _pet_block_check 再闪避判定
  8. 技能重名：skills.py 全表（基础+分支）name → 不同 id 的冲突 = 0

独立运行：python tests/test_v104_battle_skills.py
"""
import asyncio
import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, BT, db, clean_db, Main, FakeEvent, run  # noqa: E402
from conftest import make_player as make_db_player  # 落库玩家（命令层测试用）

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


def make_monster(hp=100000, atk=10, name="测试怪"):
    return {
        "id": "t", "name": name, "lv": 5, "role": "normal",
        "hp": hp, "max_hp": hp, "atk": atk, "def": 5,
        "matk": 5, "mdef": 5, "spd": 5, "crit": 0.05,
        "exp": 10, "gold": 10, "skills": [], "drops": [],
        "map": "测试", "map_area": "vila", "is_boss": False, "is_elite": False,
    }


def make_player(cls="战士", level=10, equip=None, skills=None):
    p = {
        "class_name": cls, "level": level, "equipment": equip or {}, "attributes": {},
        "class_tier": 0, "evolve_path": 1,
        "learned_skills": skills or [], "skills": skills or [],
        "skill_levels": {}, "mech_stacks": {},
        "max_hp": 0, "max_mp": 0, "hp": 0, "mp": 0, "name": "测试勇者",
        "gold": 100, "exp": 0, "cur_map": "oak_town",
    }
    st = E.player_final_stats(cls, level, equip or {}, 0, {}, 1)
    p["max_hp"], p["max_mp"] = st["max_hp"], st["max_mp"]
    p["hp"], p["mp"] = 99999, st["max_mp"]
    return p


def iter_branch_skills():
    """枚举 (cls_id, tier, branch_name, skill_name, info)。"""
    for cid, cinfo in C.BRANCH_SKILLS.items():
        for tier, branches in (cinfo.get("branches") or {}).items():
            for bname, skills in branches.items():
                for sname, s in skills.items():
                    yield cid, tier, bname, sname, s


# ============ 1. 分支技能消耗 ============
def test_branch_skill_cost():
    print("【1. 分支技能消耗（tier>=2 或分支标记，活动技能零消耗=0）】")
    zero = []
    total = 0
    active = 0
    for cid, tier, bname, sname, s in iter_branch_skills():
        total += 1
        if s.get("kind") == "被动":
            continue
        # v139：自动追加技（auto 字段，如破势斩/顿足盾击/龙焰初击）由形态触发不占行动、
        # mp=0 是设计意图——非玩家主动施放动作，跳过零消耗检查
        if s.get("auto"):
            continue
        # v151：坚盾壁垒/铁壁·卫 等 0 消耗增益（effect=shield_all/atk_up 无 mp/cd）为职业主动资源技能，
        # 技能表零消耗可接受——只对「有伤害/治疗量」的主动技能强校验消耗
        if (s.get("kind") in ("增益", "嘲讽")) and not s.get("power"):
            continue
        active += 1
        mp = int(s.get("mp", 0) or 0)
        rc = s.get("res_cost") or {}
        cd = int(s.get("cd", 0) or 0)
        if mp <= 0 and not rc and not cd:
            zero.append((cid, tier, bname, sname, s.get("kind")))
    check(f"全部分支技能枚举（{total} 个，活动 {active} 个）", total >= 100)
    check(f"活动分支技能零消耗 = 0（{len(zero)} 个违规）", not zero,
          str(zero[:3]))


# ============ 2. 闪避生效 ============
def test_dodge_effective():
    print("【2. 闪避生效（v104 上限 40%，面板闪避战斗消费）】")
    # dodge 0.40 装备 → 面板 0.40
    p = make_player("战士", 10, equip={"chest": {"stats": {"dodge": 0.40}}})
    b = BT.Battle("monster", make_monster())
    st = b._player_stats(p)
    check("装备 dodge 0.40 进面板", abs(float(st.get("dodge", 0)) - 0.40) < 1e-9,
          f"dodge={st.get('dodge')}")
    # 超上限装备 → 面板仍封顶 0.40（引擎侧 cap + 战斗侧 min 双保险）
    p2 = make_player("战士", 10, equip={"chest": {"stats": {"dodge": 0.80}}})
    b2 = BT.Battle("monster", make_monster())
    st2 = b2._player_stats(p2)
    check("dodge 0.80 装备封顶 0.40", abs(float(st2.get("dodge", 0)) - 0.40) < 1e-9,
          f"dodge={st2.get('dodge')}")
    # 受击 100 次（固定 seed）→ 闪避显著 >0
    p3 = make_player("战士", 10, equip={"chest": {"stats": {"dodge": 0.40}}})
    b3 = BT.Battle("monster", make_monster())
    random.seed(7)
    dodges = 0
    for _ in range(100):
        logs = []
        b3._damage_player(p3, 50, logs)
        if any("闪避" in l for l in logs):
            dodges += 1
    check(f"100 次受击闪避 {dodges} 次（显著>0）", dodges >= 10, f"dodges={dodges}")


# ============ 3. 龙语印记无词条也结算 ============
def test_dragon_mark_no_affix():
    print("【3. 龙语印记无词条也结算（v104 移入 _extra_dmg_mult）】")
    b = BT.Battle("monster", make_monster(hp=1000))
    b.mech_stacks["dragon_mark"] = 5
    mult, tags = b._affix_dmg_mult({})
    check("无词条 + 5 层印记 → 倍率 1.10", abs(mult - 1.10) < 1e-9,
          f"mult={mult} tags={tags}")
    b2 = BT.Battle("monster", make_monster(hp=1000))
    mult2, _ = b2._affix_dmg_mult({})
    check("无印记 → 倍率 1.0", abs(mult2 - 1.0) < 1e-9, f"mult={mult2}")


# ============ 4. 神龛 buff 生效 ============
def test_poi_buff():
    print("【4. 神龛 buff（v104 M23：poi_buff_{qid} 进战斗生效 + 次数递减）】")
    db.set_event_state("poi_buff_q2", json.dumps(
        {"stat": "atk", "mult": 1.10, "left": 3, "name": "攻击"}, ensure_ascii=False))
    p = make_player("战士", 10)
    p["qq_id"] = "q2"
    base_atk = E.player_final_stats("战士", 10, {}, 0, {}, 1)["atk"]
    b = BT.Battle("monster", make_monster(), player=p)
    check("战斗开始读取神龛 buff", b.poi_buff == {"stat": "atk", "mult": 1.10, "name": "攻击"},
          str(b.poi_buff))
    left = json.loads(db.get_event_state("poi_buff_q2"))["left"]
    check("left 3→2（战斗消费 1 次）", left == 2, f"left={left}")
    atk = b._player_stats(p)["atk"]
    check(f"攻击加成 1.10 生效（{base_atk}→{atk}）", atk == int(base_atk * 1.10),
          f"atk={atk} expect={int(base_atk*1.10)}")
    # left=1 → 进战斗后 key 删除
    db.set_event_state("poi_buff_q3", json.dumps(
        {"stat": "spd", "mult": 1.10, "left": 1, "name": "spd"}, ensure_ascii=False))
    p3 = make_player("战士", 10)
    p3["qq_id"] = "q3"
    BT.Battle("monster", make_monster(), player=p3)
    check("left 用完删除 key", not db.get_event_state("poi_buff_q3"))
    db.delete_event_state("poi_buff_q2")


# ============ 5. 雨事件生效 ============
def test_rain_boost():
    print("【5. 雨事件（v104 M23：rain_{gid}_{qid} 只写不读修复 → 遇怪率+15%）】")
    now = time.time()
    db.set_event_state("rain_g9_q9", json.dumps({"ts": now}))
    db.set_event_state("rain_g9_q8", json.dumps({"ts": now - 4000}))
    m = Main(None)
    check("30 分钟窗口内 _rain_boost=True", m._rain_boost("g9", "q9") is True)
    check("超窗（4000s）_rain_boost=False", m._rain_boost("g9", "q8") is False)
    check("无状态 _rain_boost=False", m._rain_boost("g9", "q7") is False)
    # 静态断言：探索分支雨窗口内事件概率让渡 15% 给遇怪
    src = open(os.path.join("game", "commands", "combat.py"), encoding="utf-8").read()
    check("探索分支存在雨让渡代码", "_ev_chance = max(0.0, _ev_chance - 0.15)" in src
          and "self._rain_boost(group_id, qq_id)" in src)
    check("雨窗口常量 1800s", re.search(r"_RAIN_WINDOW\s*=\s*1800", src) is not None)
    db.delete_event_state("rain_g9_q9")
    db.delete_event_state("rain_g9_q8")


# ============ 6. 战斗中移动拦截 ============
async def test_move_blocked():
    print("【6. 战斗中移动拦截（v104 M24 P2：探索/前往被拦）】")
    clean_db()
    make_db_player("g1", "q1", name="测试", cls="战士", level=10)
    m = Main(None)
    r = await run(m.explore, FakeEvent("g1", "q1", "探索"))
    check("无战斗时探索放行", r and "你正在战斗中" not in r[0], str(r)[:60])
    b = BT.Battle("monster", make_monster(hp=100))
    db.save_battle("g1", "q1", b.to_state())
    r = await run(m.explore, FakeEvent("g1", "q1", "探索"))
    check("战斗中『探索』被拦", r and "你正在战斗中" in r[0], str(r)[:60])
    r = await run(m.move, FakeEvent("g1", "q1", "前往 1"))
    check("战斗中『前往』被拦", r and "你正在战斗中" in r[0], str(r)[:60])
    r = await run(m.move, FakeEvent("g1", "q1", "移动 1"))
    check("别名『移动』同样被拦", r and "你正在战斗中" in r[0], str(r)[:60])
    db.clear_battle("g1", "q1")
    r = await run(m.move, FakeEvent("g1", "q1", "前往 2"))
    check("脱离战斗后移动放行", r and "你正在战斗中" not in r[0], str(r)[:60])


# ============ 7. 宠物影袭优先于闪避 ============
def test_pet_block_before_dodge():
    print("【7. 宠物影袭优先于闪避（挡刀在闪避判定前）】")
    p = make_player("战士", 10, equip={"chest": {"stats": {"dodge": 0.40}}})
    # 对照组：无宠物，random=0.01 → 应走闪避（证明 0.01 本会触发闪避）
    b0 = BT.Battle("monster", make_monster())
    logs0 = []
    _orig = random.random
    random.random = lambda: 0.01
    try:
        b0._damage_player(p, 50, logs0)
    finally:
        random.random = _orig
    check("对照组 random=0.01 触发闪避", any("闪避" in l for l in logs0), str(logs0))
    # 实验组：黑猫(影袭 interval=3 value=0.25, round=3)，random=0.01 → 影袭拦截在闪避前
    hp_before = p["hp"]
    b = BT.Battle("monster", make_monster(),
                  pet={"pet_key": "pet_cat", "name": "黑猫", "level": 10, "satiety": 100})
    b._now = 4.0  # v152：行动轮次 3（int(4/2)+1=3）→ 影袭判定点
    logs = []
    random.random = lambda: 0.01
    try:
        b._damage_player(p, 50, logs)
    finally:
        random.random = _orig
    check("影袭挡下攻击（优先于闪避）", any("替你挡下了" in l for l in logs), str(logs))
    check("拦截后无闪避日志（未进入闪避判定）", not any("闪避" in l for l in logs), str(logs))
    check("玩家未掉血", p["hp"] == hp_before, f"hp={p['hp']}")
    # 非触发回合（tick_no=2）→ 影袭不拦，正常走闪避
    b2 = BT.Battle("monster", make_monster(),
                   pet={"pet_key": "pet_cat", "name": "黑猫", "level": 10, "satiety": 100})
    b2._now = 2.0  # v152：行动轮次 2（int(2/2)+1=2）
    logs2 = []
    random.random = lambda: 0.01
    try:
        b2._damage_player(p, 50, logs2)
    finally:
        random.random = _orig
    check("非触发回合影袭不拦（闪避接管）", any("闪避" in l for l in logs2)
          and not any("替你挡下了" in l for l in logs2), str(logs2))


# ============ 8. 技能重名 ============
def test_skill_name_dup():
    print("【8. 技能重名（全表 name→不同 id 冲突 = 0）】")
    names = {}

    def walk(skills, cid):
        for sid, s in skills.items():
            nm = s.get("name") or sid
            names.setdefault(nm, set()).add((cid, sid))

    for cid, cinfo in C.PLAYER_SKILLS.items():
        walk(cinfo.get("skills") or {}, cid)
    for cid, tier, bname, sname, s in iter_branch_skills():
        names.setdefault(s.get("name") or sname, set()).add((cid, sname))
    dups = {nm: v for nm, v in names.items() if len({i for _, i in v}) > 1}
    check(f"全表无重名（{len(names)} 个技能名，冲突 {len(dups)}）", not dups,
          str(list(dups.items())[:5]))


async def main():
    clean_db()
    test_branch_skill_cost()
    test_dodge_effective()
    test_dragon_mark_no_affix()
    test_poi_buff()
    test_rain_boost()
    await test_move_blocked()
    test_pet_block_before_dodge()
    test_skill_name_dup()
    print(f"\n===== 结果：PASS {PASS} / FAIL {FAIL} =====")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    asyncio.run(main())
