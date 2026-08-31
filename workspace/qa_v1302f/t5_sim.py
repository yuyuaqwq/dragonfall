# -*- coding: utf-8 -*-
"""T5 边缘模拟：只读验证（不写库）"""
import sys, os, random
_ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from game import engine as E
from game.battle import Battle
from game import content as C
import tests.test_v1302f_job_quality as T  # 复用其构造脚手架

def mk(cls, path, tier, learned, level=60, **kw):
    return T.new_battle(cls, path, tier, learned=learned, level=level, **kw)

print("== 1. 致命预谋 consume_all 分支（暗影处刑）==")
try:
    b, p = mk("cls_ci_ke", 0, 0, learned=["致命预谋", "暗影处刑"], level=95)
    b.resources["cp"] = 5
    logs = T.cast_capture(b, "暗影处刑", p)[1]
    print("   cp after consume_all+返还 =", b.resources.get("cp"), "(期望 1)", "| flag:", getattr(b, "_assassin_refund_used", None))
    print("   log:", [l for l in logs if "致命预谋" in l])
except Exception as ex:
    print("   ERR", ex)

print("\n== 2. 致命预谋 序列化还原（to_state/from_state 防重复）==")
try:
    b, p = mk("cls_ci_ke", 0, 0, learned=["致命预谋", "暗杀"], level=70)
    b.resources["cp"] = 3
    st = b.to_state()
    b2 = Battle.from_state(st)
    print("   flag restored:", getattr(b2, "_assassin_refund_used", None), "(期望 False)")
    b2.resources["cp"] = 3
    T.cast_capture(b2, "暗杀", p)
    print("   cp after first finisher (restored battle):", b2.resources.get("cp"), "(期望 1 返还)")
    st2 = b2.to_state()
    b3 = Battle.from_state(st2)
    print("   flag restored after refund:", getattr(b3, "_assassin_refund_used", None), "(期望 True)")
    b3.resources["cp"] = 3
    T.cast_capture(b3, "暗杀", p)
    print("   cp after second finisher (restored battle):", b3.resources.get("cp"), "(期望 0 不再返还)")
except Exception as ex:
    print("   ERR", ex)

print("\n== 3. 亡灵祭仪：敌方亡灵计入？阵亡骷髅（hp=0）不计？==")
try:
    b, p = mk("cls_hymn", 0, 0, learned=["召唤骷髅"])
    # 敌方亡灵（名字含骷髅/亡灵）
    b.enemy["name"] = "骷髅兵"
    b.enemies[0]["name"] = "骷髅兵"
    # 一只存活骷髅 + 一只 hp=0 骷髅（阵亡未清理）
    b.summons = [{"tid": "skeleton", "name": "骷髅兵", "hp": 50, "max_hp": 50},
                 {"tid": "skeleton", "name": "骷髅兵", "hp": 0, "max_hp": 50}]
    n = b._undead_count()
    print("   _undead_count =", n, "(存活骷髅1 + 敌方骷髅1 = 期望2；hp=0 不计)")
    b._turn_start(p)
    print("   canticle after turn_start =", b.resources.get("canticle"), "(期望 +2)")
except Exception as ex:
    print("   ERR", ex)

print("\n== 4. 亡灵祭仪 满悼咏溢出转盾（无日志但转盾）==")
try:
    b, p = mk("cls_hymn", 0, 0, learned=["召唤骷髅"])
    b.resources["canticle"] = 10
    b.summons = [{"tid": "skeleton", "name": "骷髅兵", "hp": 50, "max_hp": 50}]
    logs = b._turn_start(p)
    sh = sum(int(v.get("value", 0) or 0) for v in (b.p_shields or {}).values())
    print("   canticle:", b.resources.get("canticle"), "| shield:", sh, "| 祭仪日志:", any("亡灵祭仪" in l for l in logs))
except Exception as ex:
    print("   ERR", ex)

print("\n== 5. 反击回气：反击伤害被 Boss 护盾吸收为 0 时是否仍回气 ==")
try:
    import game.battle as BT
    b, p = mk("cls_wu_seng", 1, 1, learned=["以守为攻"], level=60)
    b.resources["chi"] = 0
    # 玩家攻击 1 → 护盾 50% 减伤 → int(1*0.5)=0
    p["atk"] = 1; p["level"] = 60
    b.enemy["def"] = 0
    b.enemy["boss_shield"] = 1000
    b.enemy["mech"] = "shield"
    logs = []
    with __import__("unittest").mock.patch.object(BT.random, "random", side_effect=[0.50, 0.05, 0.99]):
        b._damage_player(p, 50, logs)
    print("   chi =", b.resources.get("chi"), "(0 伤害反击仍 +2 回气 => 命中语义缺口)", [l for l in logs if "反击" in l])
except Exception as ex:
    import traceback; traceback.print_exc()

print("\n== 6. 主攻击路径闪避 vs 反击路径无闪避（对照）==")
try:
    import game.battle as BT
    b, p = mk("cls_wu_seng", 1, 1, learned=["以守为攻"], level=60)
    b.enemy["dodge"] = 0.30
    p["precise"] = 0.0
    logs = []
    with __import__("unittest").mock.patch.object(BT.random, "random", return_value=0.01):  # 主攻击必闪
        dmg = b._player_attack(p, logs)
    print("   主攻击 30% 闪避下 dmg =", dmg, "| logs:", [l for l in logs if "闪避" in l][:1])
except Exception as ex:
    print("   ERR", ex)

print("\n== 7. 歌类技判定 & 非歌者分支误触发（伴奏x大主教x基础技能）==")
try:
    from game import content as C
    mi = (C.CLASSES.get("cls_mu_shi") or {}).get("evolve_branches") or {}
    print("   evolve_branches:", mi)
    b, p = mk("cls_mu_shi", 1, 1, learned=["伴奏", "战歌"], level=95)  # 与官方测试同构造（tier1 path1）
    print("   玩家分支:", b._branch_name(p) if hasattr(b, "_branch_name") else "?")
    print("   吟游诗人(t1 p1) 施放 战歌:", b._is_bard_skill(p, E.skill_info("cls_mu_shi", "战歌")))
    b3, p3 = mk("cls_mu_shi", 1, 2, learned=["伴奏", "鼓舞"], level=95)  # tier2 path1=灵魂歌者
    if hasattr(b3, "_branch_name"):
        print("   玩家分支(t1?)→", b3._branch_name(p3))
    print("   灵魂歌者(t2 p1) 施放 鼓舞:", b3._is_bard_skill(p3, E.skill_info("cls_mu_shi", "鼓舞")),
          "| owner:", E.branch_skill_owner("cls_mu_shi", "鼓舞"))
    print("   灵魂歌者 施放 大治愈术(基础):", b3._is_bard_skill(p3, E.skill_info("cls_mu_shi", "大治愈术")))
    print("   大主教(t2 p2) 施放 神圣恩典:", mk("cls_mu_shi", 2, 2, level=95)._is_bard_skill(
        None if False else p3, E.skill_info("cls_mu_shi", "神圣恩典")))
    bzp = (E.skill_info("cls_mu_shi", "伴奏") or {}).get("passive") or {}
    print("   伴奏数据 chance =", bzp.get("chance"), "| proc =", bzp.get("proc"))
except Exception as ex:
    import traceback; traceback.print_exc()

print("\n== 8. 歌类技是否含蓄力技（蓄力路径回声/返还覆盖）==")
try:
    src = open(os.path.join(_ROOT, 'game', 'data', 'skills.py'), encoding='utf-8').read()
    import re
    # 找牧师德鲁伊歌者分支里带 charge 的技能
    seg = src[src.find('"cls_mu_shi"'):src.find('"cls_ci_ke"')]
    charges = re.findall(r'"name"\s*:\s*"([^"]+)"[^}]{0,200}?"charge"\s*:\s*\d+', seg)
    print("   mu_shi 技能中含 charge 的：", charges)
    # 刺客蓄力技
    seg2 = src[src.find('"cls_ci_ke"'):src.find('"cls_wu_seng"')]
    charges2 = re.findall(r'"name"\s*:\s*"([^"]+)"[^}]{0,200}?"charge"\s*:\s*\d+', seg2)
    print("   ci_ke 技能中含 charge 的：", charges2)
except Exception as ex:
    print("   ERR", ex)