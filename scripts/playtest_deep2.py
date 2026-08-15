# -*- coding: utf-8 -*-
"""格温放假游玩·第三弹：日常系统 / 钓鱼深度 / 拍卖行 / 坐骑套装 / 组队讨伐 / 边界测试（2026-08-08）

用法:
  python scripts/playtest_deep2.py <阶段号>
  阶段 10=日常·签到·声望·排行
  阶段 11=钓鱼深度（多钓点/档位/鱼王/彩蛋/宠物蛋渠道）
  阶段 12=拍卖行深度（竞拍/超越退还/自加价/一口价/流拍结算）
  阶段 13=坐骑·套装·洗点·转职重置
  阶段 14=组队·讨伐·世界事件效果
  阶段 15=边界与异常测试

复用 playtest_full / playtest_deep 的 GM 工具与指令封装。
"""
import os, sys, asyncio, json, time, random, re

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)
sys.path.insert(0, os.path.join(PLUGIN_DIR, "scripts"))

from playtest_full import (cmd, ensure_player, gm_level, gm_gold, gm_item, gm_tp, gm_kill,
                           G, M, ISSUES, issue, player_hp_full, fight_loop, explore_fight,
                           save_issues, clean, db, C)
from playtest_deep import cmd_as, register_player2, inject_boss, Q, Q2
import playtest_full as PF
import playtest_deep as PD

async def q2_cmd(text, label="", quiet=False):
    """第二玩家发指令"""
    return await cmd_as(Q2, text, label, quiet)

def gm_prof_finish():
    """GM 秒完成当前等待型副业（把 finish 改成过去再结算）"""
    st = M._prof_wait_state(PF.G, PF.Q)
    if not st:
        print("  [i] 无等待中的副业")
        return ""
    st["finish"] = int(time.time()) - 1
    return M._prof_settle(PF.G, PF.Q, st) or ""

def gm_add_equip(slot, lv, quality, set_name=None, name=None):
    """GM 直接塞一件装备进背包（可指定套装）"""
    import uuid
    eq = C.generate_equip(slot, lv, quality)
    if set_name:
        eq["set"] = set_name
        eq["name"] = f"{set_name}{random.choice(['之刃','战甲','护手','之戒','项链','护腿'])}"
    if name:
        eq["name"] = name
    key = f"eq_{uuid.uuid4().hex[:8]}"
    db.add_item(PF.G, PF.Q, key, eq, count=1)
    print(f"  [GM] 装备+{eq['name']}（{slot} Lv.{lv} {quality}）")
    return eq

def inject_auction(items):
    """注入拍卖事件（items: [{id,name,slot,quality,base,buyout,bids}]）"""
    data = {"items": items}
    db.save_world_event("auction", int(time.time()) + 7200, data)
    print(f"  [GM] 拍卖事件注入: {len(items)} 件拍卖品")

def inject_event(etype, ends_in=7200, boss_name=None):
    """注入世界事件（merchant/swarm/festival/omen/boss/auction）"""
    evt = next((e for e in C.WORLD_EVENT_POOL if e["type"] == etype), None)
    data = {}
    if etype == "auction":
        pool = random.sample(C.AUCTION_POOL, min(3, len(C.AUCTION_POOL)))
        items = []
        for i, ap in enumerate(pool, 1):
            equip = C.generate_equip(ap["slot"], ap["lv"], ap["quality"])
            items.append({"id": i, "name": equip["name"], "slot": ap["slot"],
                          "stats": equip.get("stats", {}), "desc": equip.get("desc", ""),
                          "base": ap["base"], "buyout": ap["buyout"], "bids": {}})
        data["items"] = items
    elif etype == "boss":
        if boss_name:
            b = next((x for x in C.WORLD_BOSS_POOL if x["name"] == boss_name), C.WORLD_BOSS_POOL[0])
        else:
            b = random.choice(C.WORLD_BOSS_POOL)
        data["boss"] = {"name": b["name"], "icon": b["icon"], "lv": b["lv"], "hp": b["hp"],
                        "max_hp": b["hp"], "reward": b["reward"], "contrib": {},
                        "mech": b.get("mech", ""), "map": b.get("map", ""),
                        "map_name": b.get("map_name", "")}
    db.save_world_event(etype, int(time.time()) + ends_in, data)
    print(f"  [GM] 世界事件注入: {etype}" + (f"（{boss_name}）" if boss_name else ""))

# ============ 阶段实现 ============
STAGE_FUNCS = {}
def stage(n):
    def deco(f):
        STAGE_FUNCS[n] = f
        return f
    return deco

@stage(10)
async def stage10_daily_social():
    """阶段十：日常·签到·声望·排行·称号·编年史"""
    print("\n╔══ 阶段十：日常·签到·声望·排行 ══╗")
    await ensure_player(lv=30, gold=50000)
    # 1. 签到
    r = await cmd("签到", "签到")
    print(f"  [i] 签到: {r[:200]}")
    r = await cmd("签到", "重复签到（应拒绝）")
    print(f"  [i] 重复签到: {r[:80]}")
    # 2. 每日任务
    r = await cmd("每日", "领取每日任务")
    print(f"  [i] 每日: {r[:200]}")
    r = await cmd("每日", "重复领取（应拒绝）")
    print(f"  [i] 重复每日: {r[:80]}")
    r = await cmd("任务", "任务面板")
    print(f"  [i] 任务面板: {r[:200]}")
    # 3. 声望
    r = await cmd("声望", "声望面板")
    print(f"  [i] 声望: {r[:250]}")
    # 4. 排行
    r = await cmd("排行", "强者榜")
    print(f"  [i] 排行: {r[:200]}")
    r = await cmd("排行 副业", "副业榜")
    print(f"  [i] 排行副业: {r[:150]}")
    # 5. 编年史
    r = await cmd("编年史", "编年史")
    print(f"  [i] 编年史: {r[:150]}")
    # 6. 称号
    r = await cmd("称号", "称号面板")
    print(f"  [i] 称号: {r[:150]}")
    # 7. 成就面板
    r = await cmd("成就 战斗", "成就·战斗")
    print(f"  [i] 成就战斗: {r[:150]}")
    r = await cmd("成就", "成就总览")
    print(f"  [i] 成就总览: {r[:150]}")
    print("\n── 阶段十完成 ──")

@stage(11)
async def stage11_fishing():
    """阶段十一：钓鱼深度"""
    print("\n╔══ 阶段十一：钓鱼深度 ══╗")
    await ensure_player(lv=30, gold=50000)
    db.activate_prof(PF.G, PF.Q, "fishing")
    print("  [GM] 副业激活：垂钓")
    # 找钓点：橡木溪流（oak_town 附近？）看 FISHING_SPOTS
    spots = C.FISHING_SPOTS or {}
    print(f"  [i] 钓点: {list(spots.keys())[:10]}")
    # 主钓点：橡木溪流
    spot_map = next((k for k in spots if "oak" in k or "溪" in spots[k].get("name", "")), list(spots.keys())[0])
    m = C.MAP_BY_ID.get(spot_map, {})
    sa = ""
    if isinstance(spots.get(spot_map), dict) and spots[spot_map].get("subarea"):
        sa = spots[spot_map]["subarea"]
    gm_tp(spot_map, sa)
    print(f"  [i] 钓点: {spots.get(spot_map)}")
    # 连续钓 8 次（GM 秒结算）
    results = {"鱼王": 0, "宝物": 0, "垃圾": 0, "普通鱼": 0, "彩蛋": 0, "宠物蛋": 0}
    for i in range(8):
        r = await cmd("垂钓", f"垂钓{i+1}")
        r2 = gm_prof_finish()
        if "鱼王" in r2:
            results["鱼王"] += 1
        elif "宝物" in r2:
            results["宝物"] += 1
        elif "垃圾" in r2:
            results["垃圾"] += 1
        elif "彩蛋" in r2 or "收藏" in r2:
            results["彩蛋"] += 1
        if "宠物蛋" in r2:
            results["宠物蛋"] += 1
        if r2 and ("鱼" in r2 or "材料" in r2):
            results["普通鱼"] += 1
        print(f"  [i] 第{i+1}竿: {r2[:120]}")
    print(f"  [i] 8 竿统计: {results}")
    # 出售鱼
    r = await cmd("背包", "钓鱼后背包")
    print(f"  [i] 背包: {r[:250]}")
    r = await cmd("出售 鱼", "出售鱼（测试）")
    print(f"  [i] 出售: {r[:150]}")
    # 高级水域限制（垂钓 Lv 不足）
    high = next((k for k, v in spots.items() if isinstance(v, dict) and v.get("min_lv", 1) >= 5), None)
    if high:
        hm = C.MAP_BY_ID.get(high, {})
        hsa = spots[high].get("subarea", "") if isinstance(spots[high], dict) else ""
        if hsa:
            # 传过去试钓（应提示等级不足）
            r = await cmd_as(Q, f"前往 {hsa}" if False else "垂钓", "高级水域垂钓")
            # 直接改位置验证提示
            db.update_player(PF.G, PF.Q, cur_map=high, cur_subarea=hsa)
            r = await cmd("垂钓", "高级水域垂钓（应提示等级不足）")
            print(f"  [i] 高级水域: {r[:120]}")
            db.update_player(PF.G, PF.Q, cur_map=spot_map, cur_subarea=sa)
    print("\n── 阶段十一完成 ──")

@stage(12)
async def stage12_auction():
    """阶段十二：拍卖行深度"""
    print("\n╔══ 阶段十二：拍卖行深度 ══╗")
    await ensure_player(lv=30, gold=100000)
    await register_player2(lv=30, gold=100000, cls="游侠", name="买家酱")
    # 注入拍卖事件：2 件物品（1号底价5000/一口20000，2号底价3000/一口10000）
    inject_auction([
        {"id": 1, "name": "霜之利刃", "slot": "weapon", "quality": "purple",
         "stats": {"atk": 30}, "desc": "测试品", "base": 5000, "buyout": 20000, "bids": {}},
        {"id": 2, "name": "星辉之戒", "slot": "ring", "quality": "purple",
         "stats": {"int": 15}, "desc": "测试品", "base": 3000, "buyout": 10000, "bids": {}},
    ])
    # 1. 查看拍卖
    r = await cmd("拍卖", "拍卖面板")
    print(f"  [i] 拍卖: {r[:250]}")
    # 2. P1 出价 5000
    r = await cmd("竞拍 1 5000", "P1出价5000")
    print(f"  [i] P1出价: {r[:120]}")
    gold_p1 = db.get_player(PF.G, PF.Q)["gold"]
    print(f"  [i] P1 金币: {gold_p1}（期望 95000）")
    # 3. P2 超越 8000
    r = await q2_cmd("竞拍 1 8000", "P2超越8000")
    print(f"  [i] P2超越: {r[:120]}")
    gold_p1b = db.get_player(PF.G, PF.Q)["gold"]
    print(f"  [i] P1 金币（应退还5000→100000）: {gold_p1b}")
    gold_p2 = db.get_player(PF.G, Q2)["gold"]
    print(f"  [i] P2 金币: {gold_p2}（期望 92000）")
    # 4. P1 自加价 3000（低于自己的旧价 5000 → 疑似漏洞）
    r = await cmd("竞拍 1 3000", "P1自加价3000（低于旧价5000）")
    print(f"  [i] P1自加价: {r[:120]}")
    gold_p1c = db.get_player(PF.G, PF.Q)["gold"]
    print(f"  [i] P1 金币: {gold_p1c}（若>100000 → 漏洞！倒赚）")
    if gold_p1c > gold_p1b:
        issue(12, "高", "拍卖自加价低于旧价 → 倒赚金币（经济漏洞）")
    # 5. P2 一口价 10000 买 2 号
    r = await q2_cmd("竞拍 2 10000", "P2一口价买2号")
    print(f"  [i] P2一口价: {r[:200]}")
    gold_p2b = db.get_player(PF.G, Q2)["gold"]
    print(f"  [i] P2 金币: {gold_p2b}")
    r = await q2_cmd("背包", "P2背包（应有星辉之戒）")
    print(f"  [i] P2背包: {r[:200]}")
    # 6. 查看当前拍卖（2号应已消失）
    r = await cmd("拍卖", "拍卖（2号应消失）")
    print(f"  [i] 拍卖: {r[:250]}")
    # 7. 流拍结算：把 1 号改过期 → 触发结算
    cur = db.get_world_event(include_expired=True)
    if cur and cur["etype"] == "auction":
        cur["ends_at"] = int(time.time()) - 10
        db.save_world_event("auction", cur["ends_at"], cur["data"])
        r = await cmd("拍卖", "过期拍卖结算")
        print(f"  [i] 结算: {r[:400]}")
    # 8. 结算后 P1/P2 金币核对（1号流拍或成交都应收支平衡）
    print(f"  [i] 最终 P1: {db.get_player(PF.G, PF.Q)['gold']} / P2: {db.get_player(PF.G, Q2)['gold']}")
    # 双保险：对“自加价低于旧价 → 倒赚金币”独立显式断言（不等即失败退出）
    if gold_p1c > gold_p1b:
        print("  [E] 经济漏洞：自加价低于旧价导致 P1 金币倒赚！")
        sys.exit(1)
    print("\n── 阶段十二完成 ──")

@stage(13)
async def stage13_mount_set():
    """阶段十三：坐骑·套装·洗点·转职重置"""
    print("\n╔══ 阶段十三：坐骑·套装·洗点·转职重置 ══╗")
    await ensure_player(lv=30, gold=50000)
    # 1. 坐骑：商店买老马
    r = await cmd("坐骑", "坐骑面板（应空）")
    print(f"  [i] 坐骑: {r[:150]}")
    gm_tp("oak_town", "oak_town_3")
    r = await cmd("购买 老马", "买老马")
    print(f"  [i] 购买: {r[:120]}")
    r = await cmd("骑乘 老马", "骑乘")
    print(f"  [i] 骑乘: {r[:120]}")
    r = await cmd("坐骑", "坐骑面板（应骑乘中）")
    print(f"  [i] 坐骑: {r[:150]}")
    r = await cmd("下马", "下马")
    print(f"  [i] 下马: {r[:80]}")
    # 2. 套装：GM 生成 2 件寒霜 → 装备看 2 件套
    await cmd("背包", "套装前背包")
    eq1 = gm_add_equip("weapon", 25, "blue", set_name="寒霜")
    eq2 = gm_add_equip("armor", 25, "blue", set_name="寒霜")
    await cmd("背包", "套装后背包")
    r = await cmd("套装", "套装面板")
    print(f"  [i] 套装面板: {r[:250]}")
    # 装备看加成
    r = await cmd("装备 寒霜之刃", "装备1")
    print(f"  [i] 装备1: {r[:100]}")
    r = await cmd("装备 寒霜战甲", "装备2")
    print(f"  [i] 装备2: {r[:100]}")
    r = await cmd("套装", "套装面板（2件套）")
    print(f"  [i] 套装2件: {r[:250]}")
    r = await cmd("战力", "战力（含套装加成）")
    print(f"  [i] 战力: {r[:200]}")
    # 3. 洗点
    await cmd("加点 力量 10", "加点力量")
    r = await cmd("属性", "属性面板")
    print(f"  [i] 属性: {r[:150]}")
    r = await cmd("洗点", "洗点")
    print(f"  [i] 洗点: {r[:150]}")
    r = await cmd("属性", "洗点后属性")
    print(f"  [i] 属性: {r[:150]}")
    # 4. 技能洗点（需已学技能）
    r = await cmd("技能学习 1", "学技能")
    r = await cmd("技能洗点", "技能洗点")
    print(f"  [i] 技能洗点: {r[:150]}")
    # 5. 转职重置（未转职应提示）
    r = await cmd("转职重置", "转职重置（未转职）")
    print(f"  [i] 转职重置: {r[:120]}")
    print("\n── 阶段十三完成 ──")

@stage(14)
async def stage14_party_hunt():
    """阶段十四：组队·讨伐·世界事件效果"""
    print("\n╔══ 阶段十四：组队·讨伐·世界事件 ══╗")
    await ensure_player(lv=30, gold=50000)
    await register_player2(lv=30, gold=50000, cls="游侠", name="战友酱")
    # 1. 组队
    PF.HANDLERS["组队"] = "party"
    PF.HANDLERS["队伍"] = "party"
    PF.HANDLERS["退队"] = "party_leave"
    r = await cmd("组队", "组队面板（空）")
    print(f"  [i] 组队: {r[:150]}")
    r = await cmd("组队 战友酱", "P1组队邀请")
    print(f"  [i] 邀请: {r[:150]}")
    r = await q2_cmd("组队", "P2组队面板")
    print(f"  [i] P2面板: {r[:150]}")
    r = await cmd("队伍", "队伍面板")
    print(f"  [i] 队伍: {r[:200]}")
    # 2. 讨伐 Boss：注入迷雾沼泽的巨史莱姆王（压低血量方便双人打）
    inject_event("boss", boss_name="巨史莱姆王·咕噜咕噜")
    cur = db.get_world_event()
    cur["data"]["boss"]["hp"] = 5000  # 压低血量方便双人打
    cur["data"]["boss"]["max_hp"] = 5000
    db.save_world_event("boss", cur["ends_at"], cur["data"])
    gm_tp("misty_swamp")
    db.update_player(PF.G, Q2, cur_map="misty_swamp")
    r = await cmd("讨伐", "P1讨伐")
    print(f"  [i] 讨伐: {r[:200]}")
    # P1 打几轮
    for i in range(3):
        r = await cmd("攻击", f"P1攻击{i+1}")
        print(f"  [i] P1攻击{i+1}: {r[:100]}")
    # P2 加入打
    r = await q2_cmd("讨伐", "P2讨伐")
    print(f"  [i] P2讨伐: {r[:150]}")
    for i in range(3):
        r = await q2_cmd("攻击", f"P2攻击{i+1}")
        print(f"  [i] P2攻击{i+1}: {r[:100]}")
    # 查看 Boss 血量
    cur = db.get_world_event()
    if cur and cur["etype"] == "boss":
        b = cur["data"]["boss"]
        print(f"  [i] Boss 剩余: {b.get('hp')} / {b.get('max_hp')} 贡献: {b.get('contrib')}")
    # 3. 世界事件效果：商队 8 折（回城镇看）
    inject_event("merchant")
    gm_tp("oak_town", "oak_town_3")
    r = await cmd("商店", "商店（8折）")
    print(f"  [i] 商店8折: {r[:200]}")
    r = await cmd("购买 治疗药水", "买药水（8折价）")
    print(f"  [i] 购买: {r[:150]}")
    # 4. 兽潮经验加成（探索打怪）
    inject_event("swarm")
    gm_tp("oak_plain", "oak_plain_2")
    for i in range(4):
        r = await cmd("探索", f"探索{i+1}（兽潮）")
        if "偶遇" in r or "遭遇" in r or "袭击" in r:
            break
    if db.get_battle(PF.G, PF.Q):
        exp0 = db.get_player(PF.G, PF.Q)["exp"]
        r = await cmd("攻击", "打怪（兽潮经验+30%）")
        exp1 = db.get_player(PF.G, PF.Q)["exp"]
        print(f"  [i] 战斗: {r[:120]}")
        print(f"  [i] 经验: {exp0} → {exp1}（+{exp1-exp0}）")
    else:
        print("  [i] 4 次探索没遇怪，跳过经验验证")
    # 5. 圣光节签到翻倍（清掉今日签到记录再测）
    inject_event("festival")
    db.save_signin(PF.G, PF.Q, "", 0, 0)
    r = await cmd("签到", "签到（圣光节翻倍）")
    print(f"  [i] 签到: {r[:150]}")
    print("\n── 阶段十四完成 ──")

@stage(15)
async def stage15_edge():
    """阶段十五：边界与异常测试"""
    print("\n╔══ 阶段十五：边界与异常 ══╗")
    await ensure_player(lv=30, gold=50000)
    # 1. 非法输入
    for t, lbl in [("", "空指令"), ("abc", "乱码"), ("前往 不存在的村", "未知地图"),
                   ("竞拍 999 100", "无拍卖"), ("技能 999", "未知技能")]:
        r = await cmd(t, lbl, quiet=True)
        print(f"  [i] {lbl}: {r[:100]}")
    # 2. 负数/零竞拍（有拍卖时）
    inject_auction([{"id": 1, "name": "测试剑", "slot": "weapon", "quality": "purple",
                     "stats": {}, "desc": "", "base": 5000, "buyout": 20000, "bids": {}}])
    r = await cmd("竞拍 1 -100", "负价竞拍")
    print(f"  [i] 负价竞拍: {r[:100]}")
    r = await cmd("竞拍 1 0", "零价竞拍")
    print(f"  [i] 零价竞拍: {r[:100]}")
    # 3. 背包满（塞满垃圾再领奖）
    db.clear_world_event()
    # 4. 红名限制：直接改红名状态
    try:
        db.set_event_state(f"redname_{PF.G}_{PF.Q}", json.dumps({"until": int(time.time()) + 3600}))
        r = await cmd("签到", "红名签到（应被拦）")
        print(f"  [i] 红名签到: {r[:100]}")
        r = await cmd("每日", "红名每日（应被拦）")
        print(f"  [i] 红名每日: {r[:100]}")
        r = await cmd("市场", "红名市场（应被拦？）")
        print(f"  [i] 红名市场: {r[:100]}")
        db.set_event_state(f"redname_{PF.G}_{PF.Q}", "")
    except Exception as e:
        print(f"  [i] 红名注入失败: {e}")
    # 5. 战斗中执行其他指令
    gm_tp("oak_plain", "oak_plain_2")
    r = await cmd("探索", "探索开战")
    if db.get_battle(PF.G, PF.Q):
        r = await cmd("签到", "战斗中签到（应被拦）")
        print(f"  [i] 战斗签到: {r[:100]}")
        r = await cmd("垂钓", "战斗中垂钓（应被拦）")
        print(f"  [i] 战斗垂钓: {r[:100]}")
        r = await cmd("逃跑", "逃跑")
        print(f"  [i] 逃跑: {r[:100]}")
    # 6. 重复领取验证（每日任务完成一次后）
    r = await cmd("每日", "每日（已有任务）")
    print(f"  [i] 每日重复: {r[:100]}")
    # 7. 超长参数
    r = await cmd("前往 " + "镇" * 50, "超长地图名")
    print(f"  [i] 超长: {r[:80]}")
    print("\n── 阶段十五完成 ──")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    n = int(sys.argv[1])
    if n not in STAGE_FUNCS:
        print(f"未知阶段 {n}，可用: {sorted(STAGE_FUNCS)}")
        return
    try:
        asyncio.run(STAGE_FUNCS[n]())
        save_issues()
    except Exception as e:
        import traceback
        traceback.print_exc()
        save_issues()

if __name__ == "__main__":
    main()
