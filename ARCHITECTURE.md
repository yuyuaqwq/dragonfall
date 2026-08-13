# 《剑与魔法》重构架构设计（v46 → 分层架构）

> ⚠️ **v110 审计现状注记（2026-08-14）**：本文档为 v46/v47 重构初稿，细节已与现状脱节，仅分层总览与依赖方向仍准确：
> - 测试：原述"19 文件/227 断言"，现状 `tests/` 下 `test_*.py` 共 **124 个**（另 conftest + 3 个审计脚本），全量回归 `scripts/run_all_tests.py`（约 9 分钟）；
> - 命令层：原述 9 文件，现状 **12 个**（新增 gm.py / instance.py / talk_actions.py）；
> - core 层：原清单缺 ~20 个现行模块（battle_mech / battle_conds / affix_effects / achievement_conds / dialogue_conds / world_event_templates / time_weather / class_sets / food_effects / event_templates / race_talent_display / title_bonus / title_conds / hidden_cond / enchant / runes / factions / mounts / pets / wild 等）；
> - services/ 目录已不存在（编排职责并入 commands 层）。
> 详细分层/依赖以 `DEVELOPMENT.md`（开发规范总纲）与代码为准，本文档待重写。

> 目标：高内聚低耦合、可扩展、每层可独立单元测试。
> 前提：**删档**，移除全部迁移/兼容代码与一次性脚本。

## 一、分层总览

```
dragonfall/
├── main.py                  # AstrBot 入口：class Main(star.Star, *CommandMixins) —— 只做装配
├── metadata.yaml
├── game/
│   ├── data/                # 【数据层】纯静态内容（无逻辑、无IO）
│   ├── core/                # 【核心层】纯业务逻辑（无IO，可单测）
│   ├── store/               # 【存储层】SQLite Repository（唯一碰 DB 的层）
│   ├── services/            # 【服务层】跨领域编排（组合 core + store）
│   └── commands/            # 【命令层】QQ 交互薄层（解析+格式化，调 services/store）
└── tests/                   # 按模块单元测试 + conftest 共享脚手架
```

**依赖方向（单向）**：data ← core ← store ← services ← commands ← main
- data 不依赖任何层
- core 只依赖 data
- store 只依赖 data（+ sqlite）
- services 依赖 core + store
- commands 依赖 services + store + core + data
- main 只做 Mixin 装配

## 二、数据层 game/data/

| 文件 | 内容（从 content.py 迁出） |
|---|---|
| `index.py` | pinyin_id / build_index / resolve / display / _INDEXES |
| `classes.py` | CLASSES |
| `maps.py` | MAPS / MAP_BY_ID / MAP_AREAS / AREA_ENTRY / MAP_CONNECTIONS / HIDDEN_MAP_UNLOCK / ENCY_* |
| `monsters.py` | MONSTER_SKILLS / monster_skills_pool |
| `skills.py` | PLAYER_SKILLS / BRANCH_SKILLS |
| `equipment.py` | EQUIP_SLOTS / QUALITY / QUALITY_ORDER / WEAPON_TYPES / WEAPON_NAME_SUFFIX / WEAPON_FLAVOR / EQUIP_NAME_PREFIX / EQUIP_NAME_SUFFIX / AFFIX_* |
| `items.py` | ITEMS / MATERIALS |
| `npcs.py` | NPCS |
| `quests.py` | MAIN_QUESTS / SIDE_QUESTS / DAILY_QUESTS |
| `shop.py` | SHOP_ITEMS / SHOP_WEAPONS |
| `factions.py` | FACTIONS / FACTION_ORDER / REPUTATION_TIERS / AREA_FACTION / CHRONICLES |
| `fishing.py` | FISHING_SPOTS / FISH_POOL / FISH_WEIGHTS |
| `craft.py` | CRAFT_RECIPES / CRAFT_RECIPE_ALIASES |
| `sets.py` | SET_THEMES / SET_CHANCE / SETS / CLASS_SET_STAGES / CLASS_SET_THEMES / CLASS_SET_THEMES 装配 |
| `runes.py` | RUNES / RUNE_CONFLICTS / RUNE_DROP / RUNE_EFFECT_NAMES / RUNE_LEVEL_ROMAN / ENCHANT_STONES |
| `enchant.py` | ENCHANT_SLOTS / ENCHANT_RECIPES / ENCHANT_CRIT_CHANCE / ENCHANT_MAX_VALUE / ENCHANT_EFFECT_NAMES |
| `enhance.py` | ENHANCE_TABLE / MAX_ENHANCE / ENHANCE_FAIL_DROP / ENHANCE_SMITH_MAPS |
| `portals.py` | PORTALS |
| `gather.py` | CAMP_SPOTS / MINE_SPOTS |
| `events.py` | EXPLORE_EVENTS / EVENT_WEIGHT_SUM / WORLD_EVENT_POOL / AUCTION_POOL / WORLD_BOSS_POOL |
| `titles.py` | TITLES |
| `pets.py` | PET_POOL |
| `mounts.py` | MOUNT_POOL / MOUNT_BY_KEY / MOUNT_DROP_ELITE / MOUNT_DROP_BOSS |
| `alchemy.py` | ALCHEMY_RECIPES |
| `guild.py` | GUILD_CONFIG |
| `__init__.py` | 聚合导出（`from game.data import *` 兼容 `import content as C`） |

## 三、核心层 game/core/

| 文件 | 内容 |
|---|---|
| `stats.py` | monster_stats / equip_stats / exp_to_next / monster_exp / monster_gold |
| `drops.py` | _stage_for_lv / roll_blueprint / roll_drop / generate_equip / build_monster / roll_affixes / _affix_base_value |
| `craft.py` | craft_recipe_make / craft_recipe_search / craft_recipes_by_material / craft_recipes_for_level |
| `enchant.py` | enchant_value / enchant_match_material |
| `runes.py` | rune_value / rune_conflict / rune_item |
| `fishing.py` | roll_fish |
| `events.py` | roll_explore_event |
| `pets.py` | make_pet_egg / pet_exp_need |
| `mounts.py` | make_mount_rein / roll_mount_drop |
| `portals.py` | portal_cost |
| `factions.py` | faction_reputation_tier |
| `engine.py` | （原 game/engine.py 不动）player stats / damage / skills |
| `battle.py` | （原 game/battle.py 不动）Battle 类 |
| `__init__.py` | 聚合导出 |

## 四、存储层 game/store/

| 文件 | 内容（从 db.py 拆分） |
|---|---|
| `connection.py` | DB_PATH / _connect / _lock / init_db（建表） |
| `players.py` | create_player / get_player / update_player / top_players / all_players / find_player_by_name / get_skill_bar / set_skill_bar / get_portals / add_portal / player_groups |
| `inventory.py` | _key_to_id / add_item / get_inventory / count_item / remove_item |
| `quests.py` | get_quests / save_quests |
| `battle_state.py` | save_battle / get_battle / clear_battle |
| `stats.py` | init_stats / bump_stats / get_stats / set_achievement / get_achievements |
| `social.py` | 声望 / 签到 / 市场 / 组队 / 公会 / 宠物 |
| `world.py` | 图鉴 / 到访 / 世界事件 / event_state / 钓鱼 |
| `feedback.py` | 意见箱 |
| `__init__.py` | 聚合导出（db.xxx 兼容） |

## 五、服务层 game/services/

> ⚠️ **未实施（v47 进度 65% 时的状态）**：命令层目前直接调 store/core。
> 未来若出现跨领域编排重复，再抽 services 层（注册/转职/战斗结算/锻造/公会等编排）。

## 六、命令层 game/commands/

| 文件 | 命令组（Mixin 类，供 Main 继承） |
|---|---|
| `base.py` | CommandBase：_uid/_player/_strip_cmd/分页/格式化工具 + _find_handler/_run_shortcut（快捷指令，注册表优先、静态表回退） |
| `player.py` | PlayerCmds：注册/角色/排行/转职/称号/属性/加点/洗点/战力/技能系列/快捷 |
| `world.py` | WorldCmds：地图/移动/传送/方碑/NPC/任务/每日/交任务/休息/住宿/传说/编年史 |
| `combat.py` | CombatCmds：探索/攻击/技能/防御/逃跑/战斗结算/讨伐/PVP |
| `economy.py` | EconomyCmds：背包/装备/卸下/使用/出售/商店/购买/锻造/配方/强化/附魔/套装/图鉴/钓鱼/采集/采矿/炼金 |
| `social.py` | SocialCmds：公会系列/组队/市场/上架/下架/购入/宠物/坐骑/世界事件/拍卖/竞拍 |
| `misc.py` | MiscCmds：签到/百科/称号/成就/意见/帮助 |
| `_registry.py` | COMMAND_REGEX 静态正则表（方法名→正则，自动生成，快捷指令测试回退用） |
| `__init__.py` | 导出全部 Mixin |

**装配**：`main.py` 的 `class Main(star.Star, PlayerCmds, WorldCmds, CombatCmds, EconomyCmds, SocialCmds, MiscCmds, CommandBase)`，AstrBot 加载机制不变。

## 七、测试 tests/

```
tests/
├── conftest.py                  # 共享脚手架：FakeEvent/run/clean_db/make_player + 路径自动配置
│                                # ── data 层（按数据族拆 5）──
├── test_data_characters.py      # 角色族：职业/技能/分支/符文/称号                      14 断言
├── test_data_items.py           # 物品族：物品/材料/套装/配方/炼金/附魔                13 断言
├── test_data_world.py           # 世界族：地图/连接/NPC/传送/钓鱼/任务/事件            13 断言
├── test_data_bestiary.py        # 生物族：怪物/地区怪/怪物技能/坐骑/宠物/Boss           10 断言
├── test_data_registry.py        # 索引族：ID索引双向/resolve/display/改名映射          10 断言
│                                # ── core 层（按逻辑族拆 4）──
├── test_core_engine.py          # 数值引擎：经验曲线/怪物数值                           7 断言
├── test_core_gear.py            # 装备族：装备生成/符文强化                             6 断言
├── test_core_world.py           # 世界族：钓鱼/传送                                     3 断言
├── test_core_index.py           # 索引族：resolve/display/pinyin_id                    5 断言
│                                # ── store 层（按存储域拆 3）──
├── test_store_players.py        # 玩家族：players档案/inventory背包（v46 ID存储）      12 断言
├── test_store_progress.py       # 进度族：quests任务/battle_state战斗状态              5 断言
├── test_store_meta.py           # 统计族：feedback/stats/world_event/bestiary图鉴      4 断言
│                                # ── commands 层（按功能域，1:1）──
├── test_commands_layer.py       # commands 基础流程：注册→探索→攻击→背包→锻造→快捷     16 断言
├── test_commands_battle.py      # 战斗域：Battle状态机/buff/分支机制/数值铁律/PVP      34 断言
├── test_commands_economy.py     # 经济域：背包筛选/锻造/商店/市场/图鉴/装备             19 断言
├── test_commands_world.py       # 世界域：地图/移动/传送/NPC/任务/事件/钓鱼/采集        14 断言
├── test_commands_social.py      # 社交域：公会/宠物/坐骑/意见/签到/成就                 13 断言
├── test_commands_skills.py      # 技能域：属性/加点/技能/升级/转职/声望/战力            12 断言
└── test_command_parse.py        # 解析域：命令矩阵互斥/免空格/序号分流/fuzz            17 断言
```

运行：`python -X utf8 tests/test_*.py`（无需 pytest，直跑脚本）。共 19 文件 / 227 断言。

**v47 彻底重写完成（2026-08-05）**：旧版 58 个 `test_vXX*.py` 版本号测试全部删除，重写为按模块/功能域组织的 19 个测试。组织原则：**命令层 1:1 对应命令文件**（改动最频繁、最需要精确定位）；**底层按数据族/逻辑族分组**（data 26 模块→5 族、core 17 模块→4 族、store 9 模块→3 族），避免碎片化壳文件。命令矩阵测试从 `game/commands/*.py` 源码动态提取 @filter.regex，防双触发回归自动生效。

**v48 全 key 转 ID 完成（2026-08-05）**：所有内容表 key 统一转稳定 pinyin ID（`狼皮`→`mat_lang_pi`），值保留 `name` 字段做显示名；交叉引用全改 ID；`_INDEXES` 15 域（新增 classes/runes/monster_skills/alchemy/quality/weapon_types）；兼容层 `C.resolve(域, 中文名)`→ID、`C.display(域, ID)`→中文。命令层适配原则：玩家输入 resolve → 内部存 ID → 显示用 display；store 层保持读回中文名、engine 查表前统一 resolve。修复 2 个隐藏 bug（alchemy 畸形 product ID、_INDEXES.items 双重转 ID）及 `f"mat_{中文}"` 双重前缀、矿石过滤失效、品质档中文残留、class_name ID 与 WEAPON_TYPES 中文值比对失败、class_sets 中文 key 重复注入等问题。改名/翻译只动 name 字段，key 永不变。

## 八、删除清单（已执行 ✅）

- ✅ main.py 中 4 个 `_migrate_*` 方法（~470 行）
- ✅ db.py 中 `_migrate_legacy` / `_has_global_schema`（124 行）
- ✅ 一次性脚本：_split_content/_split_db/_split_main/_inject_regex/_gen_registry/_extract_regex/_fix_core_*/_fix_store_imports/_add_core_imports/_verify_main/_debug_craft/convert/ext_highlevel/ext_nations
- ✅ test_migrate.db（迁移测试库）
- ✅ **旧版 52 个 test_vXX + 6 个 test_commands/test_e2e/test_regex/test_move_num/test_nospace 全部删除**，由 tests/ 10 个按域测试替代

## 九、兼容策略

- `game/__init__.py` 聚合导出 data/core/store/commands 全部符号
- 保留 `import game.content as C` / `from game import content as C` 路径（content.py 变薄聚合层）
- 保留 `db.xxx` 调用（store/__init__.py 聚合）
- 命令 Mixin 继承后 @filter.regex 行为不变，AstrBot 加载机制不变
