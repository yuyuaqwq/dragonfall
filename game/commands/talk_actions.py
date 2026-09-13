# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - talk_actions.py（v101.23d B 级：对话动作注册表）

与 core/dialogue_conds.py 的 CONDITIONS 注册表对称：加新对话动作 =
register 一个函数（~5 行），_apply_talk_action 零改动，纯内容扩展不动引擎。

动作函数签名：
    fn(world, group_id, qq_id, player, npc_id, action) -> list[通知行]
    world = Main 实例（Mixin 方法可用），action = 选项里的动作 dict

注意：注册顺序 = 执行顺序（dict 保序），与 v101.23d 之前的 if 链顺序一致；
一个选项可带多个动作键（如 set_flag + quest_take），全部执行。

v113：新增异步动作支持（hidden_evolve 等需要 await async generator 的动作）——
异步动作函数用 async def 声明，world._apply_talk_action 会检测并 await。

★ B8.2 线3（2026-09-13）命令层薄壳化：本模块只留「**注册** + 消费端防御」——
  · 17 个动作的**实现正文**搬进内容包 `content/talk_actions.py`（逐字端口，只改 import 层：
    `db` / `grant_reward` 走宿主替身注入；`C.NPCS`/`C.ALL_WILD`/`C.SIDE_QUESTS`/`C.CLASSES`/
    `C.resolve`/`C.get_dialogue` 改读包内域 JSON；技能查询用包内 `content/skills.py` 端口）。
  · 本文件保留 17 个 `@register(...)` 一行转发 —— 这一步**不是形式**：
    ① `world.py:3579` 按 `ACTIONS.items()` 的注册顺序执行（条件型 `apprentice_check` 必须最先），
       注册序 = 真源序（与重构前逐行同序）；
    ② 域名 `talk_actions` 的**真源就是这个注册表**（真源 = 游戏仓；包是单向导出物），
       导出器 `scripts/export_domains/b82_l3.py` 用 AST 读本文件的 `@register` 声明。
  · `check_action_keys` 留宿主：它是**消费端防御**（未知动作键告警/测试环境 raise），
    要读宿主日志层 + `GWEN_*` 环境变量 → 属「接人性」，不进包。

包加载口 = `bootstrap.package_apply()`（本进程唯一；包根进 sys.path → `content` 命名空间包）。
"""
from ..log_setup import LOG

# ★ B8.2 线3：读包（宿主的 `..content` 聚合层与动作实现不再被本命令 import）
from .. import bootstrap as _bootstrap          # noqa: E402
from .. import db as _db                        # noqa: E402  （宿主存储层；注入给包内替身）
from .. import reward as _reward                # noqa: E402

_bootstrap.package_apply()
from content import talk_actions as _TA         # noqa: E402

# 宿主替身注入（存储层 + 发放函数）—— 包内正文 `db.xxx(...)` / `grant_reward(...)` 一字未改
_TA.bind_host(_db, _reward.grant_reward)

ACTIONS = {}


def register(key):
    """动作注册装饰器。"""
    def deco(fn):
        ACTIONS[key] = fn
        return fn
    return deco


def check_action_keys(action):
    """消费端防御：action 中未注册的动作键（set(action) - set(ACTIONS)）告警。

    v124.3（审计）：此前 _apply_talk_action 对未知 action 键静默忽略（qest_take
    笔误无告警），与 check_need 的未知 need 键防御不对称。现与
    core/dialogue.py check_need（v104 M21 P1）对齐：
      生产环境 → astrbot 日志 warn 并放行（防数据笔误静默失效）；
      测试环境（GWEN_GAME_DB 含 "test" / GWEN_TEST_MODE=1）→ 直接 raise 让单测抓笔误。
    _apply_talk_action_async / _apply_talk_action 入口调用。"""
    if not action:
        return
    unknown = set(action) - set(ACTIONS)
    if not unknown:
        return
    import os
    _db_name = os.environ.get("GWEN_GAME_DB", "")
    _msg = (f"[dragonfall] 对话动作未注册键 action{unknown}："
            f"数据笔误？已按'无动作'放行，请检查 dialogues.py")
    _test = ("test" in os.path.basename(_db_name).lower()
             or os.environ.get("GWEN_TEST_MODE") == "1")
    if _test:
        raise ValueError(_msg)
    LOG.warning(_msg)


# ================= 动作注册（实现正文在包内；注册序 = 执行序） =================

# 注册顺序 = 执行顺序。apprentice_check 必须最先注册：它是条件型动作（闸门），
# 判定失败/副业未解锁时设置 world._talk_route，消费端据此中断后续动作链——
# 与 v101.23d 前 talk_choice 特判"失败路径零动作执行（consume_item 不扣料）"一致。


@register("apprentice_check")
def action_apprentice_check(world, group_id, qq_id, player, npc_id, action):
    """v81 导师进修：考验判定（检查背包材料）——由 talk_choice 主循环特判迁入注册表。

    条件型动作：判定结果经 world._talk_route / world._talk_tail 通道传出，
    _apply_talk_action_async 返回路由，talk_choice 主循环只做通用分发：
      _talk_route = "__end__" → 副业未解锁直接结束对话（#101.29，不再渲染 fail 节点）
      _talk_route = "fail"    → 材料不足，走选项 fail_next
      通过（不设 route）     → 成功提示放 _talk_tail，待全部动作行之后追加
                                （与旧特判 notices.append("✅…") 的输出顺序一致）
    交互行为（选项显示/失败提示/通过流程）与 v101.23d 前内联特判完全一致。
    """
    return _TA.action_apprentice_check(world, group_id, qq_id, player, npc_id, action)


@register("set_flag")
def action_set_flag(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_set_flag(world, group_id, qq_id, player, npc_id, action)


@register("give_gold")
def action_give_gold(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_give_gold(world, group_id, qq_id, player, npc_id, action)


@register("give_exp")
def action_give_exp(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_give_exp(world, group_id, qq_id, player, npc_id, action)


@register("give_item")
def action_give_item(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_give_item(world, group_id, qq_id, player, npc_id, action)


@register("open_shop")
def action_open_shop(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_open_shop(world, group_id, qq_id, player, npc_id, action)


@register("hint")
def action_hint(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_hint(world, group_id, qq_id, player, npc_id, action)


@register("quest_take")
def action_quest_take(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_quest_take(world, group_id, qq_id, player, npc_id, action)


@register("side_take")
def action_side_take(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_side_take(world, group_id, qq_id, player, npc_id, action)


@register("side_offer")
def action_side_offer(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_side_offer(world, group_id, qq_id, player, npc_id, action)


@register("side_take_one")
def action_side_take_one(world, group_id, qq_id, player, npc_id, action):
    """v127.6：对话 side_menu 子选项——单条支线接取（自选，不再全接）。

    与 side_offer 对称，但只接 action['side_take_one'] 指定的那一条；
    走 world._offer_side_quest 校验 sid 在当前可接清单内才落地（防越权）。
    """
    return _TA.action_side_take_one(world, group_id, qq_id, player, npc_id, action)


@register("consume_item")
def action_consume_item(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_consume_item(world, group_id, qq_id, player, npc_id, action)


@register("unlock_prof")
def action_unlock_prof(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_unlock_prof(world, group_id, qq_id, player, npc_id, action)


@register("give_prof_exp")
def action_give_prof_exp(world, group_id, qq_id, player, npc_id, action):
    """unlock_prof 的配套参数键（拜师礼副业经验，实际由 unlock_prof 动作消费）。

    v124.3（审计）：注册为 no-op 仅为让 ACTIONS 覆盖数据中全部动作键，
    防 check_action_keys 未知键告警误报（拜师选项均带此键）。"""
    return _TA.action_give_prof_exp(world, group_id, qq_id, player, npc_id, action)


@register("unlock_class")
def action_unlock_class(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_unlock_class(world, group_id, qq_id, player, npc_id, action)


@register("tutor_skill")
def action_tutor_skill(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_tutor_skill(world, group_id, qq_id, player, npc_id, action)


@register("evolve_class")
def action_evolve_class(world, group_id, qq_id, player, npc_id, action):
    return _TA.action_evolve_class(world, group_id, qq_id, player, npc_id, action)


@register("hidden_evolve")
async def action_hidden_evolve(world, group_id, qq_id, player, npc_id, action):
    """v113 血脉传承：隐藏线导师对话『接受传承』（异步动作；同步版由消费端跳过）。"""
    return await _TA.action_hidden_evolve(world, group_id, qq_id, player, npc_id, action)
