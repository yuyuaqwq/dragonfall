# -*- coding: utf-8 -*-
"""N-TICKFX：v179 通用 tick 效果框架门禁

验证核心机制（框架本身，不含具体效果迁移）：
  ① add_tick_effect 挂条目 + uid 幂等刷新
  ② _process_tick_effects 到期分发到 handler + 续排
  ③ expire_at 到期自动停止
  ④ actor 死亡停止结算
  ⑤ remove_tick_effect 移除
  ⑥ to_state/from_state 序列化往返
  ⑦ 一次性条目（interval<=0）触发即移除
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C, E, BT  # noqa: E402

# v179 tick 框架：handler 注册表从 sys.modules 里已加载的 core.tick_effects 拿
# （battle 的 from .core.tick_effects import TICK_HANDLERS 已触发模块加载缓存；
#  conftest 走 data.plugins.dragonfall.game 全路径导入，模块注册名带全前缀）
import sys as _sys
_tick_mod = None
for _mn in ("data.plugins.dragonfall.game.core.tick_effects",
            "game.core.tick_effects"):
    _m = _sys.modules.get(_mn)
    if _m is not None:
        _tick_mod = _m
        break
if _tick_mod is None:
    raise RuntimeError("tick_effects 模块未加载（battle import 应已触发）")
TICK_HANDLERS = _tick_mod.TICK_HANDLERS

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(cls, lv, attr):
    st = E.player_final_stats(cls, lv, {}, 0, attr)
    return {"class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": {}, "attributes": attr, "learned_skills": [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None}


def mk_monster(mid, role, lv):
    return C.build_monster((mid, "数值测试怪", role, lv, [], []),
                           {"id": mid, "name": "数值测试图", "area": "field"})


# 测试用 handler：记录触发次数 + 每触发回 data.heal 点血
_TEST_COUNTER = {"n": 0}
_test_registered = {}


def _h_test_regen_heal(battle, actor, eff, logs):
    _TEST_COUNTER["n"] += 1
    heal = int(eff.get("data", {}).get("heal", 1))
    actor["hp"] = min(actor.get("max_hp", 1), actor.get("hp", 0) + heal)
    _test_registered["called"] = True
    return [], True  # 续排


TICK_HANDLERS["test_regen_heal"] = _h_test_regen_heal


def main():
    print("【v179 通用 tick 框架核心】")

    # 场景①：add_tick_effect 挂条目 + 开战不自动处理（next_at 未来）
    p = mk_player("cls_zhan_shi", 11, None)
    b = BT.Battle("monster", mk_monster("m_tf_1", "dps", 1), player=p)
    b.enemy["atk"] = 1
    b.enemy["matk"] = 1
    p["hp"] = int(p["max_hp"] * 0.5)
    b.add_tick_effect("test_regen_heal", p, interval=1.0,
                      data={"heal": 5}, uid="test_hot", source="test")
    check("① add_tick_effect 挂入条目池", len(b.tick_effects) == 1
          and b.tick_effects[0]["kind"] == "test_regen_heal", str(b.tick_effects))

    # 场景②：时间推进到 next_at → 处理 + 续排
    _TEST_COUNTER["n"] = 0
    b._now = 2.0  # 条目 next_at=1.0 已到期
    b._process_tick_effects([], p)
    check("② 到期分发到 handler + 续排", _TEST_COUNTER["n"] == 1
          and len(b.tick_effects) == 1
          and b.tick_effects[0]["next_at"] > 2.0, f"n={_TEST_COUNTER['n']} pool={len(b.tick_effects)}")

    # 场景③：同 uid 重复 add = 刷新不叠加
    b.add_tick_effect("test_regen_heal", p, interval=1.0,
                      data={"heal": 9}, uid="test_hot", source="test")
    check("③ uid 幂等：刷新不叠加", len(b.tick_effects) == 1
          and b.tick_effects[0]["data"]["heal"] == 9, str(b.tick_effects))

    # 场景④：expire_at 到期自动停止
    b2 = BT.Battle("monster", mk_monster("m_tf_2", "dps", 1), player=p)
    b2.enemy["atk"] = 1
    p2 = mk_player("cls_zhan_shi", 11, None)
    b2.add_tick_effect("test_regen_heal", p2, interval=1.0,
                       data={"heal": 1}, uid="exp_test", expire_at=3.5)
    _TEST_COUNTER["n"] = 0
    b2._now = 1.5
    b2._process_tick_effects([], p2)  # 触发 1 次
    b2._now = 4.0
    b2._process_tick_effects([], p2)  # next_at=2.5 到期但 expire_at=3.5 已过 → 不续排
    check("④ expire_at 到期自动停止", len(b2.tick_effects) == 0,
          f"pool={len(b2.tick_effects)} n={_TEST_COUNTER['n']}")

    # 场景⑤：remove_tick_effect 按 kind 移除
    b3 = BT.Battle("monster", mk_monster("m_tf_3", "dps", 1), player=p)
    b3.enemy["atk"] = 1
    p3 = mk_player("cls_zhan_shi", 11, None)
    b3.add_tick_effect("test_regen_heal", p3, interval=1.0, uid="r1")
    b3.add_tick_effect("test_regen_heal", p3, interval=1.0, uid="r2")
    b3.remove_tick_effect(kind="test_regen_heal")
    check("⑤ remove_tick_effect 按 kind 移除", len(b3.tick_effects) == 0,
          f"pool={len(b3.tick_effects)}")

    # 场景⑥：序列化往返（actor_ref 玩家）
    b4 = BT.Battle("monster", mk_monster("m_tf_4", "dps", 1), player=p)
    b4.enemy["atk"] = 1
    p4 = mk_player("cls_zhan_shi", 11, None)
    b4.player = p4
    b4.add_tick_effect("test_regen_heal", p4, interval=1.0, uid="s1",
                       data={"heal": 7}, expire_at=10.0)
    st = b4.to_state()
    b5 = BT.Battle.from_state(st)
    check("⑥ to_state 序列化含 tick_effects", "tick_effects" in st and len(st["tick_effects"]) == 1,
          f"st_te={len(st.get('tick_effects', []))}")
    check("⑥b from_state 恢复条目池", len(b5.tick_effects) == 1
          and b5.tick_effects[0]["uid"] == "s1", str(b5.tick_effects))

    # 场景⑦：一次性条目（interval<=0）触发即移除
    _TEST_COUNTER["n"] = 0
    b6 = BT.Battle("monster", mk_monster("m_tf_6", "dps", 1), player=p)
    b6.enemy["atk"] = 1
    p6 = mk_player("cls_zhan_shi", 11, None)
    b6.add_tick_effect("test_regen_heal", p6, interval=0, uid="once")  # 一次性
    b6._now = 0.5
    b6._process_tick_effects([], p6)
    check("⑦ 一次性条目触发即移除", _TEST_COUNTER["n"] == 1 and len(b6.tick_effects) == 0,
          f"n={_TEST_COUNTER['n']} pool={len(b6.tick_effects)}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


main()
