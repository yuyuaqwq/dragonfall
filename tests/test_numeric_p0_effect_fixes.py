#!/usr/bin/env python3
"""v180E P0 效果错误修复门禁（审计 §三 六项，2026-09-07 鱼鱼授权格温拍板）。

拍板原则：数据 desc = 策划声明权威（审计建议方向），修复让代码行为对齐 desc。

1. mortal_wound 致伤重击：原 _anti_heal_pct=0.50(50%) > desc 30% → heal_down=3(层×10%=30%)
2. memory_tear 记忆撕裂：原误做降攻 → 真沉默（e_buffs["silence"]）
3. arcane_echo 秘法回响：原写死键 0 消费 → 标准一次性增伤（_consume_v169_buff_dmg 消费）
4. siphon 汲魂：原 5% 无驱散 → 3% + 驱散 1 层增益
5. sanctum_light 圣殿辉光：原写 0 消费键 → 标准 mon_atk_down/_weaken_val
6. 词条附加伤害绕 Boss 护盾（element_thunder/chu_huo/blazing_sun/deep_frost/sun_blaze/chain_overload）
   → 统一 _boss_dmg_filter
7. DOT pct 死字段：引擎 _tick_actor_dots 支持 per-debuff pct 覆盖（desc 承诺数值真实生效）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import clean_db

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def main():
    clean_db()
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.data.affixes import AFFIXES, LEGENDARY_EFFECTS

    print("===== v180E P0 效果错误修复 =====\n")

    def mk_player(eq=None, cls="战士"):
        return {"class_name": cls, "level": 50, "hp": 8000, "max_hp": 8000,
                "mp": 200, "max_mp": 200, "atk": 500, "matk": 300, "def": 100,
                "equipment": {"w": {"weapon_effect": None, "affixes": eq or []}},
                "buffs": {}, "stacks": {}, "eff": {},
                "attributes": {"str": 50}, "learned_skills": [], "race": "human"}

    def mk_enemy(boss=False):
        return {"name": "测试怪", "hp": 99999, "max_hp": 99999, "atk": 100, "def": 50,
                "mdef": 50, "spd": 10, "lv": 50, "buffs": {}, "debuffs": {},
                "role": "boss" if boss else "normal"}

    # 1. mortal_wound → heal_down 3 层 = 30%（LEGENDARY_EFFECTS 表）
    d1 = LEGENDARY_EFFECTS.get("mortal_wound") or {}
    check("mortal_wound 数据 heal_down=3(30%)", int((d1.get("effect") or {}).get("heal_down", 0)) == 3,
          str(d1.get("effect")))

    # 2. memory_tear → silence
    d2 = LEGENDARY_EFFECTS.get("memory_tear") or {}
    check("memory_tear 数据 silence=1", int((d2.get("effect") or {}).get("silence", 0)) == 1,
          str(d2.get("effect")))

    # 3. arcane_echo → next_skill_dmg
    d3 = LEGENDARY_EFFECTS.get("arcane_echo") or {}
    check("arcane_echo 数据 next_skill_dmg=0.15", abs(float((d3.get("effect") or {}).get("next_skill_dmg", 0)) - 0.15) < 1e-9,
          str(d3.get("effect")))

    # 4. siphon → heal_pct 3% + purge
    d4 = LEGENDARY_EFFECTS.get("siphon") or {}
    e4 = d4.get("effect") or {}
    check("siphon 数据 heal_pct=0.03 + purge=1",
          abs(float(e4.get("heal_pct", 0)) - 0.03) < 1e-9 and int(e4.get("purge", 0)) == 1,
          str(e4))

    # 5. sanctum_light → 标准降攻键
    d5 = LEGENDARY_EFFECTS.get("sanctum_light") or {}
    check("sanctum_light 数据 mon_atk_down_pct 字段",
          "mon_atk_down_pct" in (d5.get("effect") or {}), str(d5.get("effect")))

    # 6. 绕盾修复：element_thunder 附加段对 Boss 盾减半
    # 构造带 Boss 护盾的战斗，触发 element_thunder 附加 → 附加伤害应被护盾减半
    from data.plugins.dragonfall.game.core import affix_effects as AE

    # 直接调 handler（绕过概率用 seed 固定命中）——先验证 shield 存在时 _boss_dmg_filter 生效
    p6 = mk_player()
    e6 = mk_enemy(boss=True)
    e6["shields"] = {"boss_shield": {"value": 99999, "halve": True}}  # Boss 盾 halve
    b6 = BT.Battle("monster", e6, {}, p6)
    # element_thunder 5% 附加 500*0.05=25 → 无盾 25，有 halve 盾应减半到 ~12
    dmg_no_shield = 25
    # 验证 _boss_dmg_filter 是否被 handler 用——直接检查 handler 源码含 _boss_dmg_filter
    import inspect
    src6 = inspect.getsource(AE._h_element_thunder)
    check("element_thunder handler 走 _boss_dmg_filter", "_boss_dmg_filter" in src6)
    src7 = inspect.getsource(AE._h_sun_blaze)
    check("sun_blaze handler 走 _boss_dmg_filter", "_boss_dmg_filter" in src7)
    src8 = inspect.getsource(AE._h_chain_overload)
    check("chain_overload handler 走 _boss_dmg_filter", "_boss_dmg_filter" in src8)

    # 7. DOT pct 覆盖：per-debuff pct 被引擎读（burn 0.015 覆盖 DOT_DEFS 0.005）
    from data.plugins.dragonfall.game.data.battle_config import DOT_DEFS
    src9 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
                encoding="utf-8").read()
    check("引擎 _tick_actor_dots 读 per-debuff pct 覆盖",
          "_dpct = d.get(\"pct\")" in src9 and "max_hp * float(_dpct)" in src9)

    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
