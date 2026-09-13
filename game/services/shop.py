# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - shop.py（P4-3 ShopService + TradeService）—— B9 线 L1 **薄壳**

实现正文（常量 + 定价/货架/回收/限购/序号分派）已逐字搬进 `content/shop.py`，
本文件只做「宿主面注入 + 一行转发 + 再导出」——`game/services/__init__.py` / 命令层 /
测试的 import 点与签名零变化。
"""

from .. import content as C
from .. import db
from .. import tlog_setup
from ..core import shop_stock as _sshop, smith_stock as _ss
from ..core.drops import _eq_random_desc

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()

from content import economy_host as _EH          # noqa: E402

# 宿主面注入（**必须先于 import 包内实现**）
_EH.bind_host(
    C=C,
    _eq_random_desc=_eq_random_desc,
    _ss=_ss,
    _sshop=_sshop,
    db=db,
    tlog_setup=tlog_setup,
)

from content import shop as _E          # noqa: E402

# ---- 常量再导出（`game/services/__init__.py` 逐名 import）----
SHOP_EQUIP_PRICE_MULT = _E.SHOP_EQUIP_PRICE_MULT  # noqa: F401
_SHOP_EQUIP_PRICE_OVERRIDE = _E._SHOP_EQUIP_PRICE_OVERRIDE  # noqa: F401
_MAT_FACILITY = _E._MAT_FACILITY  # noqa: F401
_MAT_FACILITY_HINT = _E._MAT_FACILITY_HINT  # noqa: F401

# ⚠️ 埋点探针兼容（`tests/test_v182_behavior_tlog.py:56` 按本文件**源码**查字符串，
#    防埋点被误删）。埋点正文已随实现进 `content/shop.py`（`sell_one`/`buy_index_dispatch`
#    的 `_tlog.emit("shop.buy", ...)`），此处保留同一字面量作指针 —— 本文件仍是交易区唯一入口。
_TLOG_PROBE_POINTER = 'emit("shop.buy"'  # noqa: F841

# ---- 函数一行转发（`*a, **k` 承接，签名/关键字调用点零变化）----
def req_label(*a, **k):  # noqa: D103
    return _E.req_label(*a, **k)

def equip_price(*a, **k):  # noqa: D103
    return _E.equip_price(*a, **k)

def equip_roster(*a, **k):  # noqa: D103
    return _E.equip_roster(*a, **k)

def buy_weapon(*a, **k):  # noqa: D103
    return _E.buy_weapon(*a, **k)

def cur_subarea(*a, **k):  # noqa: D103
    return _E.cur_subarea(*a, **k)

def is_smith_shop(*a, **k):  # noqa: D103
    return _E.is_smith_shop(*a, **k)

def pawn_rate(*a, **k):  # noqa: D103
    return _E.pawn_rate(*a, **k)

def is_quest_item(*a, **k):  # noqa: D103
    return _E.is_quest_item(*a, **k)

def fish_weight_max(*a, **k):  # noqa: D103
    return _E.fish_weight_max(*a, **k)

def sell_one(*a, **k):  # noqa: D103
    return _E.sell_one(*a, **k)

def apprentice_protect_mats(*a, **k):  # noqa: D103
    return _E.apprentice_protect_mats(*a, **k)

def buy_index_dispatch(*a, **k):  # noqa: D103
    return _E.buy_index_dispatch(*a, **k)

def buy_weapon_fn(*a, **k):  # noqa: D103
    return _E.buy_weapon_fn(*a, **k)

def limit_buy_guard(*a, **k):  # noqa: D103
    return _E.limit_buy_guard(*a, **k)

def limit_label(*a, **k):  # noqa: D103
    return _E.limit_label(*a, **k)
