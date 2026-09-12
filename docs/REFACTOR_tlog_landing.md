# tlog 落地设计（战斗流水 + 行为流水）

> 2026-09-12 设计稿。上游形状 = 框架仓 `saintess_engine.tlog`（`85c47d0`）；
> 本文只管**内容侧怎么用**（采集点、kind 词表、字段、落库、回放、开关）。
> 排期对应 `framework/docs/engine-wiki/reference/roadmap.md` #4（战斗流水）/#5（行为流水）。

---

## 一、总则

1. **零引擎改动**：采集全部走「驱动层调用点 + actor.triggers 事件探针 + 内容侧 `@register_action`」，
   引擎只提供既有事件与动作注册口（`docs` 已证 23 个自然事件点位）。
2. **可拔插**：默认**不启用**（不启用时与现状**逐字一致**：零 IO、零字段、零 monkey-patch）。
   启用 = 在 `game/tlog_setup.py` 单点开（与 `log_setup.py` 对称）。
3. **kind 与字段由本仓定义**（框架不认）——词表见 §二，注册进 `content/data/tlogs.json`
   （编辑器 `tlogs` 域可直接改）。
4. **量控**：流水只记「可回放 + 可分析」所必需的东西。**不记**逐帧中间量（乘区明细、面板快照），
   那些要查时按 `battle.to_state()` 存档查。

---

## 二、kind 词表（#4 战斗 + #5 行为）

### 战斗（可回放闭环所需）

| kind | 何时发 | 字段 | 必填 |
|---|---|---|---|
| `battle.start` | 开战（`_open_battle` 成功构造后） | `btype` | ✔ |
| | | `seed`（随机种子；复现的根） | ✔ |
| | | `player`（重建指纹：class_name/level/class_tier/evolve_path/attributes/equipment/learned_skills/race） | ✔ |
| | | `enemies`（重建指纹：`[{id,name,role,lv}]`，供 `build_monster` 重造） | ✔ |
| | | `title_bonus` / `pet` / `dmg_mult`（非默认时才带） | |
| `battle.act` | 每次人类行动决策（`human_act` 前） | `uid`（行动者）/ `action` / `skill` / `target_uid` | ✔ |
| | | `p_acts`（第几次出手，便于对账） | ✔ |
| `battle.hit` | 引擎 `skill_hit` / `attack_hit` | `uid`（攻击者）/ `subject`（受击者）/ `dmg` / `crit` / `skill` | ✔ |
| `battle.taken` | 引擎 `on_taken` | `uid`（受击者）/ `caster` / `dmg`（实际扣血）/ `real` | ✔ |
| `battle.heal` | 引擎 `on_heal` | `uid`（被治疗者）/ `amount` | ✔ |
| `battle.down` | 引擎 `on_death` | `uid`（阵亡者）/ `by`（击杀者，来自 `on_kill` 配对） | ✔ |
| `battle.end` | 结算（`battle_settlement` / 命令层判定后） | `result`（victory/defeat/fled）/ `rounds`（`int(b._now)`+1）/ `p_acts` | ✔ |
| | | `exp` / `gold` / `drops`（结算产物，便于与掉落流水对账） | |

### 行为（#5；先登记、埋点分批）

| kind | 何时发 | 字段 |
|---|---|---|
| `quest.accept` / `quest.done` | 接/交任务 | `uid` / `quest`（id）/ `name` |
| `shop.buy` / `shop.sell` | 商店买卖 | `uid` / `item` / `qty` / `unit_price` / `gold_after` |
| `market.list` / `market.sold` | 玩家市场挂单/成交 | `uid` / `item` / `qty` / `price` |
| `drop.grant` | 掉落入包 | `uid` / `item` / `qty` / `source`（怪/副本/宝箱） |
| `instance.enter` / `instance.clear` | 副本进入/通关 | `uid` / `iid` / `rounds` / `deaths` |
| `level.up` | 升级 | `uid` / `to` / `points_gained` |
| `travel.move` | 换图 | `uid` / `from` / `to` |

> 行为流水的埋点**遵循同样纪律**：默认关（`tlog_setup.enabled()` 为假时函数体第一行 return）。

---

## 三、采集架构（零引擎改动）

```
命令层/服务层（驱动点）
   ├── battle.start  ← _open_battle（开战时一行）
   ├── battle.act    ← BattleTLog.attach() 包 b.human_act（只包一层，不是逐处改）
   └── battle.end    ← 结算点一行
引擎事件（探针）
   └── battle.hit/taken/heal/down ← 内容侧 @register_action("tlog_probe")
        挂法：attach 时给双方 actor 追加 triggers[事件] = [{"type": "tlog_probe", ...}]
```

要点：

* **探针是普通动作**（`fn(battle, caster, target, params, logs)`），注册落点沿用
  `ensure_engine_configured()`（import 即注册）——不新增引擎机制。
* **探针追加而非覆盖**：`actor["triggers"][ev] = 原有 + [探针]`（不能吃掉既有词条/机制声明）。
* **probe 只读不改**：拿 ctx 的 `caster/target/dmg` 转 record，绝不修改战斗状态
  （改了就破坏"采集不影响行为"这条底线）。
* 采集器句柄挂在 `battle._tlog`（非存档键，`to_state/from_state` 不受影响）。

---

## 四、回放复现（#4 的硬验收）

```
replay(records, *, build_player, build_monster) -> {"result": …, "rounds": …, "p_acts": …}
    ① 读 battle.start → 重建双方（指纹来自记录）→ random.seed(seed) → 起战斗
    ② 依序重演 battle.act（human_act(action, skill, actor, target)）
    ③ 返回结果；与 battle.end 记录逐项对比 → 一致 = 本场可复现
```

* **复现的根是 seed**：`battle.start` 必须带；不带的场次标记 `reproducible: false`（诚实记账）。
* 对比口径：`result` 全等 + `rounds` 全等 + `p_acts` 全等（数值细节由 hit 流水可另比对）。
* 回放**不需要**原战斗对象：重建即可（这也是"流水足够完整"的证明）。

---

## 五、落库（#5）

新表（内容侧 26 张表 → 27）：

```sql
CREATE TABLE IF NOT EXISTS tlog (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      REAL    NOT NULL,
    kind    TEXT    NOT NULL,
    actor   TEXT    NOT NULL DEFAULT '',
    tags    TEXT    NOT NULL DEFAULT '',     -- 逗号分隔
    fields  TEXT    NOT NULL DEFAULT '{}'    -- JSON 文本
);
CREATE INDEX IF NOT EXISTS idx_tlog_actor_ts ON tlog(actor, ts);
CREATE INDEX IF NOT EXISTS idx_tlog_kind_ts  ON tlog(kind, ts);
```

* 出口实现：`game/services/tlog_db_sink.py::SQLiteSink`（`write(records)` / `flush()`），
  走既有 `store` 连接与事务（`atomic`），**批量写**（`executemany`）。
* 读口：`SQLiteReader`（同文件的 `read_records()`）→ 直接喂 `saintess_engine.tlog.Reader`。
* **不写进存档路径**：流水是旁路表，`battle_state` 等存档不受影响。
* 体量：单场战斗约 20~80 条；行为流水按事件量。默认 sink = `JSONLSink("data/tlog.jsonl")`
  （先落文件、易分析、零 DB 风险），SQLiteSink 作为可选（配置开）。

---

## 六、开关（`game/tlog_setup.py`）

```python
enabled() -> bool          # 环境变量 DRAGONFALL_TLOG=1 或已显式 enable()
tlog() -> TLog | None      # 全局流水实例（未启用 → None → 埋点第一行 return）
enable(sinks=…, kinds=…)   # 显式开（测试/运维）
disable()                  # 关（回默认：零行为）
```

* **默认关**：不设环境变量 = 与现状逐字一致（不给线上加 IO 风险）。
* 分析脚本 `scripts/tlog_report.py` 不依赖开关（直接读文件/库）。

---

## 七、验收

| # | 项 | 判据 |
|---|---|---|
| 4 | 战斗流水完整 | 打完一场 → 有 `start/act×N/hit…/end`，且 `act` 条数 == `p_acts` |
| 4 | **能回放复现同一场** | `replay(records)` 的 result/rounds/p_acts == `battle.end` 记录 |
| 4 | 采集不影响行为 | 启用/不启用两跑，同 seed 下 result+rounds 一致（**同场同结果**） |
| 5 | 至少 3 类行为埋点 | quest / shop / drop 各有一条流水可查 |
| 5 | 分析脚本 | `tlog_report.py --actor <uid> --since …` 出 markdown 汇总 |
| 5 | 落库往返 | JSONL 与 SQLite 两条出口读回一致（同一批记录） |

## 八、决策（实施时定，已按此落地）

1. **默认出口 = JSONL 文件**（`data/tlog.jsonl`，可 grep / 可脱敏 / 零 DB 风险）；
   `SQLiteSink` 作为可选（配置开）。开关默认**关**（`DRAGONFALL_TLOG=1` 才启用）。
2. **行为埋点范围 = quest / shop / drop / instance 四类**（覆盖核心且量可控）；
   其余 kind（`level.up` / `travel.move`）**先登记词表、暂不埋点**，要加时按同一纪律加。
3. **指令级流水（`cmd.*`）暂不做**：量最大，且有现成的宿主日志可查；词表留位，需要时再加。
