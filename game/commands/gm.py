# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - gm(GM 调试/运营指令) ★ B18-L4 终态：**注册 + 一行转发**

权限：数据库 gm_whitelist(JSON) ∪ 环境变量 GWEN_GM_QQ(逗号分隔) 白名单；
gm_ 前缀身份(测试回环)恒放行；未配置任何白名单时默认拒绝一切 GM 指令（v104.1 收紧，私聊不再放行）。
指令(gm_ 前缀防玩家误触)：
  gm_帮助 / gm_停服 / gm_开服 / gm_状态 / gm_广播
  gm_玩家 / gm_查询 / gm_发金币 / gm_发物品 / gm_发经验 / gm_设等级
  gm_传送 / gm_体力 / gm_改名 / gm_加GM / gm_删GM / gm_绑身份 / gm_身份表
  gm_伤害 / gm_play / gm_窥探（后两条见「保留」）

★ B18-L4 终态（形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3）：**19 条 GM 命令**只剩
  `@declared("gm_<key>")` + `_BRIDGE.run(self, "gm_<key>", event)` 一行转发 —— 守卫 / 取参 /
  目标解析 / 物品·地图查找 / 停服开服状态 / 玩家列表与详情 / 发金币物品经验 / 设等级 / 传送 /
  体力 / 改名 / GM 白名单增删 / 伤害倍率 / 帮助串 / 身份表**全在包内** `content/cmds_gm.py`。

**GM 权限判定 = 守卫形状**：声明在包（`content/cmds_gm.py` 的 `guards=("hook:gm",)`）→
包侧 `content/guards.py::GUARDS["gm"]` → 判定实现唯一真源 `content/gm.py::gm_auth`。
宿主壳里**不再有**「取 uid → 判权限 → 分支回话」那段业务分支（旧的每条 4 行已消）。

保留在宿主（B18_DESIGN §7 明确列出的「不适合本形状」两类，逐条给理由）
------------------------------------------------------------------------
  ① `gm_play` —— 转发任意游戏指令：走宿主注册表（`_find_handler` / `_run_shortcut`，async
     generator、可多消息），§7.1「多消息」+ §7.2「依赖 AstrBot 注册表」。
  ② `gm_spy` + `_chunk_text` / `_spy_to_role_cards` —— 调试/运维管道：读 playtest 实录 md、
     拼 NapCat 合并转发节点、`await context.send_message` 多卡投递（含 `await asyncio.sleep`）、
     写 `.spy_forward_state.json` —— §7.1「多消息/富文本」+ 平台 I/O。
  两条的**权限判定仍走包内**（`_lib().gm_auth(...)` = `content/gm.py::gm_auth`，与守卫同源同文案），
  宿主只提供身份能力（`_is_gm` / `_gm_whitelist`，真源在共享的 `commands/base.py`，本批禁改）。

行为逐字节不变；证据 = `overnight/W-B18-L4.md` 的 358 项三分支快照（sha256 改前 = 改后）。
"""
import asyncio
import glob
import json
import os
import re
import time

from ._platform import AstrMessageEvent
from ._platform import Node, Nodes, Plain
from ._platform import MessageChain

from ._declared import declared

from . import _host_bridge as _BRIDGE
from .base import CommandBase
from ..log_setup import LOG

# 窥探投递目标：鱼鱼 QQ（1454832774，GM 白名单预置角色"鱼鱼"）
# v105 配置化（鱼鱼拍板）：环境变量可覆盖，换运营号不用改代码
GM_OWNER_QQ = os.environ.get("GWEN_GM_QQ", "1454832774").split(",")[0].strip()
# ⚠️ 平台前缀必须是 AstrBot 配置里的平台 id（cmd_config.json platform[].id = "onebot_v11_qq"），
# 不是适配器 type "aiocqhttp"！用 aiocqhttp 前缀 send_message 会返回 False 静默不发（2026-08-12 实测翻车）
_PLATFORM_PREFIX = "onebot_v11_qq"
# 鱼鱼所在游戏群（player_groups 表 1454832774 注册的群）
_OWNER_GROUP = os.environ.get("GWEN_GM_GROUP", "1095961596")
# playtest 交互实录目录（playtest_spy_round{N}.md，playtest_spy_export.py 轮末生成）
_SPY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")

_LIB = None


def _lib():
    """包内 `content.gm`（GM 指令唯一实现 + 权限判定唯一真源）。

    惰性 import（不在模块级 import 包内模块：包加载口要先跑 `package_apply()` 把包根插进
    `sys.path`，那时 `content` 才是可用的命名空间包）。
    """
    global _LIB
    if _LIB is None:
        import importlib

        from .. import bootstrap
        bootstrap.package_apply()                       # 幂等；失败抛（不静默留空实现）
        _LIB = importlib.import_module("content.gm")
    return _LIB


def _chunk_text(text: str, size: int = 3800):
    """按段落分片（QQ 消息安全长度），超长段落内部硬切。返回 str 列表。"""
    chunks = []
    cur = ""
    for para in text.split("\n\n"):
        if len(para) > size:
            if cur:
                chunks.append(cur)
                cur = ""
            for i in range(0, len(para), size):
                chunks.append(para[i:i + size])
            continue
        if cur and len(cur) + len(para) + 2 > size:
            chunks.append(cur)
            cur = para
        else:
            cur = (cur + "\n\n" + para) if cur else para
    if cur:
        chunks.append(cur)
    return chunks


def _spy_to_role_cards(content: str, label: str, bot_qq: str) -> list:
    """把实录 md 按角色拆成多组合并转发节点（v101.29b：每子 agent 一张完整卡）。

    返回 [(角色名, [Node...]), ...]——每张卡片 = 一个角色**本轮完整**聊天记录：
    开头 1 条角色名总览 + 该角色全部交互段（▶ 指令+回复交替，不再截断）。
    鱼鱼要求：6 个子 agent 各自一张合并转发、整轮完整，方便逐人查看战况。

    ⚠️ ARK 限制（v101.28t 实测）：fromPacketMsg 把每条消息完整文本塞进
    bytesData，总量太大 → retcode 1200。单节点 ≤300 字、每卡 ≤8K 字以内安全。
    每角色完整记录实测 1.1K-2.7K 字（round98），单卡可容纳；超 8K 兜底截断。
    """
    m = re.match(r"^#\s+(.+?)\s*$", content, flags=re.M)
    title = m.group(1).strip() if m else label
    cards = []
    for sec in re.split(r"^## ", content, flags=re.M):
        sec = sec.strip()
        if not sec or sec.startswith("# "):
            continue
        parts = sec.split("\n", 1)
        role = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else ""
        if not body:
            continue
        # 角色名清洗："🧵 格温 (main)" → "格温"
        name = re.sub(r"^[^\w\u4e00-\u9fff]+", "", role)
        name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip() or role
        nodes = [
            Node(
                uin=bot_qq,
                name=name,
                content=[Plain("📡 {} · {}（本轮完整战况，点开查看）".format(name, title))],
            )
        ]
        # 段落按 ▶ 指令切分（实录格式：▶ 『指令』\n回复体）——v101.29b 不再截断，整轮全收
        segs = re.split(r"(?=▶)", body)
        segs = [s.strip() for s in segs if s.strip()]
        # v101.29.2 #463：按 UTF-8 字节累计（中文 3 字节/字）——8K 字符≈24KB 超 NapCat ARK
        # bytesData 上限。round101 实测成功/失败边界：13.7K 字节(小白42节点)成功、
        # 16.9K 字节(小四41节点) retcode 1200 失败 → 上限 13500 字节留余量，超限尾部截断并提示
        total_bytes = 0
        for seg in segs:
            for chunk in _chunk_text(seg, 300):
                total_bytes += len(chunk.encode("utf-8"))
                if total_bytes > 13500:
                    nodes.append(Node(uin=bot_qq, name=name, content=[Plain("…(后续交互见插件目录 scripts/{})".format(label))]))
                    break
                nodes.append(Node(uin=bot_qq, name=name, content=[Plain(chunk)]))
            else:
                continue
            break
        cards.append((name, nodes))
    return cards


class GmCmds(CommandBase):
    # ---------------- 宿主能力（包内经 env.state["shell"] 调用；非命令）----------------
    def _gm_auth(self, event, group_id, qq_id):
        """返回 (ok, 错误消息)。白名单命中(库∪env)或 gm_ 测试身份放行。

        判定与文案**唯一真源** = 包内 `content/gm.py::gm_auth`（守卫 `hook:gm` 走的是同一个函数）；
        本方法只是 `gm_play` / `gm_spy` 两条平台命令的守卫调用点（它们进不了桥接层，见模块头注）。
        `_is_gm`/`_gm_whitelist` 真源在共享 `commands/base.py`（本批禁改）。
        """
        return _lib().gm_auth(self._is_gm, self._gm_whitelist, qq_id)

    def _identity_ops(self):
        """（宿主能力口，非命令）平台身份映射模块 —— openid ↔ QQ（`commands/_identity.py`）。"""
        from . import _identity
        return _identity

    # ---------- 停服 / 开服 / 状态 / 广播 ----------
    @declared("gm_maintenance")
    async def gm_maintenance(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_maintenance", event))

    @declared("gm_open")
    async def gm_open(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_open", event))

    @declared("gm_status")
    async def gm_status(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_status", event))

    @declared("gm_broadcast")
    async def gm_broadcast(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_broadcast", event))

    # ---------- 玩家查询 ----------
    @declared("gm_players")
    async def gm_players(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_players", event))

    @declared("gm_query")
    async def gm_query(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_query", event))

    # ---------- 玩家操作 ----------
    @declared("gm_give_gold")
    async def gm_give_gold(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_give_gold", event))

    @declared("gm_give_item")
    async def gm_give_item(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_give_item", event))

    @declared("gm_give_exp")
    async def gm_give_exp(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_give_exp", event))

    @declared("gm_set_level")
    async def gm_set_level(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_set_level", event))

    @declared("gm_teleport")
    async def gm_teleport(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_teleport", event))

    @declared("gm_stamina")
    async def gm_stamina(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_stamina", event))

    @declared("gm_rename")
    async def gm_rename(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_rename", event))

    # ---------- GM 白名单管理 ----------
    @declared("gm_add_gm")
    async def gm_add_gm(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_add_gm", event))

    @declared("gm_del_gm")
    async def gm_del_gm(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_del_gm", event))

    # ---------- 平台身份（判定/文案在包，平台映射能力经 _identity_ops 取）----------
    @declared("gm_bind_identity")
    async def gm_bind_identity(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_bind_identity", event))

    @declared("gm_identity_table")
    async def gm_identity_table(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_identity_table", event))

    # ---------- 帮助 / 世界 Boss 伤害倍率 ----------
    @declared("gm_help")
    async def gm_help(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_help", event))

    @declared("gm_boss_dmg")
    async def gm_boss_dmg(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "gm_boss_dmg", event))

    # ---------- 历史保留指令（平台管道，保留原形状：见模块头注 §7.1/§7.2）----------
    @declared("gm_play")
    async def gm_play(self, event: AstrMessageEvent):
        """v92 消息转发：把 gm_play 后的内容当作游戏指令重新分发执行。"""
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

    @declared("gm_spy")
    async def gm_spy(self, event: AstrMessageEvent):
        """v101.28o 窥探：把 playtest 角色交互实录(playtest_spy_round{N}.md)私聊投递到鱼鱼 QQ。

        无参数 = 最新一轮；『gm_窥探 <轮次>』= 指定轮次。内容按段落分片发送，
        每条带「第 X/N 条」标记。playtest 轮末由主循环自动触发（loopback 发 gm_窥探）。
        """
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        raw = self._strip_cmd(event, "gm_窥探").strip()
        files = sorted(
            glob.glob(os.path.join(_SPY_DIR, "playtest_spy_round*.md")),
            # v101.29.1 #459：字符串排序在轮次≥100 失效（"round100"<"round99"），必须按轮次数字排
            key=lambda p: int(re.search(r"round(\d+)\.md$", p).group(1)),
        )
        if not files:
            yield event.plain_result("📡 暂无 playtest 交互实录（playtest_spy_round*.md 不存在）～")
            return
        # v101.28q：'gm_窥探 群' = 发到鱼鱼所在群(1095961596)（私聊被 QQ 拦截时的 fallback）
        to_group = "群" in raw
        round_raw = raw.replace("群", "").strip()
        if round_raw.isdigit():
            want = os.path.join(_SPY_DIR, "playtest_spy_round{}.md".format(round_raw))
            if want not in files:
                yield event.plain_result(
                    "❌ 没有第 {} 轮实录～（现有：最新 {}）".format(round_raw, os.path.basename(files[-1]))
                )
                return
            path = want
        else:
            path = files[-1]
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except OSError as e:
            yield event.plain_result("❌ 读取 {} 失败: {}".format(os.path.basename(path), e))
            return
        if not content:
            yield event.plain_result("📡 实录文件是空的～")
            return
        _lg = LOG
        # v101.28u：每子 agent 一张合并转发卡（鱼鱼要求）——循环发送，间隔防风控
        cards = _spy_to_role_cards(content, os.path.basename(path), event.get_self_id())
        # v101.29b：只发私聊（鱼鱼 2026-08-12 要求"群聊别发了，只私聊"）——撤销 v101.29a 双发
        # v2026-09-07 QQ官方迁移：私聊目标是 QQ 号 → 需翻成 openid 才能投递
        if to_group:
            target = "{}:GroupMessage:{}".format(_PLATFORM_PREFIX, _OWNER_GROUP)
        else:
            from . import _identity
            _owner_openid = _identity.qq_to_openid(GM_OWNER_QQ)
            if _owner_openid:
                target = "{}:FriendMessage:{}".format(_PLATFORM_PREFIX, _owner_openid)
            else:
                # 未绑定 openid 时退回 QQ 号（NapCat 旧平台语义；官方 bot 下会静默失败，
                # 但至少不报错——绑定后即恢复）
                target = "{}:FriendMessage:{}".format(_PLATFORM_PREFIX, GM_OWNER_QQ)
        sent_ok, sent_fail = 0, 0
        for _name, _nodes in cards:
            try:
                _lg.info("[dragonfall] gm_窥探 角色卡 {}（{} 节点）→ {}".format(_name, len(_nodes), target))
                _ret = await self.context.send_message(
                    target,
                    MessageChain([Nodes(_nodes)]),
                )
                _lg.info("[dragonfall] gm_窥探 角色卡 {} send_message 返回: {!r}".format(_name, _ret))
                if _ret is False:
                    sent_fail += 1
                else:
                    sent_ok += 1
            except Exception as _e:
                _lg.warning("[dragonfall] gm_窥探 角色卡 {} 投递失败: {}".format(_name, _e))
                sent_fail += 1
            await asyncio.sleep(1.2)  # 连续多卡间隔，防 QQ 频率风控
        # v101.28s：有成功发送 → 同步 .spy_forward_state.json（spy_forward cron 防重）
        if sent_ok > 0:
            try:
                _m = re.search(r"playtest_spy_round(\d+)\.md$", path)
                if _m:
                    with open(os.path.join(_SPY_DIR, ".spy_forward_state.json"), "w", encoding="utf-8") as _f:
                        json.dump({"last_sent_round": int(_m.group(1)), "sent_at": int(time.time())}, _f, ensure_ascii=False)
            except Exception as _e:
                _lg.warning("[dragonfall] gm_窥探 state 同步失败: {}".format(_e))
        if sent_ok == 0:
            yield event.plain_result("❌ {} 张角色卡全部投递失败，详见 AstrBot 日志～".format(len(cards)))
            return
        yield event.plain_result(
            "✅ 已把 {} 拆成 {} 张角色卡合并转发（成功 {} / 失败 {}）{}～".format(
                os.path.basename(path), len(cards), sent_ok, sent_fail,
                "投递到游戏群 1095961596" if to_group else "私聊投递到鱼鱼 QQ",
            )
        )
