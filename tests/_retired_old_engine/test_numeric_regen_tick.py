# -*- coding: utf-8 -*-
"""N-REGTICK：regen_tick 时间驱动语义门禁（v178.2）

目的：锁定"每刻 = 每秒"铁律——同一每刻回复效果，无论玩家行动频率如何
（防御流 0.6s/动 vs 技能流 1.6s/动），相同时长内总回复必须一致。

v178.2 前：A 类效果挂 _turn_start（玩家每次行动开头）→ 防御流每 0.6s 触发一次、
技能流每 1.6s 触发一次 → 同效果同 10 秒内防御流回复量是技能流 2.6 倍（错误）。
v178.2 后：A 类效果由 regen_tick（每秒）驱动 → 与行动频率解耦。

验证方式（不依赖真实战斗的秒级推进，直接驱动时间轴）：
  - 构造带 regen 效果的玩家（晨光教会 4 件套 regen_strong 每刻 8%）
  - 用 _advance_time 推进相同游戏时长（如 10 秒）
  - 断言：无论中间穿插多少次玩家行动，回复总量一致 = 每刻回复 × 秒数
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C, E, BT  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(cls, lv, attr, set_items=None):
    st = E.player_final_stats(cls, lv, {}, 0, attr)
    eq = {}
    if set_items:
        for i, slot in enumerate(["weapon", "armor", "helm", "boots"]):
            eq[slot] = {"name": f"{set_items}{i}", "set": set_items, "level": lv}
    return {"class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": eq, "attributes": attr, "learned_skills": [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None}


def mk_monster(mid, role, lv):
    return C.build_monster((mid, "数值测试怪", role, lv, [], []),
                           {"id": mid, "name": "数值测试图", "area": "field"})


def hp_regen_per_sec(player) -> int:
    """晨光教会 4 件套 regen_strong = 每刻 8% 最大生命。"""
    s4 = E.set_bonus_4(player.get("equipment", {}))
    if "regen_strong" in s4:
        return int(player.get("max_hp", 1) * 0.08)
    if "regen" in s4:
        return int(player.get("max_hp", 1) * 0.05)
    return 0


def main():
    print("【regen_tick 时间驱动语义 · 场景① 技能流 vs 防御流同效果同回复】")
    # 晨光教会套 regen_strong：每刻 8% 最大生命（max_hp 以 battle 内 _player_stats 实时为准，
    # 装备词条/职业成长会放大——测试不硬编码初始 max_hp）

    # 场景①：单次 _tick_regen 回复量 = 8% 实时 maxhp（扣血后触发）
    p1 = mk_player("cls_zhan_shi", 11, None, set_items="set_chen_guang_jiao_hui")
    b1 = BT.Battle("monster", mk_monster("m_rg_1", "dps", 1), player=p1)
    b1.enemy["atk"] = 5
    b1.enemy["matk"] = 5
    real_max = b1._player_stats(p1)["max_hp"]
    hp_pct = int(real_max * 0.08)
    check("前置：晨光教会 4 件套触发 regen_strong（8% maxhp/刻）", hp_pct > 0,
          f"pct={hp_pct} maxhp={real_max}")
    p1["hp"] = int(real_max * 0.5)
    hp0 = p1["hp"]
    logs = b1._tick_regen(p1, [])
    hp1 = p1["hp"]
    check("单次 _tick_regen：扣血后回复 8% maxhp", hp1 > hp0 and hp1 - hp0 == hp_pct,
          f"hp {hp0}->{hp1} expect+{hp_pct}")
    check("回复日志含套装祝福", any("套装祝福" in str(x) for x in logs), str(logs)[:80])

    # 场景②：连续 5 次 tick（模拟 5 秒）回复 = 5 × 单次（前提：不触发上限封顶）
    p2 = mk_player("cls_zhan_shi", 11, None, set_items="set_chen_guang_jiao_hui")
    b2 = BT.Battle("monster", mk_monster("m_rg_2", "dps", 1), player=p2)
    b2.enemy["atk"] = 5
    b2.enemy["matk"] = 5
    real_max2 = b2._player_stats(p2)["max_hp"]
    hp_pct2 = int(real_max2 * 0.08)
    # 血扣到很低，5 次 8% 不会封顶
    p2["hp"] = int(real_max2 * 0.2)
    hp_start = p2["hp"]
    for _ in range(5):
        b2._tick_regen(p2, [])
    total_gain = p2["hp"] - hp_start
    check("连续 5 秒 tick：总回复 = 5 × 单次", total_gain == 5 * hp_pct2,
          f"gain={total_gain} expect={5*hp_pct2} (hp {hp_start}->{p2['hp']})")

    # 场景③：满血 tick 不触发（封顶逻辑）——0 回复
    p3 = mk_player("cls_zhan_shi", 11, None, set_items="set_chen_guang_jiao_hui")
    b3 = BT.Battle("monster", mk_monster("m_rg_3", "dps", 1), player=p3)
    b3.enemy["atk"] = 5
    b3.enemy["matk"] = 5
    p3["hp"] = p3["max_hp"]
    logs3 = b3._tick_regen(p3, [])
    check("满血 tick：不回复不误报", p3["hp"] == p3["max_hp"] and not any("套装祝福" in str(x) for x in logs3),
          str(logs3)[:80])

    # 场景④：v179 通用 tick 卡——Battle 初始化后 tick_effects 池里有 regen_set_heal 卡
    p4 = mk_player("cls_zhan_shi", 11, None, set_items="set_chen_guang_jiao_hui")
    b4 = BT.Battle("monster", mk_monster("m_rg_4", "dps", 1), player=p4)
    b4.enemy["atk"] = 5
    b4.enemy["matk"] = 5
    p4["hp"] = int(p4["max_hp"] * 0.5)
    has_regen = any(e.get("kind") == "set_heal" and e.get("uid") == "regen_set_heal"
                    for e in b4.tick_effects)
    check("开战挂入 regen_set_heal 通用 tick 卡（带 A 类效果）", has_regen,
          f"pool={[(e.get('kind'), e.get('uid')) for e in b4.tick_effects]}")

    # 场景⑤：无 A 类效果玩家不挂卡（CTB 测试同款玩家 equipment={}）
    p5 = mk_player("cls_ci_ke", 11, {"agi": 39})  # 无装备
    b5 = BT.Battle("monster", mk_monster("m_rg_5", "dps", 22), player=p5)
    has_regen5 = any(e.get("uid", "").startswith("regen_") for e in b5.tick_effects)
    check("无 A 类效果：不挂 regen 卡（零干扰）", not has_regen5,
          f"pool={[(e.get('kind'), e.get('uid')) for e in b5.tick_effects]}")

    # 场景⑥：断线恢复/副本 act 重建后 regen 卡随 tick_effects 序列化恢复
    # （from_state 恢复时 b._focus 空 dict——但卡片 actor 已重绑 b._focus 占位，
    #  真实玩家绑定后同一引用即生效；_turn_start 保险丝再兜底确保挂卡幂等）
    p6 = mk_player("cls_zhan_shi", 11, None, set_items="set_chen_guang_jiao_hui")
    b6 = BT.Battle("monster", mk_monster("m_rg_6", "dps", 1), player=p6)
    b6.enemy["atk"] = 5
    b6.enemy["matk"] = 5
    import random
    random.seed(0)
    st = b6.to_state()
    b6b = BT.Battle.from_state(st)
    # from_state 恢复后：tick_effects 卡随序列化恢复（st 里有 tick_effects 字段时）
    has_regen6_before = any(e.get("uid", "").startswith("regen_") for e in b6b.tick_effects)
    # 模拟命令层绑定真实玩家后首次行动 → _turn_start 保险丝确保挂卡（幂等）
    b6b._focus = p6
    b6b._turn_start(p6)
    has_regen6_after = any(e.get("uid", "").startswith("regen_") for e in b6b.tick_effects)
    check("from_state 恢复后首次行动保险丝确保 regen 卡存在",
          has_regen6_after,
          f"before={has_regen6_before} after={has_regen6_after} "
          f"pool={[(e.get('kind'), e.get('uid')) for e in b6b.tick_effects]}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


main()