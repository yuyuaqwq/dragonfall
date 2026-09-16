# P4-9 BattleSettlementService 实施任务书

> 任务出处：`docs/archive/REFACTOR_P4_services.md` §4 批次表 P4-9（压轴：`combat._handle_victory`/`_handle_defeat` 约 510 行，全项目最厚单体）
> 目标：把 `game/commands/combat.py` 的胜利/战败结算抽到新建 `game/services/battle_settlement.py`，命令层只留壳。
> 铁律：**行为零变化**；py_compile + 相关单测全绿 + numeric 门禁；数据/规则数值零改动、文案逐字符等价；每批独立 commit `v181.P4-9`。
> 依赖方向红线（services 全局）：可 import `game.data`/`game.core`/`game.store(db)`/`game.engine`/`game.battle`/`game.reward`/同级 services；**禁止 import `game.commands.*`**。`db` 等一律函数体内惰性 import（防 data/_assembly 加载期循环）。
> 环境：worktree 只读主仓（绝不 git 操作）；沙盒验证复制到 `Temp/df_wt_copy*/data/plugins/dragonfall`。

---

## 1. 摸底结论（只读侦察已确认的事实）

### 1.1 两个目标函数定义位置（行号均为当前 combat.py 行号）

| 函数 | 定义行 | 跨度 | 代码量级 | 形态 |
|---|---|---|---|---|
| `CombatCmds._handle_victory` | **1786** | 1786–2297 | ~512 行 | **async generator**（yield event.plain_result 单点收尾），内部大量同步副作用 |
| `CombatCmds._handle_defeat` | **2345** | 2345–2412 | ~68 行 | async generator（yield 单点收尾），两处提前 yield return（复活羽毛分支） |

两个函数**都是方法（带 self）**，签名 `(self, event, group_id, qq_id, player, monster, result, extra_kills=None)` / `(self, event, group_id, qq_id, player, monster, result)`，`player` 与 `monster` 是**可变 dict**（函数内会改写并重读）。二者都是 async generator：唯一 yield 是收尾 `yield event.plain_result("\n".join(lines))`，defeat 在复活羽毛分支有第二个提前 `yield + return`。**注意：`_handle_defeat` 并非"纯同步函数"，它是 generator（函数体内有 yield 关键字），调用点全部用 `for _r in self._handle_defeat(...)` 迭代**。胜利/失败两函数被 8 个调用点消费（combat 内 942/946/1182/1186/1508/1560 + economy 5939/5943 + worldboss 2686/2702）。

### 1.2 全函数结构（victory 1786–2297 逐步）

| 段 | 行号 | 内容 | 说明 |
|---|---|---|---|
| 0 前置 | 1790–1795 | `self._unlock_battle` + `db.clear_battle` + exp/gold 兜底 | 战斗锁/清战斗 |
| 1 等级差曲线 | 1803–1814 | `diff=monster["lv"]-player["level"]`；`mult=1.0+0.015*diff*diff` cap 2.0 / `0.85**(-diff-3)` 最低 0.15；`_exp_note` | v173.2a |
| 2 组队加成 | 1818–1822 | `db.party_members(group_id, qq_id)` 有 → exp×1.1 + `party_bonus_line` | |
| 3 公会加成 | 1825–1830 | `db.guild_get_by_member(qq_id)` → `min(g["level"]*GUILD_CONFIG.exp_bonus_per_level, max_bonus)` | C.GUILD_CONFIG |
| 4 宠物段 | 1833–1865 | `db.pet_get`→`pet_decay_satiety`；`C.pet_exp_bonus`；饱食度 0 减半；bond≥50 +5%；**扣饱食度 -2（仅胜利）**；宠物分经验 20%×pet_exp_mult、循环升级 while 封顶 PET_MAX_LEVEL、`C.pet_exp_need`；升级文案三态 | 有副作用（pet_update） |
| 5 坐骑 | 1868–1872 | `C.mount_effects(player)["exp_mult"]` → `mount_bonus` | |
| 6 世界事件 | 1877–1896 | `db.get_world_event`；命中 → `db.init_stats`+`bump_stats(world_events=1)`；`C.WORLD_EVENT_POOL` etype → effects exp_mult/gold_mult | |
| 7 每日运势 | 1899–1915 | `db.get_event_state(f"daily_fortune_...")` json，大吉×1.10 / 小凶 gold×0.90 | import json/datetime 局部 |
| 8 任务统计/图鉴/声望 | 1917–1934 | `init_stats`、boss_kills/elite_kills/kills/day_kills；`bump_bestiary`；`area_key`→`C.AREA_FACTION`→rep_gain 5/3/1×rep_mult →`add_reputation` | |
| 9 图纸掉落 | 1937–1965 | luck 上限 0.5 → `C.roll_drop(lv, role, luck)`；已学图纸→图纸残页(白1绿1蓝2紫4橙6)；未学→uuid eq_<hex8> 入包 | 局部 import uuid |
| 10 装备掉落 | 1967–1994 | drop_equip None 且 elite/boss → ELITE_EQUIP_DROP/`roll_drop_equip`；质量 qmark 文案 | random |
| 11 宠物蛋 | 1999–2017 | `C.PET_EGG_ROLL` 匹配 role/is_elite/is_boss/name_kw + rate → `C.make_pet_egg`→add_item petegg_ | random |
| 12 坐骑缰绳 | 2020–2024 | `C.roll_mount_drop(role)` → `make_mount_rein`→add_item mountrein_ | |
| 13 符文 | 2028–2054 | roll 分 elite_boss×3 / 普通 only blue；`C.RUNE_DROP`/`RUNES`/`rune_item`；r_lvl 随机 | random |
| 14 原石 | 2061–2067 | `C.roll_gem_drop(monster)` → add_item gem_ | 局部 uuid |
| 15 符文收益 | 2069–2079 | equipment enchant 扫描 → scavenger/exp_bless → `C.rune_value` | |
| 16 幸运护符 | 2082–2084 | `player["lucky_until"]>now` → gold×1.5 | |
| 17 材料折算 | 2088–2135 | luck/gold_bonus（`E.player_final_stats` 上限 0.5）→`mat_value=gold*1.5*(1+luck)*(1+gb)`；drop_pool→`random.sample`；`E.resolve_drop`→C.MATERIALS/ITEMS→add_item 材料/消耗品（cap 20/10） | 大段 |
| 18 求知 | 2138–2149 | exp_bonus cap 0.5 → exp×(1+exp_bonus) + `exp_bonus_line` | |
| 19 exp 落库/刷新 | 2153–2164 | player["exp"]+=exp → `db.update_player` → **`player = self._player(group_id, qq_id)` 重新读档** → player_final_stats 重算 max_hp/max_mp | self._player 依赖 |
| 20 rule_fire | 2167–2169 | `self._rule_fire("battle_win", ..., {"event":"win","enemy":monster})` | self._rule_fire 依赖（命令层 base 方法，转 core.rule_engine.fire + hooks title_bonus） |
| 21 面板行 | 2170–2201 | lines 组装：`exp_to_next` 进度条；`_exp_note` insert 3；lucky/exp_bonus/party 行；drop_lines、gem/rune/pet_egg/mount/rep/guild/pet/mount_bonus/evt_bonus 段 | |
| 22 公会任务推进 | 2203–2223 | `guild_get_by_member`→`guild_get_task` 跨天重置→+1→达标 `guild_add_exp`+**`player=self._player` 重读 + `update_player(gold=+task_gold)`**；进度行 | self._player 依赖 |
| 23 升级 | 2225–2231 | `player["_title_bonus"] = self._title_bonus(...)` → `E.check_player_level_up` → 若升级 `db.update_player` 全字段（level/exp/hp/mp/max_*/skills/attr_pts/skill_points/learned_skills） | self._title_bonus 依赖；E.check_player_level_up 跨域 |
| 24 任务进度 | 2234–2243 | killed 组装（extra_kills + 主怪去重）→ 循环 `self._update_quests(group_id,qq_id,k)`（壳→services.quests_flow.quest_kill_progress + weekly_bump_kill） | self._update_quests 依赖 |
| 25 野王 | 2245–2257 | id startswith `b_guard_` → `wild_king_on_kill` → lines 追加 + `self._broadcast` | self._broadcast 依赖 |
| 26 塔卫 | 2260–2267 | id startswith `tower_` → `tower_guard_on_kill(self,...)`（**命令层顶层函数，签名带 inst**） | 命令层函数依赖 |
| 27 隐藏怪成就 | 2271–2280 | `hm_defeated_{gid}_{qid}` event_state 读写 | |
| 28 成就 | 2281–2286 | `C.check_achievements(...,{"defeated_hidden_monsters":hm_defeated})` + 文案 | C 聚合 |
| 29 rule 尾 | 2288–2289 | `_rule_txt` 追加 | |
| 30 下一步指引 | 2292–2294 | `self._next_step_hint(...)` | self._next_step_hint 依赖（纯渲染方法，读 C.exp_to_next） |
| 31 收尾 | 2295–2297 | `━━━━` 行 + 血蓝行 + **`yield event.plain_result`** | async generator |

**defeat（2345–2412）**：
1. `self._unlock_battle`+`db.clear_battle`+`init_stats`+`bump_stats(deaths=1)`；
2. `lost = int(player["gold"]*0.1)`；`new_gold=max(0,gold-lost)`；
3. 红名额外 `if self._is_redname(qq_id): extra=min(int(gold*0.1),2000)`（**self._is_redname 依赖**，命令层方法 `time.time()<int(event_state red_)`）；
4. `_town_id=self._nearest_town(player.cur_map)`（**self._nearest_town 依赖**，BFS 纯函数可整体搬 services）；_town_sas/subareas[0] 城镇子区域落点；
5. 复活羽毛分支：`db.count_item(i_fu_huo_yu_mao)`>0 → **写 event_state `revive_choice_{gid}_{qid}`（json {ts,lost,extra,monster}）** + `db.update_player(hp=max_hp,mp=max_mp,cur_map,cur_subarea)` + 文案 + `self._rule_fire(...event:"lose")` + `yield`+`return`；
6. 普通分支：`db.update_player(gold=new_gold,hp,mp,max_hp,max_mp,cur_map,cur_subarea)` + 文案 + `self._rule_fire(...event:"lose")` + `yield`。

> 注：**复活羽毛的二段消费命令 `revive_confirm`（combat 674–723）不搬** —— 它是独立 async 命令（读 event_state、扣金币/道具），保持命令层（P4-9 只搬结算函数）。

### 1.3 内部 self._* 依赖（逐条）

**victory 内**：
- `self._unlock_battle(group_id, qq_id)` —— L1790；模块级 `_battle_locks` set 实现（combat.py:36/519–520）。**命令层内存锁，不可搬**；结算要解锁。
- `self._player(group_id, qq_id)` —— L2155、L2219 两处**重读 DB player**（`db.get_player` 一行壳，base.py:590）。等价替换 `db.get_player(...)` 即可（行为一致，service 内惰性 import db）。
- `self._title_bonus(group_id, qq_id)` —— L2225（升级前塞 player["_title_bonus"]）；base.py:648 一行壳→`core.title_bonus.title_bonus(group_id,qq_id,player)`。service 内直接调 `core.title_bonus.title_bonus`（有 core 单点，`_title_bonus` 的 docstring 明言与 store 共用实现）。**等价替换点**。
- `self._rule_fire("battle_win", ...)` —— L2167（win）；base.py:641 → `core.rule_engine.fire(group_id,qq_id,player,cur_map,"battle_win",evt,hooks={"title_bonus":lambda q:self._title_bonus(group_id,q)})`。service 内直接调 `core.rule_engine.fire` + hooks title_bonus=lambda q: core.title_bonus.title_bonus(group_id,q,db.get_player(...) or {})。**注意 hooks 语义**：原 base._rule_fire 的 hook 是 `title_bonus(q)` → 查 q 的 title_bonus（默认 None player 参数 → 函数内 db.get_player）。service 直接等价实现。**等价替换点**。
- `self._update_quests(group_id, qq_id, k)` —— L2239；combat.py:2414 方法已经是壳：`quest_kill_progress`(services.quests_flow) + `weekly_bump_kill(self,...)`（命令层顶层，签名带 inst）。**不搬**：保留命令层壳方法；victory 壳里循环调用不变。
- `self._broadcast` —— L2253（野王击杀文案广播，**await 能力**，base.py:555 async）。**必须留在命令层**（依赖 self.context.send_message + db.get_player_groups）。壳内 await。
- `self._next_step_hint(group_id, qq_id, player, monster)` —— L2292；combat.py:2299–2322 **纯函数**（只读 player dict + C.exp_to_next + 文案分支，不碰 db/self 其它方法）→ **可原样搬 service**（改名为 `next_step_hint(player, monster)`，签名可去 group_id/qq_id——但为最小 diff 建议保留全签名或只留 player）。

**defeat 内**：
- `self._unlock_battle` —— L2347（同 victory）。
- `self._is_redname(qq_id)` —— L2356；combat.py:2758 = `time.time() < self._red_until(qq_id)`，_red_until=读 event_state `red_{qq_id}`。两方法都很薄、只读 db + time → **可整体搬 services**（`red_until(qq_id)` + `is_redname(qq_id)`，service 内惰性 import db）。**注意 PVP 区也有大量使用**：`_pvp_finish` L3070/3107、honor_shop L2847、`_pvp_act` L3043… **全部改 import services 版本**（或保留 combat 方法转发壳——最小改动：方法体改成一行 `return is_redname(qq_id)`）。
- `self._nearest_town(cur_map)` —— L2363；combat.py:2324–2343 BFS 纯函数（只读 C.MAP_BY_ID/MAP_CONNECTIONS/MAP_TYPE_TOWN/START_MAP）→ **可原样搬 service**（economy.py:607 也有一份相同实现——但**本 P4-9 不动 economy 副本**，只收 combat 内引用；economy 的 `_nearest_town` 是它自己的副本，item_templates hook 在用，不碰）。
- `self._rule_fire` —— L2394/L2409（event:"lose"）→ 同 victory 处理。

### 1.4 db.* / C.* / E.* 跨域调用清单（victory+defeat）

**db.**（全部函数内可用 `from .. import db`）：
`clear_battle` / `party_members` / `guild_get_by_member` / `pet_get` / `pet_decay_satiety` / `pet_update` / `get_world_event` / `init_stats` / `bump_stats(world_events/boss_kills/elite_kills/kills/day_kills/deaths)` / `bump_bestiary` / `add_reputation` / `add_item` / `update_player` / `get_event_state` / `set_event_state` / `count_item` / `guild_get_task` / `guild_set_task` / `guild_add_exp`。

**C.（game.content 聚合，service 顶层 `from .. import content as C` 安全——services/quests.py 已用）**：`GUILD_CONFIG`（exp_bonus_per_level/max_bonus/kill_task/task_exp/task_contribute/task_gold）、`pet_exp_bonus` / `pet_exp_mult` / `pet_exp_need` / `PET_MAX_LEVEL` / `PET_SKILL_UNLOCK_LV` / `pct_str` / `mount_effects` / `WORLD_EVENT_POOL` / `roll_drop` / `roll_drop_equip` / `ELITE_EQUIP_DROP` / `ELITE_EQ_DROP_CHANCE` / `generate_roster_equip` / `PET_EGG_ROLL` / `make_pet_egg` / `roll_mount_drop` / `make_mount_rein` / `RUNE_DROP` / `RUNES` / `rune_item` / `rune_value` / `roll_gem_drop` / `MATERIALS` / `ITEMS` / `display` / `exp_to_next` / `MAP_BY_ID` / `MAP_CONNECTIONS` / `MAP_TYPE_TOWN` / `START_MAP` / `AREA_FACTION` / `FACTIONS` / `HIDDEN_MONSTERS` / `check_achievements`。

**E.（game.engine）**：`player_final_stats`（4 次：luck/gold_bonus/exp_bonus/max_hp/max_mp 段）、`check_player_level_up`、`resolve_drop`、`race_stats`。

### 1.5 yield 点（async generator 交互）

- victory：**单点收尾** L2297 `yield event.plain_result("\n".join(lines))`。
- defeat：**两处** —— 复活羽毛分支 L2397（提前 yield+return）+ 普通分支 L2412。
- 没有 mid-function yield 让玩家做选择（不是多段对话流）——整函数是"算完一把 yield 一次"，所以**全部同步副作用可以在 service 内完成、只把收尾的 yield 留命令层**。

### 1.6 全局变量/常量依赖

- 模块级 `_battle_locks`（combat.py:36，`_unlock_battle`/`_lock_battle`/`_in_battle` 用）→ **不能搬**，命令层锁。
- 模块级 `WORLD_BOSS_DROPS`（L82–90 dict，按 Boss 中文名配 mat/mount 池）→ 消费点 `_worldboss_act` L2646（**不在 _handle_victory/defeat 内**）。可选随迁 service（worldboss 结算若也做）；保守：P4-9 只在搬 worldboss 段时搬。
- `WORLD_BOSS_DOT_INTERVAL=4`（L40）→ `_worldboss_act` L2608 用，随 worldboss 段处理。
- 无其它模块级可变全局在胜利/战败路径上。

---

## 2. 建议的 service 拆分边界（对齐 P4-1/P4-2 模式）

**核心原则（P4 方案 §3.3/§2.4 先例）**：service = **纯同步函数**，返回结构化结果；命令层保留 async generator/yield/`self._broadcast`/`await` 壳。async generator **不硬拆**（v3.4 铁律）——即 `_handle_victory`/`_handle_defeat` 的 **yield 流本身留在命令层**，被抽走的是函数体内"全部同步副作用编排"。

### 2.1 建议新建 `game/services/battle_settlement.py`（纯函数模块）函数清单

按原段顺序拆为以下**顶层同步函数**（全部同步 def、函数内惰性 import db；返回结构化 lines/None/文本，供命令层拼 `\n`.join 后 yield）：

| service 函数（建议名） | 原段（combat 行） | 返回 | 说明 |
|---|---|---|---|
| `exp_curve(exp, monster_lv, player_level)` | 1803–1814 | `(exp, note)` | 等级差曲线 + _exp_note（纯计算，最好抽，快照直测最易） |
| `party_exp_bonus(group_id, qq_id, exp)` | 1818–1822 | `(exp, line)` | 组队 ×1.1 + 文案 |
| `guild_exp_bonus(qq_id, exp)` | 1825–1830 | `(exp, lines)` | 公会加成 |
| `pet_exp_gain(qq_id, exp, monster)` | 1833–1865 | `(exp, lines, pet_changed?)` | 宠物加成+bond+扣饱食度+分经验升级（**有 pet_update 副作用**——函数内惰性 import db 执行） |
| `mount_exp_bonus(player, exp)` | 1868–1872 | `(exp, lines)` | 坐骑 |
| `world_event_bonus(group_id, qq_id, exp, gold)` | 1877–1896 | `(exp, gold, lines)` | 世界事件加成 + world_events 计数 |
| `fortune_bonus(group_id, qq_id, exp, gold)` | 1899–1915 | `(exp, gold, line)` | 每日运势 |
| `bump_kill_stats(group_id, qq_id, monster)` | 1917–1934 | None/lines | 统计/图鉴/声望（全部写 db） |
| `roll_blueprint_drop(group_id, qq_id, player, monster)` | 1937–1965 | lines | 图纸（roll_drop + 残页/入包） |
| `roll_equip_drop(group_id, qq_id, monster)` | 1967–1994 | lines | 装备 |
| `roll_pet_egg(group_id, qq_id, monster)` | 1999–2017 | line | 宠物蛋 |
| `roll_mount_drop(group_id, qq_id, monster)` | 2020–2024 | line | 缰绳 |
| `roll_rune_drop(group_id, qq_id, monster)` | 2028–2054 | line | 符文 |
| `roll_gem_drop(group_id, qq_id, monster)` | 2061–2067 | line | 原石 |
| `rune_income(group_id, qq_id, player, exp, gold)` | 2069–2079 | `(exp, gold)` | 装备符文收益 |
| `lucky_charm(gold, player, now)` | 2082–2084 | `(gold, line)` | 幸运护符 |
| `material_fold(group_id, qq_id, player, monster, gold)` | 2088–2135 | `(lines)` | 材料折算（含 luck/gold_bonus/聚宝 段） |
| `know_exp_bonus(group_id, qq_id, player, exp)` | 2138–2149 | `(exp, line)` | 求知 |
| `grant_player_exp(group_id, qq_id, player, exp)` | 2153–2164 | `player`（**重读后的 dict**） | `db.update_player` + `db.get_player` 重读 + max_hp/max_mp 重算（**这是 self._player 的等价替换点**） |
| `guild_task_progress(group_id, qq_id, player)` | 2202–2223 | `(player, lines)` | 公会每日任务推进（跨天重置/达标发奖/重读 player） |
| `apply_level_up(group_id, qq_id, player)` | 2225–2231 | `(player, lines)` | title_bonus(core 单点) + E.check_player_level_up + 落库 |
| `next_step_hint(player, monster)` | 2292（2299–2322 整函数搬） | `str` | 纯函数原样搬（去 group_id/qq_id 或保留均可，保守保留全签名） |
| `nearest_town(cur_map)` | 2324–2343 整函数搬 | `str` | BFS 纯函数原样搬 |
| `red_until(qq_id)` / `is_redname(qq_id)` | 2752–2759 整函数搬 | int/bool | 红名判定（供 defeat + PVP 共用） |
| `grant_worldboss_drop(group_id, qq_id, key)` | 2556–2570 整函数搬 | `str|None` | 世界 Boss 单发掉落发放 |

**大编排函数（命令层壳调它）**：
- `victory_settle(event, group_id, qq_id, player, monster, result, extra_kills=None, hooks=None) -> dict`：把 1790–2296 的**全部同步编排**按上述小函数顺序原样串起来（保持调用/写库顺序与 now 现实现完全一致），**返回结构化结果**，例如：
  ```python
  {
    "lines": [...],          # 与现函数 L2296 前拼好的 lines 完全一致（含 _next_step_hint 文案、━━ 行、血蓝行）
    "rule_txt": ...          # rule_fire("battle_win", win) 的返回值（或由 hooks 内做，返回文本）
    "need_broadcast": [...], # 野王 _wk_lines（壳决定 await self._broadcast）
    "player": player,        # 结算后 player dict（供壳拼尾行）
  }
  ```
  由于**中途有两个 `player = self._player(group_id, qq_id)` 重读点**（L2155/L2219，在 grant_player_exp 与 guild_task_progress 内各自重新 db.get_player），函数返回的 player 是最终 dict，命令层用它拼血蓝行即可。**hooks 参数设计**（对齐 quests_flow/profession 先例）：`hooks={"broadcast_lines": callable}` 不必要——野王广播拆出返回项由壳 await 更清晰；但**塔卫段依赖命令层顶层 `tower_guard_on_kill(self,...)` 与 `weekly_bump_kill(self,...)`（在 _update_quests 壳内，L2239 循环调 self._update_quests）** → 处理：
  - `_update_quests` 方法壳**留在命令层不动**（已是壳），victory 壳在 service 返回后循环 `self._update_quests(...)` 追加 quest_lines，**或** service 收 `hooks={"quest_progress": callable(group_id,qq_id,monster)->lines}`（命令层传 `self._update_quests`）——**推荐前者**：quest_lines 段与野王/塔卫/成就段顺序敏感（原顺序 L2239 quest → L2245 野王 → L2259 塔卫 → L2271 成就），若 service 分段太碎，把 2202–2294 段整体保留在**命令层壳里**（它们是命令层能力密集区：quest/野王广播/塔卫/成就/rule/_next_step），而 service 只收 1790–2201 的"加成+掉落+exp 结算"段，返回 `(exp, gold, player, lines_pre)` + 命令层续拼。**实施建议**：以 1790–2201 为 service 主边界（收益最大、跨域最纯），2202–2297 段由命令层壳续做（改动最小、风险最低、diff 最可审）。详细见 §3 步骤。

- `defeat_settle(event, group_id, qq_id, player, monster, result) -> dict`：同步编排 2347–2411（unlock/clear/stats/扣金/红名/nearest_town/羽毛挂起/落库），返回 `{"lines": [...], "revive_state": {...}|None, "player": player}`；复活分支把 `lost/extra/monster` 与是否写 `revive_choice` 状态返回，**落库动作**（set_event_state revive_choice + update_player 回城满血）可在 service 内完成（纯 db），yield 由壳根据 `revive_state is not None` 决定走哪个文案分支。

### 2.2 必须留在命令层（壳）的部分

1. **`yield event.plain_result` / async generator 本身**（v3.4 铁律）——service 全同步。
2. **`self._unlock_battle`/`_lock_battle`/`_in_battle`/`_battle_locks`**（模块级内存锁，命令层设施）。victory/defeat 第一行 `self._unlock_battle`+`db.clear_battle` → 壳先做（或壳在调 service 前后做——**顺序必须保持：先 unlock+clear 再结算**）。
3. **`self._broadcast`（野王文案、worldboss 击杀公告）**——async I/O + self.context。
4. **`self._update_quests` 壳**（内含 `weekly_bump_kill(self,...)` 命令层顶层函数）+ **`tower_guard_on_kill(self,...)`** 调用（命令层顶层函数，签名带 inst）。
5. **`self._rule_fire`** 语义：虽然可等价替换成 `core.rule_engine.fire`（推荐 service 内直接用 core 单点，删除 self._rule_fire 依赖），**若想零风险则把 win/lose rule_fire 调用留在壳里、service 返回结构化让壳触发**——但 rule_fire 会写 db（event 模板可能 loot_gold/exp_gain）且原实现**在 L2167（进度条前）就触发**（#262 语义：先 fire 再拼面板行、fire 内可能改 player["exp"]）→ **顺序极其敏感，必须与现实现逐点一致**。**推荐：service 内按原位置调用 `core.rule_engine.fire(...)`（用 core 单点等价替换 self._rule_fire），并把 fire 后返回文本放回结构化结果**。
6. **`player = self._player(...)` 重读点**：等价替换为 service 内 `db.get_player(...)`（base._player 就是一行壳，P4-1 已确立该替换等价）。**无 self 依赖残留**。

---

## 3. 实施步骤（可直接执行）

### Step 0 — 前置：胜利结算行为快照测试（P4-9 唯一可信等价证明，P4 方案 §5.2 要求）

1. **新文件 `tests/test_services_battle_settlement_snapshot.py`**（放 dragonfall/tests，先在旧实现上跑绿存 baseline）：
   - 用 conftest（`FakeEvent`/`Main`/`clean_db`/`make_player`/`run`）+ `random.seed` 固定 → 构造低等级普通怪/精英/Boss 三档怪物 + 玩家（含装备/宠物/坐骑/公会/队伍等状态可选组合）→ 直调 `Main(None)._handle_victory(FakeEvent(gid,qid), gid, qid, player, mon, result, extra_kills=...)` 收集 yield。
   - **逐字段断言**（锁定旧实现输出）：经验面板行数值、材料/图纸/装备入包 key 集合、宠物 exp/level/satiety 变化、stats（kills/day_kills/boss_kills/world_events）、bestiary、reputation、quests 进度、升级日志、achievements 增量、复活羽毛分支（defeat 给背包 1 根 i_fu_huo_yu_mao → event_state `revive_choice_*` 存在且 gold 未扣）、红名 defeat（gold 43000 式断言可抄 test_v85_pvp_honor L126-135 已用旧语义）。**先跑绿存档为 baseline**，P4-9 改造后再跑必须**逐字段全等**。
   - 可抄现有锚点代码风格：`test_v104_achievements` L209-226（world_events 直调 victory）、`test_v136_gem_drops` L207-270（spy roll_gem_drop + 直调 victory）、`test_v1307_multi_kill_quest`（造 Battle → cmd attack 全流程 + 面板行断言）、`test_v84_pet_system` L129-144（宠物 exp/satiety 断言）、`test_v85_pvp_honor` L126-135（红名 defeat）、`test_v104_explore_map` L161-216（世界 Boss 掉落 + `_grant_worldboss_drop` 直调）。

### Step 1 — 建 `game/services/battle_settlement.py`（纯函数模块，不 import commands）

- 文件头 docstring 写机制（同 services/quests.py / profession.py 风格：v181.P4-9、combat._handle_victory/_handle_defeat 原样随迁、可 import 范围、db 惰性 import）。
- 模块顶部 `import random, time, uuid, json, datetime`（需要的局部 import 保留在函数内也行，样板是函数内惰性 import——统一照 profession.py 的"常量顶置 + 函数内 import"风格）。
- 按 §2.1 清单逐个搬函数：**逐行 copy（含注释、空行、文案 emoji），函数名去 `_` 前缀、签名去掉 self 与不需要参数、self._xxx → 对应 core/db 单点**。diff 白名单：**只允许出现 ①去掉 self 参数 ②self._player→db.get_player ③self._title_bonus→core.title_bonus.title_bonus ④self._rule_fire→core.rule_engine.fire(hooks=...) ⑤self._nearest_town/_is_redname/_red_until→模块内同名纯函数 ⑥文件名/函数名变更**；任何数值/概率/文案/emoji/顺序差异 = 失败回退。
- 搬完在文件末尾提供：
  ```python
  # 大编排（命令层壳调用）：完整同步结算，返回结构化结果
  def victory_settle(group_id, qq_id, player, monster, result, extra_kills=None, hooks=None) -> dict: ...
  def defeat_settle(group_id, qq_id, player, monster, result, hooks=None) -> dict: ...
  ```
  大编排把 1790–2296 段按原顺序串起；**2202–2297 段默认留命令层壳**（见 Step 2 落地两方案，保守选方案 A）。

### Step 2 — combat.py 命令层改壳（两方案，推荐 A）

**方案 A（推荐，最小 diff、风险最低）：service 收 1790–2201（加成+掉落+exp 结算），2202–2297（公会任务/升级/任务进度/野王/塔卫/成就/rule/_next_step/收尾）留命令层壳。**

- `_handle_victory` 改为：
  ```python
  def _handle_victory(self, event, group_id, qq_id, player, monster, result, extra_kills=None):
      self._unlock_battle(group_id, qq_id)          # 壳先做（顺序保持：先解锁清战斗）
      db.clear_battle(group_id, qq_id)
      from ..services.battle_settlement import victory_settle
      r = victory_settle(group_id, qq_id, player, monster, result, extra_kills=extra_kills)
      # r 含: exp/gold/player(重读后)/lines_pre(1803-2201 段的奖励+掉落+经验面板行骨架)
      player = r["player"]
      # —— 以下 2202-2297 原样保留在命令层（公会任务/升级/quest/野王/塔卫/成就/rule/_next_step）——
      ... 原代码 2202–2294 ...
      lines = r["lines_pre"] + 后续行
      yield event.plain_result("\n".join(lines))
  ```
  **等价性检查点**：原实现 L2153 `player["exp"] += exp; db.update_player(...); player=self._player(...)` 在 1803–2201 段内 → 移到 service `victory_settle` 返回前执行并重读 player 返回 → 壳 2202+ 拿到的 `player` 与旧实现 L2203 处的 player 完全一致（dict 值相同）。同理 L2219 重读点原在 2210 段（guild 达标）→ 保留在命令层壳原位置 `player = self._player(group_id, qq_id)`（壳内保留原行）。**注意**：`_rule_txt` 变量：方案 A 中 L2167 的 rule_fire 在原位置（进度条前、1803–2201 段内）→ 壳要在 service 返回后把 r 里的 rule 文本在**原插入点**（L2288，所有加成段后）追加——所以 r 中 rule 文本项被壳存变量，在 2288 处 append，顺序与旧实现一致。
- `_handle_defeat` 改为：
  ```python
  def _handle_defeat(self, event, group_id, qq_id, player, monster, result):
      self._unlock_battle(group_id, qq_id)
      db.clear_battle(group_id, qq_id)
      from ..services.battle_settlement import defeat_settle
      r = defeat_settle(group_id, qq_id, player, monster, result)  # 含 lost/extra/town/revive_state/落库/rule文本/lines
      lines = r["lines"]
      yield event.plain_result("\n".join(lines))
      return
  ```
  复活分支判断放 service（feather>0 时内部完成写 revive_choice + update_player 回城满血 + rule_fire(lose) 文案），返回 lines 即现 L2389-2392 文案段 → 壳 yield。**与旧实现 diff**：仅去 self（红名判定/nearest_town 用 service 同名单点），行为逐字段等价（快照测试证明）。

**方案 B（激进，service 全收 1790–2297）**：需要把 `_update_quests` 循环、`tower_guard_on_kill(self,...)`、`wild_king_on_kill`+`_broadcast`、成就段全部转 hooks 或拆回——风险高、diff 大，**不推荐本批做**；把方案 B 留作后续可选（若鱼鱼要 service 全收，则 hooks 传 `quest_progress`/`broadcast`/`tower_kill` callable）。

### Step 3 — 引用的命令层方法收敛（P4 惯例：方法体变一行转发 / 调用点改 import）

- `_next_step_hint` / `_nearest_town` / `_red_until` / `_is_redname` 定义**移到 service 后**，combat.py 里这四个方法体改成一行 `return battle_settlement.xxx(...)` 转发壳（保留方法名，供 combat 其它调用点：`_nearest_town` 还用于 `_pvp_finish` L3075 与 instance 侧/`_is_redname` 用于 PVP/honor 区——避免全量改调用点，先留转发壳最稳，P4-9 后清理可选）。或者直接把调用点改成 service 直调（instance.py:4011 的 `self._nearest_town` 是 InstanceCmds 继承链调用 combat 方法 → 保留壳则 instance 不用动）。**推荐保留转发壳**，减少波及面。
- `_grant_worldboss_drop` 搬 service 后保留转发壳（`_worldboss_act` L2660 调用点不变）。
- **删除/收敛 import**：`from ..services.quests import DAILY_META_KEYS, settle_daily_quest`（L27）在 victory 壳改造后如不再直接用可保留（_update_quests 已由 quests_flow 处理）；`weekly_bump_kill`/`tower_guard_on_kill` import 保留（壳用）。
- 完成后反扫：`grep -c "def _handle_victory" combat.py` == 1（壳），`grep -c "def victory_settle" services/battle_settlement.py` == 1；`grep -c "def _handle_defeat"` == 1 / `defeat_settle` == 1。

### Step 4 — services/__init__.py 聚合导出（对齐现有 9 文件）

在 `game/services/__init__.py` 追加：
```python
from .battle_settlement import (  # noqa: F401
    exp_curve, ... victory_settle, defeat_settle, next_step_hint, nearest_town,
    red_until, is_redname, grant_worldboss_drop,
)
```

### Step 5 — WORLD_BOSS_DROPS / WORLD_BOSS_DOT_INTERVAL（可选随迁）

`_worldboss_act`（L2572–2727）**不在本次 P4-9 目标函数内**；但其内部调用 `_grant_worldboss_drop`（搬了）与 `WORLD_BOSS_DROPS`/`WORLD_BOSS_DOT_INTERVAL` 常量。**保守**：常量留在 combat.py 模块级（壳区），`_grant_worldboss_drop` 壳转发 service；worldboss 整段服务化单独小批做（或明确不做，写进本任务书"不做项"）。

---

## 4. 验证清单（按序执行，全绿才 commit）

### 4.1 编译
- `python -m py_compile game/services/battle_settlement.py game/commands/combat.py game/services/__init__.py`（沙盒：`Temp/df_wt_copy*/data/plugins/dragonfall` 下用 AstrBot uv python 或 `uv run python -m py_compile ...`）。

### 4.2 既有单测（覆盖结算路径，逐文件跑）
| 测试文件 | 覆盖点 |
|---|---|
| **test_services_battle_settlement_snapshot.py（新增）** | Step 0 快照 baseline：改前绿 → 改后逐字段全等（**最强证据**） |
| test_v1267_victory_exp_fix.py | _origin_enemy 兜底 + attack/skill 调用点源码检查（`inspect.getsource(CombatCmds.attack/skill)` 含 "_origin_enemy"——**壳改造后 attack/skill 调用点不变仍含**，绿即可） |
| test_v1307_multi_kill_quest.py | 双怪战 victory 全流程：主线/每日/支线 +2、经验单次、掉落单行、killed_enemies 持久化（attack 壳路径） |
| test_v136_gem_drops.py | victory 消费 roll_gem_drop（spy + 直调 victory） |
| test_v104_achievements.py | world_events 写入（直调 victory） |
| test_v84_pet_system.py | 宠物 exp/饱食度/升级（直调 victory 段 L139） |
| test_v85_pvp_honor.py | 红名死亡 defeat（直调 L132：金 50000→43000 断言**锁红名扣 10%+额外 10% 数值**） |
| test_v104_explore_map.py | 世界 Boss 掉落 + `_grant_worldboss_drop` 直调（L180-184） |
| test_v1252_mech_behavior.py | 每日/quests 结算单点 + inspect 断言（若改造不影响 quests 段应仍绿） |
| test_commands_battle.py / test_v109_2_combat_mech.py | 战斗指令回归（attack/defend/flee 壳路由不变） |
| test_commands_world.py | 世界域 + 讨伐拦截（若 world 未动，回归确认无连带） |
| test_commands_instance.py / test_v141_instance_world.py / test_v137_dungeon.py / test_v104_instance_party_pet.py / test_v95_77_instance_kill_reward.py | 副本结算路径（不动 instance 但确认无连带） |
| test_v97_05_rule_engine.py | rule_engine battle_win 触发（rule_fire 等价替换验证） |

跑法（项目惯例）：把测试复制进沙盒 `Temp/df_wt_copy*/data/plugins/dragonfall/tests/` 后 `python tests/test_xxx.py`（conftest 自动 GWEN_GAME_DB=test 库、GWEN_TEST_MODE=1、shim astrbot）；**绝不并发跑多个 test**（test_game_data.db 污染铁律）。

### 4.3 numeric 门禁
- `python scripts/run_numeric_tests.py`（51 文件基线全绿；本批不动数值，应保持全绿——若红即回退检查数值漂移）。

### 4.4 反扫 + diff 白名单
- `git diff`（只读主仓不可 git——在沙盒副本 diff 旧版 vs 新版）：搬移区**零数值/文案/emoji/顺序差异**；只允许 §3 白名单 5 类改动。
- 反扫 `grep -c "def _handle_victory" game/commands/combat.py` → 1（壳）；`grep -c "def victory_settle" game/services/battle_settlement.py` → 1；`grep -rn "from ..services.battle_settlement" game/commands/combat.py` → 存在。
- `grep -rn "self\._handle_victory\|self\._handle_defeat" game/commands/*.py` 调用点仍为 `for _r in self._handle_*` 形式（函数仍是 generator 语义——**必须保证壳函数体内仍有 yield**，否则调用点 StopIteration 语义变化 → 测试必红，正好是探针）。

### 4.5 OLD==NEW 探针（可选加强）
在沙盒里跑一次对拍脚本：`NEW = victory_settle(group_id, qq_id, player, monster, result, ...)` 全量副作用结果 dict vs 旧实现同输入同 seed 的最终 DB/面板行快照（只读 DB 前后 diff）——直接比较 `db` 快照 key 集合与 lines。可以复用 Step 0 快照测试框架做"双实现对比"探针：定义 OLD 函数 = 改造前代码副本（从 git 检出旧 combat.py 提取函数体逐字粘贴到测试文件做 reference），NEW = service 直调；同一 seed/玩家/怪物下断言 DB 全表 diff 为空 + lines 逐行相等（对齐 test_p2dd4b_revive 的 OLD/NEW 对拍风格）。

---

## 5. 风险点清单

1. **async generator → 同步的坑**：`_handle_victory`/`_handle_defeat` 当前是 generator（函数体含 yield）。壳改造后**必须仍是 generator**（保留 `yield event.plain_result`）否则 8 个 `for _r in self._handle_*(...)` 调用点变"迭代非迭代器"崩。**验证法**：改造后每个调用点文件 py_compile + 相关命令测试跑绿；快照测试 `list(inst._handle_victory(...))` 能正常收集。
2. **`player = self._player(...)` 重读点顺序**（L2155 与 L2219）：service 内重读时机必须与旧实现完全一致（一次在 exp 落库后、一次在公会任务达标时）。任何一次重读提前/滞后都会导致后续加成/彩蛋金币（rule_fire loot_gold）基数不同 → #262 语义破坏。**验证法**：快照测试断言三连胜 exp 入账与 rule_fire loot_gold 同场生效（可造 rule_win_streak 场景）。
3. **rule_fire 触发点顺序**（L2167 在进度条前、L2288 只追加文本；defeat L2394/L2409 在 yield 前）：若 service 收段内调用 core.rule_engine.fire 但 hooks 的 title_bonus 实现不等价（原 hook 是 `self._title_bonus(group_id,q)` → title_bonus(group_id, q, db.get_player(group_id,q) or {})），**必须照抄 base.py:648 语义**；fire 会写 db（模板 loot_gold/exp_gain），**只可触发一次、位置原样**。
4. **红名/nearest_town 双副本**：economy.py:607 有 combat 版 `_nearest_town` 的**同逻辑副本**（item_templates hook 用）。搬 combat 版去 services 后**不要顺手改 economy 副本**（数值/逻辑等价但消费者不同，动它 = 扩 scope）。
5. **`tower_guard_on_kill(self,...)`/`weekly_bump_kill(self,...)` 命令层顶层函数带 inst**：service 不能 import commands → 这俩调用点只能留在壳（方案 A 天然满足，段 24/26 留壳）。若强行收 service 需改 tower/weekly 的签名（inst 参数变 hooks）→ 属 P4 外的跨命令重构，**不在本批**。
6. **`_broadcast` await**：野王击杀文案广播（L2253）与 worldboss 击杀公告（L2680）都在 async 上下文，service 纯同步函数不能 await → 野王段留壳（方案 A）。若 service 尝试收野王段必须返回文本让壳 `await self._broadcast`——注意原实现是 try/except 静默，壳保留同款 try/except。
7. **random 调用点数量与顺序**（v103 确定性铁律）：victory 内 random 调用序列 = 图纸 roll_drop 内部 + ELITE_EQ_DROP_CHANCE + PET_EGG_ROLL rate + roll_mount_drop + rune roll + roll_gem_drop + 材料 random.sample；还有 `uuid.uuid4()` 入包 key。**service 拆分后函数内/跨函数调用顺序必须与现实现一字不差**，否则既有战斗回归测试（seed 固定）随机序列错位 → 掉落断言漂移。**验证法**：快照测试固定 seed 断言掉落 key 集合 + run_all 战斗族全绿。
8. **文案逐字符等价**（v98 铁律）：搬移 diff 出现任何文案/emoji/空格差异 = 失败回退。
9. **`_battle_locks` 不可搬**：若错误把 unlock 搬进 service（纯函数无 self 概念会写成 db-only），战斗锁逻辑断 → 同玩家双线战斗漏洞。unlock/clear 行留在壳最前（顺序：先 unlock+clear_battle 再结算——与旧实现一致）。
10. **defeat 复活羽毛分支**：挂起状态 key `revive_choice_{gid}_{qid}` 由 `revive_confirm`（命令层）消费——service 写 state 的 json 结构（ts/lost/extra/monster）必须原样，字段名/类型一字不改，否则二段命令读错。
11. **测试直接调 `_handle_victory`/`_handle_defeat` 的兼容**：现有测试（test_v84/v85/v104_achievements/v136/v104_explore_map）以 `Main` 实例方法身份直调 → 壳保留方法名与 generator 语义即可全兼容；**service 只给新快照测试直测**（不依赖 Main）。
12. **升级段 update_player 巨行**（L2231 全字段）在方案 A 留壳 —— 若 service 收升级段需把 db.update_player 的字段全集照抄，漏一个字段 = 升级存档损坏；保守留在壳。

---

## 6. 交付产物（commit v181.P4-9 内）

- 新增 `game/services/battle_settlement.py`（纯函数模块 + victory_settle/defeat_settle 编排 + 搬入 next_step_hint/nearest_town/red_until/is_redname/grant_worldboss_drop）。
- `game/services/__init__.py` 追加聚合导出。
- `game/commands/combat.py`：`_handle_victory`/`_handle_defeat` 改壳（保留 generator 语义）；被搬方法的调用点收敛（转发壳或直调 service）；import 区加 `from ..services import battle_settlement`（或函数内惰性 import，样板两种都见过——文件顶部 import 同 services.quests 先例更整洁，但 services/__init__ 聚合与惰性二选一，**推荐 combat.py 顶部 `from ..services.battle_settlement import victory_settle, defeat_settle, ...`**，防环由 services 不 import commands 保证）。
- 新增 `tests/test_services_battle_settlement_snapshot.py`（Step 0 快照，改前后都跑）。
- 可选新增 `tests/test_services_battle_settlement.py` 薄直测（service 不依赖 Main 直测 exp_curve 等纯函数确定性）。

## 7. 不做项（明确排除，防 scope 膨胀）

- worldboss 整段（`_worldboss_act` 2572–2727 / `hunt_boss` 2434–2554 / `WORLD_BOSS_DROPS` / `WORLD_BOSS_DOT_INTERVAL`）不搬（保留 combat 壳区；`_grant_worldboss_drop` 搬 service 但 combat 留转发壳）。
- `revive_confirm`（674–723）不搬。
- `_pvp_*` / `_worldboss_act` 内红名/荣誉逻辑不改（只把 `_is_redname`/`_nearest_town` 方法变转发壳）。
- economy.py 的 `_nearest_town` 副本与 item_templates hooks 不动。
- 不顺手下沉任何数值到 game/data（数值随迁、零变化，下沉单独小批）。
- instance.py 副本结算（`_instance_victory`/`_instance_kill_reward`/宠物段等）不动——只确认无连带回归。

---

*（本任务书由只读侦察产出：行号全部直读 combat.py 当前内容核实；未改任何文件。执行者照 Step 顺序做即可。）*
