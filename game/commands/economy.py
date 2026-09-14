# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - economy（economy）—— B9 线 L1 **薄壳**（2026-09-13）

本文件只做四件事：**命令注册（真装饰器）/ 取玩家 / 调包 / 渲染消息**。实现正文
（模块常量、物品详情渲染器、`EconomyCmds` 的 131 个方法）已逐字搬进内容包
`content/economy_cmds.py`（类 `EconomyImpl`），宿主面经 `content/economy_host.bind_host()`
注入（包不 import 宿主）。`EconomyCmds(_E.EconomyImpl, CommandBase)` 的 MRO 与重构前
（economy 方法定义在 CommandBase 子类里）逐位等价；46 个注册指令在这里**一行转发**，
`@declared` / `@require_player` 与重构前逐字同序。

私有助手（`_prof_wait_*` / `_settle_*` / `_shop_limit_*` …）由 `EconomyImpl` 继承提供，
宿主其它模块与本命令内部的 `self._xxx(...)` 调用点零变化。

B12-L3 收口（2026-09-14）：两个宿主面 `_shop_svc` / `_prof_svc` 改注入**宿主薄壳模块**
（`game/services/{shop,profession}.py`），回到重构前的模块身份（此前注入的是包内模块）。
两份壳已逐名 re-export 包内实现（profession 壳含私表 `_GATHER_COND_CHECKERS`），故行为
逐字节不变；economy 因此不再直连别线正在搬的包内模块。证据：`overnight/W-B12-L3-economy-gm.md`。
"""

from ._declared import declared
from .base import CommandBase, require_player
from .. import content as C
from .. import db
from ..content_rules.panel import STAT_NAMES, _set_info, player_final_stats, race_stats
from ._platform import AstrMessageEvent, MessageChain, Plain
from ..core import item_templates, shop_stock as _sshop, smith_stock as _ss
from ..core.affix import stat_affix_stats
from ..core.drops import _eq_random_desc, _merge_legendary_stats
from ..core.runes import rune_item
from ..core.stats import ARMOR_FAMILY_ALIAS, equip_value
from ..core.title_conds import TitleCtx, CONDITIONS, check_pro_title
from ..services import crafting as _craft_svc
from ..services import profession as _prof_svc  # B12-L3 收口：注入宿主薄壳（原注入包内模块）
from ..services import shop as _shop_svc        # B12-L3 收口：交易区注入宿主薄壳（同上）
from ..services.battle_bridge import sync_player_from_actor
from ..store.inventory import _possessed_key
from .battle_item_use import can_translate, make_override

# 包加载口（本进程唯一）：包根进 sys.path → `content` 命名空间包
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()

from content import economy_host as _EH          # noqa: E402
from content.catalog_b143 import QUALITY         # noqa: E402  B14 收口：原 ..data.equipment

# ① 宿主面注入（**必须先于 import 包内实现** —— 后者模块级即读宿主面）
_EH.bind_host(
    ARMOR_FAMILY_ALIAS=ARMOR_FAMILY_ALIAS,
    AstrMessageEvent=AstrMessageEvent,
    C=C,
    CONDITIONS=CONDITIONS,
    MessageChain=MessageChain,
    Plain=Plain,
    QUALITY=QUALITY,
    STAT_NAMES=STAT_NAMES,
    TitleCtx=TitleCtx,
    _craft_svc=_craft_svc,
    _eq_random_desc=_eq_random_desc,
    _merge_legendary_stats=_merge_legendary_stats,
    _possessed_key=_possessed_key,
    _set_info=_set_info,
    _ss=_ss,
    _sshop=_sshop,
    can_translate=can_translate,
    check_pro_title=check_pro_title,
    db=db,
    equip_value=equip_value,
    item_templates=item_templates,
    make_override=make_override,
    player_final_stats=player_final_stats,
    race_stats=race_stats,
    rune_item=rune_item,
    stat_affix_stats=stat_affix_stats,
    sync_player_from_actor=sync_player_from_actor,
)

# ② 交易区 / ③ 副业：注入**宿主薄壳**（`game/services/shop.py` / `game/services/profession.py`）
#    —— 与重构前同模块身份（重构前 economy 就是 `from ..services import shop/profession`）：
#    两份壳已逐名 re-export 包内实现（profession 壳含私表 `_GATHER_COND_CHECKERS`）→ 注入壳
#    等价于注入实现，且 economy 不再直连别线正在搬的包内模块（BRIEF §3.5 跨线依赖）。
#    绑定必须早于下行 `import content.economy_cmds`（后者模块级即读宿主面）。
_EH.bind_host(_shop_svc=_shop_svc, _prof_svc=_prof_svc)

from content import economy_cmds as _E          # noqa: E402  （模块级即读宿主面）

# ---- 再导出：模块级常量 / 渲染器（既有 import 点零变化：tests 直接 import 这些名字）----
_RECIPE_ROSTER_IDS = _E._RECIPE_ROSTER_IDS  # noqa: F401
_MAT_FACILITY = _E._MAT_FACILITY  # noqa: F401
_MAT_FACILITY_HINT = _E._MAT_FACILITY_HINT  # noqa: F401
_item_kind_type = _E._item_kind_type  # noqa: F401
_STAT_NAMES = _E._STAT_NAMES  # noqa: F401
_REQ_NAMES = _E._REQ_NAMES  # noqa: F401
_AFFIX_FEATURE_RULES = _E._AFFIX_FEATURE_RULES  # noqa: F401
_equip_affix_features = _E._equip_affix_features  # noqa: F401
_upgrade_recalc_equip = _E._upgrade_recalc_equip  # noqa: F401
_render_equip = _E._render_equip  # noqa: F401
_render_material = _E._render_material  # noqa: F401
_render_fish = _E._render_fish  # noqa: F401
_render_rune = _E._render_rune  # noqa: F401
_render_encyclopedia_equip = _E._render_encyclopedia_equip  # noqa: F401
_roster_gen_equip = _E._roster_gen_equip  # noqa: F401
_render_blueprint = _E._render_blueprint  # noqa: F401
_render_pet_egg = _E._render_pet_egg  # noqa: F401
_render_mount = _E._render_mount  # noqa: F401
_render_consumable = _E._render_consumable  # noqa: F401
_ITEM_DETAIL_RENDERERS = _E._ITEM_DETAIL_RENDERERS  # noqa: F401
item_detail_render = _E.item_detail_render  # noqa: F401
_render_item_tags = _E._render_item_tags  # noqa: F401
_GATHER_COND_CHECKERS = _E._GATHER_COND_CHECKERS  # noqa: F401

# ---- 46 个指令：注册（真装饰器，与重构前逐字同序）+ 一行转发 ----

class EconomyCmds(_E.EconomyImpl, CommandBase):
    """背包/装备/锻造/强化/商店/采集/垂钓/炼金"""

    @declared('gather')
    @require_player()
    async def gather(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.gather(self, event):
            yield _item

    @declared('mining')
    @require_player()
    async def mining(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.mining(self, event):
            yield _item

    @declared('alchemy')
    @require_player()
    async def alchemy(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.alchemy(self, event):
            yield _item

    @declared('alchemy_craft')
    @require_player()
    async def alchemy_craft(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.alchemy_craft(self, event):
            yield _item

    @declared('cooking_list')
    @require_player()
    async def cooking_list(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.cooking_list(self, event):
            yield _item

    @declared('cooking')
    @require_player()
    async def cooking(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.cooking(self, event):
            yield _item

    @declared('bp_craft')
    @require_player()
    async def bp_craft(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.bp_craft(self, event):
            yield _item

    @declared('profession_view')
    @require_player()
    async def profession_view(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.profession_view(self, event):
            yield _item

    @declared('prof_forget')
    @require_player()
    async def prof_forget(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.prof_forget(self, event):
            yield _item

    @declared('daily_prof')
    @require_player()
    async def daily_prof(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.daily_prof(self, event):
            yield _item

    @declared('fishing')
    @require_player()
    async def fishing(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.fishing(self, event):
            yield _item

    @declared('craft')
    @require_player()
    async def craft(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.craft(self, event):
            yield _item

    @declared('craft_commission')
    @require_player()
    async def craft_commission(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.craft_commission(self, event):
            yield _item

    @declared('learn')
    @require_player()
    async def learn(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.learn(self, event):
            yield _item

    @declared('recipe_list')
    @require_player()
    async def recipe_list(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.recipe_list(self, event):
            yield _item

    @declared('enhance')
    @require_player()
    async def enhance(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.enhance(self, event):
            yield _item

    @declared('equip_upgrade')
    @require_player()
    async def equip_upgrade(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.equip_upgrade(self, event):
            yield _item

    @declared('gem_drill')
    @require_player()
    async def gem_drill(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.gem_drill(self, event):
            yield _item

    @declared('gem_socket')
    @require_player()
    async def gem_socket(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.gem_socket(self, event):
            yield _item

    @declared('gem_remove')
    @require_player()
    async def gem_remove(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.gem_remove(self, event):
            yield _item

    @declared('gem_combine')
    @require_player()
    async def gem_combine(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.gem_combine(self, event):
            yield _item

    @declared('gem_view')
    @require_player()
    async def gem_view(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.gem_view(self, event):
            yield _item

    @declared('rune_craft')
    @require_player()
    async def rune_craft(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.rune_craft(self, event):
            yield _item

    @declared('rune_remove')
    @require_player()
    async def rune_remove(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.rune_remove(self, event):
            yield _item

    @declared('refine_equip')
    @require_player()
    async def refine_equip(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.refine_equip(self, event):
            yield _item

    @declared('calamity_forge')
    @require_player()
    async def calamity_forge(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.calamity_forge(self, event):
            yield _item

    @declared('enchant')
    @require_player()
    async def enchant(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.enchant(self, event):
            yield _item

    @declared('set_view')
    @require_player()
    async def set_view(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.set_view(self, event):
            yield _item

    @declared('monster')
    @require_player()
    async def monster(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.monster(self, event):
            yield _item

    @declared('adventure_book')
    @require_player()
    async def adventure_book(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.adventure_book(self, event):
            yield _item

    @declared('footprint')
    @require_player()
    async def footprint(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.footprint(self, event):
            yield _item

    @declared('bestiary')
    @require_player()
    async def bestiary(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.bestiary(self, event):
            yield _item

    @declared('encyclopedia')
    @require_player()
    async def encyclopedia(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.encyclopedia(self, event):
            yield _item

    @declared('titles')
    @require_player()
    async def titles(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.titles(self, event):
            yield _item

    @declared('inventory')
    @require_player()
    async def inventory(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.inventory(self, event):
            yield _item

    @declared('bag_filter')
    @require_player()
    async def bag_filter(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.bag_filter(self, event):
            yield _item

    @declared('item_view_mode_cmd', priority=50)
    @require_player()
    async def item_view_mode_cmd(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.item_view_mode_cmd(self, event):
            yield _item

    @declared('item_detail')
    @require_player()
    async def item_detail(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.item_detail(self, event):
            yield _item

    @declared('my_equipment')
    @require_player()
    async def my_equipment(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.my_equipment(self, event):
            yield _item

    @declared('equip')
    @require_player()
    async def equip(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.equip(self, event):
            yield _item

    @declared('unequip')
    @require_player()
    async def unequip(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.unequip(self, event):
            yield _item

    @declared('use')
    @require_player()
    async def use(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.use(self, event):
            yield _item

    @declared('sell')
    @require_player()
    async def sell(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.sell(self, event):
            yield _item

    @declared('shop')
    @require_player()
    async def shop(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.shop(self, event):
            yield _item

    @declared('buy')
    @require_player()
    async def buy(self, event: AstrMessageEvent):
        async for _item in _E.EconomyImpl.buy(self, event):
            yield _item
