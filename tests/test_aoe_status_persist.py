# -*- coding: utf-8 -*-
"""v114 AOE 多目标机制正式回归测试（展示 & 持久化侧）。

覆盖：
8. 援军状态显示：_status_line 有援军时含『👥 援军：名字×数量（HP 当前/最大、...）』且格式正确；
   无援军时不显示该行
10. 战斗状态持久化：aoe 结算后 e_minions/round 经 to_state/from_state 与 db 快照正确写回/读取，
    恢复后的战斗可继续结算

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
from data.plugins.dragonfall.game.core.affix import stat_affix_stats  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(hp=5000):
    return {
        "class_name": "cls_zhan_shi", "level": 30, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 100,
        "equipment": {"weapon": {"name": "测试剑", "stats": {"atk": 1000, "matk": 1000},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": [], "race": "human",
    }


def mk_enemy(hp=10 ** 9):
    return {"name": "测试怪", "hp": hp, "max_hp": hp, "atk": 0,
            "def": 0, "mdef": 0, "spd": 10}


def mk_minion(hp, name="测试怪爪牙"):
    return {"name": name, "hp": hp, "max_hp": hp, "atk": 100, "matk": 0}


def main():
    clean_db()
    m = Main(None)
    info_xf = E.skill_info("cls_zhan_shi", "旋风斩")
    check("数据：旋风斩带 aoe=True", bool(info_xf and info_xf.get("aoe")), str(info_xf))

    # ============ 8. 援军状态显示 ============
    print("\n===== 8. 援军状态显示：_status_line =====\n")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(), {}, p)
    b.e_minions = [mk_minion(500, "测试的爪牙"), mk_minion(300, "测试的爪牙")]
    line = m._status_line(p, b)
    expect_line = "👥 援军：测试的爪牙×2（HP 500/500、300/400）"
    # 第二只 hp=300 max_hp=400 → 验证『当前/最大』各自展示
    b.e_minions[1]["max_hp"] = 400
    line = m._status_line(p, b)
    check("有援军时包含援军行", "👥 援军：" in line, repr(line))
    check("格式：名字×数量（HP 当前/最大、...）", expect_line in line, f"{expect_line!r} not in {line!r}")
    # 同名分组：换一只不同名 → 两行
    b.e_minions[1]["name"] = "别的爪牙"
    line2 = m._status_line(p, b)
    check("不同名分组：两行各自 ×1",
          "👥 援军：测试的爪牙×1（HP 500/500）" in line2
          and "👥 援军：别的爪牙×1（HP 300/400）" in line2, repr(line2))
    # 无援军 → 不含该行
    b.e_minions = []
    line3 = m._status_line(p, b)
    check("无援军时不显示援军行", "援军" not in line3, repr(line3))

    # ============ 10. 战斗状态持久化 ============
    print("\n===== 10. 战斗状态持久化：e_minions / round 写回与读取 =====\n")
    random.seed(31)
    p10 = mk_player()
    b10 = BT.Battle("monster", mk_enemy(), {}, p10)
    b10.round = 5
    b10.e_minions = [mk_minion(12345), mk_minion(9999, "二号爪牙")]
    st10 = b10._player_stats(p10)
    random.seed(31)
    logs10 = b10._player_skill(st10, "旋风斩", info_xf, p10)
    m0 = [x["hp"] for x in b10.e_minions]
    check("aoe 结算后 e_minions 存活", len(b10.e_minions) == 2 and all(h > 0 for h in m0),
          str(b10.e_minions))
    st = b10.to_state()
    check("to_state 含 e_minions 与 round", st.get("e_minions") and st.get("round") == 5,
          str({k: st.get(k) for k in ("e_minions", "round")}))
    b11 = BT.Battle.from_state(st)
    check("from_state 恢复 e_minions 一致", b11.e_minions == b10.e_minions,
          f"{b11.e_minions} vs {b10.e_minions}")
    check("from_state 恢复 round 一致", b11.round == b10.round == 5,
          f"round={b11.round}")
    # db 快照往返（instance/战斗持久化同款 db.save_battle / db.get_battle）
    db.save_battle("g10", "q10", st)
    st_rt = db.get_battle("g10", "q10")["state"]
    check("db 快照写回 e_minions 一致", st_rt.get("e_minions") == st.get("e_minions"),
          str(st_rt.get("e_minions")))
    check("db 快照写回 round 一致", st_rt.get("round") == 5, f"round={st_rt.get('round')}")
    # 恢复后的战斗可继续 aoe 结算（援军继续扣血）
    random.seed(32)
    hp_before = b11.e_minions[0]["hp"]
    boss_hp_before = b11.enemy["hp"]
    logs11 = b11._player_skill(b11._player_stats(p10), "旋风斩", info_xf, p10)
    loss = hp_before - b11.e_minions[0]["hp"]
    boss_loss = boss_hp_before - b11.enemy["hp"]
    check("恢复后继续 aoe：援军扣血 == Boss 实损（全额）", loss == boss_loss and boss_loss > 0,
          f"loss={loss} boss={boss_loss}")
    check("恢复后继续 aoe：援军文案行存在",
          any("对【测试怪爪牙】造成" in x for x in logs11), str(logs11[:3]))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
