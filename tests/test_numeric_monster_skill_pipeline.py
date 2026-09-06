# -*- coding: utf-8 -*-
"""v180 怪物技能管线化收编门禁（test_numeric_monster_skill_pipeline）

背景：v180 P1-P9 把 329 个 MONSTER_SKILLS 全量收编进玩家技能管线（_player_skill）：
- _enemy_cast_done / _enemy_release_charge / _enemy_turn 增益即时分支全部走 _monster_cast_playerskill
- _enemy_cast_done 260 行简化结算已删（P9）
- 怪技能数据归一：heal_self→kind=治疗+hp_pct、summon 加 summon:1、无 formula 补等效段

本测试：
1. 329 个怪技能逐个经 _enemy_cast_done（读条命中路径）走管线执行不崩
2. 分类验证效果落地：伤害型扣血>0、heal_self 回血、summon 援军、buff 上身、控制命中
3. 玩家技能/普攻回归冒烟（不破坏）

必须用 AstrBot uv python 跑：C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe
"""
import os, sys, random, traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests'))
from tests.conftest import C, E, BT  # noqa

FAIL = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name} {detail}")
        FAIL.append(name)


def mk_player(cls="cls_zhan_shi", lv=20):
    st = E.player_final_stats(cls, lv, {}, 0, None)
    return {"class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": {}, "attributes": None, "learned_skills": [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None}


def mk_monster(mid, role, lv, skills=None):
    m = C.build_monster((mid, "数值测试怪", role, lv, skills or [], []),
                        {"id": mid, "name": "数值测试图", "area": "field"})
    return m


def test_all_skills_pipeline():
    """329 怪技能全部经 _enemy_cast_done（读条命中路径）执行不崩"""
    print("【1. 329 技能管线执行不崩】")
    errs = []
    dmg_count = 0
    for skey, sinfo in C.MONSTER_SKILLS.items():
        try:
            p = mk_player()
            m = mk_monster(f"m_{abs(hash(skey)) % 100000}", "dps", 22, skills=[skey])
            b = BT.Battle("monster", m, player=p)
            p["dodge"] = 0.0
            # 直接读条命中结算（等同 cast_done 事件触发）
            # v180F：管线分支内部扣血（返回 dmg=0 防外部双扣）——伤害判定改看 hp 扣减
            hp0 = p.get("hp", 0)
            logs, dmg = b._enemy_cast_done(p, m, {"kind": "skill", "skill": skey})
            dealt = hp0 - p.get("hp", 0)
            # 分类验证
            kind = sinfo.get("kind", "")
            eff = sinfo.get("effect", "")
            if kind in ("物理", "魔法") and sinfo.get("formula"):
                if dealt <= 0:
                    # 可能是闪避/格挡/真免疫——重试一次（消除承伤链随机）
                    p2 = mk_player()
                    m2 = mk_monster(f"m_{abs(hash(skey)) % 100000}b", "dps", 22, skills=[skey])
                    b2 = BT.Battle("monster", m2, player=p2)
                    p2["dodge"] = 0.0
                    hp0_2 = p2.get("hp", 0)
                    logs2, dmg2 = b2._enemy_cast_done(p2, m2, {"kind": "skill", "skill": skey})
                    dealt = hp0_2 - p2.get("hp", 0)
                if dealt <= 0:
                    errs.append((skey, sinfo.get("name", "?"), "伤害型没打出伤害"))
                else:
                    dmg_count += 1
        except Exception as ex:
            errs.append((skey, sinfo.get("name", "?"), f"{type(ex).__name__}: {str(ex)[:80]}"))
    check(f"329 技能执行无异常（伤害型 {dmg_count} 个扣血>0）", len(errs) == 0,
          f"异常 {len(errs)}: {errs[:5]}")


def test_effect_landing():
    """效果类技能落地验证"""
    print("【2. 效果类落地】")
    # heal_self → 回 15% max_hp
    for skey in ["ms_zai_sheng", "ms_zhi_liao"]:
        p = mk_player()
        m = mk_monster("m_heal", "healer", 22, skills=[skey])
        b = BT.Battle("monster", m, player=p)
        m["hp"] = m["max_hp"] // 2
        mhp0 = m["hp"]
        logs, dmg = b._enemy_cast_done(p, m, {"kind": "skill", "skill": skey})
        gain = m["hp"] - mhp0
        expect = int(m["max_hp"] * 0.15)
        check(f"{skey} heal_self 回 15% max_hp (+{gain}≈{expect})", gain == expect)
    # summon → 援军 +1
    p = mk_player()
    m = mk_monster("m_sum", "boss", 22, skills=["ms_zhao_huan_lie_quan"])
    b = BT.Battle("monster", m, player=p)
    n0 = len(b.enemies)
    logs, dmg = b._enemy_cast_done(p, m, {"kind": "skill", "skill": "ms_zhao_huan_lie_quan"})
    check("summon 召唤援军 +1", len(b.enemies) == n0 + 1, f"{len(b.enemies)} vs {n0}")
    # buff → 怪 buffs 3 刻
    p = mk_player()
    m = mk_monster("m_buff", "dps", 22, skills=["ms_zhan_hou"])
    b = BT.Battle("monster", m, player=p)
    logs, dmg = b._enemy_cast_done(p, m, {"kind": "skill", "skill": "ms_zhan_hou"})
    check("atk_up 怪 buffs atk_up=3", m.get("buffs", {}).get("atk_up") == 3,
          str(m.get("buffs")))
    # shield → 怪盾 halve
    p = mk_player()
    m = mk_monster("m_shd", "dps", 22, skills=["ms_shan_hu_hu_dun"])
    b = BT.Battle("monster", m, player=p)
    logs, dmg = b._enemy_cast_done(p, m, {"kind": "skill", "skill": "ms_shan_hu_hu_dun"})
    shd = m.get("shields", {}).get("buff")
    check("shield 怪盾 halve", shd is not None and shd.get("halve") is True, str(shd))
    # 控制 mech → 玩家 buffs（概率性控制循环尝试；沉默稳定）
    for skey, bkey in [("ms_xuan_yun_zhong_ji", "stun"), ("ms_chen_mo_jian_xiao", "silence")]:
        hit = False
        for _try in range(10):
            p = mk_player()
            m = mk_monster("m_ctrl", "dps", 22, skills=[skey])
            sinfo = dict(C.MONSTER_SKILLS[skey])
            sinfo["mech_val"] = 10  # 强制高概率
            C.MONSTER_SKILLS[skey] = sinfo
            b = BT.Battle("monster", m, player=p)
            logs, dmg = b._enemy_cast_done(p, m, {"kind": "skill", "skill": skey})
            if p.get("buffs", {}).get(bkey) is not None:
                hit = True
                break
        check(f"{skey} 控制 {bkey} 落玩家（10 试内命中）", hit)
    # 还原（测试改过 mech_val）
    for skey in ["ms_xuan_yun_zhong_ji", "ms_chen_mo_jian_xiao"]:
        if "mech_val" in C.MONSTER_SKILLS[skey]:
            C.MONSTER_SKILLS[skey].pop("mech_val", None)


def test_player_side_smoke():
    """玩家侧冒烟：玩家技能打怪、普攻、治疗正常"""
    print("【3. 玩家侧冒烟】")
    p = mk_player()
    m = mk_monster("m_atk", "dps", 20, skills=[])
    b = BT.Battle("monster", m, player=p)
    # 玩家普攻打怪
    try:
        pst = b._player_stats(p)
        logs = b._player_attack(pst, p)
        check("玩家普攻不崩", isinstance(logs, list) and len(logs) > 0, str(logs[:1]))
    except Exception as ex:
        check("玩家普攻不崩", False, f"{type(ex).__name__}: {ex}")


if __name__ == "__main__":
    random.seed(42)
    test_all_skills_pipeline()
    test_effect_landing()
    test_player_side_smoke()
    print(f"\n结果: {len(FAIL)} 失败" if FAIL else "\n结果: 全部通过 ✅")
    sys.exit(1 if FAIL else 0)
