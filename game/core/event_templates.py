# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - event_templates.py（★ B13-L3 起 = 薄壳）

实现真源已进内容包：`content/event_templates.py`（`EventContext` / `execute_event_template` /
`register` / `_add_bp_or_pages` / `_BP_PAGE_BY_QUALITY` + 19 个模板里的 **18** 个逐字端口；
搬的边界 / 正文改动面 / 缺口全写在那边的头注里）。本文件只剩三件事：

  1. **加载包**：`bootstrap.package_apply()`（本进程唯一包加载口，幂等；失败大声抛）
  2. **tpl_merchant**：唯一一个**故意留宿主**的模板（宿主源码级门禁，不是遗漏 —— 见下）
  3. **同名单 re-export**（`game/core/__init__.py:97` · `game/core/rule_engine.py:193` ·
     `tests/test_v97_03/05/06` · `tests/test_v113_5_copy_fixes` · `tests/test_v184_loot_tiers`
     · `scripts/audit_mesh.py` 的 import 点零改动）+ `__getattr__` 兜底

★ 为什么 `tpl_merchant` 留宿主（与 B9 线2 `commands/world.py` 的 `quest_view` /
  `_instance_gate_block` 同款处置）：`tests/test_v184_loot_tiers.py:690-709` 是**源码级绑定**
  断言，按本文件路径 grep 源码：

      ("game/core/event_templates.py",
       'QUALITY_TIERS.pick_weights({"white": 45, "green": 40, "blue": 15}, rng=random)', True)

  外加一条**同款反向断言**：本文件**不许**再出现旧的「`random.choices` + 三档字面权重列表」
  写法（本头注刻意不抄那串字面量 —— 抄了就是自己把反向断言撞红）。
  实现搬走后这两句就不在宿主文件里了 → 门禁红。故该模板**只此一份**留在本文件，
  用包内导出的同一个 `register` 注册进**同一个** `TEMPLATES`（19 键不变，无双源）。

★ 宿主替身注入：**不需要**。`db` / `content` 聚合层由包内按 `sys.modules` 惰性解析；
  core 模块级 `from .. import content` 会撞 §8-R1 导入环（先 data → 半初始化的 content），
  所以本文件**不** import 它们。

改造前 530 行 → 现在 105 行。等价证据：`overnight/w1213_b13l3_snap.py`（124 用例逐字节快照）
· `overnight/W-B13-L3-events-dialogue.md`。
"""
from .. import bootstrap as _bootstrap                          # noqa: F401

_bootstrap.package_apply()                                      # 本进程唯一包加载口（幂等）

from content import event_templates as _IMPL                    # noqa: E402  包内唯一实现
import random                                                   # noqa: E402  （真源模块级 import random：tpl_merchant 用它）

# ---- 同名单 re-export（真源符号名一字不变；同一个对象：函数 / 字典）----
EventContext = _IMPL.EventContext
execute_event_template = _IMPL.execute_event_template
register = _IMPL.register                # 与包内同一个装饰器 → 注册进同一个 TEMPLATES
TEMPLATES = _IMPL.TEMPLATES
_BP_PAGE_BY_QUALITY = _IMPL._BP_PAGE_BY_QUALITY
_add_bp_or_pages = _IMPL._add_bp_or_pages


# ============================================================
# ★ 故意留宿主的模板：tpl_merchant（真源正文逐字，一行未改）
#   理由见头注 ★：宿主源码级门禁按本文件 grep 源码
# ============================================================
@register("merchant")
def tpl_merchant(ctx):
    """流浪商人：低价装备（可拒绝）。沿用原 merchant 逻辑。
    v113.5 O71 修复：探索强卖无确认直接扣钱 → 改为挂起报价（set_event_state），
    玩家回复『确认购买/拒绝』由 combat.py trader_confirm 命令消费。"""
    import uuid
    db = ctx._db()
    C = ctx._C()
    # v184：档位抽取问唯一真相源 QUALITY_TIERS（权重行按档位序对齐，未列档位权重 0）。
    # 延迟导入＝本模块既有风格（模板函数内才 import，防 core 聚合链循环）。
    from .quality_tiers import QUALITY_TIERS
    q = QUALITY_TIERS.pick_weights({"white": 45, "green": 40, "blue": 15}, rng=random)
    equip = C.generate_equip(random.choice(["weapon", "ring", "necklace"]), max(1, ctx.lv), q)
    price = int(equip["price"] * 0.6)
    # F1 审计修复（C-D3.3）：按 DB 最新 gold 判能否出价（原用 ctx._focus 陈旧对象——调用方在
    # _rule_fire 前可能已通过其他路径加/扣过金币，旧 dict 覆盖会误判出价；与 tpl_loot_gold 同型口径）
    _cur_gold = db.get_player(ctx.group_id, ctx.qq_id).get("gold", 0)
    if _cur_gold >= price and random.random() < C.TRADER_DEAL_CHANCE:  # v101.5 常量
        # v113.5 O71：原逻辑直接扣金币入包（强卖无确认）——先挂起报价等玩家答复
        import json as _json, time as _time
        db.set_event_state(f"trader_{ctx.group_id}_{ctx.qq_id}", _json.dumps({
            "ts": _time.time(),
            "price": price,
            "equip": equip,
        }))
        return (f"🛒 【流浪商人】一个商人拉住你：“勇士，看货！便宜卖你了！”\n"
                f"{C.QUALITY[equip['quality']]['color']}【{equip['name']}】只要 {price} 金币！\n"
                f"是否购买？回复 确认购买/拒绝")
    return (f"🛒 【流浪商人】一个商人向你兜售 {C.QUALITY[equip['quality']]['color']}【{equip['name']}】，"
            f"只要 {price} 金币……你摇了摇头：不买不买。商人悻悻地走了。")


# ---- 注册顺序还原到真源键序（merchant 原在第 11 位）----
# 键序本身**无语义**（消费端全部按名取 · `events` 域导出走 sort_table 排序），但改前/改后
# 逐字节快照与「19 键 ↔ 19 个 tpl_*」对拍都记键序 → 还原成原序，省一层解释成本。
_ORDER = ("loot_gold", "loot_materials", "loot_gold_mats", "exp_gain", "heal_full", "damage",
          "set_state", "set_flag", "dialog", "mystery_chest", "merchant", "wandering", "combo",
          "random_choice", "stamina_cost", "region_lore", "stamina_gift", "shrine_bless",
          "rare_find")
_T = {_k: TEMPLATES[_k] for _k in _ORDER if _k in TEMPLATES}
_T.update({_k: _v for _k, _v in TEMPLATES.items() if _k not in _T})
TEMPLATES.clear()
TEMPLATES.update(_T)
del _T, _ORDER


# 包内实现里**不外露**的宿主替身 / 私有工具名（防 `from .event_templates import db` 这类误取）
_HANDLES = frozenset(("C", "db", "bind_host", "_INJECTED", "_HOST_PKG", "_HOST_PKG_FALLBACK",
                      "_host_module", "_host_attr", "_HostMod", "check_player_level_up"))


def __getattr__(name):
    """未列名兜底：转发包内实现（`tpl_*` / 未来新增符号），宿主替身名一律不外露。"""
    if name in _HANDLES or name.startswith("__"):
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    return getattr(_IMPL, name)


def __dir__():
    return sorted((set(globals()) | set(dir(_IMPL))) - set(_HANDLES))
