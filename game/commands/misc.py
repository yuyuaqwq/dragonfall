# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - misc（misc）

由 main.py 拆分而来，作为 Mixin 被 Main 继承。
"""
import functools
import inspect
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

    CMD_HELP = """⚔️ 《剑与魔法》指令大全（v49 精简版）
━━━━━━━━━━━━
💡 所有指令可不加空格：『移动1』=『移动 1』，『强化铁剑』=『强化 铁剑』
📄 列表指令支持翻页：『技能列表 2』『背包 2』『图鉴 2』『称号 2』
📚 分类详情：『帮助 技能』『帮助 战斗』『帮助 副业』『帮助 副本』『帮助 社交』『帮助 世界』

【角色】注册 角色 排行 转职 称号 属性 加点 洗点 战力
【冒险】地图 移动 探索 休息 住宿
【战斗】攻击 防御 逃跑（详见『帮助 战斗』）
【技能】技能 技能列表 技能详情 技能学习 技能升级（详见『帮助 技能』）
【副业】采集 挖掘 垂钓 炼金 打造 烹饪 强化 附魔（详见『帮助 副业』）
【副本】组队 队伍 退队 副本（详见『帮助 副本』）
【社交】公会 宠物 坐骑 市场 拍卖 快捷 签到 成就（详见『帮助 社交』）
【世界】任务 主线 每日 找 交任务 事件 讨伐 声望 图鉴 百科 方碑 传送 地契 买房 回家 拜访（详见『帮助 世界』）
【其他】帮助 <主题> 意见 <内容>（向格温提建议/反馈，会转达给鱼鱼～）"""

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
💡 战斗中『技能 <槽位>』或『技能 <名称>』施放；学会才能用
💡 转职（30 级）解锁分支专属技能，分支技能强于基础技能；部分技能带【团队】标记，组队副本中全队生效"""

    CMD_HELP_BATTLE = """⚔️ 【战斗】指令
━━━━━━━━━━━━
『探索』 在野外寻找敌人（城镇安全区无怪）
『攻击』 攻击当前敌人；野外『攻击 @玩家』可发起 PK
『技能 <名称/槽位>』 战斗中使用技能
『防御』 本回合减伤 50%
『逃跑』 脱离战斗（Boss/副本锁定无法逃跑）
『使用 <药水>』 战斗中用恢复药水算一回合

【PVP】野外可袭击其他玩家；等级差 >10 不能打；击杀变红名 30 分钟（红名不能进安全区），击杀红名者得荣誉；PVP 可『逃跑』脱离，5 分钟无行动自动解除，脱离/击杀后 2 分钟袭击 CD
【副本战斗】2-3 人轮流出手，Boss 有仇恨机制（伤害/治疗拉仇恨，『防御』嘲讽）；超时 2 分钟自动防御"""

    CMD_HELP_PROF = """⚔️ 【副业】指令
━━━━━━━━━━━━
『采集』 『挖掘』 『垂钓』 野外副业，越高级地图产出越好
『副业』 副业面板（等级/经验/激活位 2/2）
『遗忘副业 <名称>』 放弃一条副业（等级清零，重新选）
『副业排行』 副业等级排行
『每日副业』 今日随机 3 选 1 副业任务
『炼金』 炼金面板 『合成 <药水>』 炼制药水（高等级配方要炼金等级）
『打造』 当前可打造列表 『打造 全部』 全部配方 『打造 <装备名>』 打造
『代工 <装备名>』 铁匠代工（图纸+材料+3倍金币，不用打造等级）
『学习 <图纸名>』 消耗图纸永久解锁套装配方（学完直接会造）
『配方 <装备名>』 详情
『烹饪』 烹饪面板 『烹饪列表』 全部食谱（鱼+药材→料理）
『强化 <装备>』 强化装备（要打造副业 Lv.N 才能强化 +N）
『附魔 <装备> <符文名>』 给装备打符文（要炼金副业 Lv.2）
💡 每人只能发展 2 条副业！练满再选新的需『遗忘副业』（等级清零）
💡 副业 Lv.3/6/10 有成就和专属称号（大师称号有属性加成）
💡 采集多产、垂钓稀有、烹饪回血回蓝，是冒险的重要补给来源"""

    CMD_HELP_INSTANCE = """🏰 【组队副本】指令
━━━━━━━━━━━━
『组队 <对方名字>』 创建队伍（2 人）
『组队 <对方名字>』 队长再发一次可拉人（上限 4 人）
『队伍』 查看队伍成员 『退队』 离开（队长退队解散）
『副本』 副本列表 / 战斗中查看进度
『副本 <名字>』 开本（单人副本免组队；多人副本需队伍人数达标）
💡 轮流出手：队员A行动 → 队员B行动 → Boss行动 → 下一轮
💡 Boss 有仇恨：打伤害/奶人会拉仇恨，『防御』嘲讽拉怪并减伤
💡 超时 2 分钟自动防御；Boss 锁定无法逃跑；通关有材料/图纸/成就"""

    CMD_HELP_SOCIAL = """🤝 【社交】指令
━━━━━━━━━━━━
【公会】公会 创建公会 加入公会 退出公会 解散公会 公会签到 公会任务 公会排行
【宠物】宠物 宠物改名 喂养 放生（宠物蛋打怪掉落）
【坐骑】坐骑 骑乘 <名称> 下马（精英/Boss 掉缰绳解锁，传送省钱）
【市场】市场 上架 <物品> <价格> 下架 <编号> 购入 <编号> 摆摊 <物品> [价格] 收摊 摊位
【拍卖】拍卖 竞拍 <编号> <金币>（世界事件·神秘拍卖行）
【快捷】快捷绑定 <数字> <指令> 快捷 快捷列表 快捷删除 <数字> 快捷清除
【其他】签到 成就 称号 图鉴 百科 意见 <内容>"""

    CMD_HELP_WORLD = """🗺️ 【世界】指令
━━━━━━━━━━━━
【地图】地图 移动 <名称/序号> 探索 休息 住宿
【传送】方碑（查看激活列表） 激活（解锁传送点） 传送 <名称/序号>（付费直达）
【任务】任务 主线 每日 找 <NPC> 交任务
【事件】事件（查看当前世界事件） 讨伐（世界 Boss，需到达指定地点）
【房产】地契（在售/我的） 买房 <编号> 卖房 回家 出门 拜访 <玩家> 仓库 取出
【社交】摊位 摆摊 <物品> [价格] 换 <编号> <物品> 收摊（不带价格=换摊；家里摆摊 = 铺面，挂机在卖）
【声望】声望 图鉴 百科（查材料/怪物/地图掉落来源）
【战斗等级】角色 排行 战力
💡 移动可能撞怪：等级低于地图容易被拦路，高级玩家威慑低级怪不撞"""

    _HELP_MAP = {
        "技能": CMD_HELP_SKILL, "技能系统": CMD_HELP_SKILL,
        "战斗": CMD_HELP_BATTLE, "pvp": CMD_HELP_BATTLE,
        "副业": CMD_HELP_PROF, "生活": CMD_HELP_PROF,
        "副本": CMD_HELP_INSTANCE, "组队": CMD_HELP_INSTANCE,
        "社交": CMD_HELP_SOCIAL, "公会": CMD_HELP_SOCIAL,
        "世界": CMD_HELP_WORLD, "冒险": CMD_HELP_WORLD, "地图": CMD_HELP_WORLD,
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
        stats = db.get_stats(group_id, qq_id)
        if not stats:
            stats = {"kills": 0, "elite_kills": 0, "boss_kills": 0, "deaths": 0}
        profs = db.get_professions(group_id, qq_id)
        # 简单成就计算（动态）
        achs = [
            ("初露锋芒", stats.get("kills", 0) >= 10, f"击杀 10 只怪物（{stats.get('kills', 0)}/10）"),
            ("老兵", stats.get("kills", 0) >= 100, f"击杀 100 只怪物（{stats.get('kills', 0)}/100）"),
            ("屠魔者", stats.get("elite_kills", 0) >= 5, f"击杀 5 只精英（{stats.get('elite_kills', 0)}/5）"),
            ("猎龙人", stats.get("boss_kills", 0) >= 3, f"击杀 3 个 Boss（{stats.get('boss_kills', 0)}/3）"),
            ("传说", player["level"] >= 30, f"达到 30 级"),
        ]
        # 副业成就（每条 3 档：Lv.3/6/10）
        prof_ach = [
            ("采药人", profs["gather"]["lv"] >= 3, f"采集 Lv.3（{profs['gather']['lv']}/3）"),
            ("草药专家", profs["gather"]["lv"] >= 6, f"采集 Lv.6（{profs['gather']['lv']}/6）"),
            ("万物采集大师", profs["gather"]["lv"] >= 10, f"采集 Lv.10（{profs['gather']['lv']}/10）"),
            ("挖矿工", profs["mining"]["lv"] >= 3, f"挖掘 Lv.3（{profs['mining']['lv']}/3）"),
            ("矿脉猎手", profs["mining"]["lv"] >= 6, f"挖掘 Lv.6（{profs['mining']['lv']}/6）"),
            ("群山之王", profs["mining"]["lv"] >= 10, f"挖掘 Lv.10（{profs['mining']['lv']}/10）"),
            ("垂钓新手", profs["fishing"]["lv"] >= 3, f"垂钓 Lv.3（{profs['fishing']['lv']}/3）"),
            ("捕鱼能手", profs["fishing"]["lv"] >= 6, f"垂钓 Lv.6（{profs['fishing']['lv']}/6）"),
            ("深海渔神", profs["fishing"]["lv"] >= 10, f"垂钓 Lv.10（{profs['fishing']['lv']}/10）"),
            ("炼金学徒", profs["alchemy"]["lv"] >= 3, f"炼金 Lv.3（{profs['alchemy']['lv']}/3）"),
            ("药剂师", profs["alchemy"]["lv"] >= 6, f"炼金 Lv.6（{profs['alchemy']['lv']}/6）"),
            ("贤者之石", profs["alchemy"]["lv"] >= 10, f"炼金 Lv.10（{profs['alchemy']['lv']}/10）"),
            ("铁匠学徒", profs["craft"]["lv"] >= 3, f"打造 Lv.3（{profs['craft']['lv']}/3）"),
            ("锻造师", profs["craft"]["lv"] >= 6, f"打造 Lv.6（{profs['craft']['lv']}/6）"),
            ("神锻宗师", profs["craft"]["lv"] >= 10, f"打造 Lv.10（{profs['craft']['lv']}/10）"),
            ("厨房新手", profs["cooking"]["lv"] >= 3, f"烹饪 Lv.3（{profs['cooking']['lv']}/3）"),
            ("料理人", profs["cooking"]["lv"] >= 6, f"烹饪 Lv.6（{profs['cooking']['lv']}/6）"),
            ("食神", profs["cooking"]["lv"] >= 10, f"烹饪 Lv.10（{profs['cooking']['lv']}/10）"),
            ("鱼王猎手", db.get_fish_king(group_id, qq_id) >= 1, f"钓上鱼王（{db.get_fish_king(group_id, qq_id)}/1）"),
        ]
        achs += prof_ach
        lines = ["🏅 【成就】", "━━━━━━━━━━━━"]
        for i, (name, done, desc) in enumerate(achs, 1):
            mark = "✅" if done else "⬜"
            lines.append(f"{i:>2}. {mark} {name}：{desc}")
        lines.append(f"\n💀 阵亡次数：{stats.get('deaths', 0)}")
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
            yield event.plain_result("❌ 意见太长啦（≤200 字），精简一下再说～")
            return
        try:
            fid = db.add_feedback(qq_id, group_id, args)
            # 主动通知 Hermes（格温本体）：异步 POST，不阻塞玩家回复
            await self._notify_hermes(group_id, qq_id, args, "feedback")
            yield event.plain_result(
                f"📮 收到你的意见啦！（编号 #{fid}）\n「{args}」\n\n我会整理给鱼鱼看的，感谢你让这个世界变得更好✂️"
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
                "MLS6me_1R1PvCCnPHCcv_lzH7KONlyv-1Mz3OorGIYg",
            )
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
