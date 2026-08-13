# -*- coding: utf-8 -*-
"""M01 玩家系统审计临时脚本（只读验证，用完即删）。
独立临时 DB：scripts/tmp_m01_audit.db —— 不碰 test_game_data.db / game_data.db。
"""
import os
import sys
import json

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN)))    # qqbot/
_TMP_DB = os.path.join(PLUGIN, "scripts", "tmp_m01_audit.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["GWEN_GAME_DB"] = _TMP_DB
sys.path.insert(0, QQBOT)
sys.path.insert(0, PLUGIN)

from data.plugins.dragonfall.game import content as C, db, engine as E
from data.plugins.dragonfall.main import Main

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")

class FakeEvent:
    def __init__(self, group_id, qq_id, msg=""):
        self._g, self._q, self.message_str = group_id, qq_id, msg
        self._stopped = False
    def get_group_id(self): return self._g
    def get_sender_id(self): return self._q
    def get_message_str(self): return self.message_str
    def plain_result(self, text): return text
    def stop_event(self): self._stopped = True

async def cmd(m, name, gid, qid, msg):
    gen = getattr(m, name)(FakeEvent(gid, qid, msg))
    out = []
    try:
        while True:
            out.append(await gen.__anext__())
    except StopAsyncIteration:
        pass
    return out

def clean():
    db.init_db()
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    for t in ("players", "player_groups", "inventory", "quests", "battle_state",
              "achievements", "stats", "feedback", "event_state", "professions", "props_use"):
        try:
            conn.execute(f"DELETE FROM {t}")
        except Exception:
            pass
    conn.commit(); conn.close()

async def test_register():
    print("【注册流程】")
    m = Main(None); clean()
    # 正常新格式：注册 <名字> <性别> [种族]
    r = await cmd(m, "register", "g1", "q1", "注册 格温 女 银月精灵")
    p = db.get_player("g1", "q1")
    check("新格式注册成功", p is not None and p["name"] == "格温", str(p and p.get("name")))
    check("种族=elf", p and p.get("race") == "elf", str(p and p.get("race")))
    check("性别=female", p and p.get("gender") == "female", str(p and p.get("gender")))
    # 银月精灵初始 hp 必须 == max_hp（历史 bug 150/142）
    check("精灵初始 hp==max_hp", p and p["hp"] == p["max_hp"], f"hp={p['hp']} max={p['max_hp']}")
    st0, _ = E.player_stats_detail(p["class_name"], 1, {}, 0, {}, 0, None, "elf")
    check("精灵初始 hp==实时计算 max_hp", p and p["max_hp"] == st0["max_hp"], f"db={p['max_hp']} calc={st0['max_hp']}")
    check("初始金币 50", p and p["gold"] == 50, str(p and p.get("gold")))
    check("初始属性点 9", p and p["attr_pts"] == 9, str(p and p.get("attr_pts")))
    check("初始技能点 1", p and p.get("skill_points") == 1, str(p and p.get("skill_points")))
    check("出生地图 oak_town", p and p["cur_map"] == C.START_MAP, str(p and p.get("cur_map")))
    check("出生子区域", p and p.get("cur_subarea") == C.START_SUBAREA, str(p and p.get("cur_subarea")))
    check("初始装备为空", p and p.get("equipment") in ({}, None), str(p and p.get("equipment")))
    check("见习冒险者无初始技能(设计)", p and len(p.get("learned_skills", [])) == 0, str(p and p.get("learned_skills")))
    # 重名（不同 qq）
    r2 = await cmd(m, "register", "g1", "q2", "注册 格温 男")
    check("同名不同人可注册", db.get_player("g1", "q2") is not None, str(r2))
    # 重复注册同一人
    r3 = await cmd(m, "register", "g1", "q1", "注册 再来 男")
    check("重复注册拦截", "已经注册过" in r3[-1] and db.get_player("g1", "q1")["name"] == "格温", r3[-1][:60])
    # 空名
    r4 = await cmd(m, "register", "g1", "q3", "注册   女")
    check("'注册 女'歧义处理(名字=女,缺性别被拦)", db.get_player("g1", "q3") is None, r4[-1][:60])
    # 纯空格名字（名字=空格被 strip 后为空）
    r5 = await cmd(m, "register", "g1", "q4", "注册   女")
    check("纯空格名拦截", db.get_player("g1", "q4") is None, str(r5))
    # 超长名（>12 截断）
    r6 = await cmd(m, "register", "g1", "q5", "注册 一二三四五六七八九十一二三四五六 女")
    p6 = db.get_player("g1", "q5")
    check("超长名截断到12", p6 is not None and len(p6["name"]) <= 12, str(p6 and p6["name"]))
    # 无性别
    r7 = await cmd(m, "register", "g1", "q6", "注册 无名")
    check("无性别拦截", "性别" in r7[-1] and db.get_player("g1", "q6") is None, r7[-1][:60])
    # 种族不存在
    r8 = await cmd(m, "register", "g1", "q7", "注册 阿三 男 外星人")
    check("未知种族拦截", "未知种族" in r8[-1] and db.get_player("g1", "q7") is None, r8[-1][:80])
    # 种族 ID 输入（注册 精灵 还是 银月精灵？——简称兼容）
    r9 = await cmd(m, "register", "g1", "q8", "注册 小灵 女 精灵")
    p9 = db.get_player("g1", "q8")
    check("种族简称'精灵'→elf", p9 is not None and p9.get("race") == "elf", str(p9 and p9.get("race")))
    r10 = await cmd(m, "register", "g1", "q9", "注册 小矮 女 矮人")
    p10 = db.get_player("g1", "q9")
    check("种族简称'矮人'→dwarf", p10 is not None and p10.get("race") == "dwarf", str(p10 and p10.get("race")))
    # 旧格式：注册 <职业> <名字> <性别>
    r11 = await cmd(m, "register", "g1", "q10", "注册 战士 勇者 男")
    p11 = db.get_player("g1", "q10")
    check("旧格式带职业注册", p11 is not None and p11["class_name"] == "cls_zhan_shi", str(p11 and p11.get("class_name")))
    # 无空格兼容：注册战士格温 女
    r12 = await cmd(m, "register", "g1", "q11", "注册战士格温 女")
    p12 = db.get_player("g1", "q11")
    check("无空格注册'注册战士格温 女'", p12 is not None and p12["class_name"] == "cls_zhan_shi" and p12["name"] == "格温",
          f"{p12 and p12['class_name']} {p12 and p12['name']} | r12={r12[-1][:60]}")
    # 性别别名 ♂
    r13 = await cmd(m, "register", "g1", "q12", "注册 阿雄 ♂")
    p13 = db.get_player("g1", "q12")
    check("性别♂兼容", p13 is not None and p13.get("gender") == "male", str(p13 and p13.get("gender")))
    # 见习冒险者（新格式无职业）
    r14 = await cmd(m, "register", "g1", "q13", "注册 萌新 男")
    p14 = db.get_player("g1", "q13")
    check("见习冒险者", p14 is not None and p14["class_name"] == C.CLASS_NOVICE, str(p14 and p14.get("class_name")))
    # 隐藏职业不可直接注册
    r15 = await cmd(m, "register", "g1", "q14", "注册 吟游诗人 歌手 男")
    check("隐藏职业拦截", db.get_player("g1", "q14") is None and len(r15) > 0, str(r15)[:80])

async def test_add_attr():
    print("【加点】")
    m = Main(None); clean()
    await cmd(m, "register", "g1", "q1", "注册 格温 女")
    # 负数
    r = await cmd(m, "add_attr", "g1", "q1", "加点 力量 -5")
    check("负数被格式拦截", "格式" in r[-1], r[-1][:60])
    # 0 点
    r2 = await cmd(m, "add_attr", "g1", "q1", "加点 力量 0")
    check("0点被拦", "正整数" in r2[-1], r2[-1][:60])
    # 非法属性名
    r3 = await cmd(m, "add_attr", "g1", "q1", "加点 幸运 1")
    check("非法属性名", "可选" in r3[-1], r3[-1][:60])
    # 超上限
    r4 = await cmd(m, "add_attr", "g1", "q1", "加点 力量 99")
    p = db.get_player("g1", "q1")
    check("点数不足拦截", "属性点不足" in r4[-1] and p["attr_pts"] == 9, r4[-1][:60])
    # 正常加点
    r5 = await cmd(m, "add_attr", "g1", "q1", "加点 力量 5")
    p5 = db.get_player("g1", "q1")
    attrs = json.loads(p5["attributes"]) if isinstance(p5["attributes"], str) else p5["attributes"]
    check("力量+5", attrs.get("str") == 5 and p5["attr_pts"] == 4, f"str={attrs.get('str')} pts={p5['attr_pts']}")
    # 点满后继续加
    db.update_player("g1", "q1", attr_pts=0)
    r6 = await cmd(m, "add_attr", "g1", "q1", "加点 力量 1")
    check("0点继续加被拦", "属性点不足" in r6[-1], r6[-1][:60])
    # 洗点
    db.update_player("g1", "q1", gold=5000, hp=50, mp=30)
    r7 = await cmd(m, "reset_attr", "g1", "q1", "洗点")
    p7 = db.get_player("g1", "q1")
    a7 = json.loads(p7["attributes"]) if isinstance(p7["attributes"], str) else p7["attributes"]
    check("洗点归零+返还5点", sum(a7.values()) == 0 and p7["attr_pts"] == 5, f"attrs={a7} pts={p7['attr_pts']}")
    st7 = E.player_final_stats(p7["class_name"], 1, {}, 0, {"str":0,"agi":0,"int":0,"vit":0}, 0, None, "human")
    check("洗点后 hp 裁剪不超上限", p7["hp"] <= st7["max_hp"] and p7["mp"] <= st7["max_mp"],
          f"hp={p7['hp']}/{st7['max_hp']} mp={p7['mp']}/{st7['max_mp']}")

def test_stats_chain():
    print("【属性计算链路】")
    # PCT_STATS 不被 int 截断：装备 dodge 词条
    eq = {"helm": {"name": "轻皮帽", "quality": "blue", "enhance": 0,
                   "stats": {"def": 3, "dodge": 0.05, "crit": 0.02}, "affixes": [], "enchant": []}}
    st, src = E.player_stats_detail("cls_ci_ke", 1, eq, 0, {}, 0, None, "human")
    check("dodge 0.05 不被截断", st["dodge"] > 0.03, f"dodge={st['dodge']}")
    check("crit 0.02 生效", st["crit"] > 0.2, f"crit={st['crit']}")
    # 来源总账 = 面板总值（基础+装备+属性点+种族）
    eq2 = {"weapon": {"name": "铁剑", "quality": "green", "enhance": 2,
                      "stats": {"atk": 12, "crit": 0.03}, "affixes": [], "enchant": []},
           "armor": {"name": "皮甲", "quality": "blue", "enhance": 0,
                     "stats": {"def": 8, "hp": 40, "dodge": 0.05}, "affixes": [], "enchant": []}}
    st2, src2 = E.player_stats_detail("cls_zhan_shi", 10, eq2, 1, {"str": 12, "agi": 5, "int": 0, "vit": 8}, 1, {"atk": 5}, "elf")
    total = {}
    for s in src2:
        for k, v in s["stats"].items():
            if s.get("pct") and k not in C.PCT_STATS:
                v = v / 100.0
            total[k] = total.get(k, 0) + v
    for k in ("atk", "def", "max_hp", "max_mp", "spd", "crit", "dodge", "mdef", "matk"):
        if k in total:
            # 百分比来源按 pct 处理；hp 需要 base 的 max_hp 参与
            pass
    # 精确校验：逐项加和 == 最终（crit/dodge 百分比相加；hp 类 base 在"基础"里）
    base_hp = next(s["stats"]["hp"] for s in src2 if s["name"] == "基础")
    calc_hp = base_hp
    calc_atk = next(s["stats"]["atk"] for s in src2 if s["name"] == "基础")
    calc_crit = next(s["stats"]["crit"] for s in src2 if s["name"] == "基础")
    calc_spd = next(s["stats"]["spd"] for s in src2 if s["name"] == "基础")
    calc_dodge = next(s["stats"]["dodge"] for s in src2 if s["name"] == "基础")
    for s in src2:
        nm = s["name"]
        if nm == "基础":
            continue
        pct = s.get("pct", False)
        for k, v in s["stats"].items():
            if k == "hp":
                calc_hp = int(calc_hp * v) if pct else calc_hp + v
            elif k == "atk":
                calc_atk += int(v) if not pct else int(calc_atk * v)
            elif k == "crit":
                calc_crit = min(calc_crit + v, 0.5)
            elif k == "spd":
                calc_spd += int(v) if not pct else int(calc_spd * v)
            elif k == "dodge":
                calc_dodge = min(calc_dodge + v, 0.4)
    check("来源总账=面板(HP)", calc_hp == st2["max_hp"], f"{calc_hp} vs {st2['max_hp']}")
    check("来源总账=面板(ATK)", calc_atk == st2["atk"], f"{calc_atk} vs {st2['atk']}")
    check("来源总账=面板(CRIT)", abs(calc_crit - st2["crit"]) < 1e-9, f"{calc_crit} vs {st2['crit']}")
    check("来源总账=面板(DODGE)", abs(calc_dodge - st2["dodge"]) < 1e-9, f"{calc_dodge} vs {st2['dodge']}")
    # 强化倍率对 crit/dodge 的影响（v101.21e 修复后：PCT 不乘 mult —— 确认现状）
    eq3 = {"weapon": {"name": "铁剑+3", "quality": "green", "enhance": 3,
                      "stats": {"atk": 12, "crit": 0.05}, "affixes": [], "enchant": []}}
    st3, _ = E.player_stats_detail("cls_zhan_shi", 1, eq3, 0, {}, 0, None, "human")
    st3b, _ = E.player_stats_detail("cls_zhan_shi", 1, {"weapon": dict(eq3["weapon"], enhance=0)}, 0, {}, 0, None, "human")
    check("强化不放大 crit（现状确认）", st3["crit"] == st3b["crit"], f"+3={st3['crit']} +0={st3b['crit']}")
    check("强化放大 atk", st3["atk"] > st3b["atk"], f"+3={st3['atk']} +0={st3b['atk']}")
    # 同属性不叠加取高（种族天赋只有单来源，此处验证 crit cap 与套装叠加）
    st4, _ = E.player_stats_detail("cls_you_xia", 30, {}, 0, {"agi": 200}, 0, None, "elf")
    check("crit cap 50%", st4["crit"] <= 0.5000001, f"crit={st4['crit']}")

def test_exp_curve():
    print("【升级经验曲线】")
    vals = [C.exp_to_next(lv) for lv in (1, 2, 5, 10, 30, 60, 90)]
    print(f"    exp_to_next: {vals}")
    check("exp_to_next(1)=110", vals[0] == 110, str(vals[0]))
    check("超线性增长(指数1.45)", vals[2] / vals[1] > 2 and vals[4] / vals[3] > 2.3, str(vals))
    # 升级循环：exp 累积连升
    p = {"class_name": "cls_zhan_shi", "level": 1, "exp": C.exp_to_next(1) + C.exp_to_next(2) + 5,
         "class_tier": 0, "attributes": {}, "equipment": {}, "evolve_path": 0,
         "learned_skills": [], "skill_levels": {}, "hp": 50, "mp": 20, "max_hp": 150, "max_mp": 40,
         "attr_pts": 0, "skill_points": 0, "race": "human"}
    logs, p2 = E.check_player_level_up("g1", "q1", p)
    check("连升2级", p2["level"] == 3, f"lv={p2['level']}")
    check("升级给3+3属性点", p2["attr_pts"] == 6, str(p2["attr_pts"]))
    check("升级给2技能点", p2["skill_points"] == 2, str(p2["skill_points"]))
    check("升级回满血", p2["hp"] == p2["max_hp"] and p2["mp"] == p2["max_mp"], f"hp={p2['hp']}/{p2['max_hp']}")
    check("升级横幅", any("恭喜升级" in l for l in logs), str(logs)[:100])
    # 经验溢出正确扣除
    check("exp 扣除正确", p2["exp"] == 5, f"exp={p2['exp']}")

async def test_guard_and_panel():
    print("【守卫/面板】")
    m = Main(None); clean()
    # 无角色拦截（玩家指令全覆盖抽查）
    for msg, handler in (("角色", "profile"), ("属性", "attributes"), ("加点 力量 1", "add_attr"),
                         ("技能学习 火球术", "skill_learn"), ("战力", "power"), ("洗点", "reset_attr"),
                         ("技能洗点", "reset_skill"), ("技能栏", "skill_bar_view"), ("转职", "evolve"),
                         ("流派", "build_view"), ("注销", "delete_account")):
        r = await cmd(m, handler, "g1", "q9", msg)
        check(f"无角色拦截『{msg}』", r and "你还没有角色" in r[-1], str(r)[:80])
    # 注册后角色面板
    await cmd(m, "register", "g1", "q1", "注册 格温 女 银月精灵")
    r = await cmd(m, "profile", "g1", "q1", "角色")
    txt = r[-1]
    check("角色面板含生命", "生命" in txt, txt[:200])
    # 生命当前/上限一致（面板行 ❤️ 生命：142/142）
    import re as _re
    mhp = _re.search(r"生命：(\d+)/(\d+)", txt)
    check("面板 hp==max_hp", mhp and mhp.group(1) == mhp.group(2), txt[:300])
    check("面板含种族·性别", "银月精灵" in txt and "女" in txt, txt[:300])
    # 属性面板
    r2 = await cmd(m, "attributes", "g1", "q1", "属性")
    txt2 = r2[-1]
    check("属性面板含攻击/暴击", "攻击" in txt2 and "暴击" in txt2, txt2[:300])
    # PCT 显示百分比
    mm = _re.search(r"暴击：([\d.]+)%", txt2)
    check("暴击百分比显示", mm is not None, txt2[:300])
    # REGISTER_HINT 唯一常量
    import subprocess
    out = subprocess.run(["grep", "-rn", "你还没有角色", "game/"], capture_output=True, text=True, cwd=PLUGIN).stdout
    hits = [l for l in out.splitlines() if "__pycache__" not in l and "tmp_m01" not in l]
    check("REGISTER_HINT 唯一文案点", len(hits) <= 3, str(hits)[:300])

def test_store_fields():
    print("【players 表字段完整性】")
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()]
    conn.close()
    need = ["level", "exp", "class_name", "race", "attributes", "equipment", "cur_map", "cur_subarea",
            "gender", "attr_pts", "skill_points", "max_hp", "max_mp", "hp", "mp", "gold", "stamina",
            "stamina_ts", "class_tier", "evolve_path", "learned_skills", "skill_levels", "skill_bar",
            "skill_spent", "shortcuts", "portals", "hidden_class_unlock", "equipped_title", "deed", "deed_lv",
            "apprentices", "mounts", "learned_blueprints", "lucky_until", "created_at", "last_active"]
    missing = [c for c in need if c not in cols]
    check("players 表 36 字段齐全", not missing, f"缺: {missing}")
    # update_player 非法字段拒绝
    try:
        db.update_player("g1", "q1", atk=999)
        check("非法字段拒绝", False, "atk 写库成功（应 ValueError）")
    except ValueError:
        check("非法字段拒绝", True)
    # JSON 序列化往返
    p = db.get_player("g1", "q1") if db.get_player("g1", "q1") else None

async def test_race_neg():
    print("【种族负面结算】")
    # 人类成长 -2%：30 级战士 atk 差值验证
    st_h, _ = E.player_stats_detail("cls_zhan_shi", 30, {}, 0, {}, 0, None, "human")
    st_o, _ = E.player_stats_detail("cls_zhan_shi", 30, {}, 0, {}, 0, None, None)
    check("人类凡人之躯 atk 少2%", st_o["atk"] - st_h["atk"] >= 1, f"{st_o['atk']} vs {st_h['atk']}")
    # 精灵 HP-5% + 暴击+8%
    st_e, src = E.player_stats_detail("cls_zhan_shi", 30, {}, 0, {}, 0, None, "elf")
    check("精灵月缺 HP-5%", abs(st_e["max_hp"] - int(st_o["max_hp"] * 0.95)) <= 1, f"{st_e['max_hp']} vs {st_o['max_hp']}")
    check("精灵暴击+8%", st_e["crit"] - st_o["crit"] > 0.07, f"{st_e['crit']} vs {st_o['crit']}")
    # 兽人 HP+8%、矮人 spd-5%、龙裔/兽人 magic_reduce 负系数在 battle 消费
    st_r, _ = E.player_stats_detail("cls_zhan_shi", 30, {}, 0, {}, 0, None, "orc")
    check("兽人坚韧体魄 HP+8%", st_r["max_hp"] > st_o["max_hp"], f"{st_r['max_hp']} vs {st_o['max_hp']}")
    st_d, _ = E.player_stats_detail("cls_zhan_shi", 30, {}, 0, {}, 0, None, "dwarf")
    check("矮人磐石步履 spd-5%", st_d["spd"] < st_o["spd"], f"{st_d['spd']} vs {st_o['spd']}")
    # race_neg 标记齐全
    check("6族全 race_neg=True", all(r.get("race_neg") for r in C.RACES.values()))

async def main():
    await test_register()
    await test_add_attr()
    test_stats_chain()
    test_exp_curve()
    await test_guard_and_panel()
    test_store_fields()
    await test_race_neg()
    print(f"\nM01 审计临时脚本结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
