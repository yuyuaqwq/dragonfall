# L3 玩家事件层 —— 新订阅方接入指南（v181 L3-P4 收官文档）

> 目标读者：给战斗胜利/击杀加"玩家级反应"的开发者（包括未来的格温）。
> 读完本文件 2 分钟内能加好一个新玩法反应，不用碰任何结算函数。
> 权威思想：docs/DESIGN_v181_L3_player_event_bus.md；实施细节：docs/REFACTOR_v181_L3_P0_task.md。

## 0. 一分钟上手

想让"玩家赢得一场战斗后"发生点什么（推任务进度/解锁成就/发奖励/广播……）：

```python
# game/services/player_event_subscribers.py（或你自己的新模块）
from ..services.player_event_bus import register

def my_handler(ctx):
    # ctx 只读字段 + 回填行；写 DB 自由（db/store 均可）
    player = ctx["player"]
    ...做反应...
    return ["📜 新玩法：你的进度 3/5"]   # 要回填进战斗结算的行；无行返回 []/None

register("battle_victory", my_handler, blank_line=True)
# 事件：battle_victory（起步全集 battle_defeat/monster_killed 已定义，需要再启用）
# blank_line=True = 该段行前自动补一个空行（对齐结算文案排版）；False = 紧跟上一段
```

**不需要**：改 combat._handle_victory / instance.* / _worldboss_act / 任何结算函数。

## 1. 事件与 fire 位点（谁在什么时候 fire）

| 事件 | fire 位点 | ctx.kind | 频率 |
|---|---|---|---|
| battle_victory | combat._handle_victory 壳（野外/塔/野王） | field | 每场胜利 1 次（单玩家） |
| battle_victory | instance._instance_kill_reward（副本小怪/精英/守卫战） | instance | 每场战斗 × 存活成员 |
| battle_victory | instance._instance_victory（副本 Boss 通关） | instance | 通关 × 存活成员 |
| battle_victory | combat._worldboss_act（世界Boss 死亡） | worldboss | Boss 死 × 每个 contrib>0 玩家 |
| battle_defeat | （无 fire 点，起步空跑） | — | 成就失败计数类未来用 |
| monster_killed | （无 fire 点，起步零订阅；胜利按 killed 列表逐只在 quests 订阅内处理） | — | 独立击杀场景未来用 |

> PVP **不 fire**（打人不是杀怪，monster=None）。副本 Boss 战**不会**重复 fire
> （Boss 死亡只走 _instance_victory，_instance_kill_reward 只在非 Boss 房/切怪/层清调）。

## 2. ctx 字段（fire 点已构造好，订阅方只读 + 回填）

```python
ctx = {
    "event": "battle_victory",      # fire 自动补
    "kind": "field"|"instance"|"worldboss",
    "group_id": str, "qq_id": str,  # 本 ctx 结算的玩家（副本/世界Boss 逐成员各 fire 一次）
    "player": dict,                 # 当前结算 player（field 可能被 levelup 订阅重绑）
    "monster": dict,                # 主怪/首领（name/lv/is_boss/is_elite/id...）；副本/世界Boss 有兜底
    "killed": [dict],               # 全部击杀单位（field=主怪打头+extra_kills；副本=_last_killed）
    "side_effects": [],             # 非文案副作用通道：append {"type": "broadcast", "text": ...}（fire 点处理）
    "meta": {...},                  # 场景附加事实（instance: inst_id/flawless；worldboss 空）
}
```

⚠️ 订阅方不要依赖 `ctx["player"]` 里的 exp/gold 为"最新"（资源结算顺序因入口而异）；
需要最新值自己 `db.get_player`。副本组队 fire 时行由调用方加了成员名前缀
（`  {name}：你的行`），订阅方**不要自带成员名前缀**。

## 3. kind 语义（订阅方按什么决定跑不跑）

鱼鱼 2026-09-09 语义决策：**任何击杀都算数**——quests/公会等"击杀反应"对三个 kind
全推（老配置副本/世界Boss 不推任务 = 各入口独立实现时漏接，非设计）。kind 分支只在两处：

1. **升级反应**（levelup 订阅）：仅 field。副本/世界Boss 结算**不主动升级**
   （副本 docstring 铁律：check_player_level_up 回满 hp 破坏连续战斗节奏，经验攒到出副本
   统一结算；玩家副本内后续读档仍会惰性升级——store/players.py v95.7 机制，不受本守卫影响）。
   新订阅方若做"升级/回血"类副作用，同样加 `if ctx.get("kind") != "field": return []`。
2. **成就 extra 组装**（achievements 订阅）：field=defeated_hidden_monsters /
   instance=inst_id+flawless / worldboss=worldboss:1——场景决定 extra，解锁判定全局一致。

其余反应（任务/周常/公会/图鉴……）按**怪属性/名字**自己决定（quest_kill_progress 内部
已按 obj.kill 前缀精确 / kill_any / kill_elite / kill_boss 匹配），不需要 kind 分支。

## 4. blank_line 空行规则（对齐结算排版）

总线按注册顺序逐订阅方执行，段间空行由 blank_line 参数统一实现，语义 =
原手写 `if lines: lines.append("")`（lines 非空且上一行非空才补一个 ""）。

注册顺序 = 结算文案行顺序。现有 6 订阅方顺序（勿乱插——新订阅方按行序插在合适位置）：

| # | 订阅方 | 事件 | blank | 触发条件（自判） | 行前缀 |
|---|---|---|---|---|---|
| 1 | guild_daily（公会每日任务） | battle_victory | False | 有公会 | 🎯 |
| 2 | levelup（胜利升级） | battle_victory | True | kind=field | 🎉 |
| 3 | quests（主线/每日/支线）+ weekly | battle_victory | True | killed 逐只按怪匹配 | 📜 |
| 4 | wild_king（野王死亡） | battle_victory | True | monster.id 前缀 b_guard_ | 👑 |
| 5 | tower_guard（塔卫突破） | battle_victory | True | monster.id 前缀 tower_ | 🏯 |
| 6 | achievements（成就解锁） | battle_victory | True | kind 分支组 extra | 🏆 |

## 5. 订阅方编写规范（北极星对齐）

- **薄壳**：只做"查自己进度 → 推进 → 回填行"，逻辑留在原 service/模块（照 P2 先例：
  guild/quests/levelup 都是 1:1 搬原函数进 handler 壳）。
- **容错**：订阅方抛异常 → 总线 log + 跳过（不阻断其他订阅方，对齐命令层宽容铁律）。
  但**别故意吞异常**——总线已兜底，能裸奔就裸奔（log 比静默好排查）。
- **行格式**：返回纯文本行列表；空行由 blank 统一补（订阅方段内不要自带首/尾空行）。
  副本入口会给你的行加"成员名前缀"，你的行内容保持与 field 一致（同文案同 diff）。
- **广播**：要群发 → append 到 `ctx["side_effects"]`（fire 点负责 `_broadcast`），别直接发。
- **DB**：写库自由（db/store）；需要 player 最新值自己读，不赌 ctx.player。
- **不 import commands***：订阅注册模块放 services 层（services 禁 import commands 红线）。
  需要命令层能力的逻辑先下沉 services（先例：tower/weekly 状态族下沉 P2a）。

## 6. 接入示例：给"剧情进度"加击杀反应

场景：新主线系统"每杀 3 只任意精英推进一段剧情"。

```python
# game/services/story_progress.py（假想新模块）
from .. import db

def _state(qq_id):
    raw = db.get_event_state(f"story_{qq_id}")
    ...读/建状态...

def on_kill(ctx):
    """订阅 battle_victory：统计精英击杀 → 推进剧情段。"""
    st = _state(ctx["qq_id"])
    elites = [k for k in ctx["killed"] if k.get("is_elite") or k.get("is_boss")]
    if not elites or st.get("seg_done"):
        return []
    st["elite_kills"] = int(st.get("elite_kills") or 0) + len(elites)
    if st["elite_kills"] >= 3:
        st["seg_done"] = True
        db.set_event_state(f"story_{ctx['qq_id']}", json.dumps(st, ensure_ascii=False))
        return ["📖 剧情推进：你击破了三头精英，传闻中的遗迹入口出现了！（『剧情』查看）"]
    db.set_event_state(...)
    return []
```

在 player_event_subscribers.py（或你自己的模块）注册一行即可，**零结算函数改动**。

> ⚠️ 反例警示（v181 L3-P4 收尾记录）：**图鉴/声望不在本总线**——它们仍由 settlement 段8
> bump_kill_stats 统一推进（P0 差异表 #1 范围外：行夹资源行中段，迁订阅 = 行序重组 + 零收益；
> 本指南因此不给"声望订阅示例"——照抄会与结算段双发）。rule_fire 行为规则（settlement 段20）
> 同理不在 L3。判断标准：该反应现在是否已在 settlement / 现有订阅方推进——**已在做的别重复接**；
> 只有"现有代码没在做的新反应"才注册订阅。

## 7. 验证（提交前必跑）

- 单测/集成：`PY tests/test_l3_player_events.py`（18 断言，订阅方行为网）+
  `PY tests/test_player_event_bus.py`（总线规则 15 断言）
- 全量：`PY scripts/run_all_tests.py`（当前 209 文件全绿基线，含 2 个 L3 测试文件）
- 注意：改行序/文案 = 动结算视觉 → 跑 snapshot 快照测试
  `PY tests/test_services_battle_settlement_snapshot.py` 对拍
- 提交格式：`v181.L3-xxx <改动>`；双仓 push（GitHub yuyuaqwq）
