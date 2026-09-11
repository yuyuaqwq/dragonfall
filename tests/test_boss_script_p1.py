# -*- coding: utf-8 -*-
"""5c P1 验证：Boss 剧本导演 phases 转阶段（battle2 script_hook）。

真实数据（INSTANCES inst_old_king_tomb 内联 phases 3 条 + MONSTER_MODS b_king_odric）：
- cfg 解析：副本覆盖优先（inst 内联 3 条 > mods 2 条）
- 血量 40%（<60%）→ 阶段 2：演出王冠威临 / add ms_zhao_ku_lou_mi / auto_act 切招 /
  旧行为 atk ×1.2（normal 无 phase_id 无 atk_mult）
- 血量 25%（<30%）→ 阶段 3：演出王座之怒 / add 2 技能 / merge enrage 模板 atk ×1.25
- rampage（min 0）不触发（血量 10% 仍 phase_count=2）
- 演出刻：触发帧 Boss 不造成伤害（引擎 script_hook 拦截）
- 序列化：st["boss_script"] 导演状态持久化（battle state 不带导演字段，from_state
  重挂后 phase_count 保留）

跑法：python tests/test_boss_script_p1.py
"""
import os
import sys
import tempfile
import json

os.environ["GWEN_GAME_DB"] = os.path.join(tempfile.mkdtemp(), "game.db")
os.environ["GWEN_TEST_MODE"] = "1"
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN_DIR, "framework"))  # 引擎框架包（S8 物理分离：framework/ 为引擎 submodule）
sys.path.insert(0, _PLUGIN_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from battle2 import config as _b2c  # noqa: E402
from game.content_rules.apply import ensure_engine_configured as _eng_cfg; _eng_cfg()  # noqa: E402
from game.store.connection import init_db  # noqa: E402
init_db()

from game import content as C  # noqa: E402
from game import db  # noqa: E402
from game.content_rules.panel import player_final_stats
from game.commands import instance_battle as IB  # noqa: E402
from battle2 import Battle as B2  # noqa: E402

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


GID = "g_bs"
INST_ID = "inst_old_king_tomb"
BOSS_ID = "b_king_odric"


def mk_snap(qid, name, cls="cls_zhan_shi", level=40):
    db.create_player(GID, qid, name, cls, {}, 100, 100)
    db.update_player(GID, qid, level=level, cur_map="king_road", cur_subarea="king_road_3",
                     learned_skills=[], stamina=999,
                     attributes=json.dumps({"str": 5, "agi": 5, "int": 5, "vit": 5}))
    pl = db.get_player(GID, qid)
    st = player_final_stats(cls, level, {}, 0, pl.get("attributes"), 0, {}, pl.get("race"))
    mh = int(st.get("max_hp", 100))
    db.update_player(GID, qid, max_hp=mh, max_mp=50, hp=mh, mp=50)
    pl = db.get_player(GID, qid)
    return {"name": name, "qq_id": qid, "class_name": cls, "level": level,
            "hp": int(pl.get("hp", 0)), "max_hp": mh, "mp": 50, "max_mp": 50,
            "equipment": {}, "skills": [], "learned_skills": [],
            "class_tier": 0, "evolve_path": 0, "attributes": pl.get("attributes"),
            "bonus": {"panel": {}, "cap": {}, "cost": {}}, "race": pl.get("race"), "uid": f"p_{qid}",
            "buffs": {}, "stacks": {}, "defending": False, "charging": None,
            "ct": 0.0, "p_shields": {}, "spd": int(st.get("spd", 0) or 0)}


def mk_boss_st():
    """玩法壳开本同款：INSTANCES boss 六元组 → build_monster + _inst_id + 缩放。"""
    inst = C.INSTANCES[INST_ID]
    mon = C.build_monster(inst["boss"], {"id": INST_ID, "name": inst["name"],
                                          "area": "instance"})
    mon["_inst_id"] = INST_ID
    hp_mult = inst["hp_mult"] + 0.65 * (1 - inst.get("min_players", 1))
    mon["max_hp"] = int(mon["max_hp"] * hp_mult)
    mon["hp"] = mon["max_hp"]
    mon["atk"] = int(mon["atk"] * inst["atk_mult"])
    mon["matk"] = int(mon["matk"] * inst["atk_mult"])
    st = {"type": "instance", "inst_id": INST_ID, "leader": "80001",
          "members": ["80001"], "alive": {"80001": True},
          "players": {"80001": mk_snap(80001, "勇者")},
          "boss": mon, "enemy": mon, "enemies": [mon], "pets": {},
          "p_buffs": {"80001": {}}, "p_hot": {"80001": {}},
          "p_food_effects": {"80001": []}, "p_defending": {"80001": False},
          "mech_stacks": {"80001": {}}, "now": 0.0, "battle": None,
          "contribution": {}, "threat": {"80001": 0}, "over": False,
          "turn_time": 0, "stage_pending": [], "inst_stages": [],
          "stage_idx": 0, "stage_cleared": False, "world_id": ""}
    return st


def boss_frame(st, hp_ratio):
    """boss 行动一帧（hp 压到 ratio 后 actor_auto）。返回 (logs, ended)。"""
    b = B2.from_state(st["battle"])
    IB._attach_instance_hooks(b, st)
    boss = b.sides_of("enemy")[0]
    boss["hp"] = int(int(boss.get("max_hp", 1)) * hp_ratio)
    logs, ended = b.actor_auto(boss)
    st["battle"] = b.to_state()
    return logs, ended


def test_1_cfg_resolution():
    print("【1. cfg 解析：inst 内联 phases 副本覆盖优先】")
    st = mk_boss_st()
    IB.build_battle(st)
    b = B2.from_state(st["battle"])
    boss = b.sides_of("enemy")[0]
    from game.commands.boss_script import boss_script_cfg
    cfg = boss_script_cfg(st, boss)
    check("有 cfg（phases 非空）", cfg is not None and bool(cfg.get("phases")))
    check("inst 内联 3 条（副本覆盖 > mods 2 条）", len(cfg.get("phases") or []) == 3,
          str(len(cfg.get("phases") or [])))
    check("mech token 并集（E2：phase,summon,enrage）",
          sorted(cfg.get("mech") or []) == ["enrage", "phase", "summon"],
          str(cfg.get("mech")))


def test_2_phase_entry_normal():
    print("【2. 40% 血 → 阶段 2（normal 王冠威临）：演出/换招/atk×1.2】")
    st = mk_boss_st()
    IB.build_battle(st)
    b = B2.from_state(st["battle"])
    IB._attach_instance_hooks(b, st)
    boss = b.sides_of("enemy")[0]
    ph_before = int((st.get("boss_script") or {}).get("phase_count", 0) or 0)
    # 触发帧
    boss["hp"] = int(boss["max_hp"] * 0.40)
    logs, ended = b.actor_auto(boss)
    joined = "\n".join(logs)
    bs = st["boss_script"]
    check("phase_count=1", bs.get("phase_count") == 1,
          f"before={ph_before} after={bs.get('phase_count')}")
    check("演出文案【王冠威临】", "王冠威临" in joined, joined[-200:])
    check("add_skills 幂等追加 ms_zhao_ku_lou_mi",
          "ms_zhao_ku_lou_mi" in (boss.get("skills") or []), str(boss.get("skills")))
    check("auto_act 切阶段主技能", (boss.get("auto_act") or {}).get("act", {}).get("skill")
          == "ms_zhao_ku_lou_mi", str(boss.get("auto_act")))
    # 演出刻拦截：本帧 Boss 没造成伤害（触发帧日志无对玩家的伤害行）
    check("演出刻拦截本刻行动（无伤害行）",
          not any("受到" in x and "点伤害" in x for x in logs), joined[-200:])
    # normal 无 phase_id 无 atk_mult → 旧行为 1+0.2×1 = 1.2
    ef = boss.get("effects") or {}
    check("atk 乘区 ×1.2（旧行为）",
          abs(float((ef.get("boss_phase_atk") or {}).get("mult", 0) or 0) - 1.2) < 0.001,
          str(ef.get("boss_phase_atk")))


def test_3_phase_entry_enrage():
    print("【3. 25% 血 → 阶段 3（enrage 王座之怒）：模板 merge atk×1.25】")
    st = mk_boss_st()
    IB.build_battle(st)
    b = B2.from_state(st["battle"])
    IB._attach_instance_hooks(b, st)
    boss = b.sides_of("enemy")[0]
    # 先进阶段 2 再压到 25%（阶段链逐条：60% → 30%）
    boss["hp"] = int(boss["max_hp"] * 0.40)
    b.actor_auto(boss)
    boss["hp"] = int(boss["max_hp"] * 0.25)
    logs, ended = b.actor_auto(boss)
    joined = "\n".join(logs)
    bs = st["boss_script"]
    check("phase_count=2", bs.get("phase_count") == 2, str(bs.get("phase_count")))
    check("演出文案【王座之怒】", "王座之怒" in joined, joined[-250:])
    check("enrage add_skills 追加（王座之怒/亡语唤魂）",
          "ms_wang_zhe_zhi_nu" in (boss.get("skills") or [])
          and "ms_wang_yu_huan_hun" in (boss.get("skills") or []),
          str(boss.get("skills")))
    check("auto_act 切 ms_wang_zhe_zhi_nu",
          (boss.get("auto_act") or {}).get("act", {}).get("skill") == "ms_wang_zhe_zhi_nu",
          str(boss.get("auto_act")))
    ef = boss.get("effects") or {}
    check("enrage 模板 atk ×1.25（merge_phase_config）",
          abs(float((ef.get("boss_phase_atk") or {}).get("mult", 0) or 0) - 1.25) < 0.001,
          str(ef.get("boss_phase_atk")))


def test_4_rampage_not_triggered():
    print("【4. rampage（min 0）不触发（10% 仍 phase_count=2）】")
    st = mk_boss_st()
    IB.build_battle(st)
    b = B2.from_state(st["battle"])
    IB._attach_instance_hooks(b, st)
    boss = b.sides_of("enemy")[0]
    boss["hp"] = int(boss["max_hp"] * 0.40)
    b.actor_auto(boss)
    boss["hp"] = int(boss["max_hp"] * 0.25)
    b.actor_auto(boss)
    boss["hp"] = int(boss["max_hp"] * 0.10)
    logs, ended = b.actor_auto(boss)
    bs = st["boss_script"]
    check("10% 血仍 phase_count=2（min 0 阈值永不触发）",
          bs.get("phase_count") == 2, str(bs.get("phase_count")))
    check("无第三次演出（亡者终末未触发）",
          not any("亡者终末" in x for x in logs), str(logs)[-150:])
    # 10% 后本帧应正常行动（非演出刻）。
    # 2026-09-11：引擎修掉「运行期换招索引失效」后，Boss 转阶段加的技能真能被
    # 解析并结算（此前索引不含阶段新招 → do_skill 静默空放、0 伤害）。本用例玩家
    # 面板是裸身（atk 0 / 1020 HP）而 Boss atk 1452 → 必被打倒，故 ended=True
    # 属正常；断言改为「本帧有真实伤害结算 = 没被演出拦截、也不是空放」。
    _dealt = any(("勇者" in str(x) and "伤害" in str(x)) or "倒下" in str(x)
                 for x in logs)
    check("非演出帧正常行动（真实结算伤害，非空放）", _dealt, f"logs={logs} ended={ended}")


def test_5_serialize_persist():
    print("【5. 序列化：导演状态 st[\"boss_script\"] 跨 from_state 保留】")
    st = mk_boss_st()
    IB.build_battle(st)
    b = B2.from_state(st["battle"])
    IB._attach_instance_hooks(b, st)
    boss = b.sides_of("enemy")[0]
    boss["hp"] = int(boss["max_hp"] * 0.40)
    logs, ended = b.actor_auto(boss)
    # battle state 序列化（不落导演回调/状态——st 顶层持久化）
    st["battle"] = b.to_state()
    s = json.dumps(st["battle"], ensure_ascii=False)  # 可 JSON 化
    check("battle state 可 JSON 序列化", len(s) > 0)
    # 模拟断线恢复：新 st 顶层的 boss_script 保留（命令层 st 整包存 DB）
    bs = st.get("boss_script") or {}
    check("导演状态在 st（phase_count=1）", bs.get("phase_count") == 1, str(bs))
    check("导演状态可 JSON 化", json.dumps(st["boss_script"], ensure_ascii=False))
    # from_state 重建 + 重挂 hooks → 导演继续工作（再压血触发阶段 2）
    b2 = B2.from_state(st["battle"])
    IB._attach_instance_hooks(b2, st)
    boss2 = b2.sides_of("enemy")[0]
    boss2["hp"] = int(boss2["max_hp"] * 0.25)
    logs2, ended2 = b2.actor_auto(boss2)
    check("重挂后导演继续（25% → phase_count=2）",
          (st.get("boss_script") or {}).get("phase_count") == 2,
          str((st.get("boss_script") or {}).get("phase_count")))
    check("重挂后演出文案正常", any("王座之怒" in x for x in logs2), str(logs2)[-150:])


def main():
    print("5c P1 Boss 剧本导演 phases 转阶段")
    test_1_cfg_resolution()
    test_2_phase_entry_normal()
    test_3_phase_entry_enrage()
    test_4_rampage_not_triggered()
    test_5_serialize_persist()
    print(f"\n结果：{PASS} 通过 / {FAIL} 失败")
    if FAILURES:
        for f in FAILURES:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
