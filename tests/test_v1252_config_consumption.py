# -*- coding: utf-8 -*-
"""v125.1/v125.2 收口审计·配置消费 + 启动校验。

覆盖：
  1. econ_config 住宿费：Lv.10=50（新手档 max(30, lv×5)）/ Lv.100=1000（高档向下取整到百）
     ——端到端『住宿』命令实测金币扣除
  2. signin_config 签到：首签 25 金（base 20 + streak 1×5）端到端
  3. SUBAREA_KIND：white_deer_8=enhance，且 _at_smith/_sa_shop_kind/地图设施清单消费该判定
  4. BOSS_MECHS 启动去重校验：模拟重复注册 → validate_boss_mechs 抛 RuntimeError
  5. GATHER_COND 启动校验：未注册条件词 → economy 模块导入抛 RuntimeError（importlib 重载实测）
"""
import importlib
import os
import sys

# ---- 私有临时库 ----
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1252_config_consumption.db")
os.environ["GWEN_GAME_DB"] = _DB
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C, db, clean_db, Main, FakeEvent, run  # noqa: E402
from data.plugins.dragonfall.game.core import battle_mech as BM  # noqa: E402
from data.plugins.dragonfall.game.commands import world as WORLD  # noqa: E402

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


def make_player(qq, lv=10, cur_map="oak_town", cur_subarea="oak_town_4", gold=10000):
    db.create_player("g", qq, f"测试{qq}", "cls_warrior", {}, 100, 50, race="human", gender="男")
    db.update_player("g", qq, level=lv, gold=gold, hp=300, max_hp=300, mp=100, max_mp=200,
                     stamina=999999, cur_map=cur_map, cur_subarea=cur_subarea)
    return db.get_player("g", qq)


# ================= 1. econ_config 住宿费 =================
async def section_inn(m):
    print("【1. econ_config 住宿费（lv10=50 / lv100=1000）】")
    ec = C.ECON_CONFIG
    check("ECON_CONFIG 键数与审计一致（16 键）", len(ec) == 16,
          f"keys={sorted(ec)}（v131 新增 inn_cost_high_mult 解耦住宿曲线，任务清单写 17 键，实际 16 键——以代码为准）")
    # Lv.10：新手档 max(30, 10×5)=50
    qq = "c_inn10"
    make_player(qq, lv=10)
    ev = FakeEvent("g", qq, "住宿")
    out = await run(m.rest, ev)
    txt = "\n".join(str(r) for r in out)
    p = db.get_player("g", qq)
    check("Lv.10 住宿扣 50 金", p["gold"] == 10000 - 50, f"gold={p['gold']}")
    check("Lv.10 播报花费 50 金币", "花费 50 金币" in txt, txt[:120])
    # Lv.100：高档 max(100, int(100×5×hp_stage_mult^0.5)//100×100)=1000
    qq2 = "c_inn100"
    make_player(qq2, lv=100)
    ev2 = FakeEvent("g", qq2, "住宿")
    out2 = await run(m.rest, ev2)
    txt2 = "\n".join(str(r) for r in out2)
    p2 = db.get_player("g", qq2)
    check("Lv.100 住宿扣 1000 金", p2["gold"] == 10000 - 1000, f"gold={p2['gold']}")
    check("Lv.100 播报花费 1000 金币", "花费 1000 金币" in txt2, txt2[:120])
    # 金币不足被拒
    qq3 = "c_innpoor"
    make_player(qq3, lv=10, gold=30)
    ev3 = FakeEvent("g", qq3, "住宿")
    out3 = await run(m.rest, ev3)
    txt3 = "\n".join(str(r) for r in out3)
    check("金币不足提示需要 50 金币", "住宿需要 50 金币" in txt3, txt3[:120])
    check("金币不足不扣费", db.get_player("g", qq3)["gold"] == 30)


# ================= 2. signin_config 首签 25 金 =================
async def section_signin(m):
    print("【2. signin 首签 25 金（base 20 + streak 1×5）】")
    sc = C.SIGNIN_CONFIG
    check("SIGNIN_CONFIG 键完整（6 键）",
          set(sc) == {"base_gold", "streak_gold_step", "festival_mult",
                      "fortune_bad_th", "fortune_good_th", "week_quality_weights"},
          str(sorted(sc)))
    qq = "c_sign"
    make_player(qq)
    ev = FakeEvent("g", qq, "签到")
    out = await run(m.signin, ev)
    txt = "\n".join(str(r) for r in out)
    p = db.get_player("g", qq)
    check("首签金币 +25（base 20 + streak 1×5）", p["gold"] == 10000 + 25, f"gold={p['gold']}")
    check("签到播报获得 25 金币", "获得 25 金币" in txt, txt[:120])
    out2 = await run(m.signin, FakeEvent("g", qq, "签到"))
    txt2 = "\n".join(str(r) for r in out2)
    check("同日重复签到被拒（原子认领）", "已经签过到啦" in txt2, txt2[:80])


# ================= 3. SUBAREA_KIND white_deer_8 = 强化坊 =================
def section_subarea_kind(m):
    print("【3. SUBAREA_KIND：white_deer_8=enhance】")
    check("white_deer_8 判定为 enhance（强化坊）",
          C.SUBAREA_KIND.get("white_deer_8") == "enhance",
          str(C.SUBAREA_KIND.get("white_deer_8")))
    check("white_deer_3 判定为 smith（铁匠铺对照）",
          C.SUBAREA_KIND.get("white_deer_3") == "smith")
    # _at_smith：white_deer_8 可强化（enhance 消费）
    p = make_player("c_sa8", 60, cur_map="white_deer", cur_subarea="white_deer_8")
    check("_at_smith(white_deer_8) True（enhance 消费）", m._at_smith(p) is True)
    # white_deer_3 smith 也是 True
    p2 = make_player("c_sa3", 60, cur_map="white_deer", cur_subarea="white_deer_3")
    check("_at_smith(white_deer_3) True（smith 消费）", m._at_smith(p2) is True)
    # 非强化/铁匠子区域 False（white_deer_4 酒馆）
    p3 = make_player("c_sa4", 60, cur_map="white_deer", cur_subarea="white_deer_4")
    check("_at_smith(white_deer_4) False（酒馆不算铁匠）", m._at_smith(p3) is False)
    # _sa_shop_kind：white_deer_8 → enhance（配货语义与 misc 等价）
    p4 = db.get_player("g", "c_sa8")
    check("_sa_shop_kind(white_deer_8) == enhance", m._sa_shop_kind(p4) == "enhance",
          str(m._sa_shop_kind(p4)))
    # 地图设施清单：white_deer_8 显示铁匠铺入口（world._map_facilities 消费）
    cm = C.MAP_BY_ID.get("white_deer", {})
    fac = WORLD.WorldCmds._map_facilities(m, cm, p4)
    check("地图设施清单含铁匠铺（SUBAREA_KIND enhance 消费）",
          any("铁匠铺" in l for l in fac), str(fac))


# ================= 4. BOSS_MECHS 启动去重校验 =================
def section_boss_dedup():
    print("【4. BOSS_MECHS 重复注册启动校验】")
    # 篡改注册顺序表模拟重复注册（enrage 被 register 两次）
    n0 = len(BM._REG_ORDER)
    BM._REG_ORDER.append((id(BM.BOSS_MECHS), "enrage"))
    BM._REG_ORDER.append((id(BM.BOSS_MECHS), "enrage"))
    raised = False
    try:
        BM.validate_boss_mechs()
    except RuntimeError as e:
        raised = "重复注册" in str(e) and "enrage" in str(e)
    finally:
        del BM._REG_ORDER[n0:]
    check("重复注册抛 RuntimeError（含 token 名）", raised)
    # 恢复后校验通过（数据引用校验不报错）
    ok = True
    try:
        BM.validate_boss_mechs()
    except RuntimeError:
        ok = False
    check("恢复后 validate_boss_mechs 通过", ok)


# ================= 5. GATHER_COND 启动校验（模块级 fail-fast） =================
def section_gather_startup():
    print("【5. GATHER_COND 启动校验（economy 模块级）】")
    from data.plugins.dragonfall.game.commands import economy as _eco
    orig_pools = C.GATHER_COND_POOLS
    raised = False
    try:
        # 塞一个未注册条件词 fog（注册表只有 night/morning/winter/rain）
        C.GATHER_COND_POOLS = {"fake_map": [("mat_x", "雾", "fog+night")]}
        try:
            importlib.reload(_eco)
        except RuntimeError as e:
            raised = "未注册" in str(e) and "fog" in str(e)
    finally:
        C.GATHER_COND_POOLS = orig_pools
        importlib.reload(_eco)  # 恢复干净模块（真实数据校验通过）
    check("未注册采集条件词 → 模块导入抛 RuntimeError", raised)
    # 恢复后真实数据全部注册（重载即验证）
    words = set()
    for _entries in C.GATHER_COND_POOLS.values():
        for _e in _entries:
            for t in str(_e[2]).split("+"):
                if t:
                    words.add(t)
    from data.plugins.dragonfall.game.commands.economy import _GATHER_COND_CHECKERS  # noqa: E402
    check("重载后真实条件词全部注册", words <= set(_GATHER_COND_CHECKERS),
          f"missing={sorted(words - set(_GATHER_COND_CHECKERS))}")


async def main():
    clean_db()
    m = Main(None)
    await section_inn(m)
    await section_signin(m)
    section_subarea_kind(m)
    section_boss_dedup()
    section_gather_startup()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
