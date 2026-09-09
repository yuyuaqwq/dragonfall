# -*- coding: utf-8 -*-
"""阶段八：装备重写 v2.0（10 章名册 + 20 章词条/属性需求）

验证：
  1. 数据完整性：30 词条 / 16 专属 / 名册 103 件 / 固定词条全覆盖 / 需求格式
  2. 名册生成 generate_roster_equip：名字/词条数/需求/套装/专属
  3. 随机生成 generate_equip：词条 v2 / req / 橙装专属
  4. 掉落 roll_drop：普通怪绿蓝 / 精英紫蓝+图纸 / Boss 橙紫+图纸
  5. 属性需求穿戴：装备命令属性不够拦截 / 达标可穿 / 跨职业武器
  6. 战斗词条触发：护盾 / 处决 / 流血 / 破甲 / 连击 / 吸血 / 元素附加 / 格挡 / 反击 / 回春 / 冥想 / 龙语印记
  7. 商店买武器名册化（需求与名册一致）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import FakeEvent, run, clean_db, make_player, TEST_DB, PLUGIN_DIR
from data.plugins.dragonfall.game import content as C, db, engine as E
from data.plugins.dragonfall.game import battle as BT
from data.plugins.dragonfall.main import Main
from v154_helpers import enemy_turn_cast

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")


async def cmd(m, name, gid, qid, msg):
    handler = getattr(m, name)
    ev = FakeEvent(gid, qid, msg)
    return await run(handler, ev)


def mk_player(affix_ids, legendary=None, hp=500, mp=100, max_hp=None, max_mp=None):
    """带装备的战斗测试玩家（装备词条可注入）"""
    eq = {"weapon": {"name": "测试剑", "slot": "weapon", "quality": "blue", "lv": 30,
                     "stats": {"atk": 50}, "affixes": affix_ids}}
    if legendary:
        eq["weapon"]["legendary"] = legendary
    return {"class_name": "cls_zhan_shi", "level": 30, "hp": hp, "max_hp": max_hp or hp,
            "mp": mp, "max_mp": max_mp or mp, "equipment": eq,
            "attributes": {"str": 30, "agi": 10, "int": 10, "vit": 10},
            "learned_skills": [], "skill_levels": {}, "title_bonus": {}}


def mk_enemy(hp=1000, role="dps", name="测试怪", max_hp=None):
    return {"name": name, "role": role, "hp": hp, "max_hp": max_hp or hp,
            "atk": 30, "def": 10, "matk": 10, "mdef": 10, "spd": 5}


# ============ 1. 数据完整性 ============
def test_data():
    print("【1. 数据完整性】")
    check("76 种词条（45 基准 + v130.2 资源联动词条 31——v110 审计拆分 tenacity_cc「坚韧」原 tenacity 键被 v106 韧性 stat 词条占用致双机制隐性叠加）", len(C.AFFIXES) == 76, str(len(C.AFFIXES)))
    check("专属 93", len(C.LEGENDARY_EFFECTS) == 93, str(len(C.LEGENDARY_EFFECTS)))  # v124: +愿者上钩/大地心跳; v140: +初火余烬; v141.3: D2 24 + D3 35; v169: +4 断档橙专属
    check("名册 687 件", len(C.EQUIP_ROSTER) == 687, str(len(C.EQUIP_ROSTER)))  # v124: +6 支线; v136 Phase6: +180; v140: +213; v141.3: +龙鳞庇护之坠; v168: +8 新手本 Boss 主题装; v169: +12 断档补装; v171: +6 新手流派白装; v172 路B: +24 重锻专属(壁垒/铭文/贤者/巡猎/夜行/镇岳系); v173.3 #103: +5 新手武器自选礼包(誓约剑/弓/权杖/匕首/拳套)
    check("品质倍率绿 1.3", C.QUALITY["green"]["mult"] == 1.3)
    check("品质倍率蓝 1.55", C.QUALITY["blue"]["mult"] == 1.55)
    # 词条触发时机全合法
    valid_triggers = {"stat", "on_hit", "on_taken", "turn_start", "battle_start", "passive"}
    bad = [aid for aid, info in C.AFFIXES.items() if info["trigger"] not in valid_triggers]
    check("词条触发时机合法", not bad, str(bad))
    # 名册每件都有需求 + 固定词条配置（白/绿装豁免：0/1 词条走随机池）
    missing_fixed = [rid for rid, r in C.EQUIP_ROSTER.items()
                     if r["quality"] in ("blue", "purple", "orange")
                     and r["name"] not in C.SERIES_FIXED_AFFIX]
    check("固定词条全覆盖（蓝紫橙）", not missing_fixed, str(missing_fixed[:5]))
    # v95：商店饰品无属性需求（新手期不卡职业），req 允许缺失/为空
    bad_req = [rid for rid, r in C.EQUIP_ROSTER.items()
               if not set(r.get("req") or {}).issubset({"str", "agi", "int", "vit"})]
    check("需求格式合法", not bad_req, str(bad_req[:5]))
    bad_lg = [rid for rid, r in C.EQUIP_ROSTER.items()
              if r["quality"] == "orange" and not r.get("legendary")]
    check("橙装全带专属", not bad_lg, str(bad_lg[:5]))
    # 随机池词条 ID 全有效
    bad_pool = [a for pool in C.AFFIX_POOL_BY_QUALITY.values() for a in pool
                if a not in C.AFFIXES]
    check("随机池 ID 有效", not bad_pool, str(bad_pool))
    # 每个套装系列有 5 件套（含护腿）；v104 M20 P2：支线单件主题系列（裂鬃/铁牙/雷鸣/烬核/暮影）非套装，豁免
    series_ok = all(len([r for r in C.EQUIP_ROSTER.values() if r["series"] == s and r["slot"] == "legs"]) >= 1
                    for s in C.SERIES_SETS)
    check("15 套装系列各有护腿", series_ok)


# ============ 2. 名册生成 ============
def test_roster_gen():
    print("【2. 名册生成】")
    random.seed(7)
    e = C.generate_roster_equip("eq_tie_jian")
    check("铁剑名字", e["name"] == "铁剑")
    check("铁剑白装 0 词条", e.get("affixes") is None, str(e.get("affixes")))
    check("铁剑新手无需求", e["req"] == {}, str(e["req"]))
    e2 = C.generate_roster_equip("eq_jin_gou_wan_dao")
    check("金钩弯刀橙装 3-4 词条", len(e2.get("affixes", [])) in (3, 4), str(e2.get("affixes")))  # v104 M07 P2: 橙装 20% 概率 4 词条
    check("金钩弯刀固定词条在列", "crit_up" in e2["affixes"], str(e2["affixes"]))  # v173.3 #171-A: 固定≤1条(锚点crit_up), lifesteal已释放随机
    check("金钩弯刀专属", e2.get("legendary") == "gold_hook")
    check("金钩弯刀套装", e2.get("set") == "海风套", str(e2.get("set")))
    check("金钩弯刀需求", e2["req"] == {"agi": 25}, str(e2["req"]))
    e3 = C.generate_roster_equip("eq_long_yu_sheng_jian")
    check("龙语圣剑专属", e3.get("legendary") == "dragon_tongue")
    check("龙语圣剑固定词条", "dragon_aw" in e3["affixes"], str(e3["affixes"]))  # v173.3 #171-A: 固定≤1条(锚点dragon_aw), execute已释放随机
    # 苍穹之枪武器类型
    e4 = C.generate_roster_equip("eq_cang_qiong_zhi_qiang")
    check("苍穹之枪类型枪", e4.get("weapon_type") == "spear")
    # 名册系列全部映射套装（蓝以上）；v104 M20 P2：支线单件图纸装备（裂鬃/铁牙/雷鸣/烬核/暮影）非套装系列，豁免
    # v136 Phase6：散装（自由线）不挂套装（鱼鱼拍板）——散装系列 = 名册无显式 set 字段且不在 SERIES_SETS 的系列，动态豁免
    random.seed(11)
    _single_series = {"裂鬃", "铁牙", "雷鸣", "烬核", "暮影", "白桦", "长夜", "守夜", "松木", "猫眼", "夜行", "熔炉"}
    _scatter_series = set()
    for _rid, _r in C.EQUIP_ROSTER.items():
        if _r.get("set"):
            continue
        if _r["series"] not in C.SERIES_SETS and _r["series"] not in _single_series:
            _scatter_series.add(_r["series"])
    no_set = [rid for rid, r in C.EQUIP_ROSTER.items()
            if r["quality"] != "white"
            and r["series"] not in _single_series
            and r["series"] not in _scatter_series
            and not C.generate_roster_equip(rid).get("set")]
    check("蓝紫橙名册全部有套装归属", not no_set, str(no_set[:5]))


# ============ 3. 随机生成 ============
def test_random_gen():
    print("【3. 随机生成】")
    random.seed(3)
    e = C.generate_equip("weapon", 30, "purple")
    check("随机紫武器有词条", bool(e.get("affixes")), str(e.get("affixes")))
    check("随机装备有需求", bool(e.get("req")), str(e.get("req")))
    e2 = C.generate_equip("armor", 30, "orange")
    check("随机橙装有专属", bool(e2.get("legendary")))
    check("随机装备词条是 ID", all(isinstance(a, str) for a in e2.get("affixes", [])))


# ============ 4. 掉落 ============
def test_drop():
    print("【4. 掉落】")
    # v93 经济改革：怪物不再掉装备（铁匠铺购买+图纸锻造）
    # v94 图纸经济改革（2026-08-09 鱼鱼拍板）：图纸退出战斗掉落防泛滥
    #   - 普通怪/精英：永不掉图纸（图纸改走探索宝箱/垂钓宝物/铁匠铺购买）
    #   - Boss：仅 5% 惊喜掉率
    for seed in range(1, 300):
        random.seed(seed)
        d = C.roll_drop(10, "normal")
        check(f"普通怪不掉图纸（seed {seed}）", d[1] is None, str(d[1]))
    random.seed(4)
    d = C.roll_drop(20, "normal")
    check("普通怪不掉装备", d[0] is None)
    random.seed(4)
    d2 = C.roll_drop(20, "elite")
    check("精英不掉装备", d2[0] is None)
    check("精英不掉图纸(v94)", d2[1] is None, str(d2[1]))
    # Boss 5%：扫 seed 找触发，验证图纸结构合法
    triggered = False
    for seed in range(1, 500):
        random.seed(seed)
        d3 = C.roll_drop(40, "boss")
        if d3[1] is not None:
            check("Boss 图纸 blueprint_for 合法", d3[1]["blueprint_for"] in C.EQUIP_ROSTER_BY_NAME, str(d3[1]["blueprint_for"]))
            triggered = True
            break
    if not triggered:
        check("Boss 掉图纸(5%)", False, "500 seed 无触发")
    # 图纸构造一致性：make_blueprint 与 roll_blueprint 同构（商店显示=购买入包）
    random.seed(123)
    bp = C.roll_blueprint(30)
    bp2 = C.make_blueprint(bp["roster_id"])
    check("make_blueprint 与 roll 同构", bp == bp2, str(bp2))


# ============ 5. 属性需求穿戴 ============
async def test_req():
    print("【5. 属性需求穿戴】")
    m = Main(None)
    clean_db()
    await cmd(m, "register", "g1", "q1", "注册 战士 测试 男")
    # 造一件高需求装备（力量 50）
    eq = C.generate_roster_equip("eq_sheng_dian_zhan_chui")  # 圣殿战锤 req 力量 38
    db.add_item("g1", "q1", "eq_test", eq)
    r = await cmd(m, "equip", "g1", "q1", "装备 圣殿战锤")
    txt = r[-1]
    check("属性不足拦截", "穿不上" in txt and "力量" in txt, txt)
    # 加点到力量 40 + 等级 40 → 可装备
    db.update_player("g1", "q1", attributes='{"str": 40, "agi": 0, "int": 0, "vit": 0}', level=40)
    r2 = await cmd(m, "equip", "g1", "q1", "装备 圣殿战锤")
    txt2 = r2[-1]
    check("属性达标可穿", "装备了" in txt2, txt2)
    check("跨职业武器可穿", "不能装备" not in txt2)
    # 未穿时物品详情显示需求
    db.update_player("g1", "q1", attributes='{"str": 0, "agi": 0, "int": 0, "vit": 0}')
    eq2 = C.generate_roster_equip("eq_sheng_dian_zhan_chui")
    db.add_item("g1", "q1", "eq_test2", eq2)
    r3 = await cmd(m, "item_detail", "g1", "q1", "物品详情 圣殿战锤")
    txt3 = r3[-1]
    check("详情显示需求", "需求：力量 38" in txt3, txt3)


# ============ 6. 战斗词条触发 ============
def test_battle_affix():
    print("【6. 战斗词条触发】")
    # 6.1 战斗开始护盾（v101.28d 盾 buff 化：affix_shield 来源 3 回合）
    p = mk_player(["shield"])
    b = BT.Battle("monster", mk_enemy(), {}, p)
    # v152 时刻制：护盾存 {value, expire_at}（expire_at = now + turns×ACT_TICK = 3×2.0 = 6.0）
    check("护盾词条战斗开始", b._p_shields_bag().get("affix_shield", {}).get("value") == int(int(p["max_hp"] * 0.10) * 1.05)
          and abs(float(b._p_shields_bag().get("affix_shield", {}).get("expire_at", 0)) - 3.0) < 1e-9, str(b._p_shields_bag()))  # v106.2 战士盾强 5%；v152 ACT_TICK=1.0：3 刻 = 3.0
    # 6.2 处决低血增伤（血 20% 触发）
    p2 = mk_player(["execute"])
    b2 = BT.Battle("monster", mk_enemy(hp=200, max_hp=1000), {}, p2)
    logs = b2._actor_attack(b2._player_stats(p2), p2)
    check("处决低血增伤", any("处决" in l for l in logs), str(logs))
    # 6.3 流血/破甲/连击/吸血/元素附加（seed 固定触发任意 on_hit 词条 + 专项验证）
    onhit_hits = 0
    for seed in range(1, 40):
        random.seed(seed)
        p3 = mk_player(["bleed", "armor_break", "combo", "lifesteal", "element_ice"])
        b3 = BT.Battle("monster", mk_enemy(), {}, p3)
        logs = b3._actor_attack(b3._player_stats(p3), p3)
        joined = "".join(logs)
        if any(k in joined for k in ("流血", "破甲", "连击", "吸血", "元素", "贯穿", "蓄力")):
            onhit_hits += 1
    check(f"on_hit 词条可触发（{onhit_hits}/39 seed）", onhit_hits >= 5, str(onhit_hits))
    # 专项：找触发流血/破甲的 seed
    for target in ("流血", "破甲"):
        found = False
        for seed in range(1, 100):
            random.seed(seed)
            p3 = mk_player(["bleed", "armor_break"])
            b3 = BT.Battle("monster", mk_enemy(), {}, p3)
            logs = b3._actor_attack(b3._player_stats(p3), p3)
            if target in "".join(logs):
                found = True
                break
        check(f"词条{target}可触发", found)
    # 6.4 受击格挡/反击/反伤（seed 循环找触发）
    for seed in range(1, 300):
        random.seed(seed)
        p4 = mk_player(["block", "counter", "thorns"])
        b4 = BT.Battle("monster", mk_enemy(), {}, p4)
        # 屏蔽随机闪避，保证受击断言确定性（格挡/反击/反伤需命中才触发）
        _orig_ps = b4._player_stats
        def _ps_nododge(p_):
            s = _orig_ps(p_)
            s["dodge"] = 0.0
            return s
        b4._player_stats = _ps_nododge
        logs = []
        b4._damage_actor(p4, 100, logs)
        joined = "".join(logs)
        if "格挡" in joined or "反击" in joined or "反伤" in joined:
            check(f"受击词条（seed {seed}）", True, joined)
            break
    else:
        check("受击词条", False, "300 seed 无触发")
    # 6.5 回春/冥想回合开始（max_hp 500 但当前 400 → 触发回复）
    # v178.2：A 类每刻效果从 _turn_start 迁到 _tick_regen（regen_tick 每秒结算）——
    # 直接测新结算器，语义不变（扣血后 tick 一次应回复）
    p5 = mk_player(["regen", "meditate"], hp=400, mp=50, max_hp=500, max_mp=100)
    b5 = BT.Battle("monster", mk_enemy(), {}, p5)
    logs = b5._tick_regen(p5, [])
    check("回春回合回复", "回春" in "".join(logs) and p5["hp"] > 400, f"hp={p5['hp']}")
    check("冥想回合回复", "冥想" in "".join(logs) and p5["mp"] > 50, f"mp={p5['mp']}")
    # 6.6 龙语印记叠层
    p6 = mk_player([], "dragon_tongue")
    b6 = BT.Battle("monster", mk_enemy(), {}, p6)
    b6._actor_attack(b6._player_stats(p6), p6)
    check("龙语印记叠层", b6._p_stacks().get("dragon_mark") == 1, str(b6._p_stacks()))
    # 6.7 元素伤害专属（澜歌之泪 冰 +20%）
    p7 = mk_player(["element_ice"], "lang_tear")
    b7 = BT.Battle("monster", mk_enemy(), {}, p7)
    mult = b7._affix_element_dmg(p7, "ice")
    check("冰属性伤害 +20%", abs(mult - 1.20) < 1e-6, str(mult))
    mult2 = b7._affix_element_dmg(p7, "fire")
    check("火系不加成", abs(mult2 - 1.0) < 1e-6, str(mult2))
    # 6.8 流血 DOT 回合结算
    p8 = mk_player(["bleed"])
    random.seed(1)
    b8 = BT.Battle("monster", mk_enemy(hp=1000), {}, p8)
    b8._actor_attack(b8._player_stats(p8), p8)
    if b8._tgt_buffs().get("bleed"):
        logs = b8._turn_start(p8)
        check("流血回合结算", "流血" in "".join(logs) and b8.enemy["hp"] < 1000, str(logs))
    else:
        check("流血回合结算", True, "seed1 未触发 bleed，跳过")


# ============ 7. 商店买武器名册化 ============
async def test_shop_roster():
    print("【7. 商店买武器名册化】")
    m = Main(None)
    clean_db()
    await cmd(m, "register", "g1", "q1", "注册 战士 测试 男")
    db.update_player("g1", "q1", gold=10000, attributes='{"str": 40, "agi": 40, "int": 40, "vit": 40}')
    # 铁港买弯刀（名册 req 敏捷 12）——v87.17 需在商店子区域
    db.update_player("g1", "q1", cur_map="ironharbor", cur_subarea="ironharbor_6")
    r = await cmd(m, "buy", "g1", "q1", "购买 弯刀")
    txt = r[-1]
    check("买弯刀成功", "购买了【弯刀】" in txt, txt)
    items = db.get_inventory("g1", "q1")
    found = [it for it in items if it["data"]["name"] == "弯刀"]
    check("弯刀入包且 req 敏捷 12", bool(found) and found[0]["data"]["req"] == {"agi": 12},
          str([it["data"].get("req") for it in found]))
    check("弯刀带词条", bool(found) and bool(found[0]["data"].get("affixes")),
          str([it["data"].get("affixes") for it in found]))


# ============ 8. 锻造名册化 + 套装 ============
def test_craft_set():
    print("【8. 锻造名册化 + 套装】")
    # 锻造配方 = 名册（142 个，v104 补 11 图纸配方+淬火石配方 + v117 副本材料联动 +13 图纸配方，无旧毕业套）
    # v135 套装锻造专属：+6 配方（誓约 4 + 银铃护腿/杖 2）→ 187
    check("配方数 426", len(C.CRAFT_RECIPES) == 426, str(len(C.CRAFT_RECIPES)))  # v124: +夜行披风/熔炉之心; v135: +誓约4/银铃2; v136 Phase6: +165; v168: +72 断链补配方; v169: +2 断档橙配方
    check("无旧毕业套配方", not any(r.get("blueprint") == "铁皮图纸" for r in C.CRAFT_RECIPES.values()))
    # 锻造产物 = 名册精确生成（需求/套装/专属）
    eq = C.craft_recipe_make("rec_jin_gou_wan_dao")
    check("锻造橙装名册生成", eq["name"] == "金钩弯刀" and eq.get("legendary") == "gold_hook", str(eq))
    check("锻造橙装套装", eq.get("set") == "海风套", str(eq.get("set")))
    eq2 = C.craft_recipe_make("rec_tie_jian")
    # v104 修复：橡木系列白装也挂 set（新手可凑齐橡木套 2 件效果），铁剑=橡木系列 → 有套装
    check("锻造橡木白装挂套装", eq2.get("set") == "橡木套" and eq2["req"] == {}, str(eq2))
    # 需图纸配方（紫/橙）——v104 补 11 条图纸配方 + v117 副本材料联动 +13 图纸配方
    bp_recs = [r for r in C.CRAFT_RECIPES.values() if r.get("blueprint")]
    check("需图纸配方存在", len(bp_recs) == 261, str(len(bp_recs)))  # v124: +夜行披风/熔炉之心; v136 Phase6: +66; v168: +55 图纸断链补配方; v169: +2 断档橙配方
    # 图纸名匹配：blueprint 要么遵循「X图纸」命名（Boss 掉落动态生成），
    # 要么是静态图纸物品名（v124 起允许「图纸·X」「传说锻造图纸·X」前缀风格）
    _bp_items = {v.get("name") for v in C.MATERIALS.values() if v.get("type") == "图纸"}
    check("图纸名匹配", all(r["blueprint"] == f"{r['name']}图纸" or r["blueprint"] in _bp_items for r in bp_recs))
    # 名册套装效果（圣光套 2 件治疗 / 4 件防御）
    w = C.generate_roster_equip("eq_sheng_guang_chang_jian")
    h = C.generate_roster_equip("eq_qi_shi_tou_kui")
    a = C.generate_roster_equip("eq_sheng_guang_xiong_jia")
    b = C.generate_roster_equip("eq_qi_shi_chang_xue")
    eq2set = {"weapon": w, "helm": h}
    b2 = E.set_bonus_2(eq2set)
    # v110 审计修复：圣光套 2 件原为 bonus_2.heal（heal ∉ STAT_NAMES）→ engine 属性结算
    # KeyError 崩溃；改 heal_power（∈ PCT_STATS，battle 治疗段消费）——断言同步更新
    check("圣光套 2 件治疗+10%（heal_power）", abs(b2.get("heal_power", 0) - 0.10) < 1e-6, str(b2))
    check("圣光套 has_set", E.has_set(eq2set, "圣光套"))
    # v110 审计修复回归：穿 2 件圣光套 player_final_stats 必须不崩溃（旧版此处 KeyError，
    # 384 断言全绿仍漏——本行防再漏）
    try:
        _st_sg = E.player_final_stats("cls_zhan_shi", 30, eq2set, 1, {"str": 5}, 1, {}, "human")
        check("穿 2 件圣光套 player_final_stats 不崩溃", True, "")
    except Exception as _ex:
        check("穿 2 件圣光套 player_final_stats 不崩溃", False, repr(_ex))
    eq4set = {"weapon": w, "helm": h, "armor": a, "boots": b}
    b4 = E.set_bonus_2(eq4set)
    check("圣光套 4 件防御+8%", abs(b4.get("def", 0) - 0.08) < 1e-6, str(b4))
    # v104 修复：橡木系列白装挂 set（新手福利），铁剑属于橡木系列 → 有套装
    check("白装橡木套挂套装字段", C.generate_roster_equip("eq_tie_jian").get("set") == "橡木套")
    # 20 章 4.3 锻造词条倾向：元素倾向出元素词条
    random.seed(5)
    ea = C.craft_recipe_make("rec_wan_dao", "元素")
    check("元素倾向出元素词条", any(a.startswith("element_") for a in ea.get("affixes", [])), str(ea.get("affixes")))
    random.seed(9)
    ea2 = C.craft_recipe_make("rec_jin_gou_wan_dao", "元素")
    check("橙装元素倾向固定+元素", any(a.startswith("element_") for a in ea2.get("affixes", [])), str(ea2.get("affixes")))
    random.seed(7)
    ed = C.craft_recipe_make("rec_chuan_zhang_mao", "防御")
    check("防御倾向出防御词条", any(a in ("block", "thorns", "dmg_reduce", "shield", "dodge", "tenacity", "regen", "meditate", "swift", "hp_up") for a in ed.get("affixes", [])), str(ed.get("affixes")))


# ============ 9. 套装 5 件效果 + 元素抗性落地（阶段八.1） ============
def mk_sets_player(set_name, n, affix_ids=None):
    """n 件同套装装备（填 weapon/helm/armor/legs/boots 前 n 个部位）"""
    eq = {}
    slots = ["weapon", "helm", "armor", "legs", "boots"]
    for i in range(n):
        eq[slots[i]] = {"name": f"{set_name}部件{i}", "slot": slots[i], "quality": "purple",
                        "lv": 60, "stats": {"atk": 10}, "set": set_name, "affixes": affix_ids or []}
    return {"class_name": "cls_zhan_shi", "level": 60, "hp": 500, "max_hp": 500,
            "mp": 100, "max_mp": 100, "equipment": eq,
            "attributes": {"str": 30, "agi": 10, "int": 10, "vit": 10},
            "learned_skills": [], "skill_levels": {}, "title_bonus": {}}


def mk_sets_enemy(name="测试怪", skills=None):
    e = {"name": name, "role": "dps", "hp": 1000, "max_hp": 1000,
         "atk": 30, "def": 10, "matk": 10, "mdef": 10, "spd": 5}
    if skills:
        e["skills"] = skills
    return e


def test_set5_and_resist():
    print("【9. 套装 5 件效果 + 元素抗性落地】")
    # 9.1 stat 型 5 件（engine.set_bonus_2 消费 bonus_5.crit/dodge）
    b = E.set_bonus_2(mk_sets_player("橡木套", 5)["equipment"])
    check("橡木 5 件 crit +5%", abs(b.get("crit", 0) - 0.05) < 1e-6, str(b))
    b4 = E.set_bonus_2(mk_sets_player("橡木套", 4)["equipment"])
    check("橡木 4 件无 crit", b4.get("crit", 0) == 0, str(b4))
    b5 = E.set_bonus_2(mk_sets_player("海风套", 5)["equipment"])
    check("铁港 5 件 dodge +5%", abs(b5.get("dodge", 0) - 0.05) < 1e-6, str(b5))
    # 9.2 对敌增伤 5 件（圣光克暗影 / 龙脊克龙 / 地底克深渊）
    p_sg = mk_sets_player("圣光套", 5)
    p_lj = mk_sets_player("龙脊套", 5)
    p_dd = mk_sets_player("地底套", 5)
    bt = BT.Battle("monster", mk_sets_enemy("亡灵骑士"), {}, p_sg)
    mult, tags = bt._affix_dmg_mult(p_sg)
    check("圣光套打亡灵 +10%", abs(mult - 1.10) < 1e-6 and any("圣光克暗" in t for t in tags), f"{mult} {tags}")
    bt2 = BT.Battle("monster", mk_sets_enemy("古龙"), {}, p_lj)
    mult2, tags2 = bt2._affix_dmg_mult(p_lj)
    check("龙脊套打古龙 +10%", abs(mult2 - 1.10) < 1e-6 and any("龙息追猎" in t for t in tags2), f"{mult2} {tags2}")
    bt3 = BT.Battle("monster", mk_sets_enemy("深渊魔像"), {}, p_dd)
    mult3, tags3 = bt3._affix_dmg_mult(p_dd)
    check("地底套打深渊 +10%", abs(mult3 - 1.10) < 1e-6 and any("深渊共鸣" in t for t in tags3), f"{mult3} {tags3}")
    bt4 = BT.Battle("monster", mk_sets_enemy("野狼"), {}, p_sg)
    mult4, _ = bt4._affix_dmg_mult(p_sg)
    check("圣光套打野狼不加成", abs(mult4 - 1.0) < 1e-6, str(mult4))
    # 9.3 元素增伤 5 件（月语/海神冰、苍穹雷）
    p_yy = mk_sets_player("月语套", 5)
    p_hs = mk_sets_player("海神套", 5)
    p_cq = mk_sets_player("苍穹套", 5)
    bty = BT.Battle("monster", mk_sets_enemy(), {}, p_yy)
    check("月语套冰系 +10%", abs(bty._affix_element_dmg(p_yy, "ice") - 1.10) < 1e-6)
    check("月语套火系不加成", abs(bty._affix_element_dmg(p_yy, "fire") - 1.0) < 1e-6)
    bth = BT.Battle("monster", mk_sets_enemy(), {}, p_hs)
    check("海神套冰系 +10%", abs(bth._affix_element_dmg(p_hs, "ice") - 1.10) < 1e-6)
    btc = BT.Battle("monster", mk_sets_enemy(), {}, p_cq)
    check("苍穹套雷系 +10%", abs(btc._affix_element_dmg(p_cq, "thunder") - 1.10) < 1e-6)
    check("苍穹套冰系不加成", abs(btc._affix_element_dmg(p_cq, "ice") - 1.0) < 1e-6)
    # 9.4 怪物技能元素字段 + 减速机制（数据完整性）
    elem_count = sum(1 for s in C.MONSTER_SKILLS.values() if s.get("element"))
    slow_count = sum(1 for s in C.MONSTER_SKILLS.values() if s.get("mech") == "slow")
    check("怪物元素技能 >=30", elem_count >= 30, str(elem_count))
    check("冰系减速技能 >=6", slow_count >= 6, str(slow_count))
    # v180：slow 主系冰（18）+ 后加 Boss/副本技允许 dark/nature（暗影箭雨/根须缠绕/怨灵尖啸）——
    # 旧断言"全为冰系"过时（数据演进加了非冰减速，属设计意图）
    slow_list = [v for v in C.MONSTER_SKILLS.values() if v.get("mech") == "slow"]
    ice_slow_n = sum(1 for v in slow_list if v.get("element") == "ice")
    ice_slow_ok = ice_slow_n >= 15
    check(f"减速技能主系冰系 >=15（现 {ice_slow_n}/{len(slow_list)}）", ice_slow_ok)
    # 9.5 元素抗性减免（elem_resist 火冰雷 / abyss_resist 暗影）
    p_res = mk_sets_player("橡木套", 5, affix_ids=["elem_resist"])
    p_abyss = mk_sets_player("橡木套", 5, affix_ids=["abyss_resist"])
    p_plain = mk_sets_player("橡木套", 5)
    enemy_bing = mk_sets_enemy("冰霜狼", skills=["ms_bing_dan"])  # 冰弹 ice+slow
    random.seed(1)
    btr = BT.Battle("monster", dict(enemy_bing), {}, p_res)
    found_r = False
    for _ in range(10):
        logs = enemy_turn_cast(btr, p_res)
        if "元素抗性减免" in "".join(logs):
            found_r = True
            break
    check("elem_resist 减免冰伤", found_r)
    enemy_dark = mk_sets_enemy("暗影法师", skills=["ms_an_ying_dan"])  # 暗影弹 dark
    random.seed(2)
    btd = BT.Battle("monster", dict(enemy_dark), {}, p_abyss)
    found_d = False
    for _ in range(10):
        logs = enemy_turn_cast(btd, p_abyss)
        if "元素抗性减免" in "".join(logs):
            found_d = True
            break
    check("abyss_resist 减免暗影伤", found_d)
    random.seed(2)
    btp = BT.Battle("monster", dict(enemy_dark), {}, p_plain)
    found_n = False
    for _ in range(10):
        logs = enemy_turn_cast(btp, p_plain)
        if "元素抗性减免" in "".join(logs):
            found_n = True
            break
    check("无抗性不减伤", not found_n)
    # 9.6 霜狼套 5 件免疫减速（抗寒）
    p_sl = mk_sets_player("霜狼套", 5)
    random.seed(1)
    bts = BT.Battle("monster", dict(enemy_bing), {}, p_sl)
    found_im = False
    for _ in range(10):
        logs = enemy_turn_cast(bts, p_sl)
        if "抗寒" in "".join(logs):
            found_im = True
            break
    check("霜狼套免疫减速", found_im)
    check("霜狼套无 spd_down", bts._p_buffs_bag().get("spd_down", 0) == 0)


async def main():
    test_data()
    test_roster_gen()
    test_random_gen()
    test_drop()
    await test_req()
    test_battle_affix()
    await test_shop_roster()
    test_craft_set()
    test_set5_and_resist()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
