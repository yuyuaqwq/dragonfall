# L3 玩家事件层 P0 —— 字段级任务书

> 2026-09-09（会话 2026-09-09 午后）P0 产出：基于真实代码侦察，把
> `docs/DESIGN_v181_L3_player_event_bus.md` 细化到字段/行号级，可直接派 P1/P2 实施。
> 本文件 = 任务书（P2E_task 先例），设计文档 = 权威思想；两者冲突以本文件侦察修订为准
> （差异均在 §2 列出）。审过本文件后 P1 可开工。
> 完成状态：✅ P1-P4 已全部落地（2026-09-09；P1 e26f92a / P2a b7f509c / P2 ee19c45 /
> P3 0f722cd / P4 f9493e5+收尾，落地与裁定记录见 §9 P4 完成注、设计文档 §3 排期表）。

## 1. 侦察结论摘要

- 设计文档 §0 写的"victory_settle 手动逐个调任务/公会/成就"**已过时**：P4-9 重构后
  victory_settle 是纯资源结算段（等级差/加成/掉落/exp/rule），任务/公会/野王/塔卫/
  成就的手动接线在**命令层壳** `combat._handle_victory` L2034-2118。
- **胜利入口不是 1 个而是 4 类**（见 §3 地图），其中副本/世界Boss/PVP 各自独立结算，
  从没调过 _handle_victory——L3 首批只迁 field 入口，其余场景后续逐个收编。
- `guild_kill_progress`（services/guild.py:250）**已是死代码**（全仓零调用点，注释过时）——
  combat 的公会每日任务是内联的 db.guild_* 操作，迁移目标 = 内联段抽订阅，不是搬死函数。
- 设计文档把公会当 `monster_killed` 逐只订阅是**行为陷阱**：真实代码公会每日任务是
  **每场胜利 +1**（与杀几只无关）→ 必须订阅 `battle_victory`。

## 2. 与设计文档差异修订（实施按本表）

| # | 设计文档原述 | 真实代码 | 修订 |
|---|---|---|---|
| 1 | victory_settle 编排手动调任务/公会/成就/野王/塔卫 | 手动段在 combat._handle_victory 壳 L2034-2118；victory_settle 只剩 bump_kill_stats(段8) 属玩家级 | P2 迁移点 = _handle_victory 壳段；settlement 段8 图鉴/声望**不迁**（在资源行中段，动它=行序重组+零收益，标范围外） |
| 2 | 公会订阅 monster_killed 逐只 | 公会每日任务每场 +1 | 公会订阅 `battle_victory`（每场一次），handler 内 +1 |
| 3 | 事件全集 = battle_victory/defeat/monster_killed | 任务进度逐只循环、野王/塔卫只看主怪前缀 | quests 订阅 battle_victory 并在 handler 内按 ctx["killed"] 循环（原壳同款）；monster_killed 保留事件定义，本批零订阅方（留独立击杀场景未来用） |
| 4 | ctx = {group_id, qq_id, player, monster, result, lines} | 需要场景标记（field/instance/worldboss）+ 击杀列表 + 广播副作用通道 + 段落空行规则 | ctx 见 §4 扩展 |
| 5 | （隐含）单胜利入口、单玩家 | 副本/世界Boss 多人逐成员、独立结算 | ctx.kind 场景维度；P2 只迁 field，instance/worldboss/PVP 现状不动（P3 再收编） |
| 6 | 订阅方回填行直接 append | 升级段（check_player_level_up）夹在 guild 与 quest 之间，行序敏感 | 升级也建模为 battle_victory 订阅方（玩家级反应），注册序=原行序（§5 对照表） |

## 3. 真实接线地图（4 类胜利入口侦察）

| 入口 | 代码位置 | 玩家级手动段（行号=2026-09-09 HEAD 336ead8） | 场景 |
|---|---|---|---|
| 野外普通战斗（attack/skill/use_item 击杀） | combat._handle_victory → 调 victory_settle 后壳续做 | 公会每日(2034-2055) → 升级(2056-2063) → quest 循环 killed 每只(2064-2075，_update_quests=quest_kill_progress+weekly) → 野王 b_guard_(2076-2089+广播) → 塔卫 tower_(2090-2099) → 成就 hm(2100-2118) → rule/next/收尾(2119-2128 留壳) | **field** |
| 塔卫/野王击杀 | 同上（特殊怪走普通胜利，订阅方按主怪 id 前缀自判） | 同上 | field 特例 |
| 副本 Boss 通关 | instance._instance_victory:3013（独立结算，不走 _handle_victory） | 每存活成员：金币/exp/宠物/主线进度(_instance_main_kill_progress 只主怪名)/图纸/掉落/材料 + 成就(inst_id+flawless)(3187) + 首通 | instance |
| 副本小怪击杀 | instance._instance_kill_reward:2536 | exp/材料分摊/宠物/主线进度(2687 段)；**无**每日/支线/周常/公会/野王/塔卫 | instance |
| 世界Boss 死亡 | combat._worldboss_act:2405-2457 | 贡献排行奖励 → 每参与玩家 check_achievements(worldboss)(2432) → 广播；**无** quest/公会 | worldboss |
| PVP | combat._pvp_act（不调 _handle_victory） | 无玩家级反应（monster=None） | —— 排除 |

**field 是唯一"全量手动段"入口** → P2 试点迁它；instance/worldboss 手动段少而散 → P3 按入口逐个收编。

## 4. ctx schema 逐字段（P1 总线 + P2 订阅方共用）

```python
ctx = {
    # --- 固定字段（fire 点必填） ---
    "event": "battle_victory",          # fire 时自动补
    "kind": "field" | "instance" | "worldboss",   # 场景（P2 只有 field 会 fire）
    "group_id": str,
    "qq_id": str,                        # 本 ctx 结算的玩家（instance/worldboss 逐成员各 fire 一次）
    "player": dict,                      # 当前结算中 player dict（victory_settle 返回的重读版）；
                                         # 订阅方可原地改（dict 引用共享），升级 handler 会重绑 ctx["player"]
    "monster": dict,                     # 主怪/首领（name/lv/id/is_boss/is_elite/exp/gold）；PVP 不 fire 所以必在
    "killed": [dict],                    # 全部击杀单位（field=monster 打头+extra_kills 逐只；副本=_last_killed）
    "lines": [],                         # 行收集器：总线内部 append（订阅方只读不用管）
    "side_effects": [],                  # 非文案副作用（总线不解释）：订阅方 append dict
                                         # {"type": "broadcast", "text": "..."}（野王广播）——fire 返回后命令层处理
    # --- 场景附加（fire 点按需放，订阅方 .get） ---
    "meta": {                            # 各场景额外事实
        # field: 无
        # instance: {"inst_id": str, "flawless": bool}
        # worldboss: {"contrib": dict(qq->dmg), "top_qq": str, "boss_name": str, "reward": {...}}
    },
}
```

字段口径铁律：
- `monster` 必须是"死亡不移除的存活引用/原主怪引用"（_b_enemy 语义），不能是已清空 dict——
  副本 Boss 需按 instance._instance_victory L3016-3028 三阶兜底取（boss/st/enemies/role=boss/_last_killed）。
- `player` 传**壳当前持有**的 dict（升级订阅方重绑后，后续订阅方拿新 dict——与原代码
  `player = lv_logs 后更新` 的局部变量演进一致）。

## 5. 订阅注册表（P2 落地：6 订阅方 = 原壳段 1:1 抽取）

总线注册序 = 原代码行序（零变化关键）。blank_line = 该段前是否补空行（模拟原壳手写空行）。

| # | 订阅方（模块:函数） | 原代码段 | 事件 | blank | ctx 消费 | 回填行格式（原样） |
|---|---|---|---|---|---|---|
| 1 | guild_daily：`services/guild.py` 新 `guild_daily_kill_progress(group_id, qq_id)`（内联 L2034-2055 原样搬，纯 db） | combat 2034-2055 | battle_victory | False | group_id/qq_id | `🎯 公会任务进度 {t}/{kill_task}` 或 `🎯 【公会任务完成】击杀…达成！公会经验 +X 贡献 +Y 金币 +Z`（二选一互斥） |
| 2 | levelup：`services/battle_settlement.py` 新 `victory_levelup(ctx)`（原 L2056-2063 + _title_bonus 注入；title_bonus→`core/stat_bonus.stat_bonus` 纯函数等价；**重绑 ctx["player"]**） | combat 2056-2063 | battle_victory | True | player（可变）/group_id/qq_id | `""` + lv_logs（升级才有行；无升级返回 []） |
| 3 | quests_field：`services/quests_flow.py` 新 `on_monster_killed_batch(ctx)`：`for k in ctx["killed"]: quest_kill_progress(...)` + weekly 下沉版 | combat 2064-2075（_update_quests 壳） | battle_victory | True | killed 逐只 | `📜 主线/支线/每日/周常` 行组 |
| 4 | wild_king：`core/wild_king.py` 原 `wild_king_on_kill(group_id, qq_id, monster)`（纯） | combat 2076-2089 | battle_victory | True | monster.id 前缀 `b_guard_` 自判；**返回行外还需 side_effects 广播**（原壳 self._broadcast） | `👑` 野王死亡行组 |
| 5 | tower_guard：`commands/tower.py` → 下沉 `services/` 新函数（原 tower_guard_on_kill 逻辑，inst._player→db 等价读） | combat 2090-2099 | battle_victory | True | monster.id 前缀 `tower_` 自判 | `💰 塔层赏金` / `🏯 第 N 层突破` |
| 6 | achievements_field：`services/quests_flow.py`? → 新 `services/player_event_subscribers.py` 聚合壳，原 L2100-2118（hm_defeated event_state + check_achievements(extra=hm)） | combat 2100-2118 | battle_victory | True | monster.id ∈ HIDDEN_MONSTERS、player | `🏆 成就解锁：…` 行组（内部空行 `[""]+ach` 由 blank 统一替代，行内容不变） |

注册代码落点（新文件 `game/services/player_event_subscribers.py`，import 各原模块函数并 register；
命令层/入口 import 一次该模块触发注册——**显式 import 触发，不做 import 魔法自动注册**）：
- guild_daily → blank=False；levelup → blank=False；quests_field → blank=True；
  wild_king → blank=True；tower_guard → blank=True；achievements_field → blank=True

⚠️ 原代码空行细节核对（照抄不改）：guild 行直接 append **无空行**；升级 `if lv_logs: if lines: lines.append("")`；
quest 同款（先空行）；野王/塔卫同款；成就 `lines += [""] + ach_lines`。→ 订阅注册 blank 参数即此三态：
False / True（仅在 lines 非空且末尾非空行时补一个）/ 成就段其实也是"空行+行组"=True。行组内容与顺序零变化。

**留在壳不动**（非玩家级反应或需 yield）：rule_txt 公告(2119-2121) / _next_step_hint(2122-2126) /
分隔线+HP(2127-2128) / _unlock_battle+db.clear_battle(2027-2028) / 升级外的资源段。

## 6. 回填顺序对照表（P2 验收逐行 diff 基准）

field 场景最终行序（迁移后 = 迁移前，行内容逐行相等）：

```
[1] victory_settle lines_pre（骨架4行+加成+掉落+gem/rune/pet/mount+rep_lines 图鉴声望+buff行）   ← 不动
[2] (fire battle_victory 起) 订阅1 guild 段（无空行前缀，直接续）
[3] 订阅2 levelup 段（无空行前缀；行= ["", lv_logs...] 若升级）——原代码升级在 guild 后且 if lines 补空行 → blank=False+段内自带"" 实现同效果？ 
```

⚠️ 对照细账（实施时逐条核对，勿想当然）：
- 原 L2060-2062：`if lv_logs: if lines: lines.append(""); lines += lv_logs` —— 空行**在 lv_logs 非空时**才插，
  且插在 lv_logs 行组前（即 guild 行之后）。若 blank=False 且段内首行 "" → 效果相同（guild 有行时中间隔空行；
  guild 无行时 "" 直接贴面板后——原代码此时 lines_pre 非空 → 也会插空行，一致 ✅）。
- quest 段空行同理（quest_lines 非空才插）；野王/塔卫/成就段同款。
- **空行补齐规则用注册参数 blank=True 由总线统一实现**：段首若 lines 为空/末尾已是空行 → 不补；否则补一个 ""。
  该规则与 6 处手写 `if lines: lines.append("")` 语义逐点等价（guild 段 blank=False 不补）。

## 7. P1 任务书（总线核心，无业务 import）

文件：`game/services/player_event_bus.py`（新，~60 行）

```python
EVENTS = ("battle_victory", "monster_killed", "battle_defeat")   # 起步全集

def register(event: str, subscriber, blank_line: bool = True) -> None
    # 同事件重复注册 = 追加（模块 import 一次天然单次，不查重）
    # 未知 event → ValueError（防拼写静默失效；fire 未知事件只 log 不 raise，见下）

def fire(event: str, ctx: dict) -> list
    # 1. ctx.setdefault("lines", []) 校验 event 合法
    # 2. 逐订阅方顺序执行：
    #    - 异常订阅不阻断（log warning + continue，对齐现状 try/except 宽容）
    #    - 返回 None/[] 跳过
    #    - 行组前按 blank_line + "lines 非空且末尾非空行" 规则补空行
    #    - ctx["lines"].extend(行组)
    # 3. 返回 ctx["lines"]（调用方直接 lines += 或拼接）
    # 4. 未知事件（未注册任何订阅方的事件 fire）→ log info + 返回 []（不 raise：battle_defeat 起步零订阅方）
```

单测：`tests/test_player_event_bus.py`（纯单测，零游戏模块）
- 注册顺序保序 / blank=False 不补空行 / blank=True 补空行条件（空 lines、末行已空、末行非空三态）/
  异常订阅不阻断后续 / 返回 None 与 [] 等价 / 未知事件名 register raise + fire 空跑 /
  重复注册同事件 append 顺序 / 同 ctx 多次 fire 行追加（幂等由订阅方保证，总线不查重）。
- P1 验收：不 import 进任何生产模块（纯新文件+测试），全量回归零新增红。

## 8. P2 任务书（field 迁移试点，原 L2034-2118 → fire）

前置下沉（小步，各自 commit）：
- P2a-1 `_title_bonus` 注入等价：levelup 段用 `core/stat_bonus.stat_bonus(group_id, qq, db.get_player(...))`
  验证与命令层 _title_bonus 同值（读代码/现网快照），若命令层壳还做别的（如缓存）→ 任务书回退标志。
- P2a-2 tower_guard 下沉：inst._player(group_id,qq_id) → db 读等价（`db.get_player` 或现 player ctx）；
  函数从 commands/tower.py 挪 services/（原命令层调用点仅 combat 2093 一处，删后无残留）。
- P2a-3 weekly 发奖下沉：_grant_rewards 的 inst._player 读 → ctx.player/db 读等价；weekly_bump_kill 挪/复制
  services 版（commands/weekly.py 原函数留作其他调用点？——先 grep 调用点，仅 combat._update_quests 则整迁）。

实施（主步，单 commit 原子切）：
1. 新 `game/services/player_event_subscribers.py`：6 订阅方按 §5 表注册（薄壳，逻辑 1:1 搬原函数/原内联段）。
2. combat._handle_victory：删除 L2034-2118 手动段，原位替换：
   ```python
   _vctx = {"kind": "field", "group_id": group_id, "qq_id": qq_id,
            "player": player, "monster": monster, "killed": killed}
   from ..services.player_event_bus import fire as _pe_fire
   from ..services import player_event_subscribers as _  # 触发注册（幂等，import 一次）
   lines += _pe_fire("battle_victory", _vctx)
   player = _vctx["player"]                      # 升级订阅方可能重绑
   for _se in _vctx["side_effects"]:            # 野王广播（原 self._broadcast 位点）
       if _se.get("type") == "broadcast":
           try: self._broadcast(_se.get("text", ""))
           except Exception: pass
   ```
   （killed 变量构造原代码 2066-2068 前移保留；_unlock_battle/clear_battle/升级以外壳逻辑原位不动。）
3. 升级段从壳删除（进 levelup 订阅方）；成就段 hm event_state 逻辑进 achievements_field 订阅方。
4. 测试：快照测试改造——原 tests 里 _handle_victory 全链路断言逐行比较不变（定位相关测试文件后逐条跑）；
   新增 `tests/test_l3_field_victory.py`：假 guild/quest/等级边缘/野王怪/塔卫怪 构造 → _handle_victory →
   yield 行 == 基线行列表（迁移前快照存测试注释/夹具）。
5. P2 验收：field 全链路行逐行 diff 零变化（含空行）；全量回归（run_all_tests.py）与迁移前同名单同结果；
   instance/worldboss/PVP/defeat 路径零改动（代码没碰）。numeric 门禁（未重建）不涉及。

## 9. P3/P4 任务书（后批，P2 审过后再细化）

> 🔴 **语义决策（鱼鱼 2026-09-09 拍板："按你觉得是否合理来决定，老配置也可能是有问题的"）**：
> 统一事件模型 = **任何击杀都算数**，订阅方按怪属性/事实自己决定推进什么，不按入口阉割。
> 老配置不一致 = 各入口独立实现时漏接（副本只推主线是 v105 M19 当年只补了主线卡死场景）。
> 具体落点：
> - 任务（主线/每日/支线）+ 周常：**instance/worldboss 也全推**（kill_any/kill_elite/kill_boss 按怪属性匹配；
>   主线按怪名匹配——副本 Boss/小怪、世界Boss 名字对得上就推）。副本 `_instance_main_kill_progress`
>   被 quests 订阅方主线分支取代（删旧，统一单点）。
> - 公会每日（每场胜利 +1）：instance 每场战斗 +1；worldboss 死亡给全体 contrib>0 玩家各 +1（同成就参与口径）。
> - 野王/塔卫：怪 id 前缀 b_guard_/tower_ 自判——副本/世界Boss 不会出现这些怪 → 天然只命中 field，无需 kind 分支。
> - 成就：extra 按场景组装（field=hm_defeated / instance=inst_id+flawless / worldboss=worldboss:1）——kind 分支只此一处。
> - PVP 不 fire（打人不是杀怪，monster=None）。
> - ⚠️ 行为变化（故意，合理）：instance/worldboss 击杀开始推进每日/支线/周常/公会计数——
>   需配套快照测试更新（旧断言若写死"副本不推进"则按新语义改断言，勿当回归）。

- P3-1 instance 收编：instance._instance_victory / _instance_kill_reward 尾段 → fire(kind="instance")（逐成员各一次），
  订阅方按上表全推；_instance_main_kill_progress 删旧。
- P3-2 worldboss 收编：_worldboss_act victory 段 per-player fire(kind="worldboss")（contrib>0 全体，含同归于尽玩家），
  订阅方全推；现状"世界Boss 不推任务"按语义决策变更为推。
- P3-3 成就 25 处调用收敛：非战斗场景调用（economy/player/social/profession/party 等 20+ 处）不在 L3 范围
  （它们是行为钩子不是战斗事件），P3 只数"战斗入口调用数可数下降"，别误迁行为钩子。
- P4 settlement 瘦身 + 新订阅方接入文档 + 本文件/设计文档回写收官。
  ✅ **完成（2026-09-09，f9493e5 + 收尾 commit）**：接入指南 = docs/L3_player_event_subscription_guide.md
  （剧情示例；声望/图鉴**刻意不给订阅示例**——见下方范围裁定，重复接线会双发）+
  验证网 tests/test_l3_player_events.py 18 断言。settlement 瘦身裁定：P2/P3 已把玩家级反应
  全部迁出结算链，victory_settle 现存唯一玩家级段 = 段8 bump_kill_stats（图鉴+势力声望），
  按本文件 §2 差异表 #1 **范围外不迁**（行夹资源行中段：rep_lines 前有 mount_line 后有
  guild_bonus，迁订阅=行序重组+零收益；且其消费 evt_effects 为结算内部传递链）——设计文档
  P4 行原预期「victory_settle 行数显著下降」随 P2 壳段迁移已达成主体。收尾动作：victory_settle
  返回 dict 删 16 个零消费者键（全仓仅 combat._handle_victory 壳消费 lines_pre/player/rule_txt；
  死字段清理铁律：先 grep 全仓引用确认无消费者再删），玩家可见输出零变化（快照测试逐字段全等）。

## 10. 风险与边界（实施前必读）

1. **行序夹心**：升级段是唯一夹心，必须建模为订阅方（§5 #2），fire 单点才成立；若跳过，
   fire 放升级后 = guild 行序错乱 → 文案 diff 必挂。
2. **guild 死代码勿碰**：guild_kill_progress 已是死函数，不迁移不删除（超范围），新函数另建。
3. **广播副作用**：野王行组必须同时广播（群发），走 ctx.side_effects 通道，不在行收集里混。
4. **副本 Boss dict 兜底**：ctx.monster 构造必须复刻 instance L3016-3028 三阶兜底，否则任务静默落空（#110 旧坑复发）。
5. **行为保真 vs 统一**：副本/世界Boss 不推每日/支线/公会/周常是**现状行为**，P3 别"顺手统一"——是玩法决策，交鱼鱼。
6. **导入触发注册**：订阅注册文件必须在 fire 前被 import；命令层显式 import 一行，不做自动发现魔法。
7. 测试跑法：主仓是运行中 bot 别热载 → 沙盒复制跑（conftest 父链），全量对照以"与基线同名单"为准（HANDOFF 铁律）。

## 11. 文件清单（本次 P0 commit）

- 本文件 docs/REFACTOR_v181_L3_P0_task.md（新建）
- docs/DESIGN_v181_L3_player_event_bus.md：状态行 ⬜→P0 完成；§3 排期表 P0 标 ✅ + 指向本文件；
  §0 痛点描述补"已随 P4-9 落 combat._handle_victory 壳"修订注。
