# -*- coding: utf-8 -*-
"""v116 公会成长纵深：职位体系 + 公会商店（创建公会→捐献→商店扣积分→职位任命）

验证：
  1. 创建公会 → 会长身份（leader）
  2. 『公会捐献』加公会积分（contribute）
  3. 『公会商店』列表展示；『公会商店 <编号>』购买扣积分并发物品
  4. 积分不足 / 公会等级门槛拦截
  5. 『公会任命 <名字> 副会长』晋升；非会长不能任命
  6. 老档 role 兼容（leader/member 直读，GUILD_ROLES 映射命中）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main, FakeEvent, run
# v116：公会新数据表/存取函数未经 data/__init__、store/__init__ 聚合导出（避免并行冲突），测试直接本地 import
from data.plugins.dragonfall.game.data import guild as _G
from data.plugins.dragonfall.game.store.social import guild_get_member, guild_set_role

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        safe = detail.encode("utf-8", "replace").decode("utf-8", "replace") if detail else ""
        print(f"  ❌ {name} {safe}")

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "g1p", "注册 战士 会长 男")
    await cmd(m, "register", "g1", "g2p", "注册 法师 副会长 男")
    await cmd(m, "register", "g1", "g3p", "注册 刺客 精英 男")
    db.update_player("g1", "g1p", level=30, gold=10000, cur_map="oak_town")
    db.update_player("g1", "g2p", level=30, gold=10000, cur_map="oak_town")
    db.update_player("g1", "g3p", level=30, gold=10000, cur_map="oak_town")

    print("【v116 职位体系：创建/加入】")
    out = await cmd(m, "guild_create_cmd", "g1", "g1p", "创建公会 勇者公会")
    check("创建成功", "创建成功" in out, out[:200])
    out = await cmd(m, "guild_join_cmd", "g1", "g2p", "加入公会 勇者公会")
    check("副会长 加入成功", "欢迎" in out, out[:200])
    out = await cmd(m, "guild_join_cmd", "g1", "g3p", "加入公会 勇者公会")
    check("精英 加入成功", "欢迎" in out, out[:200])
    g = db.guild_get_by_name("勇者公会")
    check("公会落库且会长=leader", g is not None and guild_get_member(g["gid"], "g1p")["role"] == "leader", str(g))
    check("老档 role 兼容映射", _G.GUILD_ROLES.get("leader")[1] == "👑" and _G.GUILD_ROLES.get("member")[1] == "⚔️", "")

    print("【v116 公会商店：列表 + 购买】")
    out = await cmd(m, "guild_shop", "g1", "g1p", "公会商店")
    check("商店列表展示", "公会商店" in out and "淬火石" in out and "积分" in out, out[:300])
    # 初始贡献为 0，购买前先签到/捐献给会长攒积分（直接改库里贡献以聚焦商店逻辑）
    db.guild_add_exp(g["gid"], 1, member_qq="g1p", contribute=500)
    check("会长积分 500", guild_get_member(g["gid"], "g1p")["contribute"] == 500, "")
    out = await cmd(m, "guild_shop", "g1", "g1p", "公会商店 1")
    check("购买淬火石成功", "购买成功" in out and "淬火石" in out, out[:300])
    check("积分扣除 500-30", guild_get_member(g["gid"], "g1p")["contribute"] == 470, str(guild_get_member(g["gid"], "g1p")["contribute"]))
    inv = [it for it in db.get_inventory("g1", "g1p") if it["data"].get("name") == "淬火石"]
    check("淬火石入包", len(inv) >= 1, str(len(inv)))
    # 积分不足（用贡献为 0 的成员 g3p 买 Lv.1 可购的淬火石）
    out = await cmd(m, "guild_shop", "g1", "g3p", "公会商店 1")
    check("积分不足拦截", "积分不足" in out, out[:200])
    # 公会等级门槛（公会 Lv.1 < 商品4 需 Lv.3）
    out = await cmd(m, "guild_shop", "g1", "g1p", "公会商店 4")
    check("公会等级门槛拦截", "需要公会 Lv.3" in out, out[:200])

    print("【v116 职位体系：任命 / 权限】")
    # 非会长不能任命
    out = await cmd(m, "guild_appoint", "g1", "g2p", "公会任命 精英 副会长")
    check("非会长任命被拦", "只有会长" in out, out[:200])
    # 会长公会 Lv.1 < 副会长门槛 Lv.3 → 拦截
    out = await cmd(m, "guild_appoint", "g1", "g1p", "公会任命 精英 副会长")
    check("副会长需公会 Lv.3 拦截", "需要公会 Lv.3" in out, out[:200])
    # 任命精英（无门槛）成功
    out = await cmd(m, "guild_appoint", "g1", "g1p", "公会任命 精英 精英")
    check("任命精英成功", "任命成功" in out and "精英" in out, out[:300])
    check("g3p role=elite", guild_get_member(g["gid"], "g3p")["role"] == "elite", str(guild_get_member(g["gid"], "g3p")["role"]))
    # 公会升到 Lv.3 后任命副会长成功
    db.guild_add_exp(g["gid"], 100000)  # 冲级
    gg = db.guild_get_by_name("勇者公会")
    check("公会已升 Lv.3", gg["level"] >= 3, str(gg["level"]))
    out = await cmd(m, "guild_appoint", "g1", "g1p", "公会任命 副会长 副会长")
    check("任命副会长成功", "任命成功" in out and "副会长" in out, out[:300])
    check("g2p role=vice_leader", guild_get_member(g["gid"], "g2p")["role"] == "vice_leader", str(guild_get_member(g["gid"], "g2p")["role"]))
    out = await cmd(m, "guild_demote", "g1", "g1p", "公会免职 副会长")
    check("免职成功降回成员", "免去" in out and "成员" in out, out[:300])
    check("g2p role=member", guild_get_member(g["gid"], "g2p")["role"] == "member", str(guild_get_member(g["gid"], "g2p")["role"]))

    print("【v116 公会技能：展示】")
    out = await cmd(m, "guild_skill_view", "g1", "g1p", "公会技能")
    check("技能列表展示", "公会技能" in out and "攻击强化" in out and "积分" in out, out[:300])

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
