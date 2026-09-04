# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - collection（v140 波2 成就/称号/收藏资源化 3.9：冒险者收藏册）

由 main.py 拆分而来，作为 Mixin 被 Main 继承（命令：『收藏册』『收藏册 <册名>』）。

数据源：game/data/collection_book.py COLLECTION_BOOKS（5 套，42 条目）。
收藏进度判定：背包持有（db.get_inventory 按 item key/名称匹配）+ 图鉴（db.get_bestiary
按怪物名匹配，魔物战利品册）。满套判定：全部条目已收集。

⚠️ 简易版（先做数据 + 展示）：
- 满套奖励（chest 宝箱）发放走本命令『收藏册 领取』，未满套不可领。
- 满套称号（reward.title）与永久属性（reward.bonus）——数据已登记，
  称号发放/属性消费点待主 agent 接线（本版本仅展示满套后可领宝箱）。
"""
import re

from ._platform import AstrMessageEvent, filter, MessageChain

from .. import content as C
from .. import db
from ..commands.base import CommandBase, require_player


class CollectionCmds(CommandBase):
    """收藏册：冒险者收藏集展示/满套领奖"""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?收藏册(?:\s*(.+))?$")
    @require_player()

    async def collection(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)
        raw = self._strip_cmd(event, "收藏册").strip()
        books = list(getattr(C, "COLLECTION_BOOKS", None) or [])
        if not books:
            yield event.plain_result("📖 收藏册数据缺失，请联系管理～")
            return
        # 『收藏册 领取』：满套册领宝箱
        if raw.startswith("领取"):
            lines, err = self._claim_book_reward(group_id, qq_id, raw)
            if err:
                yield event.plain_result(f"📖 {err}")
            else:
                yield event.plain_result("\n".join(lines))
            return
        # 指定册名
        target = None
        if raw:
            target = next((b for b in books if b["name"] in raw or raw in b["name"]), None)
            if not target:
                yield event.plain_result(f"📖 没找到收藏册『{raw}』，试试『收藏册』看全部～")
                return
            lines = self._book_detail(group_id, qq_id, target)
            yield event.plain_result("\n".join(lines))
            return
        # 总览
        lines = ["📖 【冒险者收藏册】", "━━━━━━━━━━━━"]
        for b in books:
            got, total = self._book_progress(group_id, qq_id, b)
            mark = "✅" if got == total else "⬜"
            lines.append(f"{mark} {b['name']}：{got}/{total}(『收藏册 {b['name']}』查看)")
        lines.append("")
        lines.append("💡 收集各册条目，集齐后可『收藏册 领取』领宝箱奖励！")
        yield event.plain_result("\n".join(lines))

    # ---------------- 内部 ----------------
    def _inv_names(self, group_id, qq_id):
        """背包持有物品名集合（key 转 display 名）"""
        names = set()
        try:
            for it in db.get_inventory(group_id, qq_id):
                nm = (it.get("data") or {}).get("name") or it.get("key")
                if nm:
                    names.add(str(nm))
                if it.get("key"):
                    names.add(str(it["key"]))
        except Exception:
            pass
        return names

    def _bestiary_names(self, group_id, qq_id):
        """图鉴击杀怪物名集合（bestiary key → display 名）"""
        names = set()
        try:
            for r in db.get_bestiary("", qq_id):
                nm = C.display("monsters", r["monster"])
                names.add(str(nm))
                names.add(str(r["monster"]))
        except Exception:
            pass
        return names

    def _book_progress(self, group_id, qq_id, book):
        """返回 (已收集数, 总条目数)。条目 key 命中背包名或图鉴怪名即算收集。"""
        inv = self._inv_names(group_id, qq_id)
        best = self._bestiary_names(group_id, qq_id)
        total = len(book.get("entries") or [])
        got = 0
        for e in book.get("entries") or []:
            k = e.get("key", "")
            nm = e.get("name", "")
            if k in inv or nm in inv or k in best or nm in best:
                got += 1
        return got, total

    def _book_detail(self, group_id, qq_id, book):
        inv = self._inv_names(group_id, qq_id)
        best = self._bestiary_names(group_id, qq_id)
        got, total = self._book_progress(group_id, qq_id, book)
        rw = book.get("reward") or {}
        lines = [f"📖 【{book['name']}】{got}/{total}", book.get("desc", ""), "━━━━━━━━━━━━"]
        for e in book.get("entries") or []:
            k = e.get("key", "")
            nm = e.get("name", "")
            ok = k in inv or nm in inv or k in best or nm in best
            mark = "✅" if ok else "⬜"
            hint = e.get("hint", "")
            lines.append(f"{mark} {nm}（{hint}）" if hint else f"{mark} {nm}")
        if got == total:
            lines.append("🎉 集齐了！可用『收藏册 领取』领奖！")
        rw_txt = []
        if rw.get("chest"):
            rw_txt.append(f"宝箱×1")
        if rw.get("title"):
            rw_txt.append(f"称号『{rw['title']}』")
        if rw.get("bonus"):
            # v174 实装：集齐即 title_bonus() 动态给永久属性（读 possessed/bestiary）
            _bn = rw["bonus"]
            _parts = [f"{k}+{v}" for k, v in _bn.items()]
            rw_txt.append(f"永久属性({'、'.join(_parts)})")
        if rw_txt:
            lines.append("🎁 满套奖励：" + "、".join(rw_txt))
        return lines

    def _claim_book_reward(self, group_id, qq_id, raw):
        """『收藏册 领取 [册名]』：集齐的册发 chest 宝箱（title/bonus 待接线）。"""
        books = list(getattr(C, "COLLECTION_BOOKS", None) or [])
        name = raw.replace("领取", "", 1).strip()
        if name:
            books = [b for b in books if b["name"] in name or name in b["name"]]
        if not books:
            return [], "没有可领取的收藏册奖励（指定册名或全领）～"
        lines = []
        for b in books:
            got, total = self._book_progress(group_id, qq_id, b)
            if got < total:
                lines.append(f"⬜ {b['name']} 未集齐({got}/{total})，无法领取")
                continue
            rw = b.get("reward") or {}
            chest = rw.get("chest")
            if chest:
                try:
                    _idata = C.ITEMS.get(chest) or C.MATERIALS.get(chest)
                    if _idata is None:
                        _idata = {"name": chest, "type": "消耗品", "stackable": True, "price": 0}
                    db.add_item(group_id, qq_id, chest, _idata, count=1)
                    lines.append(f"🎁 {b['name']} 集齐奖励：{_idata.get('name', chest)}×1 已入包！")
                except Exception:
                    lines.append(f"⚠️ {b['name']} 宝箱发放失败，请联系管理")
            else:
                lines.append(f"📖 {b['name']} 已集齐（无宝箱奖励配置）")
        return lines, ""
