# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - misc（misc）—— B9 L9 **薄壳**

命令层只做四件事：**注册 / 取玩家（含参数解析）/ 调包 / 渲染文案**。
帮助面板、新手指引、签到口径、成就面板拼装、意见箱校验与入库的实现全在内容包
`content/misc_cmds.py`（真源 = 本文件改造前正文，2026-09-13 逐字搬走）。

★ B9 L9 逐命令落点判定（详见 `overnight/B9-L9-misc.md` 的判定表）：
    help_cmd     参数解析（`[At:…]` 剥离 + 「帮助/help」前缀）留宿主 = QQ 消息形态适配；
                 主题表/11 份面板/兜底回执 → 包内 `help_reply()`
    game_tip     纯文案 → 包内常量 `GAME_TIP`
    signin       认领/运势/幸运符/金币/节日口径 → 包内 `signin_start()`；
                 **渲染留宿主**（`signin.*` 十条：`tests/test_texts_table.py:81 WIRED` 按本文件
                 AST 做「声明 ↔ 调用点」对账，搬进包 = 死文案红）；周奖励档位抽取留宿主
                 （`tests/test_v184_loot_tiers.py:697` 的源码级绑定要求
                 `QUALITY_TIERS.pick_weights(_wq, rng=random)` 字面出现在本文件里）
    achievements 面板行拼装 → 包内 `achievement_panel()`；「领取」回执 → 包内 `claim_reply()`；
                 表（**源列表序**）与成就点仍由宿主取 —— 包内 `achievements` 域丢了源列表序
                 （`derive_achievements` 无 order 注入），见报告 §缺口
    feedback_cmd 校验/频控/入库 → 包内 `feedback_precheck()` + `feedback_submit()`；
                 `_notify_hermes`（Hermes webhook 通知）留宿主 = 宿主集成，非游戏内容

包加载口 = `game.bootstrap.package_apply()`（**本进程唯一**，幂等；失败大声抛，不静默降级）。
宿主替身注入 = `db`（存储层，与 `content/talk_actions.py` 同款；包内不 import 宿主模块树）。
"""
import random
import re
import time

from ._platform import AstrMessageEvent

# 指令声明装配：正则来自 `data/command_specs.json`（声明是唯一真源）
from ._declared import declared

from .. import content as C
from .. import db
# v184：品质档位唯一真相源（TierTable）——签到周奖励的档位抽取走它
from ..core.quality_tiers import QUALITY_TIERS
from ..core import texts as T

from ..commands.base import CommandBase, require_player
from ..log_setup import LOG

# ★ B9 L9：读包（实现在包内 `content/misc_cmds.py`）。`package_apply()` = 本进程唯一包加载口
# （`saintess_engine.package.load`：包根进 sys.path → `content` 成命名空间包），幂等；
# 失败**大声抛**（读不到包 = 帮助/签到/成就全空转，比报错难查）。
from .. import bootstrap as _bootstrap          # noqa: E402

_bootstrap.package_apply()
from content import misc_cmds as _M             # noqa: E402

# 宿主替身注入：存储层（真源 `from .. import db`）
_M.bind_host(db)


class MiscCmds(CommandBase):
    """签到/成就/意见/帮助（薄壳：注册 + 取玩家 + 调包 + 渲染）"""

    # 帮助面板 11 份：真源在包内（`_M.HELP_PANELS`）；类属性照旧保留 ——
    # `tests/test_v104_commands_system.py:268-274` 直接读 `MiscCmds.CMD_HELP*` 做帮助补全断言
    CMD_HELP = _M.CMD_HELP
    CMD_HELP_CHAR = _M.CMD_HELP_CHAR
    CMD_HELP_ADV = _M.CMD_HELP_ADV
    CMD_HELP_BATTLE = _M.CMD_HELP_BATTLE
    CMD_HELP_SKILL = _M.CMD_HELP_SKILL
    CMD_HELP_PROF = _M.CMD_HELP_PROF
    CMD_HELP_ITEM = _M.CMD_HELP_ITEM
    CMD_HELP_INSTANCE = _M.CMD_HELP_INSTANCE
    CMD_HELP_SOCIAL = _M.CMD_HELP_SOCIAL
    CMD_HELP_WORLD = _M.CMD_HELP_WORLD
    CMD_HELP_OTHER = _M.CMD_HELP_OTHER

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
        # 主题 → 面板 / 兜底回执（含总览）都在包内：`content.misc_cmds.help_reply`
        yield event.plain_result(_M.help_reply(arg))

    # v134 意见#35：『游戏提示』新手引导——开局流程/体力规则/常用指令/快捷绑定/副本钥匙（纯文案）
    @declared("game_tip")
    @require_player()

    async def game_tip(self, event: AstrMessageEvent):
        yield event.plain_result(_M.GAME_TIP)

    # v105 M24 P3-2：『签到机』前缀误触 → 负向断言收窄
    @declared("signin")
    @require_player()

    async def signin(self, event: AstrMessageEvent):
        import datetime
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        today = datetime.date.today().isoformat()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        # ★ B9 L9：F1 P1-4 原子签到认领 + 每日运势 + 幸运符消解 + 金币/节日口径全在包内
        # （`content.misc_cmds.signin_start`，真源 :257-290 逐行）。异常不吞（与真源同：这几段
        # 本来就不在下面的 try 内）。
        # 幸运符的**材料键**由宿主给：包内没有 materials 域，且材料键集无法从 items 域反推
        # （598 个材料键里 7 个无 `mat_` 前缀、type 交叉 —— 见报告缺口⑤）；这一行就是真源
        # `C.resolve("materials", "幸运符")` + `key in C.MATERIALS` 的原样表达。
        _luck = C.resolve("materials", _M.LUCK_MATERIAL_NAME)
        st = _M.signin_start(group_id, qq_id, today, yesterday, C.SIGNIN_CONFIG,
                             _luck if _luck in C.MATERIALS else None)
        if st is None:
            yield event.plain_result(T.static("signin.already"))
            return
        streak, total, fortune = st["streak"], st["total"], st["fortune"]
        gold = st["gold"]
        # C8：认领为前置原子步骤已成功，此处结果构建/落库若抛错不重试认领（防重领），
        # 只回执最小成功提示，避免「已领签到但零回执」的静默失败。
        try:
            db.update_player(group_id, qq_id, gold=player["gold"] + gold)
            lines = [
                T.text("signin.title", total=total, streak=streak),
                T.text("signin.gold", gold=gold),
            ]
            # v87 / v185：运势显示（文案在文案表；这里只把「运势键」映射到「文案键」）
            _FORTUNE_TEXT = {"大吉": "signin.fortune_big", "平": "signin.fortune_flat",
                             "小凶": "signin.fortune_bad"}
            lines.append(T.static(_FORTUNE_TEXT.get(fortune, "signin.fortune_flat")))
            if fortune == "小凶":
                # vF3：小凶无预警提示——金币 -10% 早知道（概率/数值不变），可用幸运符消解或明日重roll
                lines.append(T.static("signin.bad_tip"))
            if st["festival"]:
                lines.append(T.static("signin.festival"))
            # 每 7 天额外奖励
            if streak % 7 == 0:
                import uuid
                # v184：档位抽取问唯一真相源 QUALITY_TIERS（权重行按档位序对齐，
                # 未列档位权重 0 → 只可能出 green/blue/purple，与旧 random.choices 同随机流）
                # ⚠️ 本行字面被 `tests/test_v184_loot_tiers.py:697` 源码级绑定钉住 → 留命令层
                _wq = dict(zip(("green", "blue", "purple"),
                               C.SIGNIN_CONFIG["week_quality_weights"]))
                q = QUALITY_TIERS.pick_weights(_wq, rng=random)
                equip = C.generate_equip(random.choice(["weapon", "armor", "ring"]), player["level"], q)
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip)
                lines.append(T.text("signin.week_reward", streak=streak,
                                    color=C.QUALITY[equip["quality"]]["color"],
                                    name=equip["name"]))
            yield event.plain_result("\n".join(lines))
        except Exception:
            yield event.plain_result(T.static("signin.broken"))

    @declared("achievements")
    @require_player()

    async def achievements(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)  # noqa: F841（require_player 已取；保留旧壳形状）
        raw = self._strip_cmd(event, "成就").strip()
        # v101.22 成就奖励手动领取：『成就 领取』（发放实现仍在宿主 core：`claim_achievement_rewards`）
        if raw.startswith("领取"):
            lines, err = C.claim_achievement_rewards(group_id, qq_id)
            yield event.plain_result(_M.claim_reply(lines, err))
            return
        try:
            rows = db.get_achievements(group_id, qq_id)
            unlocked = {r["ach_key"] for r in rows}
            claimed = {r["ach_key"] for r in rows if r.get("claimed")}
        except Exception:
            unlocked, claimed = set(), set()
        # ★ B9 L9：分类筛选 / 进度 / 奖励文案拼装全在包内（`achievement_panel`）；
        # 表与成就点由宿主给（源列表序 + core/achievements.py:achievement_points，见报告缺口）
        lines = _M.achievement_panel(raw, C.ACHIEVEMENTS, unlocked, claimed,
                                    C.achievement_points(qq_id))
        lines.append("")
        lines.append(self._tip("achievement"))
        yield event.plain_result("\n".join(lines))

    @declared("feedback_cmd")

    async def feedback_cmd(self, event: AstrMessageEvent):
        """玩家意见箱：『意见 <内容>』收集群友建议，供鱼鱼/格温后续改动参考"""
        group_id, qq_id = self._uid(event)
        args = self._strip_cmd(event, "意见").strip()
        _now_ts = time.time()
        # ★ B9 L9：参数校验（空 / ≤200 字）+ 30 秒频控 + 入库全在包内
        # （`feedback_precheck` / `feedback_submit`，真源 :401-425 逐行）
        reject = _M.feedback_precheck(args, qq_id, _now_ts)
        if reject:
            yield event.plain_result(reject)
            return
        try:
            res = _M.feedback_submit(group_id, qq_id, args, _now_ts)
            # 主动通知 Hermes（格温本体）：异步 POST，不阻塞玩家回复
            await self._notify_hermes(group_id, qq_id, args, "feedback")
            yield event.plain_result(res["text"])
        except Exception as e:
            LOG.warning(f"[dragonfall] 意见保存失败: {e}")
            yield event.plain_result(_M.MSG_SAVE_FAIL)

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
                    LOG.debug(
                        f"[dragonfall] 通知 Hermes: {resp.status}"
                    )
        except Exception as e:
            LOG.warning(f"[dragonfall] 通知 Hermes 失败(不影响主流程): {e}")
