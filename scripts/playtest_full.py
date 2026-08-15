# -*- coding: utf-8 -*-
"""格温放假游玩：GM 工具集 + 完整流程脚本（2026-08-08）

用法:
  python scripts/playtest_full.py <阶段号>
  阶段 1=新手村 2=副业 3=社交生活 4=战斗成长 5=副本世界 6=主线全程

GM 指令（跳过重复劳动，不跳剧情）:
  gm_level <lv>     直接升级到指定等级（补足经验）
  gm_gold <n>       加金币
  gm_item <key> [n] 加物品
  gm_tp <map> [sa]  传送到地图/子区域
  gm_kill <怪名> <n> 直接累计击杀数（完成击杀类任务目标）
"""
import os, sys, asyncio, json, time, sqlite3, re

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))  # dragonfall/ → plugins/ → data/ → qqbot/
TEST_DB = os.path.join(PLUGIN_DIR, "test_game_data.db")
os.environ["GWEN_GAME_DB"] = TEST_DB
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from data.plugins.dragonfall.game import content as C, db
from data.plugins.dragonfall.main import Main

ISSUES = []  # 问题收集

def issue(stage, sev, desc, how="", fix=""):
    ISSUES.append({"stage": stage, "sev": sev, "desc": desc, "how": how, "fix": fix})
    print(f"  📝【{stage}】【{sev}】{desc}" + (f" | 复现: {how}" if how else ""))

class FakeEvent:
    def __init__(self, group_id, qq_id, msg=""):
        self._g, self._q = group_id, qq_id
        self.message_str = msg
    def get_group_id(self): return self._g
    def get_sender_id(self): return self._q
    def get_message_str(self): return self.message_str
    def plain_result(self, text): return text

async def run(handler, ev):
    gen = handler(ev)
    results = []
    try:
        while True:
            results.append(await gen.__anext__())
    except StopAsyncIteration:
        pass
    return results

G, Q = "g_play", "q_play"
M = Main(None)

HANDLERS = {
    "注册": "register", "找": "find_npc", "探索": "explore", "攻击": "attack",
    "角色": "profile", "属性": "attributes", "背包": "inventory", "技能": "skill",
    "地图": "map_view", "帮助": "help_cmd", "商店": "shop", "任务": "quest_view",
    "前往": "move", "交任务": "turn_in", "休息": "rest_camp", "住宿": "rest",
    "签到": "signin", "副业": "profession_view",
    "采集": "gather", "挖掘": "mining", "垂钓": "fishing", "锻造": "craft",
    "炼金": "alchemy", "烹饪": "cooking", "配方": "recipe_list",
    "强化": "enhance", "附魔": "enchant", "装备": "equip", "卸下": "unequip",
    "使用": "use", "出售": "sell", "购买": "buy", "技能学习": "skill_learn",
    "技能升级": "skill_upgrade", "技能详情": "skill_detail", "技能栏": "skill_bar_view",
    "设置技能": "skill_bar_set", "流派": "branch_skill", "转职": "evolve",
    "加点": "add_attr", "洗点": "reset_attr", "技能洗点": "reset_skill",
    "公会": "guild_info", "创建公会": "guild_create_cmd", "加入公会": "guild_join_cmd",
    "退出公会": "guild_leave_cmd", "解散公会": "guild_disband_cmd", "公会签到": "guild_sign",
    "公会任务": "guild_task", "公会排行": "guild_rank",
    "宠物": "pet_view", "喂养": "pet_feed", "放生": "pet_release", "宠物改名": "pet_rename",
    "坐骑": "mount_cmd", "骑乘": "mount_cmd", "下马": "mount_cmd",
    "地契": "deed_view", "买房": "deed_buy", "卖房": "deed_sell", "回家": "go_home",
    "出门": "go_out", "拜访": "visit_home", "仓库": "home_storage", "取出": "home_storage_take",
    "市场": "market", "上架": "market_sell", "下架": "market_unsell", "购入": "market_buy",
    "摆摊": "stall", "收摊": "stall_close", "摊位": "stall_view", "换": "stall_exchange",
    "方碑": "portal_view", "激活": "portal_activate", "传送": "portal_travel",
    "快捷绑定": "shortcut", "快捷列表": "shortcut", "快捷删除": "shortcut", "快捷清除": "shortcut",
    "快捷": "shortcut", "组队": "party", "退队": "party_leave",
    "副本": "instance_cmd", "讨伐": "hunt_boss", "事件": "world_event",
    "成就": "achievements", "称号": "titles", "声望": "reputation",
    "时间": "time_cmd", "见闻录": "wild_notes", "编年史": "chronicle",
    "每日": "daily", "副业任务": "daily_prof", "战力": "power",
    "排行": "leaderboard", "图鉴": "bestiary", "百科": "encyclopedia",
    "帮助": "help_cmd", "拍卖": "auction", "竞拍": "bid", "许愿": "wish",
    "套装": "set_view", "物品详情": "item_detail", "背包筛选": "bag_filter",
    "筛选": "bag_filter", "转职重置": "evolve_reset", "遗忘副业": "prof_forget",
    "gm_帮助": "gm_help", "gm_副业位": "gm_prof_slots", "gm_伤害": "gm_boss_dmg",
}

def clean():
    db.init_db()
    conn = sqlite3.connect(db.DB_PATH)
    try:
        tables = ["players", "player_groups", "inventory", "quests", "battle_state",
                  "achievements", "stats", "feedback", "bestiary", "professions",
                  "talk_state", "pet", "market", "event_state", "props_use",
                  "visited", "portals", "reputation", "homes", "deeds", "skill_bars"]
        for t in tables:
            try:
                conn.execute(f"DELETE FROM {t}")
            except Exception:
                pass
        conn.commit()
    finally:
        conn.close()

async def cmd(text, label="", quiet=False):
    ev = FakeEvent(G, Q, text)
    handler_name = None
    # 按关键词长度降序匹配（长命令优先，避免「宠物」吞「宠物改名」、「技能」吞「技能学习」）
    for kw, hn in sorted(HANDLERS.items(), key=lambda x: -len(x[0])):
        if text.startswith(kw):
            handler_name = hn
            break
    if not handler_name or not hasattr(M, handler_name):
        return f"[无匹配 handler] {text}"
    try:
        rs = await run(getattr(M, handler_name), ev)
    except Exception as e:
        issue("通用", "高", f"指令『{text}』抛异常: {e}", how=f"cmd({text})")
        return f"[异常] {e}"
    out = "\n".join(str(r) for r in rs if r)
    if label and not quiet:
        print(f"\n{'='*66}\n▶ {label}：{text}\n{'='*66}")
        print(out[:1500])
    return out

# ============ GM 工具 ============
def gm_level(lv):
    p = db.get_player(G, Q)
    need_exp = C.exp_to_level(lv) if hasattr(C, "exp_to_level") else lv * 100
    db.update_player(G, Q, level=lv, exp=0)
    print(f"  [GM] 等级 → {lv}")

def gm_gold(n):
    p = db.get_player(G, Q)
    db.update_player(G, Q, gold=p["gold"] + n)
    print(f"  [GM] 金币 +{n}")

def gm_item(key, n=1):
    if key in C.ITEMS:
        data = C.ITEMS[key]
    else:
        data = {"name": key, "type": "材料", "price": 1, "desc": "GM 生成", "stackable": True}
    db.add_item(G, Q, key, data, count=n)
    print(f"  [GM] 物品 +{key}×{n}")

def gm_tp(mid, sa_id=None):
    if mid not in C.MAP_BY_ID:
        print(f"  [GM] 地图不存在: {mid}")
        return
    sa_id = sa_id or ""
    db.update_player(G, Q, cur_map=mid, cur_subarea=sa_id)
    print(f"  [GM] 传送 → {mid} / {sa_id}")

def gm_kill(name, n):
    """直接累计击杀（完成击杀类任务 objective）"""
    p = db.get_player(G, Q)
    key = f"kill_{name}"
    stats = db.get_stats(G, Q) if hasattr(db, "get_stats") else {}
    try:
        db.record_kill(G, Q, name, n)
    except Exception:
        pass
    print(f"  [GM] 击杀 +{name}×{n}")

def gm_quest_complete(qid):
    """直接完成指定主线任务（跳战斗，走剧情链）"""
    db.save_quests(G, Q, {"main_quest": qid, "main_status": "completed",
                          "main_progress": 1, "daily": {}, "completed_main": [qid]})
    print(f"  [GM] 主线任务 {qid} 标记完成")

def gm_activate_all_profs():
    for k in ("gather", "mining", "fishing", "craft", "alchemy", "cooking"):
        try:
            db.activate_prof(G, Q, k)
        except Exception:
            pass
    print("  [GM] 全部副业激活")

# ============ 通用小工具 ============
def pos():
    p = db.get_player(G, Q)
    return p["cur_map"], p.get("cur_subarea", ""), p["level"]

def player_hp_full():
    p = db.get_player(G, Q)
    db.update_player(G, Q, hp=p["max_hp"], mp=p["max_mp"])

async def fight_loop(max_rounds=25, label="战斗"):
    """自动打当前战斗直到结束"""
    rnd = 0
    while db.get_battle(G, Q) and rnd < max_rounds:
        rnd += 1
        await cmd("攻击", quiet=True)
    if db.get_battle(G, Q):
        print(f"  [!] {label} {rnd} 轮未结束，尝试技能/逃跑")
        await cmd("逃跑", quiet=True)
        db.clear_battle(G, Q)
    return rnd

async def explore_fight(times=1, label="探索战斗"):
    """探索遇怪并打完"""
    for i in range(times):
        r = await cmd("探索", quiet=True)
        if db.get_battle(G, Q):
            await fight_loop(label=label)
        else:
            if "附近没有敌人" in r or "城镇" in r:
                print(f"  [i] {label}: 探索未遇怪（{r[:60]}）")

# ============ 阶段实现 ============
STAGE_FUNCS = {}

def stage(n):
    def deco(f):
        STAGE_FUNCS[n] = f
        return f
    return deco

async def ensure_player(lv=1, gold=200):
    """确保玩家存在（每阶段独立清库后重建）"""
    clean()
    db.init_db()
    await cmd("注册 战士 格温酱 人类", "注册", quiet=True)
    gm_level(lv)
    gm_gold(gold)
    db.update_player(G, Q, hp=db.get_player(G, Q)["max_hp"], mp=db.get_player(G, Q)["max_mp"])
    return db.get_player(G, Q)

@stage(1)
async def stage1_newbie():
    """阶段一：新手村 1-10 级"""
    print("\n╔══ 阶段一：新手村（注册→引导→首战→行会→10级）══╗")
    clean()
    # 1. 注册
    r = await cmd("注册 战士 格温酱 人类", "注册")
    if "冒险者" not in r and "注册" not in r:
        issue("1", "高", f"注册回复异常: {r[:120]}")
    # 2. 角色/属性/帮助
    await cmd("角色", "角色面板")
    await cmd("属性", "属性面板")
    await cmd("帮助", "指令大全")
    # 3. 找镇长（新手引导）
    await cmd("找 镇长", "找镇长")
    await cmd("任务", "任务面板")
    # 4. 商店补给
    await cmd("地图", "地图")
    await cmd("商店", "商店（广场应被拦→v87.17）")
    # 5. 去铁匠铺商店
    await cmd("前往 2", "前往铁匠铺")
    await cmd("商店", "铁匠铺商店")
    r = await cmd("购买 治疗药水", "购买药水")
    # 6. 去野外首战（主线 q1_1 杀 5 史莱姆）
    await cmd("前往 3", "回广场")
    # 橡木镇结构: 1=镇长办公处? 需确认广场序号——用地图面板看
    r = await cmd("地图", "地图查看结构")
    # 出镇: 广场→东大街→镇郊→橡木平原
    await cmd("前往 5", "前往东大街")
    await cmd("前往 1", "前往镇郊")
    await cmd("前往 2", "前往橡木平原")
    # 杀史莱姆完成 q1_1（GM 跳刷怪但走任务链）
    for i in range(5):
        await explore_fight(1, "杀史莱姆")
    await cmd("任务", "任务进度")
    await cmd("交任务", "交任务（回镇长处）")
    await cmd("前往 橡木镇", "回橡木镇")
    # 行会入门 q1_2
    await cmd("找 小艾", "找行会接待员")
    await cmd("交任务", "交任务")
    await cmd("任务", "任务追踪")
    # GM 升到 10 级 + 钱（跳过刷怪）
    gm_level(10)
    gm_gold(3000)
    # 加点
    await cmd("加点 力量 5", "加点")
    # 装备商店货
    await cmd("购买 铁剑", "买铁剑")
    await cmd("装备 铁剑", "装备武器")
    await cmd("角色", "10级面板")
    print("\n── 阶段一完成 ──")

@stage(2)
async def stage2_professions():
    """阶段二：副业全体验"""
    print("\n╔══ 阶段二：副业系统 ══╗")
    await ensure_player(lv=15, gold=5000)
    r = await cmd("副业", "副业面板")
    # 采集（野外）
    gm_tp("oak_plain", "oak_plain_2")
    r = await cmd("采集", "野外采集")
    if "开始采集" in r or "选择" in r:
        db._prof_wait_clear(G, Q) if hasattr(db, "_prof_wait_clear") else None
    # 挖掘（矿道）
    gm_tp("hill_mine", "hill_mine_2")
    r = await cmd("挖掘", "矿道挖掘")
    # 垂钓（溪边草地）
    gm_tp("oak_plain", "oak_plain_3")
    r = await cmd("垂钓", "溪边垂钓")
    # 锻造（铁匠铺）
    gm_tp("oak_town", "oak_town_3")
    await cmd("配方", "锻造配方")
    r = await cmd("锻造 铁剑", "锻造铁剑（可能缺材料）")
    # 炼金
    await cmd("炼金", "炼金列表")
    # 烹饪
    await cmd("烹饪", "烹饪列表")
    # 副业任务
    await cmd("副业任务", "每日副业")
    # 副业面板
    await cmd("副业", "副业状态")
    print("\n── 阶段二完成 ──")

@stage(3)
async def stage3_social():
    """阶段三：社交与生活"""
    print("\n╔══ 阶段三：社交与生活 ══╗")
    await ensure_player(lv=20, gold=20000)
    # 签到/许愿/时间
    await cmd("签到", "签到")
    await cmd("时间", "时间")
    await cmd("许愿", "许愿")
    # 公会
    r = await cmd("创建公会 格温之家", "创建公会")
    await cmd("公会", "公会面板")
    await cmd("公会签到", "公会签到")
    await cmd("公会任务", "公会任务")
    # 宠物（GM 给宠物蛋? 先看宠物命令）
    r = await cmd("宠物", "宠物面板")
    # 坐骑：老马
    gm_gold(2000)
    await cmd("购买 老马", "买老马（铁匠铺）")
    await cmd("坐骑", "坐骑面板")
    await cmd("骑乘 老马", "骑乘")
    await cmd("下马", "下马")
    # 房产
    r = await cmd("地契", "地契列表")
    r = await cmd("买房 1", "买房（试）")
    await cmd("回家", "回家")
    await cmd("出门", "出门")
    # 市场/摆摊
    await cmd("上架 1 100", "市场挂单（需背包有货）")
    await cmd("市场", "市场列表")
    await cmd("摆摊 铁剑 500", "摆摊")
    await cmd("摊位", "摊位查看")
    await cmd("收摊", "收摊")
    # 方碑
    await cmd("方碑", "方碑列表")
    r = await cmd("激活 橡木镇", "激活方碑")
    r = await cmd("传送 白鹿城", "传送白鹿城")
    # 快捷指令
    await cmd("快捷绑定 1 探索", "快捷绑定")
    await cmd("1", "数字触发")
    await cmd("快捷列表", "快捷列表")
    print("\n── 阶段三完成 ──")

@stage(4)
async def stage4_combat_growth():
    """阶段四：战斗与成长"""
    print("\n╔══ 阶段四：战斗成长（技能/转职/强化/附魔）══╗")
    await ensure_player(lv=35, gold=20000)
    # 技能
    await cmd("技能", "技能列表")
    await cmd("技能学习 1", "学技能")
    await cmd("技能栏", "技能栏")
    await cmd("设置技能 1 1", "设技能栏")
    await cmd("技能详情 1", "技能详情")
    # 转职（30级）
    r = await cmd("转职", "转职查看")
    # 强化/附魔
    gm_tp("oak_town", "oak_town_3")
    r = await cmd("强化 铁剑", "强化装备")
    r = await cmd("附魔 铁剑", "附魔装备")
    # 洗点
    await cmd("洗点", "洗点")
    await cmd("加点 智力 3", "重新加点")
    # 战力
    await cmd("战力", "战力")
    print("\n── 阶段四完成 ──")

@stage(5)
async def stage5_instance_world():
    """阶段五：副本与世界"""
    print("\n╔══ 阶段五：副本与世界事件 ══╗")
    await ensure_player(lv=40, gold=50000)
    await cmd("副本", "副本列表")
    r = await cmd("副本 1", "进第一个副本")
    await cmd("地图", "副本内地图")
    await explore_fight(2, "副本探索")
    # 讨伐
    r = await cmd("讨伐", "讨伐")
    # 事件
    await cmd("事件", "世界事件")
    # 成就/称号/声望
    await cmd("成就", "成就")
    await cmd("称号", "称号")
    await cmd("声望", "声望")
    # 图鉴/百科
    await cmd("图鉴", "图鉴")
    await cmd("百科 绿史莱姆", "百科")
    print("\n── 阶段五完成 ──")

@stage(6)
async def stage6_main_quests():
    """阶段六：主线 70 任务全程"""
    print("\n╔══ 阶段六：主线全程 ══╗")
    await ensure_player(lv=99, gold=999999)
    from game.data.quests import MAIN_QUESTS
    qmap = {q["id"]: q for q in MAIN_QUESTS}
    qids = [q["id"] for q in MAIN_QUESTS]
    cur_qid = None
    # 从头开始走
    db.save_quests(G, Q, {"main_quest": None, "main_status": "", "main_progress": {},
                          "daily": {}, "completed_main": [], "side": {}})
    done = []
    guard = 0
    while guard < 200:
        guard += 1
        qs = db.get_quests(G, Q)
        cur_qid = qs.get("main_quest")
        if not cur_qid:
            # 找下一个未完成主线
            for qid in qids:
                if qid not in qs.get("completed_main", []):
                    cur_qid = qid
                    break
        if not cur_qid:
            break
        q = qmap.get(cur_qid)
        if not q:
            issue("6", "高", f"主线 {cur_qid} 不在 MAIN_QUESTS")
            break
        giver = q.get("giver")
        gname = C.NPCS.get(giver, {}).get("name", giver)
        print(f"\n── [{len(done)+1}] {q['id']} {q['name']}（giver: {gname}）──")
        # 找 giver 对话（若 NPC 可达）
        if giver and giver in C.NPCS:
            r = await cmd(f"找 {gname}", "找NPC", quiet=True)
        # 处理 objective
        obj = q.get("objective", {})
        if "kill" in obj:
            gm_kill(obj["kill"], obj.get("count", 1))
        if "explore" in obj:
            gm_tp(obj["explore"])
            await cmd("地图", "探索目标图", quiet=True)
        if "talk" in obj:
            await cmd(f"找 {C.NPCS.get(obj['talk'], {}).get('name', obj['talk'])}", "对话目标", quiet=True)
        # 交任务：先置 ready（模拟目标达成），再传送到 giver 所在地交
        giver_npc = C.NPCS.get(giver) or C.HIDDEN_NPCS.get(giver, {})
        if giver_npc and giver_npc.get("map"):
            gm_tp(giver_npc["map"])
        db.save_quests(G, Q, {"main_quest": cur_qid, "main_status": "ready", "main_progress": {},
                              "daily": {}, "completed_main": done, "side": {}})
        r = await cmd("交任务", "交任务", quiet=True)
        # 检查推进
        qs2 = db.get_quests(G, Q)
        if cur_qid in qs2.get("completed_main", []):
            done.append(cur_qid)
        else:
            # 手动推进（GM 保底）
            db.save_quests(G, Q, {"main_quest": q.get("next"), "main_status": "",
                                  "main_progress": {}, "daily": {},
                                  "completed_main": done + [cur_qid], "side": {}})
            done.append(cur_qid)
            issue("6", "低", f"主线 {q['id']} 未自动完成（GM 手动推进）", how="交任务后 completed_main 无此 id")
    print(f"\n── 主线完成 {len(done)}/70 ──")
    missing = [q for q in qids if q not in done]
    if missing:
        issue("6", "中", f"主线未走完: {missing[:10]}")
    print("\n── 阶段六完成 ──")

# ============ 问题导出 ============
def save_issues():
    out = ["# 游玩问题清单（2026-08-08）\n"]
    sev_order = {"高": 0, "中": 1, "低": 2}
    ISSUES.sort(key=lambda x: (sev_order.get(x["sev"], 3), x["stage"]))
    for it in ISSUES:
        out.append(f"### 【{it['stage']}】【{it['sev']}】{it['desc']}")
        if it["how"]:
            out.append(f"- 复现: {it['how']}")
        if it["fix"]:
            out.append(f"- 建议: {it['fix']}")
        out.append("")
    path = os.path.join(PLUGIN_DIR, "playtest-issues.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"\n📄 问题清单已保存: {path}（{len(ISSUES)} 条）")
    return path

async def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "1"
    if which == "all":
        for n in sorted(STAGE_FUNCS):
            await STAGE_FUNCS[n]()
    elif which == "issues":
        save_issues()
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
