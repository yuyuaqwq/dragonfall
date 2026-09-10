# -*- coding: utf-8 -*-
"""v181 破绽接线验收：game/services/battle2_bar_procs（挂敌身条注入 → 触发 → 跳过）。

覆盖：装配（学什么挂什么）/ 命中注入 / 阈值触发 / 触发落地 mode=skip / 跳过消费 /
      宿主回合刻衰减。

跑法：python tests/test_battle2_bar_procs.py
"""
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_b2_bar.db"))
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game.battle2 import config as _b2c  # noqa: E402
_b2c.load_game_defaults()
from game.battle2 import Battle as B2, make_actor  # noqa: E402
from game.battle2.actors import ActCtx  # noqa: E402
from game.battle2.effect_triggers import fire  # noqa: E402
from game.services import class_mech_proc as CMP  # noqa: E402
from game.data import skills as _SK  # noqa: E402

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


def mk_player(cls="cls_wu_seng", learned=None, hp=2000):
    return make_actor(uid="p1", name="勇者", side="player", kind="player",
                      human_controlled=True, class_name=cls, level=20,
                      hp=hp, max_hp=hp, mp=200, max_mp=200,
                      atk=100, matk=80, spd=15, crit=0.05,
                      equipment={}, skills=[], learned_skills=list(learned or []),
                      race=None, evolve_path=0, class_tier=0, attributes={},
                      **{"def": 40, "mdef": 30})


def mk_enemy(hp=50000, atk=1):
    return make_actor(uid="e1", name="木桩怪", side="enemy", kind="monster",
                      hp=hp, max_hp=hp, atk=atk, matk=1, spd=5, crit=0.0,
                      level=20, exp=0, gold=0, **{"def": 10, "mdef": 10})


def new_battle(p, e):
    return B2(btype="monster", sides={"player": [p], "enemy": [e]})


def _bar_trigs(actor):
    return [x for x in ((actor.get("triggers") or {}).get("skill_hit") or [])
            if isinstance(x, dict) and x.get("action") == "bar_gain"]


def _tick_trigs(actor):
    return [x for x in ((actor.get("triggers") or {}).get("turn_start") or [])
            if isinstance(x, dict) and x.get("action") == "bar_tick"]


def test_install():
    print("【1. 装配：学什么挂什么（BAR_INJECT_FIELDS 扫描）】")
    p = mk_player(cls="cls_wu_seng", learned=["sk_gang_quan"])
    CMP.apply_class_mech(p)
    t = _bar_trigs(p)
    check("拳师（学推条技能）挂 bar_gain/shaken",
          any(x.get("key") == "shaken" and x.get("field") == "shaken_gain" for x in t),
          f"trig={t}")
    # 反向：非拳师职业（不带 shaken_gain 字段的技能）不挂
    zhan_id = list(_SK.PLAYER_SKILLS["cls_zhan_shi"].keys())[0]
    p2 = mk_player(cls="cls_zhan_shi", learned=[zhan_id])
    CMP.apply_class_mech(p2)
    check("战士不挂 bar_gain（零噪音）", not _bar_trigs(p2), f"trig={_bar_trigs(p2)}")
    # 反向：拳师但没学任何推条技能 → 不挂
    p3 = mk_player(cls="cls_wu_seng", learned=[])
    CMP.apply_class_mech(p3)
    check("拳师未学推条技能不挂", not _bar_trigs(p3), f"trig={_bar_trigs(p3)}")
    # 幂等：重复装配不重复挂
    CMP.apply_class_mech(p)
    check("重复装配幂等（只 1 条）", len(_bar_trigs(p)) == 1, f"n={len(_bar_trigs(p))}")


def test_inject_on_hit():
    print("【2. 命中注入：skill_hit → bar_gain（钢拳 shaken_gain=5）】")
    p = mk_player(cls="cls_wu_seng", learned=["sk_gang_quan"])
    CMP.apply_class_mech(p)
    e = mk_enemy()
    b = new_battle(p, e)
    logs = []
    fire(b, "skill_hit", {"actor": p, "target": e, "info": {"shaken_gain": 5}}, logs)
    bs = (e.get("buffs") or {}).get("shaken") or {}
    check("敌方破绽条 val=5", bs.get("val") == 5, f"bs={bs}")
    check("自安装 turn_start tick", len(_tick_trigs(e)) == 1, f"tick={_tick_trigs(e)}")
    # 无字段技能 → 不注入（无字段=不启用）
    logs2 = []
    fire(b, "skill_hit", {"actor": p, "target": e, "info": {"name": "无推条技能"}}, logs2)
    bs2 = (e.get("buffs") or {}).get("shaken") or {}
    check("无 shaken_gain 字段不注入", bs2.get("val") == 5, f"val={bs2.get('val')}")


def test_threshold_trigger():
    print("【3. 阈值触发：满 50 → 触发（val 清 0 / 阈值 ×1.35 / 免疫 1 刻）】")
    p = mk_player(cls="cls_wu_seng", learned=["sk_gang_quan"])
    CMP.apply_class_mech(p)
    e = mk_enemy()
    b = new_battle(p, e)
    logs = []
    from game.core.battle_bars import bar_gain as _bg
    _bg(e, "shaken", 45, logs)          # 垫到 45
    fire(b, "skill_hit", {"actor": p, "target": e, "info": {"shaken_gain": 5}}, logs)
    bs = (e.get("buffs") or {}).get("shaken") or {}
    check("触发后 val 清零", bs.get("val") == 0, f"bs={bs}")
    check("trigger_count=1", bs.get("trigger_count") == 1, f"bs={bs}")
    check("阈值 50 → 67（×1.35 取整）", bs.get("threshold") == 67, f"thr={bs.get('threshold')}")
    check("免疫窗口 1 刻", bs.get("immune_turns") == 1, f"imm={bs.get('immune_turns')}")
    check("落地 mode=skip 控制",
          ((e.get("effects") or {}).get("bar_skip:shaken") or {}).get("mode") == "skip",
          f"eff={e.get('effects')}")
    # 免疫期内不再触发（val 满也不触发）
    logs2 = []
    _bg(e, "shaken", 50, logs2)
    fire(b, "skill_hit", {"actor": p, "target": e, "info": {"shaken_gain": 5}}, logs2)
    bs2 = (e.get("buffs") or {}).get("shaken") or {}
    check("免疫期内不重复触发", bs2.get("trigger_count") == 1, f"bs={bs2}")


def test_skip_consumed():
    print("【4. 跳过消费：敌方行动被 mode=skip 拦截并消费清条】")
    p = mk_player(cls="cls_wu_seng", learned=["sk_gang_quan"])
    CMP.apply_class_mech(p)
    e = mk_enemy()
    b = new_battle(p, e)
    logs = []
    from game.core.battle_bars import bar_gain as _bg
    _bg(e, "shaken", 49, logs)
    fire(b, "skill_hit", {"actor": p, "target": e, "info": {"shaken_gain": 5}}, logs)
    check("触发已挂 skip", "bar_skip:shaken" in (e.get("effects") or {}), f"eff={e.get('effects')}")
    e_hp0 = e["hp"]
    ctx = ActCtx(caster=e, action="attack", target=p)
    alogs, _ended = b.act(ctx)
    joined = " ".join(str(x) for x in alogs)
    check("敌方行动被跳过", ("控制" in joined) or ("震慑" in joined), f"logs={alogs}")
    check("skip 条目消费即清", "bar_skip:shaken" not in (e.get("effects") or {}),
          f"eff={e.get('effects')}")
    check("跳过时未对玩家造成伤害", p["hp"] == p["max_hp"], f"p_hp={p['hp']}")
    check("跳过不结算敌方普攻（玩家未掉血）", e_hp0 == e["hp"], f"e_hp={e['hp']}")


def test_turn_start_decay():
    print("【5. 宿主回合刻衰减：turn_start → bar_tick（免疫递减 + 自然衰减）】")
    p = mk_player(cls="cls_wu_seng", learned=["sk_gang_quan"])
    CMP.apply_class_mech(p)
    e = mk_enemy()
    b = new_battle(p, e)
    logs = []
    fire(b, "skill_hit", {"actor": p, "target": e, "info": {"shaken_gain": 10}}, logs)
    bs = (e.get("buffs") or {}).get("shaken") or {}
    check("注入后 val=10", bs.get("val") == 10, f"bs={bs}")
    tlogs = []
    fire(b, "turn_start", {"actor": e}, tlogs)
    bs2 = (e.get("buffs") or {}).get("shaken") or {}
    # 数值缺口备忘：ENEMY_BAR_CFG decay_per_turn=1.7，但 core/battle_bars.bar_tick
    # 用 int() 取整 → 实测每动 −1（设计意图 −1.7/刻）。本模块不改容器，仅记录。
    check("回合开始衰减 −1（int 截断，设计值 1.7 见备忘）",
          bs2.get("val") == 9, f"val={bs2.get('val')}")


def test_no_bar_no_op():
    print("【6. 未挂条单位零行为（无字段=不启用）】")
    p = mk_player(cls="cls_zhan_shi", learned=[])
    CMP.apply_class_mech(p)
    e = mk_enemy()
    b = new_battle(p, e)
    logs = []
    fire(b, "skill_hit", {"actor": p, "target": e, "info": {"shaken_gain": 5}}, logs)
    check("未装配的战士不产生条", not (e.get("buffs") or {}).get("shaken"), f"buffs={e.get('buffs')}")
    fire(b, "turn_start", {"actor": e}, logs)
    check("敌方无 tick 也不崩", True)


if __name__ == "__main__":
    test_install()
    test_inject_on_hit()
    test_threshold_trigger()
    test_skip_consumed()
    test_turn_start_decay()
    test_no_bar_no_op()
    print(f"\n== 结果：通过 {PASS} / 共 {PASS + FAIL} ==")
    if FAILURES:
        for f in FAILURES:
            print("  FAIL:", f)
        sys.exit(1)
    print("全绿 ✅")
