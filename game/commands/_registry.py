# -*- coding: utf-8 -*-
"""命令正则有效表（**双来源合并，派生**）。

来源一（首选）：`game/data/command_specs.json` 的**声明表** —— 由 `@declared("key")`
装饰器注册，本表经 `_declared_patterns()` 派生。声明是唯一真源，不再手工同步。
来源二（历史遗留）：本文件下方的 `_LITERAL_REGEX` 字面量表 —— 给尚未迁移的
`@filter.regex(<字面量>)` 指令用。

    COMMAND_REGEX = {**声明的, **字面量的}      # 同名**不允许**出现（OVERLAP_KEYS 必须为空）

用途：测试环境/注册表缺失时的快捷指令校验、_GameCmdFilter 停服 gate 拦截、
快捷转发回退（base.py _static_handlers）。

迁一条指令到声明表的做法（增量，可停）：
  1. 在 `game/data/command_specs.json` 加声明（pattern/desc/category/guards…）
  2. 把该方法的 `@filter.regex(<字面量>)` 换成 `@declared("key")`
  3. **从下方 `_LITERAL_REGEX` 删掉该 key**（否则 OVERLAP_KEYS 门禁报双源）

⚠️ 尚未迁移的指令仍受「半自动维护铁律」约束：新增/修改/删除任何 @filter.regex
命令（含别名），必须同步本表的 `_LITERAL_REGEX`，否则 gate 拦截与回退会失真。同步检查：
  1. 启动校验：插件加载时 main.py 自动对比「已注册公开 handler 名」与
     本表键集，漂移以 WARNING 日志输出（见 main.py _fix_handler_module_paths）。
  2. 强校验：python tests/test_v87_command_matrix.py（表与装饰器 1:1 逐条相等 + 互斥矩阵）
  3. 解析回归：python tests/test_command_parse.py（命令矩阵互斥/免空格/序号）

真实 AstrBot 运行以全局注册表（star_handlers_registry）为准，本表仅供上述回退场景。
"""

_LITERAL_REGEX = {
    # v104 审计后由 M24 命令互斥矩阵测试（tests/test_v87_command_matrix.py）强校验：
    # 本表只剩**尚未迁到声明表**的指令（2026-09-12 起做「指令表迁移收尾」，路线图 #9）；
    # 表内条目仍与 game/commands/*.py 的 @filter.regex 装饰器 1:1（键集合 + 模式逐条相等）。
    # 迁一条：声明表加声明 → 装饰器改 @declared("key") → 删本表同名条目。
    "chronicle": r'^(?:\[At:[^\]]+\]\s*)?编年史(?:\s*|$)',
    # v140 波2 『收藏册』（成就/称号/收藏资源化：5 套冒险者收藏册）
    "collection": r'^(?:\[At:[^\]]+\]\s*)?收藏册(?:\s*(.+))?$',
    # v140 波3.7 『今日事件/事件 <地图名>』（地图随机事件菜单；裸『事件』由 world_event 占用）
    "event_menu": r'^(?:\[At:[^\]]+\]\s*)?(?:今日事件|事件\s+.+|领取补给箱)$',
    # v104 M24 P2-1：『每日副业』前缀误触『每日』面板——负向断言收窄，
    # 别名『每日副业/今日副业』注册到 daily_prof（19 章旧称呼，策划案 §六统一为『副业任务』）
    "daily": r'^(?:\[At:[^\]]+\]\s*)?每日(?!副业)(?:\s*|$)',
    # v115 探索见闻：『探索进度』指令（commands/exploration.py）
    "explore_progress": r'^(?:\[At:[^\]]+\]\s*)?探索进度(?:[\s\S]*)$',
    "time_cmd": r'^(?:\[At:[^\]]+\]\s*)?时间(?:指令)?(?:\s*|$)',
    "wild_notes": r'^(?:\[At:[^\]]+\]\s*)?见闻录(?:\s*|$)',
    # v169.2 修炼爬塔（Lv70+ 30 层单人守关，每日限 3 层）：『爬塔 [层数]』
    "tower_cmd": r'^(?:\[At:[^\]]+\]\s*)?爬塔(?:\s+(\d+))?\s*$',
    # v116 阵营国战最小闭环（四阵营/任务/商店/排行）：与 world.py @filter.regex 1:1 同步
    "camp_join": r'^(?:\[At:[^\]]+\]\s*)?加入阵营(?:\s+\S+)?$',
    "camp_task": r'^(?:\[At:[^\]]+\]\s*)?阵营任务(?:\s+\S+)?$',
    "camp_shop": r'^(?:\[At:[^\]]+\]\s*)?阵营商店(?:\s+\S+)?$',
    "camp_rank": r'^(?:\[At:[^\]]+\]\s*)?阵营排行(?:\s*|$)',
    # v130.2g 新功能：『职业』/『职业 <名称>』12 职业速查（玩家意见 #1 zerc，
    # 数据源 data/job_guide.py：classes.py + EFFECT_RULES/CORE_RESOURCE_GUIDE 派生（原 core_resources.py
    # 已随 v181.M-R2c 退役）；与转职/技能/图鉴不冲突）
    "job_guide": r'^(?:\[At:[^\]]+\]\s*)?职业(?:\s+(\S+))?\s*$',
    # v137 『加入战斗』：同队伍成员并入正在进行中的副本战斗（handler：instance.py InstanceCmds.join_battle）
    "join_battle": r'^(?:\[At:[^\]]+\]\s*)?加入战斗(?:\s*|$)',
    "map_view": r'^(?:\[At:[^\]]+\]\s*)?(?:地图|周围)(?:\s*|$)',
    # v167.1 『区域』指令：当前区域可前往总览（world.py region_view，与装饰器 1:1）
    "region_view": r'^(?:\[At:[^\]]+\]\s*)?区域(?:\s*|$)',
    # v128.2: 『位置 0』/『位置0』旧捷径已移除——正则捕获 0 后缀仅为面板提示『赶路』入口，不再切换赶路模式
    "location_view": r'^(?:\[At:[^\]]+\]\s*)?位置(?:\s*0)?(?:\s*|$)',
    "hurry_view": r'^(?:\[At:[^\]]+\]\s*)?赶路(?:[\s\S]*)$',
    "deed_view": r'^(?:\[At:[^\]]+\]\s*)?地契(?:[\s\S]*)$',
    "deed_buy": r'^(?:\[At:[^\]]+\]\s*)?买房(?:[\s\S]*)$',
    "deed_sell": r'^(?:\[At:[^\]]+\]\s*)?卖房(?:[\s\S]*)$',
    "go_home": r'^(?:\[At:[^\]]+\]\s*)?回家(?:[\s\S]*)$',
    "go_out": r'^(?:\[At:[^\]]+\]\s*)?出门(?:[\s\S]*)$',
    "visit_home": r'^(?:\[At:[^\]]+\]\s*)?拜访(?:[\s\S]*)$',
    "home_storage": r'^(?:\[At:[^\]]+\]\s*)?仓库(?:[\s\S]*)$',
    "home_storage_take": r'^(?:\[At:[^\]]+\]\s*)?取出(?:[\s\S]*)$',
    # v104 P2(M22): 『移动』补回为『前往』别名——23 章指令表主指令=『移动 <地名或序号>』，双名共存
    # v128: 『前往开始/结束』移动模式开关已删；v128.2 起『位置 0』回复 0 切换赶路亦删（入口统一『赶路』指令）；(?!开始|结束) 负向断言保留防旧指令被 move 吞
    "move": r'^(?:\[At:[^\]]+\]\s*)?(?:前往|移动)(?!开始|结束)(?:\s*|$)',
    # O74：『返回 <地名>』v101.25i 已删（传送/前往替代）但旧指令仍被使用 → 提示 handler，
    # 不再只回标题零回复（playtest 第 7 次复现）
    "back_cmd": r'^(?:\[At:[^\]]+\]\s*)?返回(?:[\s\S]*)$',
    # O115：『问路 <地名>』补路线指引（MAP_CONNECTIONS 最短路径；曾只回标题零内容）
    "ask_way": r'^(?:\[At:[^\]]+\]\s*)?(?:问路|寻路)(?:[\s\S]*)$',
    "portal_activate": r'^(?:\[At:[^\]]+\]\s*)?(?:激活祭坛|激活)(?:\s*|$)',
    "portal_travel": r'^(?:\[At:[^\]]+\]\s*)?传送(?:\s*|$)',
    "portal_view": r'^(?:\[At:[^\]]+\]\s*)?(?:祭坛|方碑)(?:\s*|$)',
    "quest_view": r'^(?:\[At:[^\]]+\]\s*)?(?:任务|主线)(?:\s*|$)',
    "reputation": r'^(?:\[At:[^\]]+\]\s*)?声望(?!商店)(?:\s*|$)',
    "rep_shop": r'^(?:\[At:[^\]]+\]\s*)?声望商店(?:\s+\S+)?$',
    "rest": r'^(?:\[At:[^\]]+\]\s*)?住宿(?:\s*|$)',
    "rest_camp": r'^(?:\[At:[^\]]+\]\s*)?休息(?:\s*|$)',
    # v101.16 裸数字优先 NPC 对话（priority=100 高于快捷指令；同 pattern 双注册，gate 判定覆盖）
    "npc_quick_dialog": r'^(?:\[At:[^\]]+\]\s*)?[0-9０-９]\d?$',
    # v104 M24 P2-2：『交任务』无命中（策划案 23 章:182 主指令）→ 补别名
    "turn_in": r'^(?:\[At:[^\]]+\]\s*)?(?:交付任务|交任务)(?:\s*|$)',
    "instance_cmd": r'^(?:\[At:[^\]]+\]\s*)?副本(?!地图)(?:[\s\S]*)$',
    # v105 M24 同步：instance_advance 装饰器已放宽『深入3层』（不带"第"，并行任务 M04/M19 改动），
    # 静态表必须与装饰器 1:1（矩阵测试强校验）
    "instance_advance": r'^(?:\[At:[^\]]+\]\s*)?深入(?:(?:第\s*)?(\d+)\s*层)?(?:[层进]\s*)?$',
    "instance_map_view_cmd": r'^(?:\[At:[^\]]+\]\s*)?副本地图\s*$',
    # v104 M24 P2-4：『调查』空参数无响应（help 写『调查』但正则强制参数）→ 空参也命中，handler 内给格式提示
    "instance_investigate": r'^(?:\[At:[^\]]+\]\s*)?调查(?:\s+(.+?))?\s*$',
    "instance_retreat": r'^(?:\[At:[^\]]+\]\s*)?撤退\s*$',
    # v173.3 意见#87：撤退二次确认（放弃副本进度）
    "instance_retreat_confirm": r'^(?:\[At:[^\]]+\]\s*)?确认撤退(?:\s*|$)',
    "instance_leave": r'^(?:\[At:[^\]]+\]\s*)?离开副本\s*$',
    "quest_accept": r'^(?:\[At:[^\]]+\]\s*)?接取(?:\s*|$)',
    # v116：放弃进行中的支线/每日任务（主线不可放弃）
    "quest_abandon": r'^(?:\[At:[^\]]+\]\s*)?放弃(?:\s*(\d+))?\s*$',
    "interact_prop": r'^(?:\[At:[^\]]+\]\s*)?交互(?:\s*|$)',
    "talk_choice": r'^(?:\[At:[^\]]+\]\s*)?(?:对话|继续|结束对话|再见|告辞)(?:[\s\S]*)$',
    # v96 停服全局 gate（base.py _maint_gate）：匹配空串/At/引用消息前缀，拦截所有游戏指令；
    # 不参与指令互斥矩阵（不匹配任何指令正文），表内保留以与装饰器 1:1 对齐。
    "_maint_gate": r'^(?:\[At:[^\]]+\]\s*)?(?:\[At:全体成员\]\s*)?(?:\[引用消息[^\]]*\]\s*)?',
}


# ============================================================
# 派生：声明表 → 有效表（与 `_LITERAL_REGEX` 合并）
# ⚠️ 本文件保持**标准库 only**：测试用 importlib 直载本模块
#    （`test_v87_command_matrix.py`），不能出现包内相对导入。
# ============================================================

def _combine_patterns(patterns):
    """多条正则合成一条（与框架 `command.combine_patterns` **同语义**）。

    此处不 import 框架，是为了让本表能被独立加载（测试直载 / 工具脚本）。
    两边一致性由 `tests/test_v181_command_declaration.py` 断言锁死（防漂移）。
    """
    pats = [p for p in (patterns or ()) if p]
    if not pats:
        return ""
    if len(pats) == 1:
        return pats[0]
    return "|".join("(?:%s)" % p for p in pats)


def _declared_patterns():
    """读声明表派生 `{key: 正则}`。

    文件缺失/损坏 → 返回空表（本表仍可用；真正注册用的 `@declared` 会 fail-closed 抛错，
    所以坏掉不会被静默忽略）。
    """
    import json
    import os
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "command_specs.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    out = {}
    for k, v in (data or {}).items():
        pats = v.get("patterns", v.get("pattern")) if isinstance(v, dict) else v
        if isinstance(pats, str):
            pats = [pats]
        combined = _combine_patterns(pats)
        if combined:
            out[str(k)] = combined
    return out


_DECLARED_REGEX = _declared_patterns()

# 双源检测：同名 key 出现在声明表与字面量表里 = 迁移做了一半 → 必须为空（门禁断言）
OVERLAP_KEYS = sorted(set(_DECLARED_REGEX) & set(_LITERAL_REGEX))

# 有效表（调用方零改动：`COMMAND_REGEX` 名字与形状不变）
COMMAND_REGEX = {**_DECLARED_REGEX, **_LITERAL_REGEX}
