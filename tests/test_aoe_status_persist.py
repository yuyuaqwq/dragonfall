# -*- coding: utf-8 -*-
"""v114 AOE 多目标机制回归测试（展示 & 持久化侧，v2 站位语义重写版）。

历史：本文件原依赖 v1 的 `e_minions` 独立字段（援军展示/持久化）。v2 已改为多对多
站位：敌方单位统一存在于 `enemies` 阵列（单位级 buffs/stacks/defending/charging），
`to_state` 不再把 `e_minions` 序列化为独立语义键（`enemies` 才是权威阵列）。

本版按 v2 语义重写，保持原测试意图不变：
- 站位/阵列展示辅助：enemies 每单位带站位字段且可序列化
- AOE 结算后阵列多目标状态（各自 hp/rank/单位级 buffs）正确
- 战斗状态持久化：enemies/round/单位级字段经 to_state/from_state 与 db 快照正确写回/读取，
  恢复后的战斗可继续 AOE 结算

环境铁律：私有库 test_aoe_status_persist.db；不改任何源码。
"""
import os
import sys
import random

os.environ["GWEN_GAME_DB"] = os.path.abspath("test_aoe_status_persist.db")
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.core import formation as FM  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(hp=5000, reach=3):
    return {
        "class_name": "cls_zhan_shi", "level": 30, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 100, "reach": reach,
        "equipment": {"weapon": {"name": "测试剑", "stats": {"atk": 1000, "matk": 1000},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": [], "race": "human",
    }


def mk_enemy(name, rank=1, hp=10 ** 9, def_=0, mdef=0, buffs=None, stacks=None, charging=None):
    return {"uid": name, "name": name, "side": "enemy", "rank": rank, "reach": 2,
            "hp": hp, "max_hp": hp, "atk": 10, "matk": 10, "def": def_, "mdef": mdef,
            "spd": 10, "crit": 0.0,
            "buffs": buffs or {}, "stacks": stacks or {},
            "defending": False, "charging": charging}


def main():
    clean_db()
    m = Main(None)
    info_xf = E.skill_info("cls_zhan_shi", "旋风斩")
    info_all = dict(info_xf)
    info_all["aoe"] = "all"   # 测试 AOE 打全阵的持久化
    info_all["aoe_falloff"] = 1.0

    # ============ 8. 阵列单位站位字段 ============
    print("\n===== 8. 阵列单位站位字段（rank/reach/buffs/stacks/defending/charging）=====\n")
    e1 = mk_enemy("爪牙甲", rank=1, hp=500)
    e2 = mk_enemy("爪牙乙", rank=2, hp=400, buffs={"atk_up": 2}, charging={"skill": "聚气", "left": 1, "name": "聚气"})
    b = BT.Battle("monster", None, {}, mk_player(), enemies=[e1, e2])
    check("enemies 每单位含站位字段",
          all(k in b.enemies[i] for i in range(2)
              for k in ("rank", "reach", "uid", "buffs", "stacks", "defending", "charging")),
          str([{k: u.get(k) for k in ("rank", "reach", "uid")} for u in b.enemies]))
    check("rank/reach 正确", [u["rank"] for u in b.enemies] == [1, 2]
          and [u["reach"] for u in b.enemies] == [2, 2], str([(u["rank"], u["reach"]) for u in b.enemies]))
    check("单位级 buffs/charging 保留", b.enemies[1]["buffs"].get("atk_up") == 2
          and b.enemies[1]["charging"]["left"] == 1, str(b.enemies[1]))
    # 兼容代理：主目标 = 最前排存活
    check("enemy property 指向最前排存活", b.enemy["name"] == "爪牙甲", str(b.enemy["name"]))

    # ============ 9. AOE 结算后阵列多目标状态 ============
    print("\n===== 9. AOE（scope=all）结算后阵列多目标各自扣血 =====\n")
    random.seed(31)
    p = mk_player(reach=3, hp=5000)
    p["learned_skills"] = ["旋风斩"]
    b9 = BT.Battle("monster", None, {}, p,
                   enemies=[mk_enemy("A", rank=1, hp=10 ** 9), mk_enemy("B", rank=2, hp=10 ** 9)])
    b9.round = 5
    st9 = b9._player_stats(p)
    random.seed(31)
    logs9 = b9._player_skill(st9, "旋风斩", info_all, p)
    a_hp, b_hp = [u["hp"] for u in b9.enemies]
    check("A 掉血且存活", a_hp < 10 ** 9 and a_hp > 0, f"hp={a_hp}")
    check("B 掉血且存活", b_hp < 10 ** 9 and b_hp > 0, f"hp={b_hp}")
    check("A/B 同掉血（aoe_falloff=1.0 前排/后排均全额）",
          (10 ** 9 - a_hp) == (10 ** 9 - b_hp) and a_hp < 10 ** 9,
          f"A={a_hp} B={b_hp}")

    # ============ 10. 战斗状态持久化：enemies/round/单位级字段 与 db 快照往返 ============
    print("\n===== 10. 战斗状态持久化：enemies/round/单位级字段 写回与读取 =====\n")
    st = b9.to_state()
    check("to_state 含完整 enemies 阵列与 round", st.get("enemies") and st.get("round") == 5,
          str({k: st.get(k) for k in ("enemies", "round")}))
    check("to_state enemies 保留单位级 buffs/stacks/charging",
          all(u.get("buffs") is not None and u.get("stacks") is not None
              and "charging" in u for u in st.get("enemies", [])),
          str([{k: u.get(k) for k in ("name", "rank", "buffs", "charging")} for u in st.get("enemies", [])]))
    b11 = BT.Battle.from_state(st)
    check("from_state 恢复 enemies 阵列一致", b11.enemies == b9.enemies,
          f"{b11.enemies} vs {b9.enemies}")
    check("from_state 恢复 round 一致", b11.round == b9.round == 5, f"round={b11.round}")
    check("from_state 恢复单位级字段（B buffs/charging）",
          b11.enemies[1]["buffs"] == b9.enemies[1]["buffs"]
          and b11.enemies[1]["charging"] == b9.enemies[1]["charging"],
          str(b11.enemies[1]))
    # db 快照往返（instance/战斗持久化同款 db.save_battle / db.get_battle）
    db.save_battle("g10", "q10", st)
    st_rt = db.get_battle("g10", "q10")["state"]
    check("db 快照写回 enemies 一致", st_rt.get("enemies") == st.get("enemies"),
          str(st_rt.get("enemies")))
    check("db 快照写回 round 一致", st_rt.get("round") == 5, f"round={st_rt.get('round')}")
    # 旧存档容错：只有 enemy（单怪）+ 旧 e_buffs 时 from_state 并入主单位 buffs
    legacy_st = {"type": "monster", "enemy": mk_enemy("旧怪", rank=1, hp=999),
                 "e_buffs": {"atk_up": 3}}
    b_legacy = BT.Battle.from_state(legacy_st)
    check("旧存档 e_buffs 并入主单位 buffs",
          b_legacy.enemy["buffs"].get("atk_up") == 3, str(b_legacy.enemy["buffs"]))
    # 恢复后的战斗可继续 aoe（阵列各单位继续扣血）
    random.seed(32)
    before = {u["name"]: u["hp"] for u in b11.enemies}
    logs11 = b11._player_skill(b11._player_stats(p), "旋风斩", info_all, p)
    loss = {u["name"]: before[u["name"]] - u["hp"] for u in b11.enemies
            if u["hp"] < before[u["name"]]}
    check("恢复后继续 aoe：A/B 都继续扣血", loss.get("A", 0) > 0 and loss.get("B", 0) > 0,
          f"loss={loss}")
    check("恢复后 aoe 文案逐目标行存在",
          all(any(f"对【{n}】造成" in x for x in logs11) for n in ("A", "B")), str(logs11))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
