# -*- coding: utf-8 -*-
"""格温放假游玩·第二弹：战斗深度 / 宠物养成 / 制作链·房产·市场（2026-08-08）

用法:
  python scripts/playtest_deep.py <阶段号>
  阶段 7=战斗深度（技能实战/元素克制/世界Boss/PVP）
  阶段 8=宠物养成（孵化/喂养/宠物战斗）
  阶段 9=制作链·房产·市场（采集→锻造→强化→附魔 / 房产 / 市场交易）

复用 playtest_full.py 的 GM 工具与指令封装。
"""
import os, sys, asyncio, json, time

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)
sys.path.insert(0, os.path.join(PLUGIN_DIR, "scripts"))

from playtest_full import (cmd, ensure_player, gm_level, gm_gold, gm_item, gm_tp, gm_kill,
                           G, M, ISSUES, issue, player_hp_full, fight_loop, explore_fight,
                           save_issues, clean, db, C)
import playtest_full as PF

Q = PF.Q  # playtest_full 模块级 Q（cmd 引用它）
Q2 = "q_play2"  # 第二玩家（PVP/市场对手）

async def cmd_as(qq, text, label="", quiet=False):
    """以指定 qq 发指令（改 playtest_full 模块级 Q，cmd 内部读取它）"""
    old = PF.Q
    PF.Q = qq
    try:
        return await cmd(text, label, quiet)
    finally:
        PF.Q = old

async def register_player2(lv=30, gold=20000, cls="法师", race="精灵", name="陪练酱"):
    """注册第二个玩家（PVP/市场用）"""
    await cmd_as(Q2, f"注册 {cls} {name} {race}", quiet=True)
    old = PF.Q
    PF.Q = Q2
    try:
        gm_level(lv)
        gm_gold(gold)
        db.update_player(G, Q2, hp=db.get_player(G, Q2)["max_hp"], mp=db.get_player(G, Q2)["max_mp"])
    finally:
        PF.Q = old
    print(f"  [GM] 第二玩家 {name} Lv.{lv} 就绪")

def inject_boss(key):
    """注入世界 Boss 事件（GM 跳过随机触发）"""
    b = next((x for x in C.WORLD_BOSS_POOL if x["name"] == key), C.WORLD_BOSS_POOL[0])
    db.save_world_event("boss", int(time.time()) + 7200, {
        "boss": {"name": b["name"], "icon": b["icon"], "lv": b["lv"], "hp": b["hp"],
                 "max_hp": b["hp"], "reward": b["reward"], "mech": b.get("mech", ""),
                 "map": b.get("map", ""), "map_name": b.get("map_name", ""), "contrib": {}}})
    print(f"  [GM] 世界 Boss 注入: {b['name']}（{b.get('map_name')} Lv.{b['lv']} HP {b['hp']:,}）")

# ============ 阶段实现 ============
STAGE_FUNCS = {}
def stage(n):
    def deco(f):
        STAGE_FUNCS[n] = f
        return f
    return deco

@stage(7)
async def stage7_combat_deep():
    """阶段七：战斗深度（技能实战/元素克制/世界Boss/PVP）"""
    print("\n╔══ 阶段七：战斗深度 ══╗")
    await ensure_player(lv=30, gold=50000)
    # 1. 技能准备
    r = await cmd("技能", "技能列表")
    r = await cmd("技能学习 1", "学习技能1")
    await cmd("技能详情 1", "技能详情")
    await cmd("技能栏", "技能栏")
    await cmd("设置技能 1 1", "技能栏设置")
    # 2. 野外实战（橡木平原，元素怪多）
    gm_tp("oak_plain", "oak_plain_2")
    r = await cmd("探索", "探索遇怪")
    if db.get_battle(G, Q):
        await cmd("技能 1", "技能实战（看伤害/MP/冷却）")
        await cmd("技能 1", "再放一次（看冷却限制）")
        await cmd("攻击", "普攻")
        await fight_loop(label="清怪")
    else:
        print("  [i] 未遇怪")
    # 3. 元素克制：找水系/火系怪对比伤害（迷雾沼泽）
    gm_tp("misty_swamp", "misty_swamp_1")
    r = await cmd("探索", "迷雾沼泽探索")
    if db.get_battle(G, Q):
        # 看敌人元素
        b = db.get_battle(G, Q)
        en = b["state"].get("enemy", {})
        print(f"  [i] 敌人: {en.get('name')} 元素={en.get('element', '无')}")
        # 普攻记录伤害
        r1 = await cmd("攻击", "普攻伤害参考", quiet=True)
        # 技能（若可用）记录伤害
        r2 = await cmd("技能 1", "技能伤害参考", quiet=True)
        await fight_loop(label="清沼泽怪")
    else:
        print("  [i] 迷雾沼泽未遇怪")
    # 4. 世界 Boss 讨伐（巨史莱姆王·咕噜咕噜，Lv.20 迷雾沼泽）
    inject_boss("巨史莱姆王·咕噜咕噜")
    await cmd("事件", "事件面板")
    r = await cmd("讨伐", "讨伐世界Boss")
    if "不在 Boss 出没地" in r:
        issue("7", "中", "讨伐提示不在 Boss 出没地（应已在迷雾沼泽）", how="inject_boss 后讨伐", fix="确认 inject 的 map 与玩家位置一致")
    rounds = 0
    while db.get_battle(G, Q) and rounds < 80:
        rounds += 1
        await cmd("攻击", quiet=True)
    await cmd("角色", "Boss战后状态")
    r = await cmd("讨伐", "再讨伐（应提示 Boss 已倒/无事件）")
    print(f"  [i] Boss 战 {rounds} 轮")
    # 5. PVP：注册第二玩家，野外决斗
    await register_player2(lv=30, cls="法师", name="陪练酱")
    gm_tp("oak_plain", "oak_plain_2")
    await cmd_as(Q2, "前往 橡木平原", quiet=True)  # 陪练也到野外
    r = await cmd(f"攻击 陪练酱", "PVP发起")
    if "安全区" in r or "新手保护" in r:
        issue("7", "中", f"PVP 被拦: {r[:100]}", how="野外攻击 @q_play2")
    # 轮流行动直到结束
    pvp_rounds = 0
    while db.get_battle(G, Q) and pvp_rounds < 40:
        pvp_rounds += 1
        st = db.get_battle(G, Q)["state"]
        actor = st.get("actor")
        if actor == "attacker":
            await cmd("攻击", quiet=True)
        else:
            await cmd_as(Q2, "攻击", quiet=True)
    await cmd("角色", "PVP后状态")
    await cmd("声望", "PVP后声望")
    print(f"  [i] PVP {pvp_rounds} 轮结束")
    print("\n── 阶段七完成 ──")

@stage(8)
async def stage8_pets():
    """阶段八：宠物养成（孵化/喂养/宠物战斗）"""
    print("\n╔══ 阶段八：宠物养成 ══╗")
    await ensure_player(lv=25, gold=30000)
    # 1. GM 给两枚蛋：狼崽（攻击型）+ 龙裔（魔攻型）
    for pk in ("pet_wolf", "pet_drake"):
        egg = C.make_pet_egg(pk)
        db.add_item(G, Q, f"petegg_{pk}", egg)
    await cmd("背包", "背包（看蛋）")
    # 2. 孵化狼崽
    r = await cmd("使用 森林狼崽蛋", "孵化狼崽")
    if "孵化" not in r and "宠物" not in r:
        issue("8", "高", f"宠物蛋使用异常: {r[:120]}", how="使用 森林狼崽蛋")
    await cmd("宠物", "宠物面板")
    # 3. 改名 + 喂养
    await cmd("宠物改名 小白", "宠物改名")
    r = await cmd("喂养", "喂养（无食物？）")
    # 4. 带宠物打怪（宠物技能 Lv.10+ 生效）
    gm_tp("oak_plain", "oak_plain_2")
    r = await cmd("探索", "探索遇怪")
    if db.get_battle(G, Q):
        rounds = await fight_loop(label="宠物助战")
        print(f"  [i] 宠物助战战斗 {rounds} 轮")
    await cmd("宠物", "宠物战后状态")
    # 5. 孵化第二只（龙裔）
    r = await cmd("使用 龙裔幼崽蛋", "孵化龙裔")
    r = await cmd("宠物", "宠物面板（应显示主宠）")
    # 6. 放生测试
    r = await cmd("放生", "放生确认")
    print("\n── 阶段八完成 ──")

@stage(9)
async def stage9_craft_home_market():
    """阶段九：制作链（采集→锻造→强化→附魔）+ 房产 + 市场交易"""
    print("\n╔══ 阶段九：制作链·房产·市场 ══╗")
    await ensure_player(lv=35, gold=100000)

    def gm_prof_finish():
        """GM 秒完成当前等待型副业（把 finish 改成过去再结算）"""
        st = M._prof_wait_state(PF.G, PF.Q)
        if not st:
            print("  [i] 无等待中的副业")
            return ""
        st["finish"] = int(time.time()) - 1
        return M._prof_settle(PF.G, PF.Q, st) or ""

    # 1. 采集 + 锻造（副业位上限 2，用完即换）
    db.activate_prof(PF.G, PF.Q, "gather")
    db.activate_prof(PF.G, PF.Q, "craft")
    print("  [GM] 副业：采集+锻造（2/2）")
    # 2. 采集 → 秒结算
    gm_tp("oak_plain", "oak_plain_2")
    r = await cmd("采集", "野外采集")
    r = gm_prof_finish()
    print(f"  [i] 采集结算: {r[:120]}")
    # 3. 锻造铁剑（缺材料则 GM 补史莱姆黏液）
    gm_tp("oak_town", "oak_town_3")
    r = await cmd("锻造 铁剑", "锻造铁剑")
    if "材料不足" in r:
        gm_item("史莱姆黏液", 5)
        r = await cmd("锻造 铁剑", "锻造铁剑（补料后）")
    print(f"  [i] 锻造结果: {r[:150]}")
    # 4. 强化（换副业：遗忘锻造→激活强化）
    db.forget_prof(PF.G, PF.Q, "craft")
    db.activate_prof(PF.G, PF.Q, "enhance")
    print("  [GM] 副业切换：强化")
    r = await cmd("强化 铁剑", "强化铁剑")
    print(f"  [i] 强化: {r[:150]}")
    # 5. 附魔（换副业：遗忘强化→激活附魔；给经验到 Lv.2）
    db.forget_prof(PF.G, PF.Q, "enhance")
    db.activate_prof(PF.G, PF.Q, "enchant")
    db.add_prof_exp(PF.G, PF.Q, "enchant", 200)
    print("  [GM] 副业切换：附魔 Lv.2")
    r = await cmd("附魔 铁剑 攻击", "附魔铁剑（攻击）")
    print(f"  [i] 附魔: {r[:150]}")
    # 加点力量（铁剑需求）后装备
    await cmd("加点 力量 9", "加点力量")
    await cmd("装备 铁剑", "装备铁剑")
    await cmd("战力", "战力（强化后）")
    # 6. 房产：地契 → 买房 → 回家 → 仓库 → 升级
    r = await cmd("地契", "地契列表")
    r = await cmd("买房 1", "买房")
    r = await cmd("回家", "回家")
    r = await cmd("仓库", "仓库面板")
    gm_item("狼皮", 3)
    r = await cmd("仓库 狼皮", "存仓库")
    r = await cmd("仓库", "仓库（存入后）")
    r = await cmd("取出 1", "取出物品")
    r = await cmd("升级", "房产升级")
    await cmd("出门", "出门")
    # 7. 市场：A 上架 → B 购入（上架未装备的狼皮）
    await register_player2(lv=25, cls="游侠", name="买家酱")
    r = await cmd("市场", "市场列表")
    r = await cmd("上架 狼皮 300", "A上架狼皮")
    r = await cmd("市场", "市场上架后")
    r = await cmd_as(Q2, "购入 1", "B购入")
    # 7. 摆摊交换：A 摆摊（不带价=换摊）→ B 交换
    r = await cmd("摆摊 狼皮", "A摆摊（换摊模式）")
    r = await cmd_as(Q2, "摊位", "B看摊")
    print(f"  [i] 摊位输出: {r[:200]}")
    import re as _re
    m = _re.search(r"#(\d+)", r)
    stall_no = m.group(1) if m else "1"
    r = await cmd_as(Q2, f"换 {stall_no} 治疗药水", f"B交换（摊位#{stall_no}）")
    print(f"  [i] 交换: {r[:150]}")
    r = await cmd("收摊", "A收摊")
    # B 背包验证（购入/交换的物品）
    r = await cmd_as(Q2, "背包", "B背包")
    print(f"  [i] B背包: {r[:200]}")
    await cmd("背包", "A最终背包")
    print("\n── 阶段九完成 ──")

def save_issues():
    out = ["# 游玩问题清单·第二弹（2026-08-08）\n"]
    sev_order = {"高": 0, "中": 1, "低": 2}
    ISSUES.sort(key=lambda x: (sev_order.get(x["sev"], 3), x["stage"]))
    for it in ISSUES:
        out.append(f"### 【{it['stage']}】【{it['sev']}】{it['desc']}")
        if it["how"]:
            out.append(f"- 复现: {it['how']}")
        if it["fix"]:
            out.append(f"- 建议: {it['fix']}")
        out.append("")
    path = os.path.join(PLUGIN_DIR, "playtest-issues2.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"\n📄 问题清单已保存: {path}（{len(ISSUES)} 条）")
    return path

async def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "7"
    if which == "all":
        for n in sorted(STAGE_FUNCS):
            await STAGE_FUNCS[n]()
    else:
        n = int(which)
        if n in STAGE_FUNCS:
            await STAGE_FUNCS[n]()
        else:
            print(f"未知阶段 {n}，可用: {sorted(STAGE_FUNCS)}")
    if ISSUES:
        save_issues()

if __name__ == "__main__":
    asyncio.run(main())
