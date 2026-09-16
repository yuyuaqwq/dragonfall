# REFACTOR P4：命令层抽 services — 只读侦察 + 方案设计（wt_p4recon）

> 分支：`wt_p4recon`（worktree w7，与 master `30933c6` 同 commit） · 状态：**只读侦察 + 方案文档，未改任何 game/ 代码**
> 任务出处：26 子 agent 审计报告 12（`_archive_unused/architecture_audit_20260907/subagent-summary-12-*.txt`）+ `docs/archive/REFACTOR_PLAN_v181.md` P4 + `docs/archive/HANDOFF_v181_refactor.md` 实施队列「P4：命令层抽 services（BattleSettlement/Quest/Shop/Crafting/Profession…）」。
> 铁律：**行为零变化**；每批 py_compile + 相关单测全绿 + numeric 门禁；每批独立 commit（`v181.P4-*`）；数据/规则数值只进 data，行为逻辑进 service，命令只留解析 + 格式化。
> 本文档 commit 到 wt_p4recon 分支供主 agent 审阅；不合并、不动主仓、不动其它 worktree。

---

## 0. TL;DR（给执行批次的一句话）

建 **`game/services/`**（相对 `game/core/` 的对等目录，拿回 v47 分层蓝图里"服务层"的位置），每域一文件、**纯函数模块**（零类、零 Mixin、零装饰器），全部走 `db.*`/`game.reward`/`core`/`data`，**禁止 import commands/**（防环 + 命令依赖方向约束）。命令层只 import service 函数：本文件能搬的**同步纯编排**部分全搬，只留解析 + 守卫 + `yield`/广播 等 I/O 壳。

**P4-1 试点 = 抽 `game/services/quests.py`（QuestService 的最小可用子集）**：把命令层三处收敛过的每日任务结算单点 `_settle_daily_quest` + `_bump_daily_progress` + `daily` 抽取/衰减/发布 + 面板常量一起下沉，拆掉 `combat.py:25 from .world import _DAILY_META_KEYS, _settle_daily_quest` 这条跨命令文件私有函数 import（审计点 ✓），为 QuestService 全量（主线/支线/每日）打样板。理由与抽法见 §3。

**后续批次（按审计收益排序，逐 service 见 §4）**：P4-2 QuestService 全量（主线/支线/转职/发奖收敛）→ P4-3 ShopService（商店/购买/出售/交易）+ P4-4 CraftingService（强化/升级/宝石/符文/附魔/炼成 的"掷骰-结算"纯逻辑）→ P4-5 AuctionService → P4-6 PartyService + GuildService（social 域）→ P4-7 ProfessionService（副业等待/结算/彩蛋）→ P4-8 TravelService（move/撞怪）→ P4-9 BattleSettlementService（combat._handle_victory/_handle_defeat 510 行，**最后做**）。

> ⚠️ **试点为什么不是 `_handle_victory`**：它是全项目最厚单体（~510 行、几十条规则、async generator、yield 交互、跨 player/battle/instance 域、`self._*` 数十个）——直接啃 = 把"验证新 services 模式"和"啃最难一段"两件事混在一起，违背小步验证。先做小收敛点证明 services 层模式成立（import 方向/循环风险/文件组织/等价验证法），再回头按 service 逐个拆大块。

---

## 1. 侦察结论（本档全部证据：审计 12 + w7 现状直读）

### 1.1 命令层 5 大文件业务泄漏全貌（审计 12 复述 + w7 核对）

| 文件 | 行数 | 命令数 | 区间均跨 | 直连 SQL | 审计健康度 | w7 核对 |
|---|---|---|---|---|---|---|
| economy.py | 7757 | 45 | ~140 | 1 处（L5701 `_visited_maps` 手写 sqlite3，store 缺封装） | ❌ | 一致 |
| world.py | 5280 | 38 | ~130 | 0 | ❌ | 一致 |
| combat.py | 3304 | 14 | ~229 | 0 | ⚠️（战斗指令薄，但 `_handle_victory` 510 行最厚） | 一致 |
| player.py | 1912 | 21 | ~86 | 0 | ⚠️ | 一致 |
| social.py | 1574 | 33 | ~46 | 0（但 L21-26 直连 data/store 内部） | ⚠️（架构最正，缺业务层） | 一致 |

命令数（w7 `@filter.regex` 计数）：economy 45 / world 38 / combat 14 / player 22 / social 33（player.py 审计口径 21 因 handler 分布差异，不影响结论）。**没有一条命令是薄壳**：`combat._handle_victory` ~510 行、`world.move` ~583、`world.daily` ~607、`world.interact_prop` ~561、`economy.buy` ~473、`economy.shop+buy` 合计 ~660。

**跨文件耦合信号（w7 实测）**：
- `combat.py:25` `from .world import _DAILY_META_KEYS, _settle_daily_quest` —— 命令层互相 import **私有函数**（审计点，P4-1 试点正打中它）。
- `combat.py:26/27` `from .weekly import weekly_bump_kill` / `from .tower import tower_guard_on_kill` —— 命令层互相 import **顶层函数**（击杀推进周常/塔卫）。这些是"命令文件里的顶层业务函数被别文件消费"的同一族信号。
- `player.py:1489` `from .combat import CombatCmds`（局部，面板构建需要多类方法）；`instance.py:1520` `from .combat import pet_battle_status_note`（顶层函数）。
- `talk_actions.py`（对话动作注册表，命令层）通过 `world._do_join_class / _take_main_quest / _complete_side_quest / _offer_side_quests / _prof_active_check / _do_evolve_via_npc` 等 **Mixin 方法委托** 命令层。

**规则数值驻留命令层重灾区**（审计 12 全量，抽样已在 w7 直读核对）：
- economy：品质价系数 `SHOP_EQUIP_PRICE_MULT`（L67，`core/smith_stock.py:360` 注释自认同源）、装备生成价公式第 4 处副本（`_upgrade_recalc_equip` L174-243，core/drops 3 处）、强化石 key 字面量散 8 处（i_stone_*）、强化成功率手艺加成 `min(prof_lv,10)*0.005` + 精炼石 +0.25 + 祝福符石 +0.15、垂钓惊喜概率表 `_FISHING_SURPRISE_*`、疲劳常量 MINING_FATIGUE_THRESHOLD、采集限定条件词注册表 `_GATHER_COND_CHECKERS`。
- world：`DAILY_LIMIT=10`、`_DAILY_REPEAT_FACTORS=(1.0,0.6,0.3,0.1)`、`WISH_WELL_EGG_CHANCE=0.05`、`_teach_by_npc` 学费公式 `cost=max(500, need_lv*100)`（L3600）、`_travel_ambush` 本地概率档 0.30/0.18/0.08（与 core/constants MOVE_ENCOUNTER_CHANCE=0.25 双轨，L42 注释自曝历史 bug）。
- combat：`WORLD_BOSS_DOT_INTERVAL=4`、`WORLD_BOSS_DROPS` 按 Boss 中文名配掉落表（L80-87）、`_handle_victory` 内 exp 曲线系数 / 0.85^(-diff-3) / 组队+10% / 大吉小凶 ×1.10/0.90 / 图纸残页折算 {white:1,…orange:6} / PET_EGG_ROLL 等（几十条）。
- social：拍卖状态机全手写进 world_event event_state JSON 槽、`it["key"].startswith("mat_")` 捐献判定、宠物喂食 `d.get("type")=="鱼"` 判定。

### 1.2 已有样板（v135/v166/v140 抽好的 service，命令只做面板）

w7 直读三个样板模块形态（都是 **core/ 下单文件纯函数模块**，模块 docstring 写机制、常量表顶置、db 一律**函数体内惰性 import**）：

| 样板 | 位置 | 形态 | 命令层消费 |
|---|---|---|---|
| smith_stock（v135 铁匠铺共享货架） | `game/core/smith_stock.py` | 模块常量 + 纯函数（`town_level/get_smith_stock/buy_stock_item/smith_stock_price`） | `economy.py:24 from ..core import smith_stock as _ss`，面板调 `_ss.get_smith_stock`，购买调 `_ss.buy_stock_item` |
| shop_stock（v166 商店限购） | `game/core/shop_stock.py` | 同上（`check_and_consume/limit_label`），数据在 `game/data/shop_limit.py` | `economy.py:25 as _sshop` |
| wild_king（v140 野王体系） | `game/core/wild_king.py` | 同上（`wild_king_tick/explore_king/wild_king_on_kill/open_chest`），数据在 `game/data/wild_king_data.py` | `combat.py:28-30` import 后探索/击杀/开箱只接 wire |
| reward（v174 统一奖励） | `game/reward.py`（game 根，非 core） | 纯函数 `grant_reward(reward_dict, group_id, qq_id, player=, lines=)`，函数内惰性 import db | world/combat/talk_actions/weekly 全走它 |

**样板模式确认**：① 命令层 import 后只做解析+格式化 → 命令体显著变薄；② 数据/配置进 `game/data/`（shop_limit.py / wild_king_data.py 先例），规则常量留在 service 文件顶置或下沉 data，**不留在命令层**；③ `db` 只在函数体内延迟 import（防 core 层在 data/_assembly 构建期被 import 时循环——`core/__init__.py` 注释明确此铁律）；④ core 文件被 `content.py`（`from .core import *`）聚合 → 命令层可通过 `C.xxx` 或直接 from-import 调用。

### 1.3 分层现状与依赖方向（决定 services/ 放哪、能 import 什么）

w7 实测分层（`ARCHITECTURE.md` v47 蓝图 + 现状演化）：

```
data/（纯数据 dict，零函数零 import，_assembly 装配）← content.py 聚合 data+core
core/（纯逻辑执行器，33+ 文件；无 IO 铁律已松动为"db 函数内惰性 import"）
store/（SQLite Repository，唯一碰 DB；store/__init__.py 聚合，db.py 是薄聚合）
commands/（Mixin 命令层：base/world/combat/economy/player/social/instance/...）
main.py（class Main 装配）＋ game/reward.py（v174 统一奖励，实际已是"services 样板"，函数内惰性 import db/engine/title_bonus）
```

依赖实测：**commands/ 无任何被 data/core/store/engine/battle import 的记录**（§1.1 的跨文件 import 全部是 commands 内部互引）。core/ 已有 9 个模块函数内 `from .. import db`（achievements/achievement_conds/event_templates/exploration/instance_gate/item_templates/maps/poi_effects/rule_engine + shop_stock/title_bonus 等）——**"core 无 IO"实际已被 9+ 模块打破，项目已接受"core 函数内惰性 db"模式**（守的是"模块加载期不 import db"，不是"永不碰 DB"）。

- `ARCHITECTURE.md` 蓝图：`data ← core ← store ← services ← commands ← main`，明确 **game/services/ 服务层 = 组合 core+store 的跨域编排**（v47 时"未实施"，命令层直调 core/store）。
- `core/__init__.py` docstring 写明「聚合导出全部计算函数，供 **services/commands** 层调用」——services/ 从蓝图到代码注释都是被预留的位置。
- **game/services/ 目录不存在**（w7 `ls` 确认）。core/ 里 smith_stock/shop_stock/wild_king/reward 这 4 个"真 service 样板"实际是**借住 core/**。

---

## 2. services 架构定稿

### 2.1 目录：新建 `game/services/`（不放 core/ 子目录，不并进 core/）

| 方案 | 结论 | 理由 |
|---|---|---|
| **A. 新建 `game/services/`（本档推荐）** | ✅ 采用 | ① `ARCHITECTURE.md` v47 蓝图与 `core/__init__.py` docstring 都预留了 services 层位置；② v181 北极星文档 `ARCHITECTURE_TARGET_STATE_v181.md` 三层模型是 **data/core/battle** 的"引擎内"模型，services 是**引擎外命令层重构**，二者不冲突、补全蓝图；③ 服务层与 core 的边界：core=无内容名、参数化执行器、被 data/_assembly 触达须延迟 db；service=跨域编排、直接碰 db/store、可含业务常量与规则（配合下沉 data）、不 import commands——两条铁律不同，放同一目录会互相污染；④ 4 个"借住 core 的样板"（smith_stock 等）**不搬**（v135/v166/v140 已在 core 聚合导出、零迁移收益），P4 新代码一律进 services/；等 P4 完成、样板家族壮大后如鱼鱼要统一，可另开"样板归位"批次（纯搬移+sha 校验），不进本 P4。 |
| B. `game/core/services/` 子目录 | 不采用 | 位置暗示"core 的子集"，但它的依赖面（db/store/reward 全链）比 core 宽；core/__init__ 聚合链与 data/_assembly 加载期循环风险会放大（core 子包被 content 聚合导入时若顶层 import db → 炸）。 |
| C. 继续并进 core/（sm ith_stock 先例） | 不采用 | 现有 4 样板是历史"借住"，不是设计目标；审计建议正是"新建 game/services/"；且后续 BattleSettlementService 要 import battle/engine/reward/core+store，塞 core 会让 core 目录语义进一步失真。 |

### 2.2 文件组织：每域一个文件、纯函数模块（零类零装饰器）

- **每域一文件**：`quests.py` `shop.py` `crafting.py` `auction.py` `party.py` `guild.py` `profession.py` `travel.py` `battle_settlement.py`；跨域编排文件可按需（`battle_settlement` 可能 import quests/profession 的服务）。
- **纯函数模块**：模块级 docstring（机制说明，同 smith_stock 风格）；常量表顶置（业务常量可留文件顶，**数值类优先下沉 `game/data/`**，遵循 v181「数值在 data」北极星——但 **P4 试点/批次第一刀只搬逻辑+常量原样随迁，数值下沉单独小批次做**，避免一锅端引入数值漂移风险）；`db` 等依赖**函数内惰性 import**（沿用样板铁律，防 data/_assembly 加载期循环）；零类、零 `@filter.regex`、零 `yield event.plain_result`（那是命令层 I/O 壳）。
- **函数签名风格**：样板已确立两种：
  1. **自给自足型**（smith_stock/shop_stock）：函数自读 db/event_state，签名 `(group_id, qq_id, ...)` → 返回 `(ok, result)` / 文本 / dict。**推荐 P4 主体采用**（收敛命令层最彻底）。
  2. **注入型**（v47 蓝图 `_settle_daily_quest(inst, ...)` 现命令层写法）：收 `inst` 实例/`self`，调 `inst._xxx()`。**只允许出现在命令层内部残留/样板已存在处**；新 service 一律不自找 `inst`——需要命令层能力（广播 `self._broadcast`、`event.send`、`self._title_bonus` 等）时：广播/推送这类 I/O 由命令层在拿到 service 返回值后做，或 service 收一个可选 `hooks: dict`（回调）参数（对齐 `rule_engine.fire(... hooks=...)` 既有先例，见 §2.4）。

### 2.3 依赖方向（红线）

```
services/ 可 import：game.data（C 内容表）/ game.core（含 C 聚合）/ game.store（db 门面）/ game.engine / game.battle / game.reward / 同级 services（跨域编排）
services/ 禁止 import：game.commands.*（任何文件、任何符号——含顶层函数如 weekly_bump_kill/tower_guard_on_kill、Mixin 类、talk_actions）
commands/  可 import：services（新的主消费方向）＋ 现状全部
```

- **零环论证**：commands 不 import services 反向、commands 内部互引已在现状存在（combat→world/weekly/tower、talk_actions→world/player），services 一建立，**跨命令文件互引的纯业务函数应逐步迁入 services 让双方共同 import**（如 weekly_bump_kill 与 tower_guard_on_kill 是"击杀结算 hook"语义，最终属 BattleSettlementService/QuestService，命令层只留一行调用）。
- 注意：**services/ 与 commands 同级**，相对导入用 `from .. import db`（同 core 惯例，services 在 game/ 下 → `game.services.xxx` 内 `from .. import db as db` / `from ..core import ...`）；main.py 不需要 import services（services 被 commands import）。

### 2.4 命令层能力边界（service 不碰、命令层留）

每个待抽业务都挂着命令层 I/O/交互，**留在命令层壳**：
- `event` 参数 / `yield event.plain_result(...)` / `MessageChain`——async generator 流程本身（v3.4 铁律：async generator yield 流程不硬拆）。
- 广播：`self._broadcast(...)` / `event.send(...)` 延迟推送（依赖 `self.context`，纯命令层设施）。
- 玩家展示名/称号加成：`self._player(...)['name']`、`self._title_bonus(...)`（涉及 get_player 惰性升级与 db 状态，作为**注入回调**传入 service（`hooks={"title_bonus": lambda q: ...}`），或在 service 返回后由命令层补文案——**首刀一律后者**（service 返回结构化结果，命令层拼玩家可读文案），hooks 注入只在确有需要时引入，且必须给默认值缺省=无副作用。
- 装饰器守卫（`require_player/@no_prof_waiting`）、体力/位置/职业守卫（`_spend_stamina/_at_smith/_at_shop/_prof_active_check`……）——这些**守卫**语义混杂（有的纯规则可下沉如 `_at_smith` 子区域判定=纯 data 查询可 service 化；有的扣体力=写库动作）。P4 规则：**能表达成"读 data + 纯条件"的守卫（位置/子区域/职业/副业激活）可下沉**；涉及扣费/扣体力副作用 + 返回玩家提示的守卫（`_spend_stamina`）**留在命令层**，service 只做"扣费动作"原子调用。守卫下沉与否逐条在批次内标注。

### 2.5 services/__init__.py 聚合导出 + 测试放置

- `game/services/__init__.py`：聚合导出各文件函数（与 store/__init__.py 同款；命令层仍可 `from ..services.quests import settle_daily_quest` 直连，聚合层保持 `services.xxx` 兼容）。
- 测试：`tests/test_services_quests.py` 等按域 1:1（与 store/core 测试组织对齐）；service 函数**不依赖 FakeEvent/Main** → 可直测（见 §5 验证策略）。

---

## 3. P4-1 试点选型与抽法

### 3.1 候选评估

| 候选 | 规模/形态 | 独立度 | 风险 | 结论 |
|---|---|---|---|---|
| **每日任务结算收敛点**（`_settle_daily_quest` 顶层函数 + `_bump_daily_progress` + `daily` 命令抽取/衰减/发布 + 面板常量 DAILY_LIMIT/_DAILY_META_KEYS/_DAILY_REPEAT_FACTORS/_daily_repeat_pct/_daily_need） | 已收敛单点（~40 行结算 + ~60 行 bump + ~85 行 daily 命令），跨文件 import 已存在（combat:25），**改一处即拆掉命令层私有互引** | 高（数据全在 quests store + DAILY_QUESTS 表；规则常量顶置 world.py:42-53） | 低（纯同步、无 yield、随机只在 `random.sample` 抽 2 个——seed 可固定） | ✅ **P4-1 试点** |
| 拍卖结算 `_settle_auction`（social L1442-1478） | ~36 行同步函数 + auction/bid 命令状态机 | 中（强依赖 world_event event_state 槽，且与 `_maybe_roll_event` 调度混在命令层） | 中 | 候选（适合 P4-5 独立批，不做试点） |
| 钓鱼/采集/挖掘结算 `_settle_fishing/_settle_gather/_settle_mining`（economy 874-1412） | 大（~500 行），`_settle_fishing` 内嵌垂钓池/惊喜池/鱼王广播（create_task 走 self._broadcast） | 中低（结算挂 timed_events 引擎 on_expire 回调 `_prof_wait_expire_cb` 在 economy 顶层注册；`_broadcast` 依赖命令层实例） | 中 | 候选（P4-7 ProfessionService，需先解广播注入） |
| 道具使用 hook `_item_use_hooks`（economy 6695-6721） | ~26 行返回 dict（remove/add_stamina/nearest_town/redname…） | 低（item_templates 引擎在 core，hook 是命令层回调注入——依赖倒置点） | 中（item_templates 引擎消费侧在 economy `use` 命令内） | 候选（可做小独立批，先例价值低） |
| 强化成功率计算（economy enhance 3100-3160） | ~60 行成功/失败/保级/降级 + 文案内嵌 | 中（失败分支 yield 文案、成功分支 add_prof_exp/bump_stats/成就） | 中 | 候选（P4-4 CraftingService 首刀） |
| combat._handle_victory（510 行） | 全项目最厚单体 | 低（async generator + 数十 self._* + 跨域） | 高 | **不做试点**（P4-9 压轴） |

### 3.2 试点为什么是"每日任务结算收敛点"

1. **打中审计点**：`combat.py:25 from .world import _DAILY_META_KEYS, _settle_daily_quest` 是审计报告点名的"命令层互相 import 私有函数"耦合信号——拆进 services 后 combat 与 world 共同 import services，互引消失。
2. **小而独立**：结算函数已收敛成单点（v125.1 做的收敛正是为抽层铺路），数据源单一（quests store + DAILY_QUESTS），不含 async generator（daily 命令的 async 壳留下），不含广播。测试锚点现成：`test_v116_quest_abandon.py`（每日衰减 60% 文案 + _completed + 防刷上限）、`test_v1277_quest_view_ui.py`（面板引导/进度）、`test_v104_fishing.py`（每日任务推进分支）。
3. **验证模式三件套**（新目录能否跑通/import 方向/等价证明法）一次到位；而且 QuestService 是审计收益排序第 2 名（BattleSettlement 之后），试点即第一批正菜。
4. **可扩展**：抽完的 `game/services/quests.py` 就是后续 P4-2 QuestService 全量的骨架文件（主线/支线状态机 → _take_main_quest/_complete_side_quest/_grant_quest_rewards/_update_quests 逐块搬入）。

### 3.3 抽法（P4-1 命令层留什么壳）

**新建 `game/services/quests.py`**（docstring 写"每日任务域服务，v116 规则；由 world/combat 命令共用"）搬入：
- `DAILY_LIMIT` / `DAILY_META_KEYS` / `DAILY_REPEAT_FACTORS` 常量（world.py:42-53 原样迁，原位置留 `from ..services.quests import ...` 兼容导出或删除并由调用点改 import——**推荐删除 world.py 本地定义，world/combat 一起改 import**，行为零变化，见 §5）。
- `daily_repeat_pct(repeat)`（= `_daily_repeat_pct`）、`daily_need(dq)`（= `_daily_need`）、`settle_daily_quest(group_id, qq_id, daily, dq, lines=None)`（= `_settle_daily_quest`，**签名去掉 `inst`**：内部 `inst._player(...)` 改 `db.get_player(...)`，`inst._title_bonus(...)` 改**调用 `core/title_bonus.title_bonus(group_id, qq_id, player)`**（这正是该 core 函数存在的意义——"命令层与 store 惰性升级共用同一实现"）——diff 只有这两处 self→db/core，等价验证见 §5.2）、`bump_daily_progress(group_id, qq_id, obj_key, lines=None)`（= `_bump_daily_progress`，同款去 self）。

**world.py 命令层留壳**：
- `async def daily`：解析+守卫（红名/上限/已有任务）+ 调用 service `draw_daily_quests(group_id, qq_id, player, pool_filter_hook?)`……——**首刀保守版**：把"抽取/衰减/发布"这 ~30 行（读 DAILY_QUESTS、random.sample、factor 乘算、写 daily、面板行拼装）也搬进 service 函数 `draw_daily`，命令只留 `self._daily_pool` 这个**等级门槛过滤器**（它混用了玩家等级/objective/min_lv/旧 cap 表——语义是"抽取资格判定"，正该进 service；但它调 `self._player`？否——只读 player dict，直接搬）。搬完 daily 命令 ≈ 守卫 + 一行 `draw_daily(...)` + yield。
- `quest_view` 每日渲染段（L2310-2357）：`_daily_need/daily_repeat_pct/DAILY_LIMIT/_DAILY_META_KEYS` 引用改 import services 常量/函数（渲染行留在命令层——纯格式化）。
- `_bump_daily_progress` 方法 → 一行 `return quests_service.bump_daily_progress(...)` 或删除由调用点改调 service（world.py:3769/4714 两调用点 + combat _update_quests 内 daily 分支改调 service 同一函数）。

**combat.py**：`from .world import _DAILY_META_KEYS, _settle_daily_quest` → `from ..services.quests import DAILY_META_KEYS, settle_daily_quest`；`_update_quests` 内调用点签名改（无 inst 版）。

**P4-1 验收**：py_compile + `test_v116_quest_abandon.py` + `test_v1277_quest_view_ui.py` + `test_v104_fishing.py` + `test_commands_world.py` + 与每日任务相关 test 全绿；行为零变化 = 相关断言全绿即证明（函数体等价搬迁 + self→db/core 两处等价替换，无数值/文案改动）。提交 `v181.P4-1`。

> 保守边界（试点不做）：不顺手改 DAILY 规则数值（如 cap 表/衰减档）；不动 daily 面板行文案（若 diff 里出现文案空格/emoji 差异 → 停下修正，证明是"逐字符等价搬运"）；不把 `daily` 的 async 壳（yield）搬进 service（v3.4 铁律）。

---

## 4. 后续批次路线（按审计收益排序，每 service 给范围/文件/风险/验证）

| 批次 | Service（文件） | 范围（搬入内容） | 涉及命令文件 | 主要风险 | 等价验证锚（现有测试 + 新增） |
|---|---|---|---|---|---|
| **P4-2** | **QuestService 全量**（services/quests.py 扩） | 主线状态机 `_take_main_quest`/quest_accept/quest_abandon 判定、支线 `_complete_side_quest`/`_offer_side_quest(s)`/`_sq_unlocked`/`_sq_stats_met`、`_grant_quest_rewards`（→ 统一走 reward.grant_reward 的 exp/gold 段，收敛 12 字段 update_player 巨行）、击杀推进 `_update_quests`（combat 版搬 service 后 world 与 combat 共同调）、`turn_in` 的判定纯逻辑；`_deliver_hint`/`_tip` 面板行留命令层 | world.py（quest 区 ~700 行）、combat.py `_update_quests`、talk_actions.py（改调 service）、player.py（如 evolve 任务解锁判定） | 大（quest 状态机分支多：branch/collect 复合目标/对话交付/序号语义/防刷），涉及 async 对话流（talk_actions） | test_v104_quests / test_v116_quest_abandon / test_v124_side_chain / test_v1276_side_menu / test_v1277_quest_view_ui / test_v1307_multi_kill_quest / test_v101_27_turn_in_period / 新增 services 直测 |
| **P4-3** | **ShopService + TradeService**（services/shop.py） | shop 面板数据组装（配货/货架/折扣/限购标签——先吃 shop_stock）、buy 的商品 key 分派（bp:/m:/e:/w:/s:/mount: 巨型 if）、sell 定价/回收（_shop_equip_price 收敛、MAT_FACILITY 表）、坐骑直购/图纸随机价；价格公式统一（smith_stock._smith_equip_price 与 commands 副本收敛单点） | economy.py shop/buy/sell 区 ~660 行 | 大（分支多、每个分支独立文案+原子写），数值副本多（价格公式 4 处） | test_commands_economy / test_v135_upgrade / test_numeric_shop_pricing / 拍卖价相关；新增 buy/sell 全 key 分派直测 |
| **P4-4** | **CraftingService**（services/crafting.py） | 装备养成一条链：enhance（成功率掷骰/手艺加成/强化石/保级降级——**纯规则段先抽**：`compute_enhance_rate(...)` 返回结构化结果，命令层按结果出文案）、equip_upgrade（_upgrade_recalc_equip 收敛 price 公式副本）、gem_*/rune_*/refine/calamity_forge/enchant 的"校验+掷骰+扣料"纯逻辑段；核心 service 化 key 字面量（i_stone_*）散点收敛 | economy.py 锻造-强化区 2301-4375 ~2000 行 | 大（每条命令都是"守卫→校验→掷骰→扣料→写回→文案"，文案内嵌使拆分需逐命令做）；v135/v166 样板在 core 不重复抽 | test_v104_prof_enhance / test_v135_upgrade / test_v1023_life_prof / test_f1_atomicity / 新增 compute_enhance_rate 确定性直测 |
| **P4-5** | **AuctionService**（services/auction.py） | 拍卖状态机：开拍（_maybe_roll_event 的 auction 分支）、出价冻结/被超退还/一口价/到期结算 `_settle_auction`、过期清理（social 与 event_menu 双份过期检查收敛）；world_event event_state 槽的读写收进 service | social.py auction/bid 区 ~176 行、event_menu.py（若有重复过期检查）、world_event 调度 | 中（event_state JSON 槽是公共区域，并发/广播文案依赖） | test_commands_world（拍卖） / 新增 auction 状态机直测（出价/退还/一口价/过期） |
| **P4-6** | **PartyService + GuildService**（services/social.py 或 party.py/guild.py） | 组队：party/邀请/踢人/退队/战斗继承判定（store/social 已有原语，命令层只留解析）；公会：成员 role 校验/捐献计数/每日重置/任命（store 原语之上编排） | social.py party 区 435-589、guild 区 590-1000 | 中（store 原语已备，纯编排；但 role 校验/捐献判定散在命令） | test_commands_social / 相关版本测试；新增 role/捐献规则直测 |
| **P4-7** | **ProfessionService**（services/profession.py） | 等待型副业：`_prof_wait_*` 状态机（duration/begin/flow/residual/expire_cb——**timed_events 引擎 on_expire 回调注册迁到 service 模块顶层**，economy.py:53 `_te.register_timed("prof_wait", ...)` 从命令层消失）、`_settle_fishing/_settle_gather/_settle_mining/_fishing_surprise/_gather_roll/_gather_cond_roll`（惊喜概率表/限定条件注册表/疲劳常量下沉）、鱼王广播经 hooks 注入（`hooks={"legend": callable}` 缺省无） | economy.py 副业区 ~700 行 | 中-大（广播/延迟推送/测试里直接操作 timed_events 存储——test_commands_world 手工写 timed_events_w1 键）；规则数值多（惊喜池） | test_commands_profession / test_commands_fishing / test_v104_fishing / test_v104_prof_enhance / test_r3_m15_fishing / test_v116_fishing_season / 新增 settle 直测（seed 固定） |
| **P4-8** | **TravelService**（services/travel.py） | move 的子区域寻址/出口校验/体力经济、`_travel_ambush` 撞怪档位（收敛双轨：core/constants MOVE_ENCOUNTER_CHANCE 与本地 0.30/0.18/0.08 合一，**先搬后统一**）、方碑/隐藏图路由纯逻辑 | world.py move 区 ~583 行 | 中-大（move 是 async generator 长流程，只能抽段不能整体搬；撞怪档位涉及所有移动测试） | test_commands_world / 移动域版本测试（撞怪档位 seed）；新增 move 路由纯函数直测 |
| **P4-9** | **BattleSettlementService**（services/battle_settlement.py）——**审计头号单体，压轴** | `_handle_victory` 的经验曲线/衰减/组队/公会加成/宠物升级循环/运势/护符/图纸残页/精英 Boss 掉落补判/PET_EGG_ROLL/符文原石材料折算（几十条规则段先拆成 service 纯函数：`victory_exp(player, monster, ctx)` / `roll_pet_egg(...)` / `fold_blueprint(...)`…，命令层按结构化结果拼文案+yield）、`_handle_defeat`（死亡经济）、`_grant_worldboss_drop`/WORLD_BOSS_DROPS（掉落表下沉 data）、WORLD_BOSS_DOT_INTERVAL 常量 | combat.py 1784-2816 ~1000 行 | 高（async generator + 数十 self._* + 跨 battle/player/wild_king/instance 域）；必须先立"胜利结算行为快照测试"（P3 遗留：行为快照测试未做——P4-9 前需补，见 §5.3） | 全量战斗族测试 + numeric 全量 + **新增胜利结算快照测试（seed 固定逐字段断言 exp/gold/掉落/任务/升级）**——这是 P4-9 唯一可信等价证明 |

**每批通用风险与应对**：
1. **async generator 流程不硬拆**（v3.4 铁律）——只抽同步纯函数段，yield 流留命令层；service 函数一律同步 def（除个别确需 await 的推送由命令层做）。
2. **数值零变化**——任何"顺手"下沉 data 的数值必须在同一 commit 用对照断言（提取值 == 现状字面量，见 §5.2）。
3. **文案逐字符等价**——搬移 diff 里出现文案差异 → 停下，这是搬运错误不是改进（v98 重构铁律）。
4. **跨命令文件互引收敛**——每批结束时重扫 `grep "from .* import" game/commands/*.py`，命令层私有函数互引清单应单调下降。
5. **talk_actions.py 依赖 world 方法**（_do_join_class 等在 player/world 域）——涉及对话动作的服务化（角色创建/转职 CharacterService 候选）放 P4-2 后单独评估，本 P4 批次表不展开（player.py 域整体较健康 ⚠️，审计建议 CharacterService 属可选）。

---

## 5. 行为零变化验证策略（service 抽出来 = 搬移逻辑，怎么证明等价）

### 5.1 总原则

**service 抽取 ≠ 重写**：就是"函数体原样搬 + 调用点改 import"。等价证明分三层，逐层加码：

### 5.2 三层验证

**L1：代码级等价（每批必做）**
- 搬迁是**逐行 copy**（含注释、含空行），`git diff` 上看不到业务行变化，只看到"函数从 A 文件搬到 B 文件 + 签名/内部 2 类改动"：
  - 去 `inst`/`self` 参数 → 内部 `inst._player(...)` 换 `db.get_player(...)`、`inst._title_bonus(...)` 换 `core.title_bonus.title_bonus(...)`（这两个替换有现成 core 单点可证明等价：title_bonus 模块 docstring 明言"命令层与 store 共用同一实现"，base._title_bonus 就是它的一行壳；db.get_player 是 _player 的实现）；
  - 需要命令层能力处 → 返回值结构化 + 命令层拼文案（或 hooks 回调，默认缺省）。
- 每批完成后**反扫**：`grep -c "def 旧函数名" <old> && grep -c "def 新函数名" <new>`（各 ==1）；命令层 import 指向新位置。
- **diff 白名单校验**：搬移 diff 中不允许出现数值/文案/概率/emoji 变化；出现 → 该批失败回退。

**L2：相关单测全绿（每批必做）**
- 抽取的函数几乎全有现成命令层行为测试（§4 表每行已列）。**在 worktree 直接跑不了**（需要 data/plugins 父链与 uv python，见 HANDOFF 环境注记：测试要复制到 `Temp/df_wt_copy*/data/plugins/dragonfall` 沙盒或用 AstrBot uv python 直接跑 tests/test_*.py）。
- 命令层行为测试全绿 = 函数体等价的最强机器证明（同一命令入口、同一 DB 状态、同一断言——改前改后必须同绿）。

**L3：数值对照 + 快照（特定批必做）**
- 任何"数值随迁或下沉 data"的批次：先跑 `scripts/run_numeric_tests.py`（数值门禁铁律，51 文件基线 ✅ 全绿）；
- 数值下沉批：写对照断言 `assert SERVICE_CONST == 现状提取值`（P0B/P2F 用过的对拍模式：先落 baseline 再改）；
- **P4-9 BattleSettlementService 前置**：victory/defeat 是命令层 async generator 内几十条规则叠加，命令层测试大多只断言"输出含某文案"而不锁字段值 → 需**先补"胜利结算行为快照测试"**（P3 遗留同款：seed 固定 → 造怪 → attack/explore 到胜利 → 逐字段断言 exp/gold/掉落/任务进度/升级/宠物等级，锁定旧实现输出），快照全绿后再拆 service（对齐 P2F calc_damage 等值回测网格思路）。

### 5.3 要不要新测试？

- **搬移批（L1+L2 已够）**：不强制新增；但**建议给新 service 文件加一层薄直测**（`tests/test_services_quests.py`：直接 import service 函数、clean_db + make_player、断言返回值与 DB 效果）——不依赖 Main/FakeEvent，跑得更快，且把"service 可独立测"这个架构收益固化下来（core/store 测试同款组织）。
- **数值下沉批**：必加对照断言测试。
- **P4-9**：必加行为快照测试（前置，见上）。

### 5.4 全量门禁节奏（对齐项目铁律）

改完每批：py_compile（game/ 全量）→ 相关单测全绿 → commit（v181.P4-N）→ **所有 P4 批合并完才跑全量 run_all**（不并发污染 test_game_data.db，HANDOFF 铁律）；全量跑时绝不动源文件。

---

## 6. 试点外候选备忘（本 P4 不做，单独立项评估）

- `economy.py:5701` 唯一手写 SQL（`_visited_maps`）→ 补 store/world 封装 `get_visited_map_ids(qq_id)`（store 层小事，随时可做，不进 P4）。
- player.py 域（CharacterService/注册/洗点/面板）审计健康度 ⚠️ 居中，面板/渲染本身偏展示层合理——**不进本 P4 默认路线**，等 P4-2 后由鱼鱼决定是否立 CharacterService 批次。
- `world.move`/`interact_prop`/`talk_choice` 的整命令服务化（TravelService/DialogueService/PropService）——interact_prop 与 talk 都混着 async 对话流与 `_talk_route` 通道（talk_actions 注册表已把动作抽到命令层文件），**建议 P4-8 只做 TravelService，Dialogue/Prop 单独立项**（收益与风险比不如清单前 8 项）。
- `item_templates` 的 hook 依赖倒置（economy._item_use_hooks）——core 模板引擎消费命令层回调，方向反了；但改法是把 hook 也搬进 core（或模板引擎改为返回"副作用清单"由命令层执行），属引擎侧重构，**不进 P4**（P2 系列更合适）。

---

## 7. 侦察方法与验证记录

- worktree w7（wt_p4recon）只读；未改任何 game/ 代码；主仓与其它 worktree 未动。
- 证据：审计 12 全文（145 行）；w7 直读 commands 5 大文件（wc -l 与审计一致）、world/combat/economy/social 关键函数与行号、cross-import 实测（combat:25/26/27、player:1489、instance:1520、talk_actions 委托清单）、core/store 分层与依赖实测（core 9+ 模块函数内惰性 db、commands 无被引记录）、样板形态直读（smith_stock/shop_stock/wild_king/reward 头部与 core/__init__ 聚合导出）、测试锚点定位（test_v116_quest_abandon 每日衰减 60% 断言行、test_v1277_quest_view_ui、test_v104_fishing、test_commands_profession、test_v104_prof_enhance、numeric 门禁脚本）。
- 本 P4 与既有批次边界：P4 只动 commands/（搬出）+ 新增 services/；不碰 battle.py/engine.py/core 执行器族（P2 系列收编中）；不动 data/（除 P4 内数值下沉小批）。REFACTOR_PLAN_v181 与 HANDOFF 的 P4 描述与本档一致（BattleSettlement→Quest→Shop/Crafting→Auction/Guild/Party→Profession→Travel），本档补了试点选型、services 落位论证与逐批等价验证法。

---

*（本档由 wt_p4recon worktree 只读侦察产出；game/ 未改动、未 commit 任何代码。下一步：主 agent 审阅本档 → 批 P4-1 试点实施（services/quests.py + world/combat 改 import）→ 按 §4 逐批推进，每批独立 commit + 相关单测 + numeric 门禁。）*
