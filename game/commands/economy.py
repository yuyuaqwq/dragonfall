# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - economy（economy）★ B18-L9 终态：**注册 + 两行转发**

45 条经济命令的**守卫 / 取参 / 分支业务 / 回话组装全在包内**
（`content/cmds_economy.py` 登记进 `content/commands.py::COMMANDS`）。本模块只剩三件事：

  ① **注册**：`@declared("<key>")`（正则/desc 来自宿主声明表 `game/data/command_specs.json`）
  ② **转发**：`async for _r in _BRIDGE.run_async(self, "<key>", event): yield _r`
     —— 桥到引擎 host 契约（造 `Env` → 声明守卫 → 包内 handler → 逐段回话）
  ③ **宿主替身注入**：`content/economy_host.bind_host()`（实现体
     `content/economy_cmds.py::EconomyImpl` 模块级即读宿主面 → 注入必须先于 import 包内实现）
     + 模块级常量 / 物品详情渲染器的**再导出**（既有 import 点零变化：tests 直接 import 这些名字）

★ B18-L9（2026-09-15）**命令整块进包**后，原先「`@require_player()` 守卫 + 一行
  `async for _item in _E.EconomyImpl.<m>(self, event): yield _item`」的宿主面全部随包内新模块
  `content/cmds_economy.py`（表形状 = 战斗族样板，处理器 async）：45 条命令的守卫声明
  （`hook:player`，判定 + 文案都在包 `content/guards.py`）、取参口径、调包、回话全在包内。
  本模块每条命令只剩 `@declared("<key>")` + 两行转发 —— 宿主里**不再有任何游戏字面量**
  （指令词 / 守卫装饰器）。

★ **45 条全部是「两行 `run_async`」**（没有一条走同步 `_BRIDGE.run`）：实现体
  `content/economy_cmds.py::EconomyImpl.<m>` 全是 **async generator**（AST 实测 45/45 带
  `yield`），旧壳正是 `async for _item in _E.EconomyImpl.<m>(self, event): yield _item`
  —— 只能 `async for` 迭代。故包内用 `_declare` 登记 `async def`（照 B18-L3c 战斗族先例
  `content/cmds_combat.py`），宿主两行逐条 `yield`：与旧壳的消息切分逐字节相同。

`EconomyCmds(_E.EconomyImpl, CommandBase)` 的 MRO 与重构前逐位等价；私有助手
（`_prof_wait_*` / `_settle_*` / `_shop_limit_*` …）由 `EconomyImpl` 提供，宿主其它模块与
本命令内部的 `self._xxx(...)` 调用点零变化。

B12-L3 收口（2026-09-14）：两个宿主面 `_shop_svc` / `_prof_svc` 注入**宿主薄壳模块**
（`game/services/{shop,profession}.py`），回到重构前的模块身份。两份壳已逐名 re-export 包内
实现（profession 壳含私表 `_GATHER_COND_CHECKERS`），故行为逐字节不变。证据：
`overnight/W-B12-L3-economy-gm.md`。

宿主里 `grep -c 'T\\.text\\|T\\.static' game/commands/economy.py` = 0（本域本来就不用文案表
key：句子是 `EconomyImpl` 里的内联字面量 / f-string，B9-L1 起就在包内）。

形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，证据 =
`overnight/b18l9_snap.py` 的 142 场景快照（sha256 改前 = 改后，含 DB 副作用逐行 dump）
+ `tests/test_texts_table.py` 的 `[13]` 段（`ECONOMY_FROZEN` / `ECONOMY_DB_SHA`）。
"""

from . import _host_bridge as _BRIDGE
from ._declared import declared
from .base import CommandBase
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

from content import cmds_economy as _CE         # noqa: E402  B18-L9：45 条命令登记进包内表
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

# ---- 45 个指令：注册（真装饰器，与重构前逐字同序）+ 两行转发 ----
# 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py`，宿主里零文案调用点。


class EconomyCmds(_E.EconomyImpl, CommandBase):
    """命令层（★ B18-L9 终态）：注册 + 两行转发；守卫/取参/业务/回话全在包内
    `content/cmds_economy.py`。"""

    @declared('gather')
    async def gather(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::gather`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "gather", event):
            yield _r

    @declared('mining')
    async def mining(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::mining`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "mining", event):
            yield _r

    @declared('alchemy')
    async def alchemy(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::alchemy`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "alchemy", event):
            yield _r

    @declared('alchemy_craft')
    async def alchemy_craft(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::alchemy_craft`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "alchemy_craft", event):
            yield _r

    @declared('cooking_list')
    async def cooking_list(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::cooking_list`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "cooking_list", event):
            yield _r

    @declared('cooking')
    async def cooking(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::cooking`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "cooking", event):
            yield _r

    @declared('bp_craft')
    async def bp_craft(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::bp_craft`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "bp_craft", event):
            yield _r

    @declared('profession_view')
    async def profession_view(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::profession_view`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "profession_view", event):
            yield _r

    @declared('prof_forget')
    async def prof_forget(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::prof_forget`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "prof_forget", event):
            yield _r

    @declared('daily_prof')
    async def daily_prof(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::daily_prof`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "daily_prof", event):
            yield _r

    @declared('fishing')
    async def fishing(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::fishing`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "fishing", event):
            yield _r

    @declared('craft')
    async def craft(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::craft`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "craft", event):
            yield _r

    @declared('craft_commission')
    async def craft_commission(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::craft_commission`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "craft_commission", event):
            yield _r

    @declared('learn')
    async def learn(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::learn`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "learn", event):
            yield _r

    @declared('recipe_list')
    async def recipe_list(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::recipe_list`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "recipe_list", event):
            yield _r

    @declared('enhance')
    async def enhance(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::enhance`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "enhance", event):
            yield _r

    @declared('equip_upgrade')
    async def equip_upgrade(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::equip_upgrade`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "equip_upgrade", event):
            yield _r

    @declared('gem_drill')
    async def gem_drill(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::gem_drill`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "gem_drill", event):
            yield _r

    @declared('gem_socket')
    async def gem_socket(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::gem_socket`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "gem_socket", event):
            yield _r

    @declared('gem_remove')
    async def gem_remove(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::gem_remove`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "gem_remove", event):
            yield _r

    @declared('gem_combine')
    async def gem_combine(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::gem_combine`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "gem_combine", event):
            yield _r

    @declared('gem_view')
    async def gem_view(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::gem_view`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "gem_view", event):
            yield _r

    @declared('rune_craft')
    async def rune_craft(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::rune_craft`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "rune_craft", event):
            yield _r

    @declared('rune_remove')
    async def rune_remove(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::rune_remove`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "rune_remove", event):
            yield _r

    @declared('refine_equip')
    async def refine_equip(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::refine_equip`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "refine_equip", event):
            yield _r

    @declared('calamity_forge')
    async def calamity_forge(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::calamity_forge`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "calamity_forge", event):
            yield _r

    @declared('enchant')
    async def enchant(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::enchant`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "enchant", event):
            yield _r

    @declared('set_view')
    async def set_view(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::set_view`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "set_view", event):
            yield _r

    @declared('monster')
    async def monster(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::monster`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "monster", event):
            yield _r

    @declared('adventure_book')
    async def adventure_book(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::adventure_book`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "adventure_book", event):
            yield _r

    @declared('footprint')
    async def footprint(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::footprint`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "footprint", event):
            yield _r

    @declared('bestiary')
    async def bestiary(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::bestiary`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "bestiary", event):
            yield _r

    @declared('encyclopedia')
    async def encyclopedia(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::encyclopedia`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "encyclopedia", event):
            yield _r

    @declared('titles')
    async def titles(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::titles`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "titles", event):
            yield _r

    @declared('inventory')
    async def inventory(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::inventory`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "inventory", event):
            yield _r

    @declared('bag_filter')
    async def bag_filter(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::bag_filter`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "bag_filter", event):
            yield _r

    @declared('item_view_mode_cmd', priority=50)
    async def item_view_mode_cmd(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::item_view_mode_cmd`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "item_view_mode_cmd", event):
            yield _r

    @declared('item_detail')
    async def item_detail(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::item_detail`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "item_detail", event):
            yield _r

    @declared('my_equipment')
    async def my_equipment(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::my_equipment`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "my_equipment", event):
            yield _r

    @declared('equip')
    async def equip(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::equip`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "equip", event):
            yield _r

    @declared('unequip')
    async def unequip(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::unequip`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "unequip", event):
            yield _r

    @declared('use')
    async def use(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::use`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "use", event):
            yield _r

    @declared('sell')
    async def sell(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::sell`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "sell", event):
            yield _r

    @declared('shop')
    async def shop(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::shop`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "shop", event):
            yield _r

    @declared('buy')
    async def buy(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_economy.py::buy`（B18 L9）
        async for _r in _BRIDGE.run_async(self, "buy", event):
            yield _r
