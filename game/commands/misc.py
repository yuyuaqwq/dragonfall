# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - misc（misc）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import functools
import inspect
import json as _json
import random
import re
import time

from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.message.message_event_result import MessageChain

from .. import content as C
from .. import db
from .. import engine as E
from .. import battle as BT
from ..commands.base import CommandBase


class MiscCmds(CommandBase):
    """签到/成就/意见/帮助"""

    CMD_HELP = """⚔️ 《奥兰迪亚：余烬纪年》指令大全
━━━━━━━━━━━━
💡 指令可不加空格：『前往1』=『前往 1』，『强化铁剑』=『强化 铁剑』
💡 列表指令支持翻页：『技能列表 2』『背包 2』『图鉴 2』
📚 『帮助 <分类>』看该分类全部指令：角色 冒险 战斗 技能 副业 物品 副本 社交 世界

🧑🤝🧑 角色系统        🌍 冒险系统
注册 角色 属性 加点    地图 移动 探索 休息
洗点 转职 战力 排行    住宿 时间 许愿 见闻录

⚔️ 战斗系统          ✨ 技能系统
攻击 技能 防御 逃跑    技能 技能列表 技能详情
使用 讨伐            技能学习 技能升级 流派

🔨 副业系统          🎒 物品系统
副业 采集 挖掘 垂钓    背包 商店 购买 市场
烹饪 炼金 锻造 强化    摆摊 拍卖 仓库
附魔

👥 社交系统          📜 世界系统
组队 副本 公会 宠物    任务 每日 方碑 传送
坐骑 快捷            地契 成就 图鉴 称号

❓ 其他
帮助 <分类> 意见 <内容>（向格温提建议，会转达给鱼鱼～）"""

    CMD_HELP_CHAR = """⚔️ 【角色】指令
━━━━━━━━━━━━
『注册 <职业> <名字>』 创建角色（可选 -r 种族）
『角色』 角色面板（等级/属性/装备/位置）
『属性』 属性明细（基础+加成来源）
『加点 <属性> [次数]』 分配属性点
『洗点』 金币重置属性点
『种族』 种族介绍与天赋
『转职』 查看/执行转职（30 级起）
『战力』 战力评估
『排行 [类别]』 等级/战力/副业排行
『注销』 删除角色（二次确认）
💡 属性加点优先级：先看角色面板缺什么，战士加力量、法师加智力"""

    CMD_HELP_ADV = """🗺️ 【冒险】指令
━━━━━━━━━━━━
『地图』 当前区域/周边可去/互动项
『前往 <地名或序号>』 前往相邻区域
『探索』 野外遇怪/偶遇/事件（城镇安全区无怪）
『休息』 野外露营（恢复部分状态）
『住宿』 城镇旅店（全额恢复）
『时间』 当前时间/季节/天气
『许愿』 许愿井（每日一次彩蛋）
『见闻录』 野外 NPC 见闻收集
💡 移动可能撞怪：等级低于地图容易被拦路，高级玩家威慑低级怪"""

    CMD_HELP_BATTLE = """⚔️ 【战斗】指令
━━━━━━━━━━━━
『探索』 在野外寻找敌人（城镇安全区无怪）
『攻击』 攻击当前敌人；野外『攻击 @玩家』可发起 PK
『技能 <名称/槽位>』 战斗中使用技能
『防御』 本回合减伤 50%
『逃跑』 脱离战斗（Boss/副本锁定无法逃跑）
『使用 <药水>』 战斗中用恢复药水算一回合
『讨伐』 挑战世界 Boss（需到达指定地点）

【PVP】野外可袭击其他玩家；等级差 >10 不能打；击杀变红名 30 分钟（红名不能进安全区），击杀红名者得荣誉；PVP 可『逃跑』脱离，5 分钟无行动自动解除，脱离/击杀后 2 分钟袭击 CD
【副本战斗】2-3 人轮流出手，Boss 有仇恨机制（伤害/治疗拉仇恨，『防御』嘲讽）；超时 2 分钟自动防御"""

    CMD_HELP_SKILL = """⚔️ 【技能系统】指令
━━━━━━━━━━━━
『技能』 技能面板（技能点/已学数量）
『技能列表』 全部技能（可翻页『技能列表 2』）
『技能详情 <名称>』 查看单个技能
『技能学习 <名称>』 消耗技能点学会技能
『技能升级 <名称>』 消耗技能点升级（满级 Lv.5，每级增益增强）
『技能洗点』 500 金币重置技能点
『技能栏』 查看快捷栏（6 格）
『设置技能 <槽位> <技能名>』 配置快捷栏
『流派』 流派方案（一键配置）
💡 战斗中『技能 <槽位>』或『技能 <名称>』施放；学会才能用
💡 转职（30 级）解锁分支专属技能，分支技能强于基础技能；部分技能带【团队】标记，组队副本中全队生效"""

    CMD_HELP_PROF = """⚔️ 【副业】指令
━━━━━━━━━━━━
『副业』 副业面板（等级/经验/激活位 2/2）
『采集』 『挖掘』 『垂钓』 野外副业，越高级地图产出越好
『副业任务』 今日随机 3 选 1 副业任务
『遗忘副业 <名称>』 放弃一条副业（等级清零，重新选）
『烹饪』 烹饪面板 『烹饪列表』 全部食谱（鱼+药材→料理）
『炼金』 炼金面板 『合成 <药水>』 炼制药水（高等级配方要炼金等级）
『锻造』 当前可锻造列表 『锻造 全部』 全部配方 『锻造 <装备名>』 锻造
『代工 <装备名>』 铁匠代工（图纸+材料+3倍金币，不用锻造等级）
『学习 <图纸名>』 消耗图纸永久解锁套装配方
『配方 <装备名>』 详情
『强化 <装备>』 强化装备（要锻造副业 Lv.N 才能强化 +N）
『附魔 <装备> <符文名>』 给装备打符文（要炼金副业 Lv.2）
『套装』 套装查看
💡 每人只能发展 2 条副业！练满再选新的需『遗忘副业』（等级清零）
💡 副业 Lv.3/6/10 有成就和专属称号（大师称号有属性加成）"""

    CMD_HELP_ITEM = """🎒 【物品】指令
━━━━━━━━━━━━
『背包 [类型] [页数]』 背包列表（类型：装备/材料/消耗品/符文/宠物蛋/坐骑/图纸/鱼）
『物品详情 <名称/序号>』 查看物品
『装备 <序号>』 穿戴 『卸下 <部位>』 脱下
『出售 <序号>』 卖物品给商店
『仓库』 房产仓库 『取出 <序号>』 仓库取物
『商店』 商店列表 『购买 <物品>』 购买商品
『市场』 玩家市场 『上架 <物品> <价格>』 『下架 <编号>』 『购入 <编号>』
『摆摊 <物品> [价格]』 摆摊（不带价格=换摊；家里摆摊=铺面挂机）
『收摊』 『摊位』 『换 <编号> <物品>』
『拍卖』 神秘拍卖行 『竞拍 <编号> <金币>』
💡 背包翻页：『背包 2』『背包 材料』『背包 装备 2』"""

    CMD_HELP_INSTANCE = """🏰 【组队副本】指令
━━━━━━━━━━━━
『组队 <对方名字>』 创建队伍（2 人）
『组队 <对方名字>』 队长再发一次可拉人（上限 4 人）
『队伍』 查看队伍成员 『退队』 离开（队长退队解散）
『副本』 副本列表 / 战斗中查看进度
『副本 <名字>』 开本（单人副本免组队；多人副本需队伍人数达标）
『深入』 副本分层：清完当前层小怪/精英后，推进到下一层
💡 部分高难/外域副本需要钥匙/信物才能进（『副本 <名字>』可看获取途径；已通关免钥匙）
💡 轮流出手：队员A行动 → 队员B行动 → Boss行动 → 下一轮
💡 Boss 有仇恨：打伤害/奶人会拉仇恨，『防御』嘲讽拉怪并减伤
💡 超时 2 分钟自动防御；Boss 锁定无法逃跑；通关有材料/图纸/成就"""

    CMD_HELP_SOCIAL = """🤝 【社交】指令
━━━━━━━━━━━━
【公会】公会 创建公会 加入公会 退出公会 解散公会 公会签到 公会任务 公会排行
【宠物】宠物 宠物改名 喂养 放生（宠物蛋打怪掉落）
【坐骑】坐骑 骑乘 <名称> 下马（精英/Boss 掉缰绳解锁，传送省钱）
【快捷】快捷 快捷绑定 <数字> <指令> 快捷删除 <数字> 快捷清除（发数字即触发）
【其他】签到 成就 称号 图鉴 百科 意见 <内容>"""

    CMD_HELP_WORLD = """🗺️ 【世界】指令
━━━━━━━━━━━━
【地图】地图 移动 <名称/序号> 探索 休息 住宿
【传送】方碑（查看激活列表） 激活（解锁传送点） 传送 <名称/序号>（付费直达）
【任务】任务 主线 每日 找 <NPC> 交任务
【事件】事件（查看当前世界事件） 讨伐（世界 Boss，需到达指定地点）
【房产】地契（在售/我的） 买房 <编号> 卖房 回家 出门 拜访 <玩家> 仓库 取出
【声望】声望 图鉴 百科（查材料/怪物/地图掉落来源）
【排行】排行 战力
💡 移动可能撞怪：等级低于地图容易被拦路，高级玩家威慑低级怪不撞"""

    _HELP_MAP = {
        "角色": CMD_HELP_CHAR, "人物": CMD_HELP_CHAR,
        "冒险": CMD_HELP_ADV, "世界": CMD_HELP_WORLD, "地图": CMD_HELP_ADV,
        "战斗": CMD_HELP_BATTLE, "pvp": CMD_HELP_BATTLE,
        "技能": CMD_HELP_SKILL, "技能系统": CMD_HELP_SKILL,
        "副业": CMD_HELP_PROF, "生活": CMD_HELP_PROF,
        "物品": CMD_HELP_ITEM, "背包": CMD_HELP_ITEM,
        "副本": CMD_HELP_INSTANCE, "组队": CMD_HELP_INSTANCE,
        "社交": CMD_HELP_SOCIAL, "公会": CMD_HELP_SOCIAL,
    }

    @filter.regex(r"^(?:\[At:\d+\]\s*)?(?:帮助|help)(?:\s*|$)")

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
                f"没有『{arg}』帮助主题～可用：技能 战斗 副业 副本 社交 世界\n\n" + MiscCmds.CMD_HELP
            )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?签到(?:\s*|$)")

    async def signin(self, event: AstrMessageEvent):
        import datetime
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        today = datetime.date.today().isoformat()
        si = db.get_signin(group_id, qq_id)
        if si.get("last_date") == today:
            yield event.plain_result("今天已经签过到啦！明天再来～")
            return
        # v87 02 章 7.6：每日运势（签到随机三档：大吉/平/小凶；幸运符可+1 档）
        fortune_roll = random.random()
        if fortune_roll < 0.15:
            fortune = "小凶"   # 15%：当日金币 -10%
        elif fortune_roll < 0.55:
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
        # 连续签到
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        streak = si.get("streak", 0) + 1 if si.get("last_date") == yesterday else 1
        total = si.get("total", 0) + 1
        db.save_signin(group_id, qq_id, today, streak, total)
        # 奖励：基础金币 + 连续加成 + 幸运宝箱
        gold = 20 + streak * 5
        # 节日庆典：签到奖励翻倍
        cur_evt = db.get_world_event()
        if cur_evt and cur_evt["etype"] == "festival":
            gold *= 2
        db.update_player(group_id, qq_id, gold=player["gold"] + gold)
        lines = [
            f"📅 【签到成功】第 {total} 次签到！连续 {streak} 天！",
            f"💰 获得 {gold} 金币",
        ]
        # v87：运势显示
        fortune_icon = {"大吉": "🌟", "平": "🍀", "小凶": "🌧️"}.get(fortune, "🍀")
        fortune_desc = {"大吉": "今日经验＋10%", "平": "今日平平无奇", "小凶": "今日金币－10%"}.get(fortune, "")
        lines.append(f"{fortune_icon} 今日运势：{fortune}({fortune_desc})")
        if cur_evt and cur_evt["etype"] == "festival":
            lines.append("🎉 节日庆典：签到奖励翻倍！")
        # 每 7 天额外奖励
        if streak % 7 == 0:
            import uuid
            q = random.choices(["green", "blue", "purple"], weights=[55, 35, 10])[0]
            equip = C.generate_equip(random.choice(["weapon", "armor", "ring"]), player["level"], q)
            db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip)
            lines.append(f"🎁 连续 {streak} 天奖励：{C.QUALITY[equip['quality']]['color']}【{equip['name']}】！")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?成就(?:\s*|$)")

    async def achievements(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "成就").strip()
        try:
            rows = db.get_achievements(qq_id)
            unlocked = {r[0] for r in rows}
        except Exception:
            unlocked = set()
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
        lines = [title, "━━━━━━━━━━━━"]
        if cat:
            lines.append(f"解锁 {sum(1 for a in achs if a['id'] in unlocked)}/{len(achs)} 个")
            for a in achs:
                mark = "✅" if a["id"] in unlocked else "⬜"
                lines.append(f"{mark} {a['name']}：{a['desc']}")
        else:
            lines.append(f"总进度：{got_all}/{total_all}　🏆 成就点：{points}")
            for c in cats:
                sub = [a for a in C.ACHIEVEMENTS if a["cat"] == c]
                got_c = sum(1 for a in sub if a["id"] in unlocked)
                lines.append(f"{'✅' if got_c == len(sub) else '⬜'} {c}：{got_c}/{len(sub)}(『成就 {c}』查看明细)")
        lines.append("")
        lines.append("💡 达成条件自动解锁，称号自动获得；『称号』可佩戴展示")
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?意见(?:[\s\S]*)$")

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
        try:
            fid = db.add_feedback(qq_id, group_id, args)
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
            secret = os.environ.get(
                "HERMES_WEBHOOK_SECRET",
                "MLS6me_1R1PvCCnPHCcv_lzH7KONlyv－1Mz3OorGIYg",
            )
            payload = _json.dumps(
                {
                    "group_id": str(group_id),
                    "qq_id": str(qq_id),
                    "content": content,
                    "msg_type": msg_type,
                },
                ensure_ascii=False,
            ).encode("utf－8")
            headers = {"Content-Type": "application/json"}
            if secret:
                sig = hmac.new(secret.encode("utf－8"), payload, hashlib.sha256).hexdigest()
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
