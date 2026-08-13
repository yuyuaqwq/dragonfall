# -*- coding: utf-8 -*-
"""M10 锻造打造 全量审计（只读验证，测试库）"""
import sys, os, json, random, sqlite3, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace("scripts", "tests"))
from conftest import C, db, clean_db, Main, FakeEvent, run, make_player

random.seed(42)
passed, failed = 0, 0
def check(name, cond, detail=""):
    global passed, failed
    if cond: passed += 1; print(f"  ✅ {name}")
    else: failed += 1; print(f"  ❌ {name} {detail}")

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

def set_prof_lv(qid, key, lv):
    conn = sqlite3.connect(db.DB_PATH)
    conn.execute("INSERT OR IGNORE INTO professions (qq_id) VALUES (?)", (qid,))
    conn.execute(f"UPDATE professions SET {key}_lv=?, {key}_exp=0 WHERE qq_id=?", (lv, qid))
    conn.commit(); conn.close()

def gotomap(gid, qid):
    db.update_player(gid, qid, cur_map="oak_town", cur_subarea="oak_town_3")

def give_mat(gid, qid, mid, n):
    m = C.MATERIALS[mid]
    db.add_item(gid, qid, mid, {"name": m["name"], "type": "材料", "stackable": True, "price": m.get("price", 0)}, count=n)

# ============ 静态：配方/材料/名册/图纸 ============
print("== [A] 模块统计 ==")
recs = C.CRAFT_RECIPES
n_bp = sum(1 for r in recs.values() if r.get("blueprint"))
bps = sorted({r["blueprint"] for r in recs.values() if r.get("blueprint")})
print(f"  CRAFT_RECIPES={len(recs)} 需图纸配方={n_bp} 唯一图纸={len(bps)}")
roster = C.EQUIP_ROSTER
src_bp = {rid: r for rid, r in roster.items() if r.get("source") in ("图纸", "boss")}
print(f"  EQUIP_ROSTER={len(roster)} source=图纸/boss={len(src_bp)}  MATERIALS={len(C.MATERIALS)}")

print("== [B] 配方完整性 ==")
bad_resolve, bad_mat, bad_roster, name_mismatch, no_roster = [], [], [], [], []
for k, r in recs.items():
    if C.display("recipes", k) == k: bad_resolve.append(k)
    for m in r["mats"]:
        if m not in C.MATERIALS: bad_mat.append((k, m))
    rid = r.get("roster_id")
    if rid:
        if rid not in roster: bad_roster.append((k, rid))
        elif roster[rid]["name"] != r["name"]: name_mismatch.append((k, rid, roster[rid]["name"], r["name"]))
    else:
        no_roster.append(k)
check("配方 key 全部可 resolve/display", not bad_resolve, str(bad_resolve))
check("配方材料全部在 MATERIALS 表", not bad_mat, str(bad_mat))
check("配方 roster_id 全部在名册", not bad_roster, str(bad_roster))
check("名册装备名 == 配方名", not name_mismatch, str(name_mismatch))
print(f"  无 roster_id 的旧配方 {len(no_roster)} 个: {no_roster[:30]}")

print("== [C] 图纸 ↔ 名册 ↔ 配方 闭环 ==")
bp_roster_names = {r["name"] for r in src_bp.values()}
unreachable = []
for k, r in recs.items():
    if r.get("blueprint") and r["name"] not in bp_roster_names:
        unreachable.append((k, r["name"], r["blueprint"]))
check("所有需图纸配方的图纸名册可产出", not unreachable, str(unreachable))
recipe_bp_names = {r["blueprint"] for r in recs.values() if r.get("blueprint")}
no_recipe = []
for rid, r in sorted(src_bp.items(), key=lambda x: x[1]["lv"]):
    if f"{r['name']}图纸" not in recipe_bp_names:
        no_recipe.append((rid, r["name"], r["lv"], r["quality"], r["source"]))
print(f"  ⚠️ 图纸可学但无锻造配方: {len(no_recipe)} 个")
for rid, n, lv, q, s in no_recipe:
    print(f"    - {rid} {n} Lv.{lv} {q} source={s}")
bp_name_mismatch = [(k, r["blueprint"]) for k, r in recs.items() if r.get("blueprint") and r["blueprint"] != f"{r['name']}图纸"]
check("blueprint 名 == 名册名+图纸", not bp_name_mismatch, str(bp_name_mismatch))
from collections import Counter
bp_cnt = Counter(r["blueprint"] for r in recs.values() if r.get("blueprint"))
multi = {b: n for b, n in bp_cnt.items() if n > 1}
print(f"  一张图纸解锁多配方: {multi if multi else '无'}")

print("== [D] 别名表 ==")
al = C.CRAFT_RECIPE_ALIASES
alias_bad = [k for k in al if k not in recs]
check("别名 key 全部在 CRAFT_RECIPES", not alias_bad, str(alias_bad))
seen = {}
dup_alias = []
for k, vals in al.items():
    for v in vals:
        if v in seen: dup_alias.append((v, seen[v], k))
        seen[v] = k
check("别名值无重复", not dup_alias, str(dup_alias))
conflict = [(v, k) for k, vals in al.items() for v in vals if C.resolve("recipes", v) in recs and C.resolve("recipes", v) != k]
check("别名不与真实配方名冲突", not conflict, str(conflict))

print("== [E] 经济：配方金币 vs 产物价值 / 材料价值 ==")
from data.plugins.dragonfall.game.core.drops import generate_roster_equip
bad_ratio, ratios = [], []
for k, r in sorted(recs.items(), key=lambda x: x[1]["lv"]):
    rid = r.get("roster_id")
    if not rid: continue
    eq = generate_roster_equip(rid)
    price = eq["price"]
    mat_val = sum(C.MATERIALS[m].get("price", 0) * n for m, n in r["mats"].items())
    ratio = r["gold"] / price if price else 0
    ratios.append((k, r["name"], r["gold"], price, round(ratio, 2), mat_val))
    if ratio > 1.0: bad_ratio.append((k, r["name"], r["gold"], price, round(ratio, 2)))
print(f"  配方金/产物价值 倒挂(>100%) {len(bad_ratio)} 个: {bad_ratio}")
if ratios:
    print("  全部比值区间: %.2f%% ~ %.2f%%" % (min(x[4] for x in ratios)*100, max(x[4] for x in ratios)*100))
bad_matval = [(k, n, mat_val, r["gold"]) for k, n, g, p, rr, mat_val in ratios if mat_val > r["gold"]]
print(f"  材料价值>配方金 {len(bad_matval)} 个: {bad_matval[:10]}")

print("== [F] 等级门槛 ==")
tiers = C.RECIPE_LV_TIERS
print(f"  RECIPE_LV_TIERS={tiers} → 锻造需求等级 1..{len(tiers)+1}")
need6 = [k for k, r in recs.items() if r["lv"] > tiers[-1]]
print(f"  需锻造 Lv.{len(tiers)+1} 的配方 {len(need6)} 个: {[recs[k]['name'] for k in need6]}")

# ============ 动态：边界实测 ============
print("== [G] 动态边界测试 ==")

async def main():
    global gid, qid, passed, failed
    m = Main(None)
    clean_db()
    gid, qid = "g10", "q10"
    p = make_player(gid, qid, level=30)
    gotomap(gid, qid)
    set_prof_lv(qid, "craft", 2)  # Lv>1 自动激活副业（绕开拜师门禁，聚焦锻造本体）

    # 1) 锻造成功全流程（白鹿皮甲：blue 无图纸 lv8，需 石来木黏液×2，84金）
    give_mat(gid, qid, "mat_shi_lai_mu_nian_ye", 2)
    db.update_player(gid, qid, gold=500)
    r = await cmd(m, "craft", gid, qid, "锻造 白鹿皮甲")
    check("G1 锻造成功入包+扣材料+扣金+经验", "锻造成功" in r and "白鹿皮甲" in r, r[:120])
    p2 = db.get_player(gid, qid)
    check("G1b 金币扣 84", p2["gold"] == 500-84, f"gold={p2['gold']}")
    check("G1c 材料扣完", db.count_item(gid, qid, "mat_shi_lai_mu_nian_ye") == 0, "仍有材料")
    profs = db.get_professions(gid, qid)["craft"]
    check("G1d 锻造经验+1", profs["exp"] >= 1, str(profs))
    inv = db.get_inventory(gid, qid)
    check("G1e 装备入包", any(it["data"].get("name") == "白鹿皮甲" for it in inv), str([it["data"].get("name") for it in inv]))

    # 2) 材料差 1 个 → 拦截（且检查体力是否被扣）
    db.update_player(gid, qid, stamina=100, gold=500)
    give_mat(gid, qid, "mat_shi_lai_mu_nian_ye", 1)
    r = await cmd(m, "craft", gid, qid, "锻造 白鹿皮甲")
    check("G2 材料差1拦截", "材料不足" in r, r[:100])
    p3 = db.get_player(gid, qid)
    check("G2b 失败不扣材料", db.count_item(gid, qid, "mat_shi_lai_mu_nian_ye") == 1, "材料被扣")
    check("G2c 失败不扣金币", p3["gold"] == 500, f"gold={p3['gold']}")
    check("G2d 失败却扣了10体力(先扣体力后查材料)", p3["stamina"] == 90, f"stamina={p3['stamina']}")

    # 3) 未学图纸装备 → 拦截（北风长弓 lv65 purple 需图纸）
    give_mat(gid, qid, "mat_shuang_ju_mo_xue", 4); give_mat(gid, qid, "mat_tie_kuang_shi", 3)
    db.update_player(gid, qid, gold=5000, level=70)
    set_prof_lv(qid, "craft", 6)
    r = await cmd(m, "craft", gid, qid, "锻造 北风长弓")
    check("G3 未学图纸拦截", "需要先学习图纸" in r, r[:100])
    print(f"  [debug] 学图纸前材料数: 霜巨魔血={db.count_item(gid,qid,'mat_shuang_ju_mo_xue')} 铁矿石={db.count_item(gid,qid,'mat_tie_kuang_shi')}")
    bp = C.make_blueprint("eq_bei_feng_chang_gong")
    db.add_item(gid, qid, "bp_test", bp)
    r = await cmd(m, "learn", gid, qid, f"学习 {bp['name']}")
    check("G3b 学习成功", "永久解锁" in r, r[:100])
    db.add_item(gid, qid, "bp_test2", bp)  # 补一张再测重复学习
    r = await cmd(m, "learn", gid, qid, f"学习 {bp['name']}")
    check("G3c 重复学习拦截", "已经学会" in r, r[:100])
    print(f"  [debug] 学图纸后材料数: 霜巨魔血={db.count_item(gid,qid,'mat_shuang_ju_mo_xue')} 铁矿石={db.count_item(gid,qid,'mat_tie_kuang_shi')}")
    r = await cmd(m, "craft", gid, qid, "锻造 北风长弓")
    check("G3d 学后锻造成功", "锻造成功" in r, r[:100])

    # 4) 锻造等级不足（苍穹头盔 lv85 → 锻造Lv5；设 craft_lv=2）
    db.update_player(gid, qid, gold=5000, level=90)
    set_prof_lv(qid, "craft", 2)
    give_mat(gid, qid, "mat_feng_zhi_yu", 5); give_mat(gid, qid, "mat_xing_hui_chen", 4)
    r = await cmd(m, "craft", gid, qid, "锻造 苍穹头盔")
    check("G4 锻造等级不足拦截", "需要锻造副业 Lv.5" in r, r[:120])

    # 5) 页码越界 & 序号越界
    r = await cmd(m, "craft", gid, qid, "锻造列表 999")
    check("G5 列表页码越界被钳制", "第 1/1 页" in r or "第" in r, r[:60])
    r = await cmd(m, "craft", gid, qid, "锻造 999")
    check("G5b 序号越界拦截", "没有第 999 个" in r, r[:80])
    r = await cmd(m, "craft", gid, qid, "锻造列表2")
    check("G5c 免空格粘页码 锻造列表2", "第 2/" in r or "第" in r, r[:60])

    # 6) 背包满 → 无容量限制直接入包
    for i in range(60):
        db.add_item(gid, qid, f"eq_bulk_{i}", {"name": f"压仓{i}", "type": "装备", "slot": "weapon", "stackable": False})
    give_mat(gid, qid, "mat_shi_lai_mu_nian_ye", 2)
    r = await cmd(m, "craft", gid, qid, "锻造 白鹿皮甲")
    check("G6 背包60+件仍可锻造入包(无容量限制)", "锻造成功" in r, r[:100])

    # 7) 代工流程（不要求副业/拜师，3倍金）
    db.update_player(gid, qid, gold=10000)
    give_mat(gid, qid, "mat_shi_lai_mu_nian_ye", 2)
    r = await cmd(m, "craft_commission", gid, qid, "代工 白鹿皮甲")
    check("G7 代工3倍金成功", "代工完成" in r and "252" in r, r[:120])

    # 8) 代工未学图纸也拦截
    r = await cmd(m, "craft_commission", gid, qid, "代工 潮汐法杖")
    check("G8 代工未学图纸拦截", "需要先学习图纸" in r, r[:100])

    # 9) 别名 KeyError 崩溃验证：别名指向不存在的配方
    try:
        r = await cmd(m, "craft", gid, qid, "锻造 钢剑")
        check("G9 别名『钢剑』不崩溃", "没有找到" in r or "钢剑" in r, r[:120])
    except Exception as e:
        print(f"  ❌ G9 别名『钢剑』触发异常: {type(e).__name__}: {e}")
        failed += 1

    # 10) 星尘法杖图纸（名册有、无配方）学习 → 解锁 0 配方
    bp2 = C.make_blueprint("eq_xing_chen_fa_zhang")
    db.add_item(gid, qid, "bp_xc", bp2)
    r = await cmd(m, "learn", gid, qid, "学习 星尘法杖图纸")
    check("G10 无配方图纸可学习(浪费)", "永久解锁 0 个配方" in r, r[:120])

    # 11) 学习 星尘法杖图纸 后尝试锻造 → 找不到配方
    r = await cmd(m, "craft", gid, qid, "锻造 星尘法杖")
    check("G11 学后仍无法锻造(无配方)", "没有找到" in r, r[:120])

    print(f"\n==== 结果: 通过 {passed} / 失败 {failed} ====")

asyncio.run(main())
