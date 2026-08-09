# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - gm(GM 调试/运营指令，v90)

权限：环境变量 GWEN_GM_QQ(逗号分隔 QQ 白名单)放行；未配置时回退——私聊放行、群聊拒绝。
指令(gm_ 前缀防玩家误触)：
  gm_帮助            查看 GM 指令说明
  gm_副业位 [n]      查看/设置当前玩家副业位上限(默认 2，范围 1-8)
  gm_伤害 [倍率]     查看/设置当前玩家世界 Boss 伤害倍率(默认 1，范围 0.1-100)
"""
import os
import re

from astrbot.api.event import AstrMessageEvent, filter

from .. import db
from .base import CommandBase


class GmCmds(CommandBase):
    def _gm_auth(self, event, group_id, qq_id):
        """返回 (ok, 错误消息)。

        白名单优先：环境变量 GWEN_GM_QQ(逗号分隔 QQ)命中才放行；
        未配置白名单时：仅私聊放行(机器人私聊默认就是管理员自己)。
        """
        whitelist = os.environ.get("GWEN_GM_QQ", "").strip()
        if whitelist:
            ok = str(qq_id) in [x.strip() for x in whitelist.split(",") if x.strip()]
        else:
            ok = group_id == "private"
        if not ok:
            return False, "⛔ GM 指令仅限管理员使用～"
        return True, ""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_play(?:\s+(.+))?$")
    async def gm_play(self, event: AstrMessageEvent):
        """v92 消息转发：把 gm_play 后的内容当作游戏指令重新分发执行。
        真实链路体验入口——不碰外部脚本，直接在 AstrBot 进程内回环。"""
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        raw = self._strip_cmd(event, "gm_play").strip()
        if not raw:
            yield event.plain_result(
                "🔄 『gm_play <指令>』把指令转发给游戏引擎执行\n"
                "例如：gm_play 注册 战士 格温 / gm_play 探索 / gm_play 地图\n"
                "💡 效果等同直接发指令，方便串联体验完整流程"
            )
            return
        if raw.startswith("gm_"):
            yield event.plain_result("⛔ 不能转发 GM 指令自身(防递归)～")
            return
        async for r in self._run_shortcut(event, raw):
            yield r

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_帮助(?:[\s\S]*)$")
    async def gm_help(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        yield event.plain_result(
            "🛠️ 【GM 指令】(调试/运营用，仅管理员)\n"
            "━━━━━━━━━━━━\n"
            "『gm_副业位』 查看你的副业位上限\n"
            "『gm_副业位 <n>』 设置副业位上限(1－8，默认 2)\n"
            "『gm_伤害』 查看你的世界 Boss 伤害倍率\n"
            "『gm_伤害 <倍率>』 设置世界 Boss 伤害倍率(0.1－100，默认 1)\n"
            "『gm_play <指令>』 转发指令给游戏引擎(真实链路体验)\n"
            "━━━━━━━━━━━━\n"
            "💡 权限：环境变量 GWEN_GM_QQ 白名单；未配置时私聊可用"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_副业位(?:[\s\S]*)$")
    async def gm_prof_slots(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "gm_副业位").strip()
        cur = db.get_prof_slot_limit(qq_id)
        if not raw:
            yield event.plain_result(f"🧵 你当前的副业位上限：{cur} 条(默认 2)\n『gm_副业位 <n>』修改(1－8)")
            return
        try:
            n = int(raw)
        except ValueError:
            yield event.plain_result("格式：gm_副业位 <n>，n 为 1－8 的数字")
            return
        if not 1 <= n <= 8:
            yield event.plain_result("范围 1－8！")
            return
        db.set_event_state(f"prof_slots_{qq_id}", n)
        yield event.plain_result(f"🧵 副业位上限已设为 {n} 条(原 {cur})！『副业』查看生效")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_伤害(?:[\s\S]*)$")
    async def gm_boss_dmg(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        player = self._player(group_id, qq_id)
        if not player:
            yield event.plain_result("你还没有角色！输入『注册 战士 名字』创建吧～")
            return
        raw = self._strip_cmd(event, "gm_伤害").strip()
        cur = db.get_boss_dmg_mult(qq_id)
        if not raw:
            yield event.plain_result(f"⚔️ 你当前的世界 Boss 伤害倍率：×{cur}(默认 1)\n『gm_伤害 <倍率>』修改(0.1－100)")
            return
        try:
            m = float(raw)
        except ValueError:
            yield event.plain_result("格式：gm_伤害 <倍率>，如 『gm_伤害 10』(10 倍)")
            return
        if not 0.1 <= m <= 100:
            yield event.plain_result("范围 0.1－100！")
            return
        m = round(m, 2)
        db.set_event_state(f"boss_dmg_{qq_id}", m)
        yield event.plain_result(f"⚔️ 世界 Boss 伤害倍率已设为 ×{m}(原 ×{cur})！『讨伐』时生效")
