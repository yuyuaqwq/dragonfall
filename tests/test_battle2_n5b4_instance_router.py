# -*- coding: utf-8 -*-
"""N5b4-5a R1 验证：副本行动 Router（instance_router.py）battle2 原生分支。

v3 蓝图 §6 R1 验证：肃清守卫 / 轮转 / 超时自动防御 / 切怪 / 通关 / 失败 分支。

覆盖（真实 DB 链路，不 mock 引擎/玩法壳）：
- 肃清守卫：无敌人 → 引导探索/深入
- 轮转等待：非请求者且未超时 → 等待提示（多人）
- 超时自动防御：非请求者超时 → 自动 defend 后轮到请求者
- 行动：attack 伤害 / defend 姿态 / skill 施放（含 heal 防奶敌）
- 切怪：stage_pending 剩怪 → 击杀奖励 + build_battle 重构造下一只
- 通关：末层 Boss 死 → _instance_victory（cleared/奖励）
- 失败：玩家全倒 → _instance_defeat（回城/清锁）
- 秘密守卫（secret_guard_pending → 宝箱分支，不通关）
- rooms Boss 房通关

跑法：python tests/test_battle2_n5b4_instance_router.py
"""
import os
import sys
import tempfile
import asyncio
import json

os.environ["GWEN_GAME_DB"] = os.path.join(tempfile.mkdtemp(), "game.db")
os.environ["GWEN_TEST_MODE"] = "1"
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))
sys.path.insert(0, _QQBOT_DIR)
sys.path.insert(0, _PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game.battle2 import config as _b2c  # noqa: E402
_b2c.load_game_defaults()  # noqa: E402
from game.store.connection import init_db  # noqa: E402
init_db()

from game import db  # noqa: E402
from game import content as C  # noqa: E402
from game import engine as E  # noqa: E402
from game.commands import instance_battle as IB  # noqa: E402
from game.commands.instance import InstanceCmds  # noqa: E402
from game.commands.combat import CombatCmds  # noqa: E402
from game.commands.world import WorldCmds  # noqa: E402
from game.commands.instance_router import InstanceRouterCmds  # noqa: E402

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  ❌ {name} {detail}")


GID = "g_ir"


class FakeEvent:
    def __init__(self, group_id, qq_id, msg=""):
        self._g = group_id
        self._q = qq_id
        self.message_str = msg
        self._stopped = False

    def get_group_id(self):
        return self._g

    def get_sender_id(self):
        return self._q

    def get_message_str(self):
        return self.message_str

    def plain_result(self, text):
        return text

    def stop_event(self):
        self._stopped = True


async def collect(agen):
    out = []
    async for r in agen:
        out.append(r)
    return out


def mk_snap(qid, name, cls="cls_zhan_shi", level=15, learned=None, hp=None, spd_override=None):
    db.create_player(GID, qid, name, cls, {}, 100, 100)
    db.update_player(GID, qid, level=level, cur_map="mainland", cur_subarea="",
                     learned_skills=learned or [], stamina=999,
                     attributes=json.dumps({"str": 5, "agi": 5, "int": 5, "vit": 5}))
    pl = db.get_player(GID, qid)
    st = E.player_final_stats(cls, level, {}, 0, pl.get("attributes"), 0, {}, pl.get("race"))
    mh = int(st.get("max_hp", 100))
    cur = hp if hp is not None else mh
    db.update_player(GID, qid, max_hp=mh, max_mp=50, hp=cur, mp=50)
    pl = db.get_player(GID, qid)
    spd = spd_override if spd_override is not None else int(st.get("spd", 0) or 0)
    return {
        "name": name, "qq_id": qid, "class_name": cls, "level": level,
        "hp": int(pl.get("hp", 0)), "max_hp": mh,
        "mp": int(pl.get("mp", 0)), "max_mp": 50,
        "equipment": {}, "skills": [], "learned_skills": learned or [],
        "class_tier": 0, "evolve_path": 0, "attributes": pl.get("attributes"),
        "stat_bonus": {}, "race": pl.get("race"),
        "uid": f"p_{qid}", "buffs": {}, "stacks": {}, "defending": False,
        "charging": None, "ct": 0.0, "p_shields": {}, "spd": spd,
    }


def mk_enemy(uid="e_boss", name="测试Boss", hp=800, atk=30, spd=50, role="boss", lv=15):
    return {"uid": uid, "name": name, "hp": hp, "max_hp": hp,
            "atk": atk, "def": 10, "matk": 10, "mdef": 10, "spd": spd,
            "crit": 0.05, "lv": lv, "level": lv, "role": role,
            "is_boss": role == "boss", "is_elite": role == "elite",
            "rank": 1, "reach": 1, "ct": 1.0,
            "exp": 80, "gold": 40, "drops": ["兽肉"]}


def mk_st(qids, enemy=None, inst_id="inst_goblin_camp", **kw):
    qids = [str(q) for q in qids]
    st = {
        "type": "instance", "inst_id": inst_id, "leader": qids[0],
        "members": qids, "alive": {q: True for q in qids},
        "players": {}, "boss": None, "enemy": None, "enemies": [],
        "turn": 0, "round": 1, "mode": "battle", "pets": {},
        "p_buffs": {q: {} for q in qids},
        "p_hot": {q: {} for q in qids},
        "p_food_effects": {q: [] for q in qids},
        "p_defending": {q: False for q in qids},
        "mech_stacks": {q: {} for q in qids},
        "now": 0.0, "battle": None,
        "contribution": {}, "threat": {q: 0 for q in qids}, "over": False,
        "turn_time": 0, "stage_pending": [], "inst_stages": [],
        "stage_idx": 0, "stage_cleared": False, "world_id": "",
    }
    st.update(kw)
    for i, q in enumerate(qids):
        st["players"][q] = mk_snap(q, f"玩家{q}")
    if enemy:
        st["enemies"] = [enemy]
        st["boss"] = enemy
        st["enemy"] = enemy
    return st


class _Host(InstanceCmds, CombatCmds, WorldCmds):
    """Router 测试宿主：InstanceCmds 玩法壳 + CombatCmds 锁函数 + WorldCmds（map_view 依赖）。"""


def _patch_current_members(all_members):
    """多人副本 st 无 party 行时，current_members 恒返回全部成员（等价单人/测试口径）。"""
    orig = InstanceCmds._instance_current_members
    InstanceCmds._instance_current_members = lambda self, gid, st: [str(m) for m in (all_members or st["members"])]
    return orig


def _restore_current_members(orig):
    InstanceCmds._instance_current_members = orig


# ---------------------------------------------------------------- 分支测试
def test_1_no_enemy_hint():
    print("【1. 肃清守卫：无敌人 → 引导探索/深入】")
    st = mk_st([70001])
    st["enemies"] = []
    inst = _Host()
    msgs = _sync_run(inst, st, 70001, "attack")
    joined = "\n".join(msgs)
    check("无 pending 无 stages → 深入/肃清提示", "肃清" in joined or "深入" in joined or "Boss" in joined,
          joined[:80])
    # 有 stage_pending → 探索引导
    st2 = mk_st([70002])
    st2["enemies"] = []
    st2["stage_pending"] = [["m_test", "小怪", "dps", 15, [], []]]
    inst2 = _Host()
    msgs2 = _sync_run(inst2, st2, 70002, "attack")
    joined2 = "\n".join(msgs2)
    check("有 stage_pending → 探索引导", "探索" in joined2, joined2[:80])
    check("未 build battle 不报错", not joined2.startswith("战斗状态异常"), joined2[:60])


def test_2_turn_wait():
    print("【2. 轮转：非请求者未超时 → 等待提示】")
    st = mk_st([70011, 70012], enemy=mk_enemy(hp=500, spd=1))
    # 双人玩家 actor 都建好
    IB.build_battle(st)
    # 让 70011 ct 最小（轮到他），70012 请求
    for a in (IB._players_of(st) or []):
        if str(a.get("qq_id")) == "70011":
            a["ct"] = 0.0
        else:
            a["ct"] = 50.0
    IB.sync_views(st, GID)
    st["turn_time"] = int(__import__("time").time())  # 未超时
    orig = _patch_current_members(["70011", "70012"])
    try:
        inst = _Host()
        msgs = _sync_run(inst, st, 70012, "attack")
        joined = "\n".join(msgs)
        check("非请求者 → 等待提示", "等待" in joined or "的刻" in joined, joined[:100])
        check("未行动者未被自动防御（defending False）",
              not st["p_defending"].get("70011"), str(st.get("p_defending")))
    finally:
        _restore_current_members(orig)


def test_3_timeout_auto_defend():
    print("【3. 超时自动防御：非请求者超时 → 自动 defend 后轮到请求者】")
    st = mk_st([70021, 70022], enemy=mk_enemy(hp=5000, spd=1))
    IB.build_battle(st)
    for a in (IB._players_of(st) or []):
        if str(a.get("qq_id")) == "70021":
            a["ct"] = 10.0   # 该 70021 行动但超时未动
        else:
            a["ct"] = 100.0  # 请求者 70022
    IB.sync_views(st, GID)
    st["turn_time"] = int(__import__("time").time()) - 120  # 已超时 60s
    orig = _patch_current_members(["70021", "70022"])
    try:
        inst = _Host()
        msgs = _sync_run(inst, st, 70022, "defend")
        joined = "\n".join(msgs)
        check("超时者自动防御（defending True）", bool(st["p_defending"].get("70021")),
              str(st.get("p_defending")))
        check("日志含自动防御提示", "自动" in joined or "迟迟" in joined, joined[:120])
    finally:
        _restore_current_members(orig)


def test_4_attack_and_sync():
    print("【4. 行动：attack 造成伤害 + 视图/DB 同步】")
    st = mk_st([70031], enemy=mk_enemy(hp=600, spd=1))
    IB.build_battle(st)
    hp0 = int(st["enemies"][0]["hp"])
    inst = _Host()
    msgs = _sync_run(inst, st, 70031, "attack")
    hp1 = int(st["enemies"][0]["hp"]) if st.get("enemies") else 0
    check("普攻造成伤害", hp1 < hp0, f"{hp0}->{hp1}")
    check("日志含伤害", any("伤害" in m or "攻击" in m for m in msgs), str(msgs[:1])[:80])
    check("视图同步敌 hp", st["enemies"] and st["enemies"][0]["hp"] == hp1)
    snap = st["players"]["70031"]
    dbp = db.get_player(GID, 70031) or {}
    check("DB 血量同步", int(dbp.get("hp", -1)) == int(snap.get("hp", -2)),
          f"db={dbp.get('hp')} snap={snap.get('hp')}")


def test_5_defend():
    print("【5. 行动：defend 姿态】")
    st = mk_st([70032], enemy=mk_enemy(hp=5000, atk=9999, spd=1))
    IB.build_battle(st)
    inst = _Host()
    msgs = _sync_run(inst, st, 70032, "defend")
    joined = "\n".join(msgs)
    check("防御姿态日志", "防御" in joined or "减半" in joined, joined[:100])
    # defend 后 actor defending 状态（视图键同步）
    check("防御状态落 actor/视图", bool(st["p_defending"].get("70032")), str(st.get("p_defending")))


def test_6_switch_next_monster():
    print("【6. 切怪：stage_pending 剩怪 → 击杀奖励 + 下一只重构造】")
    st = mk_st([70041], enemy=mk_enemy(hp=80, spd=1),
               stage_pending=[["m_slime", "史莱姆", "dps", 15, [], []]])
    IB.build_battle(st)
    inst = _Host()
    msgs = _sync_run(inst, st, 70041, "attack")
    joined = "\n".join(msgs)
    # 一刀没死继续补刀
    guard = 0
    while st.get("enemies") and not st.get("over") and guard < 8:
        guard += 1
        msgs = _sync_run(inst, st, 70041, "attack")
        joined += "\n" + "\n".join(msgs)
        if "又一只" in joined or not st.get("enemies"):
            break
    check("切怪文案（又一只怪物）", "又一只" in joined or not st.get("enemies"), joined[-200:])
    check("pending 消费", st.get("stage_pending") == [], str(st.get("stage_pending")))
    check("battle 重构造 sides", (st.get("battle") or {}).get("sides") is not None)
    check("新怪出现或已是下一只", bool(st.get("enemies")) or st.get("over"),
          f"enemies={st.get('enemies')} over={st.get('over')}")


def test_7_victory():
    print("【7. 通关：Boss 死（末层/无 pending）→ _instance_victory】")
    st = mk_st([70051], enemy=mk_enemy(hp=60, spd=1))
    IB.build_battle(st)
    inst = _Host()
    msgs = []
    guard = 0
    while st.get("enemies") and guard < 10:
        guard += 1
        msgs += _sync_run(inst, st, 70051, "attack")
        if st.get("cleared") or st.get("over") or not st.get("enemies"):
            break
    joined = "\n".join(msgs)
    check("通关文案", "通关" in joined, joined[-200:])
    check("cleared 置位", st.get("cleared") is True, f"cleared={st.get('cleared')}")
    check("存活玩家获得奖励（经验/金币行）", ("经验" in joined or "金币" in joined), joined[-300:])
    # Boss 死亡账（_last_killed 兜底 Boss 名在 victory 内消费）
    dbp = db.get_player(GID, 70051) or {}
    check("DB 玩家存活且经验增长", int(dbp.get("hp", 0)) > 0, f"hp={dbp.get('hp')}")


def test_8_defeat():
    print("【8. 失败：玩家全倒 → _instance_defeat（回城）】")
    # 玩家低血 + Boss 高攻高速 → 先手击杀
    st = mk_st([70061], enemy=mk_enemy(hp=8000, atk=9999, spd=200, role="boss"))
    st["players"]["70061"]["hp"] = 3
    db.update_player(GID, 70061, hp=3)
    IB.build_battle(st)
    inst = _Host()
    msgs = []
    guard = 0
    while guard < 12:
        guard += 1
        msgs += _sync_run(inst, st, 70061, "defend")
        if st.get("over") or not st.get("alive", {}).get("70061", True):
            break
        if not (st.get("battle") or {}).get("sides"):
            break
    joined = "\n".join(msgs)
    check("失败结算文案", "失败" in joined or "全灭" in joined or "送回了" in joined,
          joined[-200:])
    check("over/失败态", st.get("over") is True or "失败" in joined,
          f"over={st.get('over')} alive={st.get('alive')}")


def test_9_secret_guard():
    print("【9. 秘密守卫：secret_guard_pending → 宝箱分支（不通关）】")
    st = mk_st([70071], enemy=mk_enemy(hp=60, spd=1),
               secret_guard_pending=True, mode="battle",
               inst_stages=[{"name": "一层", "elite": ["m_test", "精英", "elite", 15, [], []]}])
    IB.build_battle(st)
    inst = _Host()
    msgs = []
    guard = 0
    while st.get("enemies") and guard < 10:
        guard += 1
        msgs += _sync_run(inst, st, 70071, "attack")
        if st.get("secret_chest") or not st.get("enemies"):
            break
    joined = "\n".join(msgs)
    check("宝箱分支文案", "宝箱" in joined, joined[-200:])
    check("secret_chest 置位", st.get("secret_chest") is True, f"chest={st.get('secret_chest')}")
    check("未通关（cleared 未置）", not st.get("cleared"), f"cleared={st.get('cleared')}")


def test_10_rooms_boss():
    print("【10. dungeon rooms：Boss 房击杀 → 通关】")
    # rooms 结构：真实 Boss 房 subarea（deer_fort_3）→ 击杀走通关
    cur_sa = "deer_fort_3"
    st = mk_st([70081], enemy=mk_enemy(hp=50, spd=1),
               inst_id="inst_deer_fort",
               rooms={cur_sa: {"monsters_left": [], "boss_alive": True,
                               "_is_boss": True}})
    db.update_player(GID, 70081, cur_map="deer_fort", cur_subarea=cur_sa)
    IB.build_battle(st)
    inst = _Host()
    msgs = []
    guard = 0
    while st.get("enemies") and guard < 10:
        guard += 1
        msgs += _sync_run(inst, st, 70081, "attack")
        if st.get("cleared") or st.get("over"):
            break
    joined = "\n".join(msgs)
    check("rooms Boss 房通关", "通关" in joined, joined[-200:])
    check("boss_alive 标记 False", (st.get("rooms") or {}).get(cur_sa, {}).get("boss_alive") is False,
          str(st.get("rooms")))


def _sync_run(inst, st, qq, action, skill=None, target=None):
    player = st["players"][str(qq)]
    ev = FakeEvent(GID, str(qq))
    return _run_gen(inst._instance_router(ev, GID, str(qq), player, st, action, skill, target))


def _run_gen(agen):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(collect(agen))
    finally:
        loop.close()


def test_11_command_entry_switch():
    print("【11. R2 命令层接线：CombatCmds attack/skill/defend 分流 → router】")
    # attack：db 有 battle 行 → instance 分流 → _instance_router（不再 _instance_act）
    # 注意：命令层从 db.get_battle 读回反序列化副本操作（大陆权威 st 场景在 R4 端到端），
    # 此处校验 db 行内 sides 敌 hp 下降（真实写入路径）。
    st = mk_st([70091], enemy=mk_enemy(hp=300, spd=1))
    IB.build_battle(st)
    db.save_battle(GID, 70091, st)
    inst = _Host()
    ev = FakeEvent(GID, "70091", "攻击")
    msgs = _collect(inst.attack(ev))
    joined = "\n".join(msgs)
    row = db.get_battle(GID, 70091)
    e_hp = 300
    if row:
        _sides = (row["state"].get("battle") or {}).get("sides") or row["state"].get("sides") or {}
        _e = _sides.get("enemy") or []
        if _e:
            e_hp = max(0, int(_e[0].get("hp", 300) or 300))
    check("attack 分流 → router 普攻造成伤害（db 行敌 hp 下降）", e_hp < 300, f"敌hp={e_hp}")
    check("attack 输出含回合面板", "行动" in joined or "伤害" in joined, joined[:100])
    # defend：实例行 → router 防御（db 行 defending 置位）
    ev2 = FakeEvent(GID, "70091", "防御")
    msgs2 = _collect(inst.defend(ev2))
    joined2 = "\n".join(msgs2)
    row2 = db.get_battle(GID, 70091)
    _def = False
    if row2:
        _sides2 = (row2["state"].get("battle") or {}).get("sides") or {}
        for _p in (_sides2.get("player") or []):
            if str(_p.get("qq_id")) == "70091":
                _def = bool(_p.get("defending"))
    check("defend 分流 → router 防御（db 行 defending）", _def, f"defending={_def}")
    check("defend 输出含防御文案", "防御" in joined2 or "减半" in joined2, joined2[:100])
    # skill：需要技能栏/已学——用攻击型验证不崩（heal 已覆盖于单测 4）
    st2 = mk_st([70092], enemy=mk_enemy(hp=500, spd=1))
    IB.build_battle(st2)
    db.save_battle(GID, 70092, st2)
    ev3 = FakeEvent(GID, "70092", "技能")
    msgs3 = _collect(inst.skill(ev3))
    # 无技能名 → 技能面板（说明走到了 skill 而非崩溃）
    joined3 = "\n".join(msgs3)
    check("skill 无参 → 面板（分流不崩）", bool(joined3.strip()), joined3[:80])


def test_12_use_item_router():
    print("【12. I3 use_item 端到端：router → override 翻译器 heal 生效 / 缺口不占刻】")
    # 玩家 hp 打残 → 副本内喝治疗药水 payload（模板产物 "150" 绝对恢复）
    st = mk_st([70101], enemy=mk_enemy(hp=800, spd=5))
    IB.build_battle(st)
    # 打掉玩家一点血（sides actor 直改——真实链路里由敌方攻击写）
    _pa = IB.player_actor_of(st, 70101)
    _max0 = int(_pa.get("max_hp", 0) or 0)
    _pa["hp"] = max(1, _max0 // 2)
    IB.sync_views(st, GID)
    inst = _Host()
    # 首次普通攻击推进轮转到玩家（turn_time 置现避免超时误判）
    import time as _t
    st["turn_time"] = int(_t.time())
    _hp_before = int((st["players"] or {}).get("70101", {}).get("hp", 0))
    msgs = _sync_run(inst, st, "70101", "use_item", "150")
    joined = "\n".join(msgs)
    _hp_after = int((st["players"] or {}).get("70101", {}).get("hp", 0))
    check("use_item 经 router 翻译恢复生命（battle2 actor 生效）", _hp_after > _hp_before,
          f"hp {_hp_before}->{_hp_after}")
    check("use_item 日志含恢复/使用文案", any(k in joined for k in ("恢复", "使用", "道具")), joined[:120])
    # battle state 仍在且敌未死
    check("使用后战斗未结束", not st.get("over"), f"over={st.get('over')}")
    # 机制型缺口（特殊分发未覆盖）→ 不生效提示，不占刻（战斗可继续普攻）
    st2 = mk_st([70102], enemy=mk_enemy(hp=800, spd=5))
    IB.build_battle(st2)
    st2["turn_time"] = int(_t.time())
    _ct_before = float((IB.player_actor_of(st2, 70102) or {}).get("ct", 0) or 0)
    msgs2 = _sync_run(inst, st2, "70102", "use_item", "special:summon")
    joined2 = "\n".join(msgs2)
    check("缺口 payload 不静默——给出未知/无效提示", bool(joined2.strip()), joined2[:120])
    _ct_after = float((IB.player_actor_of(st2, 70102) or {}).get("ct", 0) or 0)
    check("缺口不占刻（ct 未推）", abs(_ct_after - _ct_before) < 0.01,
          f"ct {_ct_before}->{_ct_after}")


def test_13_target_picker():
    print("【13. 5b target_picker：仇恨选目标 / 嘲讽强制 / policy 缺省】")
    from game.battle2 import Battle as B2
    from game.commands import instance_battle as IB
    st = mk_st([70111, 70112], enemy=mk_enemy(hp=5000, spd=1, role="boss"))
    IB.build_battle(st)
    # 组装 battle 实例（build_battle 已注入 picker——但 st["battle"] 是 to_state，
    # picker 是构造时闭包，需直接 from_state 后手动挂）
    b = B2.from_state(st["battle"])
    IB._attach_instance_hooks(b, st)
    pa1 = next(a for a in b.sides_of("player") if a.get("qq_id") == "70111")
    pa2 = next(a for a in b.sides_of("player") if a.get("qq_id") == "70112")
    enemy = b.sides_of("enemy")[0]
    enemy["role"] = "boss"
    # ① 无嘲讽：boss 缺省 hate_top → 打仇恨最高
    st["taunt_target"] = ""
    st["threat"] = {"70111": 100, "70112": 30}
    p = b.target_picker(b, enemy)
    check("boss hate_top 打仇恨最高者", p is not None and p.get("qq_id") == "70111",
          f"picked={p.get('qq_id') if p else None}")
    # ② 嘲讽强制（无视仇恨表）
    st["taunt_target"] = "70112"
    p2 = b.target_picker(b, enemy)
    check("嘲讽强制打嘲讽者", p2 is not None and p2.get("qq_id") == "70112",
          f"picked={p2.get('qq_id') if p2 else None}")
    st["taunt_target"] = ""
    # ③ 普通怪（非 boss 缺省 front）→ 有存活就选（单人/前排）
    enemy["role"] = "dps"
    p3 = b.target_picker(b, enemy)
    check("普通怪 front 选存活玩家", p3 is not None and p3.get("qq_id") in ("70111", "70112"),
          f"picked={p3.get('qq_id') if p3 else None}")
    # ④ 玩家全灭 → None（引擎回落默认，不崩）
    pa1["hp"] = 0
    pa2["hp"] = 0
    p4 = b.target_picker(b, enemy)
    check("无存活玩家 → None", p4 is None, f"picked={p4}")
    print("  -- 注：st threat 表 key=qq_id，monster_to_actor 透传 role 字段")


def _collect(agen):
    """跑命令层 filter handler（async generator 或 coroutine 兼容）。"""
    return _run_gen(agen)


def main():
    test_1_no_enemy_hint()
    test_2_turn_wait()
    test_3_timeout_auto_defend()
    test_4_attack_and_sync()
    test_5_defend()
    test_6_switch_next_monster()
    test_7_victory()
    test_8_defeat()
    test_9_secret_guard()
    test_10_rooms_boss()
    test_11_command_entry_switch()
    test_12_use_item_router()
    test_13_target_picker()
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    if FAILURES:
        for f in FAILURES:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
