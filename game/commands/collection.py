# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - collection（冒险者收藏册）—— B8.2 **薄壳**

命令层只做四件事：**注册 / 解析参数 / 取玩家 / 调包 / 拼文案**。读表与内容逻辑全归内容包。

真源与包内的分工（B8.2 线2，2026-09-13）
========================================
    收藏册表（5 套 / 42 条目）  真源 `game/data/collection_book.py:20 COLLECTION_BOOKS`（列表）
                              → 包内 `content/data/collection_books.json`（表：键 = 册 id + 注入
                                `order` 还原源列表序）+ 读表口 `content/collection.py`
    物品定义（满套宝箱）        真源 `game/data/items.py ITEMS`（原读 `C.ITEMS` / `C.MATERIALS`）
                              → 包内 `content/data/items.json`（items 域），经 `content.collection.item_info`
    收集判定                    原在本文件 `_book_progress` → 包内 `content.collection.book_progress`
    背包 / 图鉴读取（宿主存储）  仍在本文件（`_inv_names` / `_bestiary_names`）：db + `C.display("monsters")`
                              —— 包内不读宿主 DB（与 `content/bridge.py` 同款替身接口：调用方给集合）
    渲染文案                    全在本文件（一个字都没动）

包加载口 = `game.bootstrap.package_apply()`（**本进程唯一**，幂等；失败大声抛，不静默降级）。

⚠️ 简易版（沿旧）：满套奖励（chest 宝箱）发放走本命令『收藏册 领取』，未满套不可领。
   满套称号（reward.title）与永久属性（reward.bonus）—— 属性走 `core/stat_bonus.py` 动态给；
   称号名的名册闭合见 `scripts/export_domains/collection_exploration.py` 文件头 ① 的说明。
"""
from ._platform import AstrMessageEvent, MessageChain  # noqa: F401  (MessageChain 供类型/兼容用)

from ._declared import declared

from .. import content as C            # 只剩 `C.display("monsters", …)`：怪物显示名索引（装配期收集）
from .. import db
from .base import CommandBase, require_player

_LIB = None


def _lib():
    """包内 `content.collection`（读表 + 收藏判定）。

    惰性 import（不在模块级 import 包内模块：包加载口要先跑 `package_apply()` 把包根插进
    `sys.path`，那时 `content` 才是可用的命名空间包）。
    """
    global _LIB
    if _LIB is None:
        import importlib

        from .. import bootstrap
        bootstrap.package_apply()                       # 幂等；失败抛（不静默留空表）
        _LIB = importlib.import_module("content.collection")
    return _LIB


class CollectionCmds(CommandBase):
    """收藏册：冒险者收藏集展示/满套领奖"""

    @declared("collection")
    @require_player()

    async def collection(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)
        player = self._player(group_id, qq_id)  # noqa: F841（require_player 已取；保留旧壳形状）
        raw = self._strip_cmd(event, "收藏册").strip()
        books = _lib().books()                    # 包内表（源列表序）
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
        """返回 (已收集数, 总条目数) —— 判定归包（key/name 命中背包名或图鉴怪名即算收集）。"""
        return _lib().book_progress(book, self._inv_names(group_id, qq_id),
                                    self._bestiary_names(group_id, qq_id))

    def _book_detail(self, group_id, qq_id, book):
        inv = self._inv_names(group_id, qq_id)
        best = self._bestiary_names(group_id, qq_id)
        lib = _lib()
        got, total = lib.book_progress(book, inv, best)
        rw = book.get("reward") or {}
        lines = [f"📖 【{book['name']}】{got}/{total}", book.get("desc", ""), "━━━━━━━━━━━━"]
        for e in lib.entries(book):
            ok = lib.entry_collected(e, inv, best)
            mark = "✅" if ok else "⬜"
            nm = e.get("name", "")
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
            # v174 实装：集齐即 stat_bonus() 动态给永久属性（读 possessed/bestiary）
            _bn = rw["bonus"]
            _parts = [f"{k}+{v}" for k, v in _bn.items()]
            rw_txt.append(f"永久属性({'、'.join(_parts)})")
        if rw_txt:
            lines.append("🎁 满套奖励：" + "、".join(rw_txt))
        return lines

    def _claim_book_reward(self, group_id, qq_id, raw):
        """『收藏册 领取 [册名]』：集齐的册发 chest 宝箱（title/bonus 待接线）。"""
        books = _lib().books()
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
                    _idata = _lib().item_info(chest)     # 包内 items 域（真源 C.ITEMS/C.MATERIALS）
                    if _idata is None:
                        _idata = {"name": chest, "type": "消耗品", "stackable": True, "price": 0}
                    db.add_item(group_id, qq_id, chest, _idata, count=1)
                    lines.append(f"🎁 {b['name']} 集齐奖励：{_idata.get('name', chest)}×1 已入包！")
                except Exception:
                    lines.append(f"⚠️ {b['name']} 宝箱发放失败，请联系管理")
            else:
                lines.append(f"📖 {b['name']} 已集齐（无宝箱奖励配置）")
        return lines, ""
