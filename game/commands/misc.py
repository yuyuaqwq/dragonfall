# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - misc（misc）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import functools
import inspect
import json as _json
import random
import re
import time

from ._platform import AstrMessageEvent, MessageChain

# 指令声明装配：正则来自 `data/command_specs.json`（声明是唯一真源）
from ._declared import declared

from .. import content as C
from .. import db

from ..commands.base import CommandBase, require_player


class MiscCmds(CommandBase):
    """签到/成就/意见/帮助"""

    CMD_HELP = """⚔️《奥兰迪亚：余烬纪年》指令大全
📌 【常用指令】
━━━━━━━━━━━━
『探索』 去附近转转（遇怪/偶遇） ｜ 『打怪』 战斗入口
『地图』 看周围 ｜ 『位置』 精简导航
『状态』 看属性 ｜ 『背包』 看物品
『物品详情 <名称>』 看详情 ｜ 『技能列表』 看技能
『采集』 『挖掘』 『垂钓』 收集材料 ｜ 『商店』 买东西
『锻造』 做装备 ｜ 『副本』 组队闯关 ｜ 『帮助 <分类>』 分类指令大全
━━━━━━━━━━━━
以下是全部指令：
📚『帮助 <分类>』看该分类全部指令
👥角色系统  🤝 冒险系统
⚔️战斗系统  ✨技能系统
🔨副业系统  🎒物品系统
👫社交系统  🗺️世界系统
❓其他"""

    CMD_HELP_CHAR = """⚔️ 【角色】指令
━━━━━━━━━━━━
『注册 <名字> <性别> [种族]』 创建角色（性别必选；职业去行会就职）
『角色』 角色面板（等级/属性/装备/位置）
『属性』 属性明细（基础+加成来源）
『加点 <属性> [次数]』 分配属性点
『洗点』 金币重置属性点
『种族』 种族介绍与天赋
『职业 [名称]』 12 职业速查一览/单职业详情（v130.2g 玩家意见 #1）
『转职』 查看/执行转职（30 级起）
『转职重置』 付费清空转职分支，重新选择
『战力』 战力评估
『排行 [类别]』 等级/战力/副业排行
『注销』 删除角色（二次确认）
💡 属性加点优先级：先看角色面板缺什么，战士加力量、法师加智力"""

    CMD_HELP_ADV = """🗺️ 【冒险】指令
━━━━━━━━━━━━
『地图』 当前区域全景（设施/场景/NPC/怪物/可前往）
『位置』 当前精简导航；想赶路请发『赶路』（v128.2 起移除回复 0 捷径）
『赶路 [NPC/怪物/场景/设施]』 只看对应内容+通道，回复序号直接赶路，0 结束（v128.1）
『前往 <地名或序号>』 前往相邻区域
『寻路 <地名>』 查当前位置到目标的最短路径（『问路』同效）
『探索』 野外遇怪/偶遇/事件（城镇安全区无怪）
『休息』 野外露营（恢复部分状态）
『住宿』 城镇旅店（全额恢复）
『时间』 当前时间/季节/天气
『许愿 <经验/金币/材料>』 向流星许愿（探索偶遇流星后限时；许愿井彩蛋走『交互 许愿井』，每日一次）——v105 M23 P2-2 帮助文案与实现对齐
『见闻录』 野外 NPC 见闻收集
『足迹』 我去过的区域明细（城镇/野外子区域+首访日期） 『冒险手册』 冒险经历总览
💡 移动可能撞怪：等级低于地图容易被拦路，高级玩家威慑低级怪"""

    CMD_HELP_BATTLE = """⚔️ 【战斗】指令
━━━━━━━━━━━━
『探索』 在野外寻找敌人（城镇安全区无怪）
『攻击』 攻击当前敌人；野外『攻击 @玩家』可发起 PK
『技能 <名称/槽位>』 战斗中使用技能
『技能 <槽位> <编号>』 指定目标：a1/a2敌方、b1/b2友方（『技能1 a2』打2号）
『防御』 本刻减伤 50%
『逃跑』 脱离战斗（Boss/副本锁定无法逃跑）
『使用 <药水>』 战斗中用恢复药水算一刻
『讨伐』 挑战世界 Boss（需到达指定地点）

【PVP】野外可袭击其他玩家；等级差 >10 不能打；击杀变红名 30 分钟（红名不能进安全区），击杀红名者得荣誉；PVP 可『逃跑』脱离，5 分钟无行动自动解除，脱离/击杀后 2 分钟袭击 CD
【副本战斗】2-3 人轮流出手，Boss 有仇恨机制（伤害/治疗拉仇恨，『防御』嘲讽）；超时 2 分钟自动防御"""

    CMD_HELP_SKILL = """⚔️ 【技能系统】指令
━━━━━━━━━━━━
『技能』 技能面板（技能点/已学数量）
『技能列表』 全部技能（可翻页『技能列表 2』）
『技能详情 <名称>』 查看单个技能
『技能学习 <名称>』 消耗技能点学会技能
『技能升级 <名称>』 消耗技能点升级（满级依技能 3~5，每级增益增强）
『技能洗点』 500 金币重置技能点
『技能栏』 查看快捷栏（6 格）
『设置技能 <槽位> <技能名>』 配置快捷栏
『流派』 流派方案（一键配置）
💡 战斗中『技能 <槽位>』或『技能 <名称>』施放；学会才能用
💡 转职（30 级）解锁分支专属技能，分支技能强于基础技能；部分技能带【团队】标记，组队副本中全队生效"""

    CMD_HELP_PROF = """⚔️ 【副业】指令
━━━━━━━━━━━━
『副业』 副业面板（等级/经验/已激活条数）
『采集』 『挖掘』 『垂钓』 野外副业，越高级地图产出越好
『副业任务』 今日随机 3 选 1 副业任务
『遗忘副业 <名称>』 放弃一条副业（等级清零，重新学/重新选）
『烹饪』 烹饪面板 『烹饪列表』 全部食谱（鱼+药材→料理）
『炼金』 炼金面板 『合成 <药水>』 炼制药水（高等级配方要炼金等级）
『锻造』 当前可锻造列表 『锻造 全部』 全部配方 『锻造 <装备名>』 锻造
『代工 <装备名>』 铁匠代工（材料+3倍金币，不用图纸/锻造等级）
『学习 <图纸名>』 消耗图纸永久解锁套装配方
『配方 <装备名>』 详情
『强化 <装备>』 强化装备（要强化副业 Lv.N 才能强化 +N）
『附魔 <装备> <属性/符文名>』 附魔装备（要附魔副业 Lv.2，属性附魔或打符文）
『套装』 套装查看
💡 副业没有数量限制，可以拜师学全部生活职业，慢慢练级
💡 副业 Lv.3/6/10 有成就和专属称号（大师称号有属性加成）"""

    CMD_HELP_ITEM = """🎒 【物品】指令
━━━━━━━━━━━━
『背包 [类型] [页数]』 背包列表（类型：装备/材料/消耗品/符文/宠物蛋/坐骑/图纸/鱼）
『背包筛选 <类型>』 只看某类物品（同『背包 材料』）
『物品详情 <名称/序号>』 查看物品详情
『装备 <序号>』 穿戴 『卸下 <部位>』 脱下
『出售 <名称/序号> [数量]』 卖物品 『出售 材料/装备/全部』 一键批量卖（自动跳过任务/考验材料）
『仓库』 房产仓库 『取出 <序号>』 仓库取物
『商店』 商店列表 『购买 <物品>』 购买商品
『市场』 玩家市场 『上架 <物品> <价格>』 『下架 <编号>』 『购入 <编号>』
『摆卖 <物品/背包序号> <单价> [数量]』 摆摊卖（序号可避免同名；家里=铺面挂机）
『摆换 <物品/背包序号> [数量]』 摆摊以物换物（不带价=只换不卖）
『收摊』 『摊位』 『换 <编号> <物品>』
『拍卖』 神秘拍卖行 『竞拍 <编号> <金币>』
💡 背包翻页：『背包 2』『背包 材料』『背包 装备 2』
💡 购买容错：『购买 治疗药水（中）』全角括号自动转半角，照常买到"""

    CMD_HELP_INSTANCE = """🏰 【组队副本】指令
━━━━━━━━━━━━
『组队 <对方名字>』 创建队伍（2 人）
『组队 <对方名字>』 队长再发一次可拉人（上限 4 人）
『队伍』 查看队伍成员 『退队』 离开（队长退队解散）
『副本』 副本列表 / 战斗中查看进度
『副本 <名字>』 开本（单人副本免组队；多人副本需队伍人数达标）
『深入』 副本分层：清完当前层小怪/精英后，推进到下一层
副本内: 『副本地图』 查看当前层地图 『调查 <目标>』 探索机关/宝箱 『撤退』 保留进度离开副本
💡 部分高难/外域副本需要钥匙/信物才能进（『副本 <名字>』可看获取途径；已通关免钥匙）
💡 轮流出手：队员A行动 → 队员B行动 → Boss行动 → 下一轮
💡 Boss 有仇恨：打伤害/奶人会拉仇恨，『防御』嘲讽拉怪并减伤
💡 超时 60 秒自动防御；Boss 锁定无法逃跑；通关有材料/图纸/成就"""

    CMD_HELP_SOCIAL = """🤝 【社交】指令
━━━━━━━━━━━━
【阵营】加入阵营 <编号> 阵营任务 阵营商店 阵营排行（Lv.20 起选四大阵营；任务/商店/排行）
【公会】公会 创建公会 加入公会 退出公会 解散公会 公会签到 公会任务 公会捐献 公会排行
【宠物】宠物 宠物改名 喂养 放生（宠物蛋打怪掉落）
【坐骑】坐骑 骑乘 <名称> 下马（精英/Boss 掉缰绳解锁，传送省钱）
【快捷】快捷 快捷绑定 <数字> <指令> 快捷删除 <数字> 快捷清除（发数字即触发）
【冒险手册】冒险手册（冒险经历总览） 足迹（我去过的区域） 图鉴（怪物图鉴别名） 百科 意见 <内容>"""

    CMD_HELP_WORLD = """🗺️ 【世界】指令
━━━━━━━━━━━━
【地图】地图 位置 移动 <名称/序号> 探索 休息 住宿 探索进度（查看全大陆探索度）
【见闻】见闻录（野外 NPC 见闻收集） 编年史
【传送】方碑（查看激活列表） 激活（解锁传送点） 传送 <名称/序号>（付费直达）
【任务】任务 主线 每日 接取 对话 <NPC> 交付任务
【事件】事件（查看当前世界事件） 讨伐（世界 Boss，需到达指定地点）
【房产】地契（在售/我的） 买房 <编号> 卖房 回家 出门 拜访 <玩家> 仓库 取出
【探索】探索进度（区域探索度） 足迹（区域足迹明细） 冒险手册（总览/物品/收藏）
【声望】声望 百科（查材料/怪物/地图掉落来源）；声望商店 <势力名>（声望等级解锁专属商品）
【排行】排行 战力
💡 移动可能撞怪：等级低于地图容易被拦路，高级玩家威慑低级怪不撞"""

    CMD_HELP_OTHER = """❓ 【其他】指令
━━━━━━━━━━━━
『帮助 <分类>』 指令大全（本分类即『帮助 其他』）
『意见 <内容>』 向格温提建议（会转达给鱼鱼～）
『签到』 每日签到（金币/运势）
『成就』 成就列表 『成就 领取』 一键领取成就奖励
『称号』 称号查看/佩戴 『冒险手册』 冒险总览（区域/怪物/物品/收藏） 『足迹』 区域明细
『图鉴』 怪物图鉴（=『冒险手册 怪物』） 『百科 <关键词>』 查材料/怪物/地图掉落来源
『排行 [类别]』 等级/战力/副业排行"""

    _HELP_MAP = {
        "角色": CMD_HELP_CHAR, "人物": CMD_HELP_CHAR,
        "冒险": CMD_HELP_ADV, "世界": CMD_HELP_WORLD, "地图": CMD_HELP_ADV,
        "战斗": CMD_HELP_BATTLE, "pvp": CMD_HELP_BATTLE,
        "技能": CMD_HELP_SKILL, "技能系统": CMD_HELP_SKILL,
        "副业": CMD_HELP_PROF, "生活": CMD_HELP_PROF,
        "物品": CMD_HELP_ITEM, "背包": CMD_HELP_ITEM,
        "副本": CMD_HELP_INSTANCE, "组队": CMD_HELP_INSTANCE,
        "社交": CMD_HELP_SOCIAL, "公会": CMD_HELP_SOCIAL,
        "其他": CMD_HELP_OTHER,
    }

    # v105 M24 P3-2：『帮助中心』前缀误触 → 负向断言收窄
    @declared("help_cmd")

    async def help_cmd(self, event: AstrMessageEvent):
        msg = event.get_message_str().strip()
        msg = re.sub(r"^\[At:[^\]]*\]\s*", "", msg)
        arg = ""
        for prefix in ("帮助", "help"):
            if msg.startswith(prefix):
                arg = msg[len(prefix):].strip()
                break
        if not arg:
            yield event.plain_result(MiscCmds.CMD_HELP)
            return
        panel = MiscCmds._HELP_MAP.get(arg)
        if panel:
            yield event.plain_result(panel)
        else:
            yield event.plain_result(
                f"没有『{arg}』帮助主题～可用：角色 冒险 战斗 技能 副业 物品 社交 世界 其他\n\n" + MiscCmds.CMD_HELP
            )

    # v134 意见#35：『游戏提示』新手引导——开局流程/体力规则/常用指令/快捷绑定/副本钥匙（纯文案）
    @declared("game_tip")
    @require_player()

    async def game_tip(self, event: AstrMessageEvent):
        yield event.plain_result(
            "📖 【新手指引】刚来到奥兰迪亚的你，可以这样开始：\n"
            "━━━━━━━━━━━━\n"
            "① 开局流程：『注册 <名字> <性别>』创建角色 → 在城镇找 NPC 接任务（『任务』看主线）\n"
            "　 · 打怪练级：『探索』遇敌 → 战斗中用『技能 <名称/序号>』输出\n"
            "　 · 30 级可『转职』选择职业分支，技能/属性更专精\n"
            "② 体力规则：探索/战斗/采集等消耗体力，体力为 0 会困在野外\n"
            "　 · 恢复：城镇『休息』/『住宿』、吃食物（『背包』里的烤肉串等）\n"
            "③ 常用指令：『背包』看物品 ｜ 『技能列表』看技能 ｜ 『地图』看周围\n"
            "　 · 『商店』买补给 ｜ 『锻造』做装备 ｜ 『副本』组队闯关\n"
            "④ 快捷操作：『设置技能 <槽位> <技能名>』放技能栏，战斗中『技能 <槽位>』秒放\n"
            "　 · 列表类指令（背包/技能/任务）可发『+/-』翻页，发序号可快捷查看\n"
            "⑤ 副本钥匙：高难副本需要钥匙/信物才能进（如『王陵钥匙』）\n"
            "　 · 『副本』看每本需求 ｜ 『百科 <钥匙名>』查获取途径 ｜ 已通关可免钥匙\n"
            "━━━━━━━━━━━━\n"
            "💡 更多指令见『帮助』；卡住时试试『百科 <材料/怪物/地图/钥匙>』查询～"
        )

    # v105 M24 P3-2：『签到机』前缀误触 → 负向断言收窄
    @declared("signin")
    @require_player()

    async def signin(self, event: AstrMessageEvent):
        import datetime
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        today = datetime.date.today().isoformat()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        # F1 P1-4：原子签到认领（并发双请求只首个成功）。成功后 streak/total 已算出，
        # 替代原「读 last_date→判断→发奖励→再 save」非原子（并发可重领）。
        _claimed, streak, total = db.signin_claim(group_id, qq_id, today, yesterday)
        if not _claimed:
            yield event.plain_result("今天已经签过到啦！明天再来～")
            return
        # v87 02 章 7.6：每日运势（签到随机三档：大吉/平/小凶；幸运符可+1 档）
        # v125：阈值数据下沉 signin_config.SIGNIN_CONFIG
        fortune_roll = random.random()
        if fortune_roll < C.SIGNIN_CONFIG["fortune_bad_th"]:
            fortune = "小凶"   # 15%：当日金币 -10%
        elif fortune_roll < C.SIGNIN_CONFIG["fortune_good_th"]:
            fortune = "平"     # 40%：无效果
        else:
            fortune = "大吉"   # 45%：当日经验 +10%
        # 幸运符：使用后当日运势+1 档（小凶→平→大吉→大吉）
        if fortune == "小凶":
            luck_mat = C.resolve("materials", "幸运符")
            if luck_mat in C.MATERIALS and db.count_item(group_id, qq_id, luck_mat) > 0:
                db.remove_item(group_id, qq_id, luck_mat)
                fortune = "平"
        elif fortune == "平":
            luck_mat = C.resolve("materials", "幸运符")
            if luck_mat in C.MATERIALS and db.count_item(group_id, qq_id, luck_mat) > 0:
                db.remove_item(group_id, qq_id, luck_mat)
                fortune = "大吉"
        db.set_event_state(f"daily_fortune_{group_id}_{qq_id}", _json.dumps({"date": today, "fortune": fortune}))
        # 连续签到（streak/total 已由 signin_claim 原子算好）
        # v125：奖励数值数据下沉 signin_config.SIGNIN_CONFIG
        gold = C.SIGNIN_CONFIG["base_gold"] + streak * C.SIGNIN_CONFIG["streak_gold_step"]
        # 节日庆典：签到奖励翻倍
        cur_evt = db.get_world_event()
        if cur_evt and cur_evt["etype"] == "festival":
            gold *= C.SIGNIN_CONFIG["festival_mult"]
        # C8：认领为前置原子步骤已成功，此处结果构建/落库若抛错不重试认领（防重领），
        # 只回执最小成功提示，避免「已领签到但零回执」的静默失败。
        try:
            db.update_player(group_id, qq_id, gold=player["gold"] + gold)
            lines = [
                f"📅 【签到成功】第 {total} 次签到！连续 {streak} 天！",
                f"💰 获得 {gold} 金币",
            ]
            # v87：运势显示
            fortune_icon = {"大吉": "🌟", "平": "🍀", "小凶": "🌧️"}.get(fortune, "🍀")
            fortune_desc = {"大吉": "今日经验＋10%", "平": "今日平平无奇", "小凶": "今日金币－10%"}.get(fortune, "")
            lines.append(f"{fortune_icon} 今日运势：{fortune}({fortune_desc})")
            if fortune == "小凶":
                # vF3：小凶无预警提示——金币 -10% 早知道（概率/数值不变），可用幸运符消解或明日重roll
                lines.append("💡 今日小凶金币收益 -10%……别灰心！用『使用 幸运符』可消解，或明日签到重roll运势～")
            if cur_evt and cur_evt["etype"] == "festival":
                lines.append("🎉 节日庆典：签到奖励翻倍！")
            # 每 7 天额外奖励
            if streak % 7 == 0:
                import uuid
                q = random.choices(["green", "blue", "purple"], weights=C.SIGNIN_CONFIG["week_quality_weights"])[0]
                equip = C.generate_equip(random.choice(["weapon", "armor", "ring"]), player["level"], q)
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip)
                lines.append(f"🎁 连续 {streak} 天奖励：{C.QUALITY[equip['quality']]['color']}【{equip['name']}】！")
            yield event.plain_result("\n".join(lines))
        except Exception:
            yield event.plain_result("✅ 已签到（奖励发放异常，请联系管理）")

    @declared("achievements")
    @require_player()

    async def achievements(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "成就").strip()
        # v101.22 成就奖励手动领取：『成就 领取』
        if raw.startswith("领取"):
            lines, err = C.claim_achievement_rewards(group_id, qq_id)
            if err:
                yield event.plain_result(f"🎁 {err}")
            else:
                yield event.plain_result("\n".join(lines))
            return
        try:
            rows = db.get_achievements(group_id, qq_id)
            unlocked = {r["ach_key"] for r in rows}
            claimed = {r["ach_key"] for r in rows if r.get("claimed")}
        except Exception:
            unlocked, claimed = set(), set()
        # 分类筛选
        cats = ["战斗", "成长", "探索", "副业", "社交", "隐藏"]
        cat = raw if raw in cats else ""
        achs = [a for a in C.ACHIEVEMENTS if (not cat or a["cat"] == cat)]
        if cat:
            title = f"🏅 【成就·{cat}】"
        else:
            title = f"🏅 【成就】"
        total_all = len(C.ACHIEVEMENTS)
        got_all = len(unlocked)
        points = C.achievement_points(qq_id)
        pending_cnt = len([a for a in C.ACHIEVEMENTS if a["id"] in unlocked and a["id"] not in claimed and a.get("reward")])
        lines = [title, "━━━━━━━━━━━━"]
        if pending_cnt:
            lines.append(f"🎁 {pending_cnt} 个成就奖励待领取！『成就 领取』一键领取")
        if cat:
            lines.append(f"解锁 {sum(1 for a in achs if a['id'] in unlocked)}/{len(achs)} 个")
            for a in achs:
                mark = "✅" if a["id"] in unlocked else "⬜"
                rw = a.get("reward") or {}
                # v105 M18 P3：奖励 key 显示中文（经验/金币），对齐解锁提示 _reward_txt
                # v140 波2：items 物品奖励也显示（《物品名》×N）
                _RW_CN = {"exp": "经验", "gold": "金币"}
                rw_parts = []
                for k, v in rw.items():
                    if k == "items":
                        for _ik, _ic in (v or {}).items():
                            _nm = _ik
                            try:
                                _nm = (C.ITEMS.get(_ik) or C.MATERIALS.get(_ik) or {}).get("name", _ik)
                            except Exception:
                                pass
                            rw_parts.append(f"{_nm}×{_ic}")
                    else:
                        rw_parts.append(f"{_RW_CN.get(k, k)}+{v}")
                rw_txt = f"（{'、'.join(rw_parts)}）" if rw_parts else ""
                if a["id"] in unlocked and a["id"] not in claimed and rw:
                    mark = "🎁"
                lines.append(f"{mark} {a['name']}：{a['desc']}{rw_txt}")
        else:
            lines.append(f"总进度：{got_all}/{total_all}　🏆 成就点：{points}")
            for c in cats:
                sub = [a for a in C.ACHIEVEMENTS if a["cat"] == c]
                got_c = sum(1 for a in sub if a["id"] in unlocked)
                lines.append(f"{'✅' if got_c == len(sub) else '⬜'} {c}：{got_c}/{len(sub)}(『成就 {c}』查看明细)")
        lines.append("")
        lines.append(self._tip("achievement"))
        yield event.plain_result("\n".join(lines))

    @declared("feedback_cmd")

    async def feedback_cmd(self, event: AstrMessageEvent):
        """玩家意见箱：『意见 <内容>』收集群友建议，供鱼鱼/格温后续改动参考"""
        group_id, qq_id = self._uid(event)
        args = self._strip_cmd(event, "意见").strip()
        if not args:
            yield event.plain_result("📮 想给格温提建议？发『意见 <你的想法>』就行～\n例：『意见 希望能出个坐骑系统』")
            return
        if len(args) > 200:
            yield event.plain_result("❌ 意见太长啦(≤200 字)，精简一下再说～")
            return
        # q11 低风险项：同 qq 30 秒内限 1 条（意见箱防刷屏），沿用 event_state 存末次提交时间戳
        _cd_key = f"fb_cd_{qq_id}"
        try:
            _last_ts = float(db.get_event_state(_cd_key) or 0)
        except (TypeError, ValueError):
            _last_ts = 0.0
        _now_ts = time.time()
        if _now_ts - _last_ts < 30:
            yield event.plain_result("意见发送太频繁，请稍后再试～")
            return
        try:
            fid = db.add_feedback(qq_id, group_id, args)
            # 持续成功的频控：仅成功后更新时间戳，避免失败的尝试锁住玩家再次提交
            db.set_event_state(_cd_key, str(_now_ts))
            # 主动通知 Hermes（格温本体）：异步 POST，不阻塞玩家回复
            await self._notify_hermes(group_id, qq_id, args, "feedback")
            yield event.plain_result(
                f"📮 收到你的意见啦！(编号 #{fid})\n「{args}」\n\n我会整理给鱼鱼看的，感谢你让这个世界变得更好✂️"
            )
        except Exception as e:
            import logging
            logging.getLogger("astrbot").warning(f"[dragonfall] 意见保存失败: {e}")
            yield event.plain_result("❌ 意见保存失败，稍后再试试～")

    async def _notify_hermes(self, group_id, qq_id, content, msg_type):
        """把玩家消息主动推送给 Hermes（webhook 触发格温本体处理）
        v36: webhook 桥已停用（改为 cron 汇总报告给鱼鱼），默认不通知。
        如后续需要可设环境变量 HERMES_WEBHOOK_URL 重新启用。"""
        import os
        if not os.environ.get("HERMES_WEBHOOK_URL"):
            return
        try:
            import aiohttp
            import hashlib
            import hmac
            import json as _json
            webhook_url = os.environ.get(
                "HERMES_WEBHOOK_URL",
                "http://localhost:8644/webhooks/dragonfall-bridge",
            )
            # v105 M24 P2-9：secret 不再内置明文默认值（曾泄漏在源码），强制由环境变量提供；
            # 未配置时跳过签名（webhook 桥默认停用，需 HERMES_WEBHOOK_URL 才启用）
            secret = os.environ.get("HERMES_WEBHOOK_SECRET")
            payload = _json.dumps(
                {
                    "group_id": str(group_id),
                    "qq_id": str(qq_id),
                    "content": content,
                    "msg_type": msg_type,
                },
                ensure_ascii=False,
            ).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if secret:
                sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
                headers["X-Webhook-Signature"] = sig
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, data=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    import logging
                    logging.getLogger("astrbot").debug(
                        f"[dragonfall] 通知 Hermes: {resp.status}"
                    )
        except Exception as e:
            import logging
            logging.getLogger("astrbot").warning(f"[dragonfall] 通知 Hermes 失败(不影响主流程): {e}")
