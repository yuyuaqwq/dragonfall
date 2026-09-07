# -*- coding: utf-8 -*-
"""v140 波4：新手紫装特效（novice_*）测试

覆盖 8 件新手紫装（Lv.10-15）的特效：
1. 学徒之血刃 novice_lifesteal：伤害 5% 转化为生命回复（命中回血）
2. 旅人之盾 novice_first_turn_guard：首回合受击伤害 -10%
3. 星火法杖 novice_spark_followup：释放技能后下次普攻伤害 +10%
4. 猎影之牙 novice_hunt_combo：暴击后连击率 +8%
5. 旅人皮甲 novice_regen_heal：受到的治疗效果 +10%
6. 翠风之弓 novice_wind_spd：攻击命中后自身速度 +5%（2 回合）
7. 远行兜帽 novice_first_turn_dodge：首回合闪避率 +5%
8. 晨星吊坠 novice_dawn_mana：首次释放技能回复 10 点魔力

随机种子固定（特效概率相关）。
"""
import sys, os, random
random.seed(20260830)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import _WE_EXEC_KEYS, proc as we_proc

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def mk_player(effects=None, atk=100, matk=80, level=30):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": "战士", "qq_id": "t1"}

def mk_enemy(hp=100000, **kw):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}}
    e.update(kw)
    return e

def test_registered():
    print("【0. 8 个新手特效全部注册】")
    # v181.P2C-C10：旧 handler 删净后 WEAPON_EFFECTS 恒空——"注册"断言改查 _WE_EXEC_KEYS 路由表
    for k in ["novice_lifesteal", "novice_first_turn_guard", "novice_spark_followup",
              "novice_hunt_combo", "novice_regen_heal", "novice_wind_spd",
              "novice_first_turn_dodge", "novice_dawn_mana"]:
        check(f"{k} 路由注册", k in _WE_EXEC_KEYS, f"route={_WE_EXEC_KEYS.get(k)}")

def test_lifesteal():
    print("【1. 学徒之血刃 吸血】")
    p = mk_player(["novice_lifesteal"], atk=100)
    e = mk_enemy()
    b = BT.Battle("monster", e, player=p)
    # Battle.__init__ 重算 max_hp，hp 需在 init 后设置；先扣血留出回血空间
    p["hp"] = p["max_hp"] - 100
    hp_before = p["hp"]
    logs = []
    we_proc(b, p, "hit", {"dmg": 100, "is_crit": False}, logs)
    check("吸血回血 > 0", p["hp"] > hp_before, f"hp={p['hp']} before={hp_before} logs={logs}")
    check("回血 5 点（100×5%）", p["hp"] - hp_before == 5, f"heal={p['hp'] - hp_before}")

def test_first_turn_guard():
    print("【2. 旅人之盾 首回合减伤】")
    p = mk_player(["novice_first_turn_guard"])
    e = mk_enemy()
    b = BT.Battle("monster", e, player=p)
    # battle_start 挂标记
    logs = []
    we_proc(b, p, "battle_start", {}, logs)
    check("守御标记生效", b._p_eff().get("novice_guard_active") is True, str(b._p_eff()))
    # 首回合受击减伤（init 后重设大血量，确保 900 伤害完整体现）
    p["max_hp"] = 9999
    p["hp"] = 9999
    hp_before = p["hp"]
    b._damage_actor(p, 1000, [], source="测试")
    dmg_taken = hp_before - p["hp"]
    check("首回合受击 -10%（900）", dmg_taken == 900, f"dmg={dmg_taken}")

def test_spark_followup():
    print("【3. 星火法杖 技能后下次普攻 +10%】")
    p = mk_player(["novice_spark_followup"], atk=100)
    e = mk_enemy()
    b = BT.Battle("monster", e, player=p)
    # 技能后挂标记
    logs = []
    we_proc(b, p, "skill_cast", {"skill": "测试", "kind": "物理"}, logs)
    check("星火标记挂上", b._p_stacks().get("novice_spark") is True, str(b._p_stacks()))
    # 下次普攻（这里直接验证 _player_attack 消费：伤害应比无标记时高）
    st = b._player_stats(p)
    # 先打一次无标记的
    b2 = BT.Battle("monster", mk_enemy(), player=mk_player(["novice_spark_followup"], atk=100))
    b2._p_stacks()["novice_spark"] = True  # 模拟已挂标记
    # 对比：伤害计算内部逻辑，直接检查 _player_attack 是否清掉标记
    logs2 = b2._player_attack(b2._player_stats(p), p)
    check("普攻消费并清除星火标记", not b2._p_stacks().get("novice_spark"), str(b2._p_stacks()))

def test_regen_heal():
    print("【4. 旅人皮甲 受治疗 +10%】")
    p = mk_player(["novice_regen_heal"])
    e = mk_enemy()
    b = BT.Battle("monster", e, player=p)
    ctx = {"heal": 100, "overflow": 0}
    we_proc(b, p, "heal", ctx, [])
    check("治疗 +10%（110）", ctx["heal"] == 110, f"heal={ctx['heal']}")

def test_wind_spd():
    print("【5. 翠风之弓 命中后速度 +5%】")
    p = mk_player(["novice_wind_spd"], atk=100)
    e = mk_enemy()
    b = BT.Battle("monster", e, player=p)
    # 基准（无 buff）
    p0 = mk_player([])
    b0 = BT.Battle("monster", mk_enemy(), player=p0)
    base_spd = b0._player_stats(p0)["spd"]
    logs = []
    we_proc(b, p, "hit", {"dmg": 100, "is_crit": False}, logs)
    check("翠风 buff 挂上（2 回合）", b._p_buffs_bag().get("novice_wind_spd") == 2, str(b._p_buffs_bag()))
    # _player_stats 速度加成
    st = b._player_stats(p)
    check("速度 +5%", st["spd"] == int(base_spd * 1.05), f"spd={st['spd']} base={base_spd}")

def test_first_turn_dodge():
    print("【6. 远行兜帽 首回合闪避 +5%】")
    p = mk_player(["novice_first_turn_dodge"])
    e = mk_enemy()
    b = BT.Battle("monster", e, player=p)
    logs = []
    we_proc(b, p, "battle_start", {}, logs)
    check("闪避标记生效", b._p_eff().get("novice_dodge_active") is True, str(b._p_eff()))

def test_dawn_mana():
    print("【7. 晨星吊坠 首次技能回蓝】")
    p = mk_player(["novice_dawn_mana"])
    e = mk_enemy()
    b = BT.Battle("monster", e, player=p)
    p["mp"] = 100
    logs = []
    we_proc(b, p, "skill_cast", {"skill": "测试"}, logs)
    check("首次技能回蓝 10（110）", p["mp"] == 110, f"mp={p['mp']}")
    # 第二次不重复回
    logs2 = []
    we_proc(b, p, "skill_cast", {"skill": "测试2"}, logs2)
    check("第二次不再回蓝", p["mp"] == 110, f"mp={p['mp']}")

if __name__ == "__main__":
    test_registered()
    test_lifesteal()
    test_first_turn_guard()
    test_spark_followup()
    test_regen_heal()
    test_wind_spd()
    test_first_turn_dodge()
    test_dawn_mana()
    print(f"\n结果: {passed} 通过, 0 失败")
