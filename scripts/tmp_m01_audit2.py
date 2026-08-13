# -*- coding: utf-8 -*-
"""M01 审计补充验证（临时，用完即删）"""
import os, sys, json, sqlite3
PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN)))
_TMP_DB = os.path.join(PLUGIN, "scripts", "tmp_m01_audit2.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["GWEN_GAME_DB"] = _TMP_DB
sys.path.insert(0, QQBOT); sys.path.insert(0, PLUGIN)
from data.plugins.dragonfall.game import content as C, db, engine as E
from data.plugins.dragonfall.main import Main

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond: passed += 1; print(f"  ✅ {name}")
    else: failed += 1; print(f"  ❌ {name}: {detail}")

class FakeEvent:
    def __init__(self, g, q, msg=""): self._g, self._q, self.message_str = g, q, msg
    def get_group_id(self): return self._g
    def get_sender_id(self): return self._q
    def get_message_str(self): return self.message_str
    def plain_result(self, text): return text
    def stop_event(self): pass

async def cmd(m, name, gid, qid, msg):
    gen = getattr(m, name)(FakeEvent(gid, qid, msg))
    out = []
    try:
        while True: out.append(await gen.__anext__())
    except StopAsyncIteration: pass
    return out

def clean():
    db.init_db()
    conn = sqlite3.connect(db.DB_PATH)
    for t in ("players","player_groups","inventory","quests","battle_state","achievements","stats","feedback","event_state","professions","props_use"):
        try: conn.execute(f"DELETE FROM {t}")
        except Exception: pass
    conn.commit(); conn.close()

async def main():
    m = Main(None); clean()
    print("【惰性升级 title_bonus 一致性】")
    await cmd(m, "register", "g1", "q1", "注册 格温 女")
    # 造一个带副业称号 bonus 的玩家（TITLES 找有 bonus 的）
    bonus_title = next((t for t in C.TITLES if t.get("bonus")), None)
    if bonus_title:
        db.update_player("g1", "q1", equipped_title=bonus_title["name"])
        # 等级称号走 _earned_titles（stats 计数），直接塞 stats 模拟
        conn = sqlite3.connect(db.DB_PATH)
        conn.execute("INSERT OR REPLACE INTO stats (qq_id, kills, elite_kills, boss_kills, deaths, day_kills, day_date, visited_areas, inst_clears, party_count, fish_count, gather_count, mine_count, cook_count, alchemy_count, craft_count, enhance_count, enchant_count, world_events, catch_collect) VALUES ('q1',0,0,0,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0)")
        conn.commit(); conn.close()
        tb = m._title_bonus("g1", "q1")
        print(f"    TITLES bonus: {bonus_title['name']} → {bonus_title.get('bonus')}, 实际 _title_bonus: {tb}")
        # 直接调 get_player 触发惰性升级（level 提到 2 且 exp 溢出）
        db.update_player("g1", "q1", level=1, exp=C.exp_to_next(1) + 5, hp=50, mp=10)
        p = db.get_player("g1", "q1")
        st_calc, _ = E.player_stats_detail(p["class_name"], p["level"], p["equipment"], p.get("class_tier",0), p.get("attributes"), p.get("evolve_path",0), tb, p.get("race"))
        st_nocalc, _ = E.player_stats_detail(p["class_name"], p["level"], p["equipment"], p.get("class_tier",0), p.get("attributes"), p.get("evolve_path",0), None, p.get("race"))
        print(f"    升级后 db max_hp={p['max_hp']} | 含称号计算={st_calc['max_hp']} | 不含称号计算={st_nocalc['max_hp']}")
        check("惰性升级 max_hp 含称号", p["max_hp"] == st_calc["max_hp"], f"db={p['max_hp']} calc_with={st_calc['max_hp']}")
    else:
        print("    无带 bonus 的 TITLES，跳过")

    print("【升级广播】")
    p2 = {"class_name": "cls_zhan_shi", "level": 1, "exp": C.exp_to_next(1)+1, "class_tier": 0,
          "attributes": {}, "equipment": {}, "evolve_path": 0, "learned_skills": [], "skill_levels": {},
          "hp": 50, "mp": 20, "max_hp": 150, "max_mp": 40, "attr_pts": 0, "skill_points": 0, "race": "human"}
    logs, _ = E.check_player_level_up("g1", "q1", p2)
    print(f"    升级日志: {logs}")
    check("升级个人横幅存在", any("恭喜升级" in l for l in logs), str(logs))
    # 30 级转职提示
    p3 = dict(p2, level=29, exp=C.exp_to_next(29)+1)
    logs3, _ = E.check_player_level_up("g1", "q1", p3)
    check("30级转职提示", any("可以转职" in l for l in logs3), str(logs3))

    print("【装备等级需求联动】")
    # 穿装备等级需求：看 economy 穿戴检查
    import re
    src = open(os.path.join(PLUGIN, "game", "commands", "economy.py"), encoding="utf-8").read()
    hits = re.findall(r".{40}(?:等级需求|需求等级|level.*req|req.*level).{40}", src)
    print("    economy.py 等级需求检查:", hits[:3] if hits else "无")
    # 商店武器等级需求检查（shop 买武器是否校验等级）
    hits2 = re.findall(r".{30}(?:武器需求|等级不足|lv.*需求).{30}", src)
    print("    ", hits2[:3] if hits2 else "无")

    print("【战斗中可用的玩家指令（守卫层级）】")
    # 战斗中可否加点/看属性（设计允许？require_battle 只挂在 combat 指令）
    for name, msg in (("attributes", "属性"), ("add_attr", "加点 力量 1"), ("profile", "角色")):
        r = await cmd(m, name, "g1", "q1", msg)
        check(f"战斗中『{msg}』不误拦(无require_battle)", r and "你附近没有敌人" not in r[-1], str(r)[-60:])

    print("【职业初始技能（带职业注册）】")
    clean()
    await cmd(m, "register", "g1", "q1", "注册 战士 勇者 男")
    p4 = db.get_player("g1", "q1")
    print(f"    战士初始技能: {p4.get('learned_skills')}")
    check("战士有初始技能", len(p4.get("learned_skills", [])) >= 1, str(p4.get("learned_skills")))
    r = await cmd(m, "skill_bar_view", "g1", "q1", "技能栏")
    check("技能栏已装初始技能", "1." in r[-1] and "空" not in r[-1].split("1.")[1][:6], r[-1][:120])

    print("【见习冒险者就职（CLASS_NOVICE 链路）】")
    clean()
    await cmd(m, "register", "g1", "q1", "注册 萌新 男")
    r = await cmd(m, "skill_learn", "g1", "q1", "技能学习 火球术")
    check("见习不可学技能提示", "见习冒险者" in r[-1], r[-1][:80])

    print(f"\n补充验证结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
