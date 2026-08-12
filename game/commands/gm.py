# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - gm(GM 调试/运营指令，v96)

权限：数据库 gm_whitelist(JSON) ∪ 环境变量 GWEN_GM_QQ(逗号分隔) 白名单；
gm_ 前缀身份(测试回环)恒放行；未配置任何白名单时回退——私聊放行、群聊拒绝。
指令(gm_ 前缀防玩家误触)：
  gm_帮助 / gm_停服 / gm_开服 / gm_状态 / gm_广播
  gm_玩家 / gm_查询 / gm_发金币 / gm_发物品 / gm_发经验 / gm_设等级
  gm_传送 / gm_体力 / gm_改名 / gm_加GM / gm_删GM
  gm_伤害 / gm_play（历史保留）
"""
import glob
import json
import os
import re

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.message.message_event_result import MessageChain

from .. import content as C
from .. import db
from .base import CommandBase, require_player

# 窥探投递目标：鱼鱼 QQ（1454832774，GM 白名单预置角色"鱼鱼"）
GM_OWNER_QQ = "1454832774"
# playtest 交互实录目录（playtest_spy_round{N}.md，playtest_spy_export.py 轮末生成）
_SPY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")


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


class GmCmds(CommandBase):
    def _gm_auth(self, event, group_id, qq_id):
        """返回 (ok, 错误消息)。白名单命中(库∪env)或 gm_ 测试身份放行。"""
        if self._is_gm(qq_id):
            return True, ""
        if self._gm_whitelist():
            return False, "⛔ GM 指令仅限管理员使用～"
        # 未配置任何白名单：回退旧行为——私聊放行(机器人私聊默认就是管理员自己)
        return group_id == "private", "⛔ GM 指令仅限管理员使用～"

    # ---------- 目标解析 ----------
    def _resolve_target(self, raw: str):
        """解析 GM 指令的目标玩家：纯数字 → qq_id；否则先按角色名、再按 qq_id 精确匹配。
        返回 (qq_id, 显示名) 或 (None, 错误消息)。"""
        raw = (raw or "").strip()
        if not raw:
            return None, "格式：gm_<指令> <QQ号/角色名> ..."
        if raw.isdigit():
            p = db.get_player("", raw)
            if not p:
                return None, f"❌ 没有找到 QQ {raw} 的角色～"
            return raw, p.get("name") or raw
        hit = db.find_player_by_name(raw)
        if hit:
            return hit["qq_id"], hit["name"]
        # 名字查不到 → 回退按 qq_id 精确匹配（测试号/特殊 ID 场景）
        p = db.get_player("", raw)
        if p:
            return raw, p.get("name") or raw
        return None, f"❌ 没有找到叫『{raw}』的玩家～"

    def _find_item(self, name: str):
        """按名称查找物品定义(材料/消耗品)，返回 (item_key, item_data) 或 None。"""
        for k, v in C.ITEMS.items():
            if v.get("name") == name:
                return k, dict(v)
        # 模糊包含匹配（唯一时才用）
        hits = [(k, v) for k, v in C.ITEMS.items() if name in (v.get("name") or "")]
        if len(hits) == 1:
            return hits[0][0], dict(hits[0][1])
        return None, None

    def _find_map(self, name: str):
        """按名称/别名查找地图，返回 map_id 或 None。"""
        for m in C.MAPS:
            if m.get("name") == name or name in (m.get("alias") or []):
                return m["id"]
        hits = [m for m in C.MAPS if name in (m.get("name") or "")]
        if len(hits) == 1:
            return hits[0]["id"]
        return None

    # ---------- 停服 / 开服 / 状态 ----------
    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_停服(?:[\s\S]*)$")
    async def gm_maintenance(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        raw = self._strip_cmd(event, "gm_停服").strip()
        db.set_event_state("server_maintenance", "1")
        db.set_event_state("server_maintenance_msg", raw)
        yield event.plain_result(
            "🔧 服务器已停服！\n" + (f"📢 公告：{raw}\n" if raw else "") +
            "现在只有 GM 可以操作游戏，玩家指令会被拦截～"
        )
        await self._broadcast(
            "🔧【服务器维护公告】\n服务器已进入维护状态，暂时无法游玩～\n"
            + (f"📢 {raw}\n" if raw else "")
            + "开服后会第一时间广播通知，请耐心等待～"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_开服(?:[\s\S]*)$")
    async def gm_open(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        was_down = self._server_down()
        db.delete_event_state("server_maintenance")
        db.delete_event_state("server_maintenance_msg")
        yield event.plain_result(
            "✅ 服务器已开服！所有玩家可以正常游玩啦～"
            if was_down else "ℹ️ 服务器本来就在运行中，无需开服～"
        )
        if was_down:
            await self._broadcast("✅【服务器公告】\n维护结束，服务器已开服！欢迎回来冒险～")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_状态(?:[\s\S]*)$")
    async def gm_status(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        down = self._server_down()
        msg = self._server_down_msg()
        players = db.all_players(group_id)
        gms = self._gm_whitelist()
        gm_names = []
        for g in sorted(gms):
            p = db.get_player("", g)
            gm_names.append(f"{p.get('name') or g}({g})" if p else g)
        lines = [
            "🖥️ 【服务器状态】",
            f"状态：{'🔧 维护中' if down else '✅ 运行中'}",
            f"公告：{msg}" if msg else None,
            f"玩家数：{len(players)} 人",
            f"最高等级：{players[0]['name']} Lv.{players[0]['level']}" if players else None,
            f"GM 名单：{'、'.join(gm_names) if gm_names else '(未配置，私聊可用)'}",
        ]
        yield event.plain_result("\n".join(x for x in lines if x))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_广播(?:[\s\S]*)$")
    async def gm_broadcast(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        raw = self._strip_cmd(event, "gm_广播").strip()
        if not raw:
            yield event.plain_result("格式：gm_广播 <公告内容>")
            return
        await self._broadcast(f"📢【全服公告】\n{raw}")
        yield event.plain_result(f"📢 已广播到全服 {len(db.get_player_groups())} 个群！")

    # ---------- 玩家查询 ----------
    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_玩家(?:[\s\S]*)$")
    async def gm_players(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        raw = self._strip_cmd(event, "gm_玩家").strip()
        kw = ""
        page = 1
        for tok in raw.split():
            if tok.isdigit():
                page = int(tok)
            else:
                kw = tok
        players = db.all_players(group_id)
        if kw:
            players = [p for p in players if kw in (p.get("name") or "") or kw in (p.get("qq_id") or "")]
        page_items, pages, page = self._page_items(players, page, per_page=10)
        lines = [f"👥 玩家列表({len(players)}人" + (f"，关键词『{kw}』" if kw else "") + f"，第{page}/{pages}页)："]
        for p in page_items:
            lines.append(
                f"Lv.{p.get('level', 1):>3} {p.get('name') or '?'} 金币{p.get('gold', 0)} "
                f"{(C.display('classes', p.get('class_name')) if p.get('class_name') else '')} | {p.get('qq_id')}"
            )
        yield event.plain_result("\n".join(lines))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_查询(?:[\s\S]*)$")
    async def gm_query(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        raw = self._strip_cmd(event, "gm_查询").strip()
        tgt, terr = self._resolve_target(raw)
        if not tgt:
            yield event.plain_result(terr)
            return
        p = db.get_player("", tgt)
        if not p:
            yield event.plain_result("❌ 目标玩家不存在～")
            return
        cls = C.display("classes", p.get("class_name") or "") if p.get("class_name") else ""
        sub = p.get("cur_subarea") or ""
        loc = (C.MAP_BY_ID.get(p.get("cur_map") or "", {}) or {}).get("name") or p.get("cur_map") or "?"
        if sub:
            cm = C.MAP_BY_ID.get(p.get("cur_map") or "", {})
            for sa in (cm.get("subareas") or []):
                if sa.get("id") == sub:
                    loc += f"·{sa.get('name')}"
                    break
        lines = [
            f"🔍 【{p.get('name')}】({p.get('qq_id')})",
            f"职业：{cls}｜种族：{p.get('race') or 'human'}｜性别：{p.get('gender') or '-'}",
            f"等级：Lv.{p.get('level', 1)}｜经验：{p.get('exp', 0)}",
            f"金币：{p.get('gold', 0)}｜体力：{p.get('stamina', 0)}/{100 + (p.get('level') or 1) * 2}",
            f"HP：{p.get('hp')}/{p.get('max_hp')}｜MP：{p.get('mp')}/{p.get('max_mp')}",
            f"位置：{loc or '?'}｜转职：T{p.get('class_tier', 0)}",
            f"注册于：{p.get('created_at')}｜最近活跃：{p.get('last_active')}",
        ]
        yield event.plain_result("\n".join(lines))

    # ---------- 玩家操作 ----------
    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_发金币(?:[\s\S]*)$")
    async def gm_give_gold(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        parts = self._strip_cmd(event, "gm_发金币").split()
        if len(parts) < 2:
            yield event.plain_result("格式：gm_发金币 <QQ号/角色名> <数量>")
            return
        tgt, terr = self._resolve_target(parts[0])
        if not tgt:
            yield event.plain_result(terr)
            return
        try:
            n = int(parts[1])
        except ValueError:
            yield event.plain_result("数量必须是整数！")
            return
        p = db.get_player("", tgt)
        db.update_player("", tgt, gold=(p.get("gold") or 0) + n)
        yield event.plain_result(f"💰 已给 {p.get('name')} 发放 {n} 金币(现在 {p.get('gold', 0) + n})！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_发物品(?:[\s\S]*)$")
    async def gm_give_item(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        parts = self._strip_cmd(event, "gm_发物品").split()
        if len(parts) < 2:
            yield event.plain_result("格式：gm_发物品 <QQ号/角色名> <物品名> [数量]")
            return
        tgt, terr = self._resolve_target(parts[0])
        if not tgt:
            yield event.plain_result(terr)
            return
        item_name = parts[1]
        count = 1
        if len(parts) >= 3:
            try:
                count = max(1, int(parts[2]))
            except ValueError:
                yield event.plain_result("数量必须是整数！")
                return
        key, data = self._find_item(item_name)
        if not key:
            yield event.plain_result(f"❌ 找不到物品『{item_name}』(材料/消耗品)，试试更精确的名字～")
            return
        db.add_item("", tgt, key, data, count)
        yield event.plain_result(f"📦 已给 {db.get_player('', tgt)['name']} 发放 {data['name']} ×{count}！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_发经验(?:[\s\S]*)$")
    async def gm_give_exp(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        parts = self._strip_cmd(event, "gm_发经验").split()
        if len(parts) < 2:
            yield event.plain_result("格式：gm_发经验 <QQ号/角色名> <经验值>")
            return
        tgt, terr = self._resolve_target(parts[0])
        if not tgt:
            yield event.plain_result(terr)
            return
        try:
            n = int(parts[1])
        except ValueError:
            yield event.plain_result("经验值必须是整数！")
            return
        p = db.get_player("", tgt)
        db.update_player("", tgt, exp=(p.get("exp") or 0) + n)
        # 读档惰性升级会在下次 get_player 时结算
        yield event.plain_result(f"✨ 已给 {p.get('name')} 发放 {n} 经验(下次读档自动结算升级)！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_设等级(?:[\s\S]*)$")
    async def gm_set_level(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        parts = self._strip_cmd(event, "gm_设等级").split()
        if len(parts) < 2:
            yield event.plain_result("格式：gm_设等级 <QQ号/角色名> <等级>")
            return
        tgt, terr = self._resolve_target(parts[0])
        if not tgt:
            yield event.plain_result(terr)
            return
        try:
            n = int(parts[1])
        except ValueError:
            yield event.plain_result("等级必须是整数！")
            return
        if not 1 <= n <= 99:
            yield event.plain_result("等级范围 1－99！")
            return
        p = db.get_player("", tgt)
        try:
            from ..engine import player_final_stats
            st = player_final_stats(
                p["class_name"], n, p.get("equipment", {}), p.get("class_tier", 0),
                p.get("attributes"), p.get("evolve_path", 0), self._title_bonus("", tgt),
                p.get("race"))
        except Exception:
            yield event.plain_result("⚠️ 属性重算失败，等级未修改～")
            return
        db.update_player("", tgt, level=n, exp=0, max_hp=st["max_hp"], max_mp=st["max_mp"],
                         hp=st["max_hp"], mp=st["max_mp"])
        yield event.plain_result(f"⬆️ 已把 {p.get('name')} 设为 Lv.{n}(HP/MP 已按新等级重算回满)！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_传送(?:[\s\S]*)$")
    async def gm_teleport(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        parts = self._strip_cmd(event, "gm_传送").split()
        if len(parts) < 2:
            yield event.plain_result("格式：gm_传送 <QQ号/角色名> <地图名>")
            return
        tgt, terr = self._resolve_target(parts[0])
        if not tgt:
            yield event.plain_result(terr)
            return
        map_name = " ".join(parts[1:])
        mid = self._find_map(map_name)
        if not mid:
            yield event.plain_result(f"❌ 找不到地图『{map_name}』～")
            return
        # v101.28p：传送落点设默认子区域（优先广场），否则 cur_subarea 空=卡城镇总览无法进子区域
        db.update_player("", tgt, cur_map=mid, cur_subarea=self._default_subarea(mid))
        p = db.get_player("", tgt)
        yield event.plain_result(f"🌀 已把 {p.get('name')} 传送到【{C.MAP_BY_ID[mid]['name']}】！")

    def _default_subarea(self, mid: str) -> str:
        """gm_传送落点：优先广场，其次第一个非出口子区域；无子区域 → 空。"""
        m = C.MAP_BY_ID.get(mid, {})
        subs = m.get("subareas") or []
        for sa in subs:
            if sa.get("type") != "城镇出口" and "广场" in sa.get("name", ""):
                return sa["id"]
        for sa in subs:
            if sa.get("type") != "城镇出口":
                return sa["id"]
        return ""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_体力(?:[\s\S]*)$")
    async def gm_stamina(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        parts = self._strip_cmd(event, "gm_体力").split()
        if not parts:
            yield event.plain_result("格式：gm_体力 <QQ号/角色名> [数值](不填=回满)")
            return
        tgt, terr = self._resolve_target(parts[0])
        if not tgt:
            yield event.plain_result(terr)
            return
        p = db.get_player("", tgt)
        mx = 100 + (p.get("level") or 1) * 2
        if len(parts) >= 2:
            try:
                n = int(parts[1])
            except ValueError:
                yield event.plain_result("数值必须是整数！")
                return
            n = max(0, min(n, mx))
        else:
            n = mx
        import time
        db.update_player("", tgt, stamina=n, stamina_ts=int(time.time()))
        yield event.plain_result(f"⚡ 已把 {p.get('name')} 的体力设为 {n}/{mx}！")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_改名(?:[\s\S]*)$")
    async def gm_rename(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        parts = self._strip_cmd(event, "gm_改名").split()
        if len(parts) < 2:
            yield event.plain_result("格式：gm_改名 <QQ号/角色名> <新名字>")
            return
        tgt, terr = self._resolve_target(parts[0])
        if not tgt:
            yield event.plain_result(terr)
            return
        new_name = " ".join(parts[1:]).strip()
        if not new_name or len(new_name) > 12:
            yield event.plain_result("新名字 1－12 个字符！")
            return
        p = db.get_player("", tgt)
        db.update_player("", tgt, name=new_name)
        yield event.plain_result(f"✏️ 已把 {p.get('name')} 改名为『{new_name}』！")

    # ---------- GM 白名单管理 ----------
    def _load_wl(self) -> list:
        try:
            raw = db.get_event_state("gm_whitelist")
            return [str(x) for x in json.loads(raw)] if raw else []
        except Exception:
            return []

    def _save_wl(self, wl: list):
        db.set_event_state("gm_whitelist", json.dumps(wl, ensure_ascii=False))

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_加GM(?:[\s\S]*)$")
    async def gm_add_gm(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        raw = self._strip_cmd(event, "gm_加GM").strip()
        if not raw or not raw.isdigit():
            yield event.plain_result("格式：gm_加GM <QQ号>")
            return
        wl = self._load_wl()
        if raw not in wl:
            wl.append(raw)
            self._save_wl(wl)
        yield event.plain_result(f"👑 已把 QQ {raw} 添加为 GM！({len(wl)} 人白名单)")

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_删GM(?:[\s\S]*)$")
    async def gm_del_gm(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        raw = self._strip_cmd(event, "gm_删GM").strip()
        if not raw or not raw.isdigit():
            yield event.plain_result("格式：gm_删GM <QQ号>")
            return
        wl = self._load_wl()
        if raw in wl:
            wl.remove(raw)
            self._save_wl(wl)
        yield event.plain_result(f"🗑️ 已把 QQ {raw} 移出 GM 名单！({len(wl)} 人白名单)")

    # ---------- 历史保留指令 ----------
    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_play(?:[\s\S]*)$")
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

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_窥探(?:[\s\S]*)$")
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
        files = sorted(glob.glob(os.path.join(_SPY_DIR, "playtest_spy_round*.md")))
        if not files:
            yield event.plain_result("📡 暂无 playtest 交互实录（playtest_spy_round*.md 不存在）～")
            return
        if raw.isdigit():
            want = os.path.join(_SPY_DIR, "playtest_spy_round{}.md".format(raw))
            if want not in files:
                yield event.plain_result(
                    "❌ 没有第 {} 轮实录～（现有：最新 {}）".format(raw, os.path.basename(files[-1]))
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
        chunks = _chunk_text(content, 3800)
        total = len(chunks)
        for i, chunk in enumerate(chunks, 1):
            head = "📡 【{}】({}/{})".format(os.path.basename(path), i, total) if total > 1 else "📡 【{}】".format(os.path.basename(path))
            try:
                await self.context.send_message(
                    "aiocqhttp:FriendMessage:{}".format(GM_OWNER_QQ),
                    MessageChain().message(head + "\n" + chunk),
                )
            except Exception as e:
                import logging
                logging.getLogger("astrbot").warning("[dragonfall] gm_窥探 投递失败: {}".format(e))
                yield event.plain_result("❌ 投递第 {}/{} 条失败: {}".format(i, total, e))
                return
        yield event.plain_result(
            "✅ 已把 {}（{} 字，{} 条）私聊投递到鱼鱼 QQ～".format(os.path.basename(path), len(content), total)
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_帮助(?:[\s\S]*)$")
    async def gm_help(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        yield event.plain_result(
            "🛠️ 【GM 指令】(运营/调试用，仅管理员)\n"
            "━━━━━━━━━━━━\n"
            "🏮 服务器\n"
            "『gm_停服 [公告]』 停服(玩家无法游玩，自动广播)\n"
            "『gm_开服』 开服(自动广播)\n"
            "『gm_状态』 服务器状态/玩家数/GM 名单\n"
            "『gm_广播 <内容>』 全服公告\n"
            "━━━━━━━━━━━━\n"
            "👥 玩家管理\n"
            "『gm_玩家 [关键词] [页码]』 玩家列表\n"
            "『gm_查询 <QQ/名字>』 玩家详情\n"
            "『gm_发金币 <QQ/名字> <数量>』 发金币\n"
            "『gm_发物品 <QQ/名字> <物品名> [数量]』 发物品(材料/消耗品)\n"
            "『gm_发经验 <QQ/名字> <经验>』 发经验\n"
            "『gm_设等级 <QQ/名字> <等级>』 设等级(重算属性回满血)\n"
            "『gm_传送 <QQ/名字> <地图名>』 传送\n"
            "『gm_体力 <QQ/名字> [数值]』 设体力(默认回满)\n"
            "『gm_改名 <QQ/名字> <新名字>』 改名\n"
            "━━━━━━━━━━━━\n"
            "👑 权限管理\n"
            "『gm_加GM <QQ>』『gm_删GM <QQ>』 管理 GM 白名单\n"
            "━━━━━━━━━━━━\n"
            "🧪 调试\n"
            "『gm_伤害 [倍率]』 世界 Boss 伤害倍率(0.1-100)\n"
            "『gm_play <指令>』 转发指令给引擎(真实链路体验)\n"
            "💡 目标可以是 QQ 号或角色名；白名单存数据库，重启不丢"
        )

    @filter.regex(r"^(?:\[At:\d+\]\s*)?gm_伤害(?:[\s\S]*)$")
    @require_player()
    async def gm_boss_dmg(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        ok, err = self._gm_auth(event, group_id, qq_id)
        if not ok:
            yield event.plain_result(err)
            return
        player = self._player(group_id, qq_id)
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
