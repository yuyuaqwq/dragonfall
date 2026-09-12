# REFACTOR v185 —— 副本形状 → 引擎（路线图 #8，字段级设计）

> 目标：把「一次副本运行」的**准入 / 进度 / 名单**三件形状搬进引擎，与具体副本表解耦。
> 判据（roadmap §一）：把常量、枚举、名词全拿掉，逻辑还成立吗？成立 = 形状。
> 本轮：**框架侧新建 `saintess_engine/run/`** · **内容侧准入链 / 进度 / 名单三处收口** ·
> **编辑器新增 `instances` 域**。依赖 #6（地图 = `space`，房间连通）、#7（产出 = `loot`，房间资源池）已建成。

---

## 一、现状：一份形状，散在四个文件、五处手写

| # | 位置 | 内容 | 性质 |
|---|---|---|---|
| 1 | `game/commands/world.py:1237` `_instance_gate_block` | 徒步进图三档准入（任务放行 → 持钥匙 → 已通关豁免），**首档命中即放行** | 准入链（副本一档） |
| 2 | `game/commands/instance.py:2088` `_instance_start` | 开本准入：队伍人数 → 队长身份 → 全队等级/血量/战斗中/副业等待 → 钥匙（**扣**）→ 入口位置 → 体力（扣） | 准入链（副本二档） |
| 3 | `game/commands/instance.py:314` 恢复路径 | 「与 `_instance_start` 同规则」的人数/等级/0 血/战斗中**四连重写**（注释自己承认同源） | 准入链（第三份） |
| 4 | `game/commands/instance.py:100` `加入战斗` | 3a-3d 四条：重复加入 / 满员 / 敌方全灭 / 0 血 | 准入链（第四份） |
| 5 | `game/commands/instance.py:1822` `_instance_build_state` | 同一个 25 键状态 dict **写了三遍**（有怪层 / 单层 Boss 房 / 老副本兜底） | 进度 + 名单初值 |
| 6 | `game/commands/instance.py:361` `深入` | 层推进：`stage_idx+1` + 新层 `stage_pending` 组装 + 机关 `skip_elite/skip_wave` + 逐队员清 buff/上锁 | 进度（线性） |
| 7 | `game/commands/instance_router.py:316/345/451` | 「敌人清空 → 回地图模式」的重置块**逐字抄了三遍**（暗格守卫 / 房间 / 分层） | 进度（收尾） |
| 8 | `game/commands/instance.py:1637` `_stage_virtual_map` + `world.py:1621` `_instance_dungeon_move` | 两套「当前节点」：分层用 `stage_idx`，房间用 `cur_subarea` | 进度（两形态） |
| 9 | `game/commands/instance.py:2004/2028` `consume_monster` / `consume_poi_loot` | 房间怪池 / POI 池 / 资源池扣减（**不足只给剩余**） | 进度（剩余池） |
| 10 | 63 处 `st["members"]` / `st["alive"]` 读写 + `_instance_current_members:1355` + `_router_has_living_players:120` | 成员集合 + 队长 + 存活 + 「在场过滤」（成员 ∩ 当前队伍 ∩ 存活） | 名单 |
| 11 | `instance.py` 全员等级排序（恢复路径）、`_instance_living_player_cts`、`_instance_next_actor` | 名单的**顺序**语义（按速度降序 = CTB 行动序） | 名单（顺序） |

问题不是行数：`_instance_gate_block` 通篇没有一个游戏名词（换成任何"需要钥匙的房间"照样成立），
`_instance_current_members` 只做集合运算 —— 它们是形状，却长在内容仓里，且同一语义四处各写一份。

## 二、剥出来的形状：`saintess_engine/run/`

一次运行 = **谁能进（准入）** · **谁在里面（名单）** · **打到哪了（进度）**。三个子形状，一个模块。

```python
from saintess_engine.run import Admission, Rule, Progress, Roster

# ① 准入链：有序规则，首拒即返；副作用（消耗）延迟到全过才执行
adm = Admission([
    Rule("party",   check=has_party,            reason="你还没有队伍！先『组队 <对方名字>』～"),
    Rule("leader",  check=is_leader,            reason="只有队长才能开启副本！"),
    Rule("size",    check=size_ok,              reason=size_text),      # reason 可以是 callable(ctx)
    Rule("level",   check=all_level_ok,         reason=level_text),
    Rule("key",     check=has_key, reason=key_text,
                    consume=deduct_key),                                # ★ 副作用延迟到全过
    Rule("entry",   check=at_entrance,          reason=entry_text),
    Rule("stamina", check=stamina_ok, reason=stamina_text,
                    consume=pay_stamina),
], name="open")

v = adm.check(ctx)          # ctx 由内容侧给（dict 或任意对象）
v.ok        # ⬜ True/False
v.rule      # 首个拒绝的规则名（ok 时 None）
v.reason    # 该规则给的理由（内容侧措辞，逐字可用）——ok 时 ""
v.trace     # 逐条判定记录（规则名 → "pass"/"deny"/"skip"），审计与门禁用
adm.audit() # 重名 / 空链 / 缺 check / consume 与 check 不配对

# ② 进度：有序节点 + 每节点多个「剩余池」+ 当前位置（线性推进 or 按 key 跳转）
p = Progress([{"key": "l1", "name": "营地前哨"}, {"key": "l2", "name": "酋长帐篷"}])
p.current_key          # "l1"
p.push("l1", "monsters", mon_def)        # 入池
p.take("l1", "monsters")                 # 弹一只（空 → None）
p.left("l1", "monsters")                 # 剩几只
p.node_cleared("l1")                     # 该节点所有池都空
p.is_last() / p.advance()                # 末节点 / 推进一层（末节点返回 False）
p.goto("sa_3")                           # 房间形态：直接跳（连通性由 space 管，本形状不管）
p.done                                   # 全部节点清空
p.budget("gold") / p.spend("gold", 30)   # 资源池：不足只给剩余（返回实扣量）
p.to_dict() / Progress.from_dict(d)      # 存档往返

# ③ 名单：成员（有序 = CTB 行动序）+ 队长 + 存活 + 在场过滤
r = Roster(members=["1", "2"], leader="1")
r.members / r.leader / r.is_member(k) / r.alive(k) / r.set_alive(k, False)
r.living()                     # 存活成员（有序）
r.keep(pred)                   # 过滤（在场：成员 ∩ 当前队伍）
r.sort_by(keyfunc)             # 按速度重排（内容侧给 key）
r.join(k) / r.leave(k)         # 幂等追加 / 移除（队长离队 → 队长顺位）
r.any_alive()
r.to_dict() / Roster.from_dict(d)
```

| 形状 | 语义 | 谁给 |
|---|---|---|
| `Rule` | 命名的单条校验：`check(ctx) → None/True 通过`、`str 拒绝（措辞）`、`False 拒绝（通用措辞）` | 引擎（规则体内容侧写） |
| `Admission` | 有序链、**首拒即返**（后续规则不再求值）、**副作用延迟**（全过才按序执行一次）、`audit` | 引擎 |
| `Progress` | 有序节点 + 每节点具名剩余池（`push/take/left/cleared`）+ 当前位置（`advance`/`goto`）+ 资源预算（`budget/spend` 不足给剩余）+ 往返 | 引擎（节点 key 与池名是内容侧字符串） |
| `Roster` | 有序成员 + 队长 + 存活表 + 过滤/排序/加入退出/往返 | 引擎 |
| 槽位定义（层里有哪些怪 / 房间有几只 / POI 表） | **数据**，引擎不认识 | 内容侧 |

**两种准入语义**（写内容侧时实测发现：「徒步进图」是**任一满足即放行**，与开本的「全部满足」
是两种真实的准入形状，引擎侧据此补了 `mode` —— 缺一种就会被写成单条 OR 规则、丢掉 trace 粒度）：

| `mode` | 含义 | 判定 | 本轮用在哪 |
|---|---|---|---|
| `"all"`（默认） | 全部满足才放行（多重门槛） | 首拒即返 | 开本 / 恢复旧进度 / 加入战斗 |
| `"any"` | 任一满足即放行（多条放行通道） | 首个通过即止 | 徒步进图（任务放行 / 持有钥匙 / 已通关 三选一） |

**零知识**：引擎不出现「副本 / 层 / 房间 / 队伍 / 队长 / 钥匙」这些词，只认
`rule / node / pool / member / leader / budget`。门禁静态扫源码常量（跳过文档串）。

## 三、内容侧适配

### 3.1 准入：`game/core/instance_gate.py` 升级为「唯一真相源」

现有两函数（`find_instance_key_item` / `instance_cleared_qq`）保留（三路匹配是内容规则），
**新增**措辞表 + 规则工厂 + 四个链（实测 API）：

| 链 | 用在哪 | 规则序列 |
|---|---|---|
| `open_admission(ctx)` | `instance._instance_start` | **每名成员一条**（等级→血→战斗中→副业等待）→ key（consume）→ entry → stamina（consume）；队伍解析另走 `resolve_open_members()` |
| `resume_admission(ctx)` | `instance.py` 恢复路径 | size → 每名成员（等级/血/战斗中，**不查副业等待**） |
| `join_admission(ctx)` | `instance.py` 加入战斗 | party → member_view → has_battle → same_inst → over/retreated/is_instance → dupe/full/enemy_alive/hp/profile（链内写 `ctx["st"]`） |
| `walk_admission(ctx)` | `world._instance_gate_block` | quest / key / cleared —— `mode="any"`（只校验持有、不扣钥匙） |

**判定与措辞都在内容侧**（引擎只给「首拒即返 / 首个通过即止」的执行器）；调用方拿到 `v.reason` 直接 `yield`。
★ **一个成员一条规则**（而不是「一个检查项一条规则」）：只有这样才能保住旧实现的
「按队员逐个过四关」顺序 —— 否则 m1 掉血 + m2 等级不足时会报 m2 的等级，与旧行为不同（门禁钉住）。
措辞只有一处来源：新增 `stamina_short_msg()` 后 `commands/base._spend_stamina` 也改调它。

### 3.2 名单 / 进度：新增 `game/core/instance_run.py`（适配层，已建成）

| 旧 | 新（实测 API） |
|---|---|
| `st["members"]` / `st["alive"]` 散读散写（63 处） | `roster_of(st)` 造 `Roster` 视图 / `write_roster(st, r)` 写回；`alive_of` / `set_alive` / `living_members` / `living_players` / `sort_members_by` —— **st 的键名与形状一字不改** |
| `_instance_current_members` | `current_members(group_id, st)`（内部 = `Roster.only(party)`，**签名与语义逐字保留**） |
| `_router_has_living_players` | `living_players(st)`（= `Roster.living()` ∩ `players[k].hp > 0`） |
| `st["stage_pending"]` / `stage_idx` | `stages_progress(st)` → 节点 = 层，池 `units`；`pending_left` / `pending_take` / `stage_advance` / `is_last_stage` / `stage_name` |
| `rooms[x]["monsters_left"]` / `pois_left` | `rooms_progress(st)` → 节点 = 房间，池 `monsters` / `pois`；`take_monster` / `take_poi` / `poi_left` / `monsters_left` / `mark_boss_room_done` |
| `st["resources_pool"]`（gold/mats/equip，不足只给剩余） | `Progress` 预算：`spend_gold` / `spend_mat` / `spend_equip` |
| `_instance_build_state` 三份 25 键 dict | 一份按分支补键的构造器（**逐键全等**由门禁锁定） |

★ 两种形态共用**同一个** `Progress`：分层 = 线性节点 + 单池，房间 = 任意跳节点 + 双池 ——
「当前在哪一站 / 这一站还剩什么 / 能不能推进 / 是不是最后一站」四件事只写一遍。

**存档兼容红线**：`st` 是玩家存档里的 JSON（`battle.state`）。本层只做「视图 + 写入收口」，
**键名、类型、缺失语义全部保持原样**；`to_dict/from_dict` 仅用于门禁与编辑器，不替换存档格式。

### 3.3 三处「清空 → 回地图模式」的重复块

`instance_router.py` 的三处（暗格守卫 / 房间 / 分层）逐字相同的一段（清 boss/enemy/enemies、
清宠物 `_last_hit_at`、解锁、`_instance_save`）→ 收敛成 `instance_run` 的两个函数：
`clear_battle_view(st, **flags)`（清视图字段 + `mode="map"`，**标志差异留给调用方显式写**：
暗格守卫给 `secret_chest=True`、房间/分层给 `stage_cleared=True, over=False`）与
`clear_pet_hits(st)`；解锁与存档仍由调用方做（它们要 `self`）。

## 四、编辑器 `instances` 域

- `schemas/instances.schema.json`：一条 = 一个副本 `{name, lv, icon, min_players, max_players,
  key_item, key_source, entry{map,subarea}, boss, hp_mult, atk_mult, stages[{name, monsters, elite,
  boss, pois, secret, npc}], gold, exp, materials, ...}`；**零 enum**（boss/怪角色名是内容词汇）。
- `editor/packages.py` 一行 + 词典 + 字段分组。
- **进度视图**：`GET /api/package/<id>/d/instances/<key>/run` —— 用引擎**同一份 `Progress`**
  把 `stages` 展开成节点表（每层：怪数/精英/Boss/POI/隐藏房间）并给出 `is_last` 标记；
  数据不合法（层空 / Boss 不在末层）如实报错，不假装有内容。

## 五、验收（全部要实跑）

| # | 项 | 判据 |
|---|---|---|
| 1 | 框架门禁 | `tests/test_run.py`（准入顺序与首拒即返 / 副作用延迟 / 审计 / 进度池与推进与往返 / 预算不足给剩余 / 名单过滤排序 / 零知识静态扫描） |
| 2 | 框架全量 | 纯度 / 中立性 / wiki 行号三门禁绿；`MODULE_ATTRS` 登记 `run`；wiki README 数字同步 |
| 3 | ★ 内容侧逐格一致·准入 | `tests/test_v185_instance_admission.py`：**旧判定链逐字冻结进测试**（sha256 自检），22 副本 × 12 场景矩阵逐格比对 `(ok, rule, reason)`；两条链（开本 / 徒步）各一组 |
| 4 | ★ 内容侧逐格一致·进度/名单 | `tests/test_v185_instance_run.py`：分层/房间两形态的进度推进逐格比对（含 `深入` 的 pending 组装、机关 skip 分支、末层/通关判定）；`_instance_build_state` 三份 dict **逐键全等**；`_instance_current_members` 全矩阵比对；`resources_pool` 扣减不足给剩余逐项 |
| 5 | 真实库回归 | 游戏仓全量（当前 267 + 新门禁）/ 数值门禁 18/18 / `compileall` 零错 |
| 6 | 编辑器 | `tests/test_editor_instance.py`：域注册 / 词典 / schema 校验 / 进度视图派生 / HTTP 端到端 |

## 六、已登记的有意差异

| # | 差异 | 性质 |
|---|---|---|
| D1 | **开本钥匙的扣减时机**：旧实现「全队校验过 → 扣钥匙 → 位置校验 → 体力扣减」，**位置或体力拒绝时钥匙已经被扣走**（白扣）。新形状把 `consume` 延迟到全过 → 不会再白扣 | **修 bug**（旧行为可复现，见 §六.1） |

### 6.1 D1 复现口径（先取证再改）

`_instance_start` 顺序逐行确认（**旧源码行号，改动前 `game/commands/instance.py`**）：
① 队伍/等级/血/战斗中/副业（约 2110-2165）② 钥匙 —— `db.remove_item(group_id, qq_id, key_entry["key"])`
在 **2189** ③ 入口位置 —— 拒绝即 `return` 在 **2238** ④ 体力 —— 不足即 `return` 在 **2243**。
→ 造场景：队长**不在入口**（或**体力 < 20**）且**持有钥匙**，输入『副本 <名字>』：钥匙被扣、人没进本。
门禁登记本案并断言**新行为不扣**（`drop_key` 一次都没被调用）。

## 七、自己拍板的四项

| 项 | 决定 | 理由 |
|---|---|---|
| 模块名 | `run` | 通用名词（一次运行）；比 `instance`/`dungeon` 中性，与 `space`/`loot` 同规格 |
| 三个子形状是否拆包 | 同包三文件（`admission/progress/roster`） | 一次运行本就是一体的；拆三个顶层包会让 `run` 的语义碎掉 |
| 存档格式 | **不动**（`st` 键名照旧，适配层做视图） | 改存档 = 迁移玩家数据，超出「搬形状」范围；且会撞上线上存档兼容红线 |
| 结算（通关/失败/撤退的奖励与清理） | **本轮不抽** | 与内容奖励/成就/回城强耦合；形状边界在有 frozen 证据前不清晰 |

## 八、不做（本轮明确排除）

- 不改 `INSTANCES` 数据（`data/instances.py` 零改动）、不改 `instances_stages.json`
- 不动副本战斗（`instance_battle.py` / `saintess_engine.battle` 侧零改动）
- 不合并 `st["boss"]` 与 `st["enemies"]` 的双轨（v181 遗留，另案）
- 不动房间连通性判定（已属 #6 `space`）
- 不做「运行阶段状态机」（`mode`/`over`/`cleared`/`retreated`）：迁移面广、冻结证据弱，留待需要时再抽

---

## 九、落地记录（2026-09-12 晚 · 内容侧接线轮）

### 分工（同批并发，**按文件切**避免同仓撞车）
| 块 | 文件 | 内容 |
|---|---|---|
| 甲 | `game/commands/instance.py` | 名单（roster）· 分层进度（stage_idx/stage_pending）· 资源池（resources_pool）· `_instance_build_state` 三份 25 键 dict 合一 |
| 乙 | `game/commands/instance_router.py` · `game/core/poi_effects.py` · `game/commands/instance_battle.py` · `game/commands/world.py` | 房间剩余池（monsters_left/pois_left）· 三处「清空→回地图模式」重复块 · 名单视图 |

适配层 `game/core/instance_run.py` 在接线后成为**唯一实现**（不再有第二份散写）。

### 门禁 `tests/test_v185_instance_run.py`（30 断言，五组）
| 组 | 内容 |
|---|---|
| A. 行为冻结 | 真跑 13 步副本流程（开本 → 副本地图 → 调查 POI → 深入各分支 → 撤退 → 重开 → 离开），把每一步的**命令输出 + battle.state 快照**与 `tests/_v185run_baseline.json`（**采自接线前 commit `851913a`**）逐字比对。随机固定 seed；`world_id`（`inst:<uuid>`）等易变字段归一化。**有牙自检**：改一格必红（实测报「st 字段变了: ['stage_idx']」）。 |
| B. 旧实现对账 | `current_members` / `living_players` 与**从 `851913a` 冻结的旧源码片段**在 8 个状态矩阵上逐格比对；内嵌片段带「确实来自该提交」的逐字自检（防凭记忆重写旧语义）。 |
| C. 适配层契约 | 资源池「不足只给剩余」（返回实扣量）· 房间池弹怪/移 POI/标记 Boss 房 · 清空块的标志语义（暗格 `secret_chest` vs 房间/分层 `stage_cleared, over=False`）。 |
| D. 合成房间战 | 普通房（非 Boss 房）清怪 → 回地图模式那一支：合成 st + 真走 router → 清空后的 st 快照与接线前基线逐字比对。**这一支原先没有任何测试覆盖**（实测把旧代码 `stage_cleared = True` 改成 `False` 后，`test_battle_n5b4_instance_router` 59 / `test_commands_layer` 19 / `test_v141_instance_world` 101 个断言仍全绿）—— 补上后猴补即报红。 |
| E. 状态构造三支分支 | `_instance_build_state` 三份 25 键 dict 合一后的**三支分支**（有怪层 / 单层 Boss 房 / 无 stages 老副本）各造一次 st，比对**键集 + 关键字段**：三份合一不许丢键也不许多键（猴补实测：把 `dot_pending` 改名 → A 组报「st 键集变了」+ E 组三支全红）。 |

### 采集脚本与基线
基线由 `--write` 分支在同一份测试代码上生成（**必须在接线前的代码上跑**）：本轮用
`git worktree add --detach <tmp>/qq_base/data/plugins/dragonfall 851913a` 拉一份干净副本
（submodule 用 `git -c protocol.file.allow=always submodule update --init framework` 接上），
在那里跑 `python tests/test_v185_instance_run.py --write` 生成基线，再把 fixture 拿回主工作树。
> 细节：私有副本必须落在 `<X>/data/plugins/dragonfall/` 布局下，`tests/conftest.py` 靠这个路径
> 解析 `data.plugins.dragonfall.*`；`instance_run` 是**当时未提交**的文件，需手动拷进副本。
