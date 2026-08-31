# -*- coding: utf-8 -*-
"""T7 · 6 个改版被动节拍器全链路行为验证（只读，独立私有临时库）
覆盖：渠道匹配（普攻/施法/受击）、叠加（独立 roll / 加法）、满溢口径、继承、死代码、死被动。
运行：python workspace/qa_v1302f/t7_sim.py
"""
import io, os, sys, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

_TESTS = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\tests"
_DB = os.path.join(tempfile.gettempdir(), "t7_audit_private.db")
if os.path.exists(_DB):
    os.remove(_DB)
os.environ["GWEN_GAME_DB"] = _DB
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, _TESTS)
from conftest import C, E, BT, clean_db  # noqa: E402
from unittest import mock

clean_db()
ok = fail = 0
def chk(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1; print(f"  ✅ {name}")
    else:
        fail += 1; print(f"  ❌ {name} {detail}")

def make_enemy(hp=5000, atk=40):
    return {"name": "靶子", "hp": hp, "max_hp": hp, "atk": atk, "matk": 40,
            "def": 20, "mdef": 20, "spd": 5, "crit": 0.05}

def mk_player(cls, tier, path, learned=(), level=40):
    return {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": level,
            "hp": 400, "max_hp": 400, "mp": 200, "max_mp": 200,
            "equipment": {}, "attributes": {}, "race": None,
            "learned_skills": list(learned), "name": "T7勇者"}

def nb(cls, tier, path, **kw):
    p = mk_player(cls, tier, path, **kw)
    b = BT.Battle("monster", make_enemy(), player=p)
    return b, p

print("===== ① 鹰眼 / 追踪印记（mark_extra）：渠道可达性 =====")
b, p = nb("cls_you_xia", 0, 0, learned=["鹰眼", "追踪印记"])
pm = b._passive_map(p)
chk("被动汇总：鹰眼+追踪印记 都在 mark_extra proc 列表（独立条目）",
    len(pm["proc"].get("mark_extra", [])) == 2, str(pm["proc"].get("mark_extra")))
# 静态证明：element 技能只在法师树
from data.plugins.dragonfall.game.data import skills as SK
elm_owners = set()
def walk_elm(d, owner):
    if isinstance(d, dict):
        if d.get("kind") not in (None, "被动") and d.get("element"):
            elm_owners.add(owner)
        for v in d.values():
            walk_elm(v, owner)
for dn_ in ("PLAYER_SKILLS", "BRANCH_SKILLS", "TUTOR_SKILLS", "_ADD_HIDDEN_SKILLS"):
    for own, dd in getattr(SK, dn_, {}).items():
        walk_elm(dd, own)
chk("静态证明：全库带 element 的技能只属于 cls_fa_shi（游侠零 element 技能）",
    elm_owners == {"cls_fa_shi"}, str(elm_owners))
# 行为：游侠施放 林语印记（mech mark）→ 元素印记路径不触发
b2, p2 = nb("cls_you_xia", 0, 0, learned=["鹰眼", "追踪印记", "林语印记"], level=40)
b2.resources["energy"] = 40
with mock.patch.object(BT.random, "random", return_value=0.0):  # mark_extra 必中也会因无 element 不进入消费点
    logs = b2._do_player_skill("林语印记", p2)
mks = {k: v for k, v in b2.e_buffs.items() if k in E.ELEMENT_MARKS.values()}
chk("行为：游侠施法 林语印记 → 元素印记 0 层（mark_extra 无处消费）",
    sum(mks.values()) == 0, f"e_buffs={b2.e_buffs} 元素印记={mks}")
mark_debuff = (b2.enemy.get("debuffs") or {}).get("mark", {}).get("n", 0)
chk("对照：林语印记 mech=mark 走标记层（猎杀标记 1 层，与元素印记不同系统）",
    mark_debuff == 1, f"mark={mark_debuff}")
# 白盒：消费点循环（battle.py:3388-3390 同构）两个 mark_extra 条目独立 roll、各自 +1 层
def _loop(seq):
    extra = 1
    procs = [("鹰眼", {"chance": 0.15}), ("追踪印记", {"chance": 0.3})]
    for _pn, _ps in procs:
        if seq.pop(0) < float(_ps.get("chance", 0.3)):
            extra += 1
    return extra
chk("独立roll：鹰眼中/追踪中（roll 0.10,0.20）→ 印记 1+1+1=3",
    _loop([0.10, 0.20]) == 3)
chk("独立roll：鹰眼中/追踪否（roll 0.10,0.99）→ 印记 1+1=2",
    _loop([0.10, 0.99]) == 2)
chk("独立roll：鹰眼否/追踪中（roll 0.99,0.10）→ 印记 1+1=2（与上一个对称=独立非串联）",
    _loop([0.99, 0.10]) == 2)

print("===== ② 战争咆哮（res_gain_bonus）：渠道匹配 =====")
b, p = nb("cls_zhan_shi", 0, 0, learned=["战争咆哮"])
b._resource_on_attack(p)
chk("普攻命中：怒气 = 1(on_attack)+1(咆哮) = 2", b.resources.get("rage") == 2, f"rage={b.resources.get('rage')}")
b2, p2 = nb("cls_zhan_shi", 0, 0, learned=["战争咆哮"])
b2._resource_on_skill(p2)  # 技能命中渠道（on_skill=2）
chk("技能命中：怒气 = 2(on_skill)（咆哮未加成，与『全渠道』意图不符）",
    b2.resources.get("rage") == 2, f"rage={b2.resources.get('rage')}")
b3, p3 = nb("cls_zhan_shi", 0, 0, learned=["战争咆哮"])
b3._damage_player(p3, 50, [])
chk("受击：怒气 = 1(on_hit)（咆哮未加成）", b3.resources.get("rage") == 1, f"rage={b3.resources.get('rage')}")
# 狂战之魂（非 proc 格式同键被动）叠加面
b4, p4 = nb("cls_zhan_shi", 2, 2, learned=["战争咆哮", "狂战之魂"])
b4._resource_on_attack(p4)
chk("叠加面：战争咆哮 + 狂战之魂 普攻 = 2（狂战之魂 res_gain_bonus:1 非 proc 格式未被 _passive_map 收纳）",
    b4.resources.get("rage") == 2, f"rage={b4.resources.get('rage')} pm={ [x[0] for x in b4._passive_map(p4)['proc'].get('res_gain_bonus', [])] }")

print("===== ③ 魔力贯穿（attack_res）：渠道匹配 =====")
b, p = nb("cls_chronomancer", 1, 1, learned=["魔力贯穿"])
b._resource_on_attack(p)
chk("普攻命中：时之沙 = 0(on_attack)+1(贯穿) = 1（唯一触发渠道）",
    b.resources.get("time_sand") == 1, f"time_sand={b.resources.get('time_sand')}")
b2, p2 = nb("cls_chronomancer", 1, 1, learned=["魔力贯穿"])
b2._resource_on_skill(p2)
chk("施法命中：时之沙 = 1(on_skill)（贯穿未加成，与『施法命中+1沙』意图不符）",
    b2.resources.get("time_sand") == 1, f"time_sand={b2.resources.get('time_sand')}")

print("===== ④ 磐石体 / 墓穴护甲 / 神圣坚韧（dmg_taken reduce + res_gain）=====")
b, p = nb("cls_wu_seng", 0, 0, learned=["磐石体"])
logs = []
with mock.patch.object(BT.random, "random", return_value=0.99):
    b._damage_player(p, 50, logs)
chk("磐石体：受击 50 → 减伤 int(50×0.05)=2（dmg 48）", "被动减伤 2 点" in str(logs), str(logs[:4]))
chk("磐石体：受击 → 气 +1", b.resources.get("chi") == 1, f"chi={b.resources.get('chi')}")
b2, p2 = nb("cls_mu_shi", 0, 0, learned=["神圣坚韧"])
logs2 = []
with mock.patch.object(BT.random, "random", return_value=0.99):
    b2._damage_player(p2, 50, logs2)
chk("神圣坚韧：受击 → 信仰 1(on_hit基础)+1(被动) = 2 + 减伤 2 点", b2.resources.get("faith") == 2 and "被动减伤 2 点" in str(logs2), f"faith={b2.resources.get('faith')}")
b3, p3 = nb("cls_hymn", 1, 1, learned=["墓穴护甲"])
logs3 = []
with mock.patch.object(BT.random, "random", return_value=0.99):
    b3._damage_player(p3, 50, logs3)
chk("墓穴护甲：受击 → 悼咏 1(on_hit基础)+1(被动) = 2 + 减伤 2 点", b3.resources.get("canticle") == 2 and "被动减伤 2 点" in str(logs3), f"canticle={b3.resources.get('canticle')}")
# 叠加：磐石体 + 磐石之心（同渠道双 dmg_taken，加法）
b4, p4 = nb("cls_wu_seng", 2, 2, learned=["磐石体", "磐石之心"])
logs4 = []
with mock.patch.object(BT.random, "random", return_value=0.99):
    b4._damage_player(p4, 50, logs4)
chk("叠加：磐石体5% + 磐石之心5% = 减伤 4 点（加法，各自按原 dmg 计）",
    "被动减伤 4 点" in str(logs4), str(logs4[:4]))
# 满溢口径：满资源时 res_gain 是否转盾（对照 _res_gain_class 的 overflow_shield）
b5, p5 = nb("cls_wu_seng", 0, 0, learned=["磐石体"])
b5.resources["chi"] = 10
with mock.patch.object(BT.random, "random", return_value=0.99):
    b5._damage_player(p5, 50, [])
s5 = sum(int(v.get("value", 0) or 0) for v in (b5.p_shields or {}).values())
chk("满气边缘：磐石体受击 +1 溢出 → 气封顶 10 且无转盾（E.core_resource_gain 直调，绕过 overflow_shield 管线）",
    b5.resources.get("chi") == 10 and s5 == 0, f"chi={b5.resources.get('chi')} shield={s5}")
b6, p6 = nb("cls_hymn", 1, 1, learned=["墓穴护甲"])
b6.resources["canticle"] = 10
with mock.patch.object(BT.random, "random", return_value=0.99):
    b6._damage_player(p6, 50, [])
s6 = sum(int(v.get("value", 0) or 0) for v in (b6.p_shields or {}).values())
chk("满悼咏边缘：同一次受击 on_hit 溢出 → 转盾 5，墓穴护甲 res_gain +1 溢出 → 蒸发（同资源两条管线口径不一）",
    b6.resources.get("canticle") == 10 and s6 == 5, f"canticle={b6.resources.get('canticle')} shield={s6}（若被动也走管线应盾 10）")

print("===== ⑤ 被动学习/继承（带着进转职线）=====")
b, p = nb("cls_wu_seng", 1, 1, learned=["磐石体"])
chk("拳师攻线(T1 path1)：磐石体仍在被动汇总（基础被动带进转职线）",
    len(b._passive_map(p)["proc"].get("dmg_taken", [])) == 1)
b2, p2 = nb("cls_zhan_shi", 1, 1, learned=["战争咆哮"])
chk("战士守线(T1 path1)：战争咆哮仍在被动汇总",
    len(b2._passive_map(p2)["proc"].get("res_gain_bonus", [])) == 1)
b3, p3 = nb("cls_hymn", 1, 1, learned=["墓穴护甲", "神圣坚韧"])  # 传承后旧被动残留模拟
pm3 = b3._passive_map(p3)
chk("隐藏线(暗影神谕)：墓穴护甲 生效（觉醒即得）",
    len(pm3["proc"].get("dmg_taken", [])) == 1, str(pm3["proc"].get("dmg_taken")))
chk("隐藏线：旧牧师基础被动 神圣坚韧 不再解析（跨职业传承清空 → 无越权残留）",
    "神圣坚韧" not in [x[0] for x in pm3["proc"].get("dmg_taken", [])],
    str(pm3["proc"].get("dmg_taken")))

print("===== ⑥ 死代码 / 文案残留 =====")
b, p = nb("cls_mu_shi", 0, 0)
chk("dmg_taken_heal 消费端：当前全库无技能挂载（神圣坚韧改版后遗留死代码）",
    b._passive_map(p)["proc"].get("dmg_taken_heal", []) == [])
import re
src_bp = open(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\battle.py", encoding="utf-8").read()
src_cp = open(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\core\battle_conds.py", encoding="utf-8").read()
chk("文案残留：battle.py:5006 段注释仍称『神圣坚韧=受击按概率回血』（数据已改 dmg_taken，注释过时）",
    "被动·神圣坚韧" in src_bp and "受击后按 chance 概率回复 pct 生命" in src_bp)
chk("文案残留：battle_conds.py 注释『首回合，战争咆哮』（已改 proc，注释过时）",
    "战争咆哮" in src_cp)

print(f"\n===== T7 行为验证: {ok} passed / {fail} failed =====")
sys.exit(1 if fail else 0)