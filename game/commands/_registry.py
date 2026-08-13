# -*- coding: utf-8 -*-
"""命令正则静态注册表（半自动维护：静态表 + 装饰器需同步）。

本表原由脚本自动生成，现为人工维护的静态表（方法名 → @filter.regex 正则）。
用途：测试环境/注册表缺失时的快捷指令校验、_GameCmdFilter 停服 gate 拦截、
快捷转发回退（base.py _static_handlers）。

⚠️ 半自动维护铁律：新增/修改/删除任何 @filter.regex 命令（含别名），
必须同步本表，否则 gate 拦截与回退会失真。同步检查：
  1. 启动校验：插件加载时 main.py 自动对比「已注册公开 handler 名」与
     本表键集，漂移以 WARNING 日志输出（见 main.py _fix_handler_module_paths）。
  2. 强校验：python tests/test_v87_command_matrix.py（表与装饰器 1:1 逐条相等 + 互斥矩阵）
  3. 解析回归：python tests/test_command_parse.py（命令矩阵互斥/免空格/序号）

真实 AstrBot 运行以全局注册表（star_handlers_registry）为准，本表仅供上述回退场景。
"""

COMMAND_REGEX = {
    # v104 审计后由 M24 命令互斥矩阵测试（tests/test_v87_command_matrix.py）强校验：
    # 静态表必须与 game/commands/*.py 的 @filter.regex 装饰器 1:1 一致（键集合+模式逐条相等）。
    "achievements": r'^(?:\[At:\d+\]\s*)?成就(?:\s*(领取|列表)?(?:\s*([^\s]+))?\s*|$)',
    "add_attr": r'^(?:\[At:\d+\]\s*)?加点(?:\s*|$)',
    "alchemy": r'^(?:\[At:\d+\]\s*)?炼金(?:[\s\S]*)$',
    "alchemy_craft": r'^(?:\[At:\d+\]\s*)?合成(?:\s*|$)',
    "attack": r'^(?:\[At:\d+\]\s*)?攻击(?:\s*|$)',
    "attributes": r'^(?:\[At:\d+\]\s*)?属性(?:\s*|$)',
    "auction": r'^(?:\[At:\d+\]\s*)?拍卖(?:\s*|$)',
    "bag_filter": r'^(?:\[At:\d+\]\s*)?背包筛选(?:[\s\S]*)$',
    "bestiary": r'^(?:\[At:\d+\]\s*)?图鉴(?:\s*|$)',
    "bid": r'^(?:\[At:\d+\]\s*)?竞拍(?:\s*|$)',
    "buy": r'^(?:\[At:\d+\]\s*)?购买(?:\s*|$)',
    "chronicle": r'^(?:\[At:\d+\]\s*)?编年史(?:\s*|$)',
    "craft": r'^(?:\[At:\d+\]\s*)?锻造(?:[\s\S]*)$',
    "craft_commission": r'^(?:\[At:\d+\]\s*)?代工(?:[\s\S]*)$',
    # v104 M24 P2-1：『每日副业』前缀误触『每日』面板——负向断言收窄，
    # 别名『每日副业/今日副业』注册到 daily_prof（19 章旧称呼，策划案 §六统一为『副业任务』）
    "daily": r'^(?:\[At:\d+\]\s*)?每日(?!副业)(?:\s*|$)',
    "defend": r'^(?:\[At:\d+\]\s*)?防御(?:\s*|$)',
    "enchant": r'^(?:\[At:\d+\]\s*)?附魔(?:\s*|$)',
    "encyclopedia": r'^(?:\[At:\d+\]\s*)?百科(?:\s*|$)',
    "enhance": r'^(?:\[At:\d+\]\s*)?强化(?:\s*|$)',
    "equip": r'^(?:\[At:\d+\]\s*)?装备(?:\s*|$)',
    "evolve": r'^(?:\[At:\d+\]\s*)?转职(?!重置)(?:\s*|$)',
    "explore": r'^(?:\[At:\d+\]\s*)?探索(?:\s*|$)',
    "feedback_cmd": r'^(?:\[At:\d+\]\s*)?意见(?:[\s\S]*)$',
    "find_npc": r'^(?:\[At:\d+\]\s*)?找(?:\s*|$)',
    "time_cmd": r'^(?:\[At:\d+\]\s*)?时间(?:指令)?(?:\s*|$)',
    "wild_notes": r'^(?:\[At:\d+\]\s*)?见闻录(?:\s*|$)',
    "fishing": r'^(?:\[At:\d+\]\s*)?垂钓(?:选择|点)?(?:\s*|$)',
    "flee": r'^(?:\[At:\d+\]\s*)?逃跑(?:\s*|$)',
    "gather": r'^(?:\[At:\d+\]\s*)?采集(?:\s*|$)',
    "guild_create_cmd": r'^(?:\[At:\d+\]\s*)?创建公会(?:\s*|$)',
    "guild_disband_cmd": r'^(?:\[At:\d+\]\s*)?解散公会(?:\s*|$)',
    "guild_info": r'^(?:\[At:\d+\]\s*)?公会(?!签到|任务|捐献|排行|创建|加入|退出|解散)(?:\s*.*|$)',
    "guild_join_cmd": r'^(?:\[At:\d+\]\s*)?加入公会(?:\s*|$)',
    "guild_leave_cmd": r'^(?:\[At:\d+\]\s*)?退出公会(?:\s*|$)',
    "guild_rank": r'^(?:\[At:\d+\]\s*)?公会排行(?:\s*|$)',
    "guild_sign": r'^(?:\[At:\d+\]\s*)?公会签到(?:\s*|$)',
    "guild_task": r'^(?:\[At:\d+\]\s*)?公会任务(?:\s*|$)',
    "guild_donate_cmd": r'^(?:\[At:\d+\]\s*)?公会捐献(?:\s*|$)',
    # v105 M24 P3-2：『帮助中心』前缀误触 → 负向断言收窄（与装饰器同步）
    "help_cmd": r'^(?:\[At:\d+\]\s*)?(?:帮助|help)(?!中心)(?:\s*|$)',
    "hunt_boss": r'^(?:\[At:\d+\]\s*)?讨伐(?:\s*|$)',
    "inventory": r'^(?:\[At:\d+\]\s*)?(?:背包|物品)(?!详情|筛选)(?:\s*.*)?$',
    "item_detail": r'^(?:\[At:\d+\]\s*)?物品详情(?:[\s\S]*)$',
    "item_view_mode_cmd": r'^(?:\[At:\d+\]\s*)?物品详情(?:开始|结束)(?:\s*|$)',
    "leaderboard": r'^(?:\[At:\d+\]\s*)?排行(?:[\s\S]*)$',
    "map_view": r'^(?:\[At:\d+\]\s*)?(?:地图|位置|周围)(?:\s*|$)',
    "deed_view": r'^(?:\[At:\d+\]\s*)?地契(?:[\s\S]*)$',
    "deed_buy": r'^(?:\[At:\d+\]\s*)?买房(?:[\s\S]*)$',
    "deed_sell": r'^(?:\[At:\d+\]\s*)?卖房(?:[\s\S]*)$',
    "go_home": r'^(?:\[At:\d+\]\s*)?回家(?:[\s\S]*)$',
    "go_out": r'^(?:\[At:\d+\]\s*)?出门(?:[\s\S]*)$',
    "visit_home": r'^(?:\[At:\d+\]\s*)?拜访(?:[\s\S]*)$',
    "home_storage": r'^(?:\[At:\d+\]\s*)?仓库(?:[\s\S]*)$',
    "home_storage_take": r'^(?:\[At:\d+\]\s*)?取出(?:[\s\S]*)$',
    "market": r'^(?:\[At:\d+\]\s*)?市场(?:\s*|$)',
    "market_buy": r'^(?:\[At:\d+\]\s*)?购入(?:\s*|$)',
    "market_sell": r'^(?:\[At:\d+\]\s*)?上架(?:\s*|$)',
    "market_unsell": r'^(?:\[At:\d+\]\s*)?下架(?:\s*|$)',
    "stall": r'^(?:\[At:\d+\]\s*)?摆摊(?:[\s\S]*)$',
    "stall_close": r'^(?:\[At:\d+\]\s*)?收摊(?:[\s\S]*)$',
    "stall_view": r'^(?:\[At:\d+\]\s*)?摊位(?:[\s\S]*)$',
    "stall_exchange": r'^(?:\[At:\d+\]\s*)?换(?:[\s\S]*)$',
    "mining": r'^(?:\[At:\d+\]\s*)?挖掘(?:\s*|$)',
    "mount_cmd": r'^(?:\[At:\d+\]\s*)?(?:坐骑|骑乘|下马)(?:\s*|$)',
    # v104 P2(M22): 『移动』补回为『前往』别名——23 章指令表主指令=『移动 <地名或序号>』，双名共存
    # （v101.17 移动模式开关『前往开始/结束』不受影响；修正 v101.17 删除"移动"后主指令缺失的问题）
    "move": r'^(?:\[At:\d+\]\s*)?(?:前往|移动)(?!开始|结束)(?:\s*|$)',
    # v104 P2(M22): 移动模式开关——23 章指令表『移动开始/结束』仍为移动模式开关（v104 修复说明原话），
    # 正则扩为 (?:前往|移动)(?:开始|结束)；『前往开始 2』等尾参由 handler 内报格式错误
    "move_mode_cmd": r'^(?:\[At:\d+\]\s*)?(?:前往|移动)(?:开始|结束)(?:\s*|$)',
    "party": r'^(?:\[At:\d+\]\s*)?(?:组队|队伍)(?:[\s\S]*)$',
    "party_leave": r'^(?:\[At:\d+\]\s*)?退队(?:\s*|$)',
    "pet_feed": r'^(?:\[At:\d+\]\s*)?喂养(?:\s*|$)',
    "pet_release": r'^(?:\[At:\d+\]\s*)?放生(?:\s*|$)',
    "pet_rename": r'^(?:\[At:\d+\]\s*)?宠物改名(?:\s*|$)',
    "pet_view": r'^(?:\[At:\d+\]\s*)?宠物(?!改名)(?:\s*|$)',
    "portal_activate": r'^(?:\[At:\d+\]\s*)?(?:激活祭坛|激活)(?:\s*|$)',
    "portal_travel": r'^(?:\[At:\d+\]\s*)?传送(?:\s*|$)',
    "portal_view": r'^(?:\[At:\d+\]\s*)?(?:祭坛|方碑)(?:\s*|$)',
    "power": r'^(?:\[At:\d+\]\s*)?战力(?:\s*|$)',
    # v105 M24 P3-2：『角色扮演』前缀误触 → 负向断言收窄（与装饰器同步）
    "profile": r'^(?:\[At:\d+\]\s*)?(?:角色|我的角色)(?!扮演)(?:\s*|$)',
    "quest_view": r'^(?:\[At:\d+\]\s*)?(?:任务|主线)(?:\s*|$)',
    "recipe_list": r'^(?:\[At:\d+\]\s*)?配方(?:\s*|$)',
    # v105 M24 P3-2：『注册表』前缀误触 → 负向断言收窄（与装饰器同步）
    "register": r'^(?:\[At:\d+\]\s*)?注册(?!表)(?:\s*|$)',
    "reputation": r'^(?:\[At:\d+\]\s*)?声望(?!商店)(?:\s*|$)',
    "rep_shop": r'^(?:\[At:\d+\]\s*)?声望商店(?:\s+\S+)?$',
    "reset_attr": r'^(?:\[At:\d+\]\s*)?洗点(?:\s*|$)',
    "reset_skill": r'^(?:\[At:\d+\]\s*)?技能洗点(?:\s*|$)',
    "evolve_reset": r'^(?:\[At:\d+\]\s*)?转职重置(?:[\s\S]*)$',
    "rest": r'^(?:\[At:\d+\]\s*)?住宿(?:\s*|$)',
    "rest_camp": r'^(?:\[At:\d+\]\s*)?休息(?:\s*|$)',
    "sell": r'^(?:\[At:\d+\]\s*)?出售(?:\s*|$)',
    "set_view": r'^(?:\[At:\d+\]\s*)?套装(?:\s*|$)',
    "shop": r'^(?:\[At:\d+\]\s*)?商店(?:\s*|$)',
    "shortcut": r'^(?:\[At:\d+\]\s*)?(?:快捷绑定|快捷列表|快捷删除|快捷清除|快捷)(?:[\s\S]*)$',
    "shortcut_trigger": r'^(?:\[At:\d+\]\s*)?[0-9０-９]\d*\s*$',
    # v101.16 裸数字优先 NPC 对话（priority=100 高于快捷指令；同 pattern 双注册，gate 判定覆盖）
    "npc_quick_dialog": r'^(?:\[At:\d+\]\s*)?[0-9０-９]\d?$',
    # v105 M24 P3-2：『签到机』前缀误触 → 负向断言收窄（与装饰器同步）
    "signin": r'^(?:\[At:\d+\]\s*)?签到(?!机)(?:\s*|$)',
    "skill": r'^(?:\[At:\d+\]\s*)?技能(?!详情|学习|升级|洗点|栏)(?:[\s\S]*)$',
    "skill_bar_set": r'^(?:\[At:\d+\]\s*)?设置技能(?:\s*|$)',
    "skill_bar_view": r'^(?:\[At:\d+\]\s*)?技能栏(?:\s*|$)',
    "skill_detail": r'^(?:\[At:\d+\]\s*)?技能详情(?:[\s\S]*)$',
    "skill_learn": r'^(?:\[At:\d+\]\s*)?技能学习(?:[\s\S]*)$',
    "skill_upgrade": r'^(?:\[At:\d+\]\s*)?技能升级(?:[\s\S]*)$',
    "titles": r'^(?:\[At:\d+\]\s*)?称号(?:\s*|$)',
    # v104 M24 P2-2：『交任务』无命中（策划案 23 章:182 主指令）→ 补别名
    "turn_in": r'^(?:\[At:\d+\]\s*)?(?:交付任务|交任务)(?:\s*|$)',
    "unequip": r'^(?:\[At:\d+\]\s*)?卸下(?:\s*|$)',
    "use": r'^(?:\[At:\d+\]\s*)?使用(?:\s*|$)',
    "world_event": r'^(?:\[At:\d+\]\s*)?事件(?:\s*|$)',
    "cooking": r'^(?:\[At:\d+\]\s*)?烹饪(?!列表)(?:\s*|$)',
    "cooking_list": r'^(?:\[At:\d+\]\s*)?烹饪列表(?:[\s\S]*)$',
    "profession_view": r'^(?:\[At:\d+\]\s*)?副业(?!任务)(?:[\s\S]*)$',
    "prof_forget": r'^(?:\[At:\d+\]\s*)?遗忘副业(?:[\s\S]*)$',
    "daily_prof": r'^(?:\[At:\d+\]\s*)?(?:副业任务|每日副业|今日副业)(?:\s*|$)',
    "instance_cmd": r'^(?:\[At:\d+\]\s*)?副本(?!地图)(?:[\s\S]*)$',
    # v96 补充缺失条目（停服 gate 需要完整覆盖）
    "wish": r'^(?:\[At:\d+\]\s*)?许愿(?:[\s\S]*)$',
    "honor_shop": r'^(?:\[At:\d+\]\s*)?荣誉(?:[\s\S]*)$',
    "learn": r'^(?:\[At:\d+\]\s*)?学习(?:[\s\S]*)$',
    # v105 M24 同步：instance_advance 装饰器已放宽『深入3层』（不带"第"，并行任务 M04/M19 改动），
    # 静态表必须与装饰器 1:1（矩阵测试强校验）
    "instance_advance": r'^(?:\[At:\d+\]\s*)?深入(?:(?:第\s*)?(\d+)\s*层)?(?:[层进]\s*)?$',
    "instance_map_view_cmd": r'^(?:\[At:\d+\]\s*)?副本地图\s*$',
    # v104 M24 P2-4：『调查』空参数无响应（help 写『调查』但正则强制参数）→ 空参也命中，handler 内给格式提示
    "instance_investigate": r'^(?:\[At:\d+\]\s*)?调查(?:\s+(\S+))?\s*$',
    "instance_retreat": r'^(?:\[At:\d+\]\s*)?撤退\s*$',
    "instance_leave": r'^(?:\[At:\d+\]\s*)?离开副本\s*$',
    "races": r'^(?:\[At:\d+\]\s*)?种族(?:\s*|$)',
    "build_view": r'^(?:\[At:\d+\]\s*)?流派(?:[\s\S]*)$',
    "delete_account": r'^(?:\[At:\d+\]\s*)?注销(?:[\s\S]*)$',
    "quest_accept": r'^(?:\[At:\d+\]\s*)?接取(?:\s*|$)',
    "interact_prop": r'^(?:\[At:\d+\]\s*)?交互(?:\s*|$)',
    "talk_choice": r'^(?:\[At:\d+\]\s*)?(?:对话|继续|结束对话|再见|告辞)(?:[\s\S]*)$',
    # v96 GM 指令（gm_ 前缀，不进 gate 过滤）
    "gm_maintenance": r'^(?:\[At:\d+\]\s*)?gm_停服(?:[\s\S]*)$',
    "gm_open": r'^(?:\[At:\d+\]\s*)?gm_开服(?:[\s\S]*)$',
    "gm_status": r'^(?:\[At:\d+\]\s*)?gm_状态(?:[\s\S]*)$',
    "gm_broadcast": r'^(?:\[At:\d+\]\s*)?gm_广播(?:[\s\S]*)$',
    "gm_players": r'^(?:\[At:\d+\]\s*)?gm_玩家(?:[\s\S]*)$',
    "gm_query": r'^(?:\[At:\d+\]\s*)?gm_查询(?:[\s\S]*)$',
    "gm_give_gold": r'^(?:\[At:\d+\]\s*)?gm_发金币(?:[\s\S]*)$',
    "gm_give_item": r'^(?:\[At:\d+\]\s*)?gm_发物品(?:[\s\S]*)$',
    "gm_give_exp": r'^(?:\[At:\d+\]\s*)?gm_发经验(?:[\s\S]*)$',
    "gm_set_level": r'^(?:\[At:\d+\]\s*)?gm_设等级(?:[\s\S]*)$',
    "gm_teleport": r'^(?:\[At:\d+\]\s*)?gm_传送(?:[\s\S]*)$',
    "gm_stamina": r'^(?:\[At:\d+\]\s*)?gm_体力(?:[\s\S]*)$',
    "gm_rename": r'^(?:\[At:\d+\]\s*)?gm_改名(?:[\s\S]*)$',
    "gm_add_gm": r'^(?:\[At:\d+\]\s*)?gm_加GM(?:[\s\S]*)$',
    "gm_del_gm": r'^(?:\[At:\d+\]\s*)?gm_删GM(?:[\s\S]*)$',
    "gm_play": r'^(?:\[At:\d+\]\s*)?gm_play(?:[\s\S]*)$',
    "gm_help": r'^(?:\[At:\d+\]\s*)?gm_帮助(?:[\s\S]*)$',
    "gm_boss_dmg": r'^(?:\[At:\d+\]\s*)?gm_伤害(?:[\s\S]*)$',
    "gm_spy": r'^(?:\[At:\d+\]\s*)?gm_窥探(?:[\s\S]*)$',
    # v96 停服全局 gate（base.py _maint_gate）：匹配空串/At/引用消息前缀，拦截所有游戏指令；
    # 不参与指令互斥矩阵（不匹配任何指令正文），表内保留以与装饰器 1:1 对齐。
    "_maint_gate": r'^(?:\[At:\d+\]\s*)?(?:\[At:全体成员\]\s*)?(?:\[引用消息[^\]]*\]\s*)?',
}
