# 审计 C：副本层一致性（instance.py）审计报告

审计员：C（副本层）
依据：`design/new_world/27d_审计验收清单.md` C 部分 + `27b_多对多站位战斗引擎方案.md` §8.2/§6.3
范围：`game/commands/instance.py`（v2 多对多副本）
方式：只读核对，未修改任何文件。

---

## 一、清单 C 逐条标注

### C-1 开本：玩家按职业 default_rank 排站位（st["players"][qq]["rank"]）
✅ **通过**
- `_instance_start` 开本快照写入 rank/reach：`instance.py:1183-1185`（`C.CLASSES[...].get("default_rank",2)` / `.get("reach",...)`），uid=`p_{qq}`、buffs/stacks/defending/charging 齐全（1186-1190）。
- 老存档补缺：`_instance_ensure_player_fields` `instance.py:556-568`。
- `classes.py` 全职业 default_rank/reach 已落地（42-501 多行，近战 rank1/reach1、施法/射手/治疗/刺客 rank2/reach2）。
- 同层多人按入队顺序（`st["members"]` 保持），后按 spd 降序排行动序（`instance.py:1195`）。

### C-2 Boss 队伍：st["enemies"]（Boss+配置 minions 爪牙）；st["boss"] 兼容键=主目标
⚠️ **通过（有一处设计偏差，见深查 3）**
- `_instance_build_enemy_array` `instance.py:503-529`：Boss 主单位 = build_monster 产物；配置 minions 展开（×0.5、rank1、uid 唯一 `{base_uid}-m{mi}_{j}`、is_boss/is_elite=False、mech/mod 清空 `_scale_enemy_copy:478-500`）——均符合契约。
- `_instance_build_state:1028` / `_enter_stage_combat:475` / 切怪 `:1505` 均重建阵列。
- 兼容键 `st["boss"]`/`st["enemy"]` 初始与 enemies[0] 同对象（`enemies=[boss]`），`_instance_enemies_compact:548-553` 每轮敌人死亡后重指回 enemies[0]。
- **偏差**：Boss 本体 rank 实际=1（`drops.py:307` `rank = 2 if role in("caster","healer") else 1`，Boss role="boss"→rank1），与 §8.1「Boss(rank2)+爪牙(rank1)」不符 → 副本 Boss 与爪牙同处前排，站位无法形成"爪牙挡 Boss"（详见深查 3）。

### C-3 轮流行动保留；玩家行动传目标；Battle 构造透传 enemies/allies/charging
✅ **通过（charging 透传缺失 → 归入深查 4 缺陷）**
- 轮流行动保留：`_instance_act` 满轮转（1573-1604），超时自动防御（1311-1318）。
- 玩家传目标：`_instance_extract_target:576-607` 解析『攻击 <名>』『技能 <名> <目标>』；`instance.py:1332` 传入 `player_turn(target=...)`。
- Battle.from_state 透传 enemies（1348-1380）；allies 未传但副本 Boss 回合由 `_instance_boss_turn` 自管，`b.allies` 不使用 → 无功能影响。
- **charging 未透传/未写回**（见深查 4）→ 玩家蓄力技能在副本内回合间丢失。

### C-4 Boss 回合=敌方阵列各单位依次行动（rank升序→spd降序）；目标=select_target(threat)；嘲讽/多动保留
✅ **通过**
- `_instance_boss_turn:1679-1726`：`enemies = sorted(rank升序→spd降序)`（1694-1695）；主 Boss 多动（速度≥1.5×/2×均速，1700-1704）仅主单位额外补刀（1713-1723）。
- 每单位 `_instance_enemy_one_act:1728-1841`：目标=`FM.select_target(unit, 玩家阵列, threat_by_uid)`（1768）；嘲讽射程校验（1751-1757）；防御减半/闪避（1822-1830，1811 闪避走 `_monster_dodge_check` 由 Battle 内部处理）；逐单位独立 Battle（`enemies=[unit]`，1775-1792）。
- 敌单位蓄力 left-1/归零释放由引擎 `_enemy_turn→_enemy_charge_tick`（battle.py:2409-2522）处理，经原 st 引用持久化。

### C-5 玩家死亡→alive=False+移除压缩；敌方死亡→击杀奖励/任务统计逐单位；全灭胜负判定
✅ **通过**
- 玩家死亡：`_instance_act:1443-1454`（己方反伤/毒发）、`_instance_enemy_one_act:1835-1839`（Boss 击杀）；`st["alive"][qq]=False` + 目标池排除（`_instance_player_units:570-574` / 1742-1743 按 alive 过滤）。
- 敌方死亡：`_instance_enemies_compact:539-554` → `_instance_kill_reward:1855-1965` 按 `_last_killed` 逐单位结算（主怪全量+掉落、爪牙 ×0.5 无掉落、is_minion 判别）；主线击杀目标 `_instance_main_kill_progress:1967-2002`。
- 全灭：`_instance_act:1293/1448/1593`（失败）；`_instance_victory` / `_instance_defeat`。
- **注意**：玩家"阵列压缩"实际是按 alive 标志过滤而非 formation.compact 重排 rank（st["players"] 是 dict 非 list）；因玩家少且 rank 按职业静态，无重编号需求，功能等价。✅

### C-6 _instance_elite_scale 按人数缩放作用于 Boss 队伍全部单位
⚠️ **基本通过（缺"作用于全部单位"，因 elite 是单怪阵列）**
- `_instance_elite_scale:402-413` 在 `_enter_stage_combat:451` 与切怪 `:1502` 对 elite 主怪应用。
- 副本精英为单怪阵列（`_instance_build_enemy_array:511-512` 非 is_boss → `[boss]`），故"全单位"与"主怪"在此等价；若精英未来带爪牙，则只缩主怪不缩爪牙（与 §8.2 措辞略有出入，当前数据无此形态，⚠️豁免）。

### C-7 副本状态面板展示站位图
✅ **通过**
- `_instance_status:727-738`：`FM.formation_view(st["enemies"])`（敌方）+ `FM.formation_view(存活玩家)`（我方），蓄力单位带 ⏳；行动后 footer `:1611-1617` 展示 Boss 血量。

---

## 二、深查项代码级证据

### 1. st["boss"] 兼容键与 st["enemies"] 一致性
- **构建**：`_instance_build_enemy_array` `enemies=[boss]`（513）→ Boss 与 enemies[0] 同对象；DB 读回后为值一致的独立对象。
- **压缩同步**：`_instance_enemies_compact:548-553` 每轮 `st["boss"]=enemies[0]` / `st["enemy"]=enemies[0]`；全灭时 `setdefault` 保留原 Boss 引用供 `_instance_victory` 显示（2127）。
- **切怪/肃清/通关 busy=None 安全**：`_instance_act:1261` 前置 `if not st.get("boss")` 拦截（肃清态引导『深入』）；状态/行动 footer 均用 `st.get("boss") or (enemies[0]...)` 兜底（714/1611）；`instance.py` 内无对 None boss 的直接下标 `["hp"]`（全 guarded）。⚠️ **隐患**：因 Boss 与爪牙同为 rank1，`compact` 的稳定排序使 enemies[0] 恒为初始 Boss；但 Boss 先死、爪牙存活时，`st["boss"]` 静默变为首爪牙，`_instance_boss_turn:1696/1713` 的"主 Boss 多动"随之落到爪牙上（语义退化，非崩溃）。

### 2. 玩家站位 & 目标池排除
- `_instance_player_units:570-574` 与 `_instance_enemy_one_act:1742-1743` 均按 `st["alive"]` 过滤死亡玩家 → 死亡者不在 `select_target` 池中。✅
- reach 按职业：receive 在开本/ensure 已补全。✅

### 3. Boss 队伍生成（含畸形点）
- `_scale_enemy_copy:478-500`：×0.5 派生、rank/reach 传入、uid 唯一、is_boss/is_elite False、is_minion True、`mech=""`/`mod=""`（防逐单位 `_boss_mech` 多怪重复触发）✅。
- **畸形**：Boss 本体 rank=1（cf. `drops.py:307`），致副本 Boss 与爪牙同层 rank1。若要落实"Boss 后排、爪牙前排挡刀"（§8.1 意图），需数据层把副本 Boss 设 rank2/reach=2，命令层不需改。

### 4. 逐单位行动 / 蓄力 / 打断端到端
- **敌方蓄力**：`_instance_enemy_one_act:1775-1802` 传原 st 单位进单怪 Battle；`_enemy_turn(e=unit)`（battle.py:2381）绑定原引用 → `_enemy_charge_tick` 的 left 递减/归零释放直接改 st 单位，持久化成立。✅
- **玩家攻击命中蓄力 Boss 打断**：玩家回合 Battle 拷贝敌人（from_state `enemies=[dict(u)...]`）→ `_damage_enemy`（battle.py:3040）`_interrupt_charging` 清 copy.charging → `instance.py:1406 st["enemies"]=b.enemies` 整体写回 → 打断持久化。✅
- **❌ 玩家侧蓄力不持久（P1 缺陷）**：`_instance_act` 的 from_state（1348-1380）不含 `charging`，且写回块（1382-1404）**未写回 `b.charging`**；副本也无 `st["charging"][qq]`（§6.3 要求）。→ 玩家施放蓄力技能后当回合 `b.charging` 随即在下一回合新 Battle 构造时丢失，蓄力不会归零释放、返回 MP 逻辑也无法触发。副本内玩家读条技能完全不可用。

### 5. 目标选择：threat uid 映射 / 嘲讽射程
- **threat 键**：st 里 threat 按 `str(qq)`（`_enter_stage_combat:464`、`_instance_act:1421`）；`_instance_enemy_one_act:1744-1747` 把 `{玩家uid: threat[str(qq)]}` 转换给 `FM.select_target(unit, ..., threat=threat_by_uid)`，而 `select_target`（formation.py:64-68）按 `u["uid"]` 取威胁 → 映射正确。✅
- **嘲讽射程**：`_instance_enemy_one_act:1751-1757` 校验 taunt 玩家 `rank<=unit.reach` 且存活、在队；射程外视为无效并清除（1764-1766）。✅
- **防御减半/闪避/倒地**：防御减半 `:1822-1830`（引擎 `_damage_enemy` defending 段+命令层补格挡文案）；闪避由 Battle 内 `_monster_dodge_check` 判定；倒地 `:1835-1839`。✅

### 6. 击杀结算
- `_instance_kill_reward:1855-1965`：逐 `_last_killed` 单位；slave(is_minion)→×0.5 无掉落；mainlike→全量+掉落；任务/图鉴统计（精英/普通/首领存档）。✅
- 主线击杀目标只认主怪？`_instance_main_kill_progress:1989` 名称级匹配（非 is_boss 限定）——若主线目标名恰为爪牙名（当前数据只有 Boss 级目标名），仅 Boss 名命中主怪语义成立；单个 Boss+爪牙场景，`killed` 中主怪会带 is_boss 但不影响主线名匹配。✅
- 切怪/通关靠 `_instance_enemies_alive`（any hp>0）。✅

### 7. 仇恨累积 / taunt 生命周期
- dealt=敌方各阵位 hp 减少总和（`_instance_act:1408-1417`）；治疗仇恨（1424-1427）；防御嘲讽（1428-1437）；团队 taunt（1457-1465，拉满+2 回合）。✅
- taunt_target 生命周期：`_instance_enemy_one_act:1758-1766` 每次消耗递减、归零清除、目标死亡/射程外清除。✅
- **注意**：`st["contribution"]` 只加不减、跨阵位累计，delt 按敌方全阵——符合 §8.1"贡献=全阵列伤害合计"。

### 8. 轮流回合
- acted/turn 轮转（1573-1581）、全活者行动完 Boss 回合（1584-1600）、超时自动防御（1311-1318）、死亡跳过（1306/1577-1580）、无可行成员→失败（1291-1297）、全灭失败（1593-1600）。✅
- **round +1 只在玩家 Battle 内部**（1389 写回），Boss 回合不再额外 +1（注释 1587-1589）。✅

### 9. _instance_extract_target 与 combat.py 路由
- **『攻击 <名>』**：combat.py `attack`（941-964）解析 target_arg；副本内非数字/@ → 不 PVP → 路由 `_instance_act(...,"attack",None)`（962）；`_instance_extract_target(event,"attack")` 从 raw 消息再解析目标（`rest!="" and "@" not in rest and not rest.isdigit()`→返回名）→ **双解析不冲突**，instance 自取目标。✅
- **『技能 <名> <目标名>』❌（P1 缺陷，跨文件）**：combat.py `skill`（1018-1028）算 `_skill_target` 但**未把目标从 skill_name 剥离**；多 token 时 `skill_name="名 目标"`，`E.skill_info`（combat.py:1123 → engine.py:737 resolve 失败）返 None → "没有技能『名 目标』" 直接 return（1125-1131），**根本不进 instance**。→ `_instance_extract_target(event,"skill",skill_name)` 的 skill 目标分支（593-606）**不可达**，技能指定目标功能整链失效。

---

## 三、必须修复项（按严重程度排序）

| 序 | 级别 | 位置 | 问题 | 影响 |
|----|------|------|------|------|
| 1 | **P1** | combat.py:1016-1131 + instance.py:593-606 | 技能带目标『技能 <名> <目标名>』把目标并入 skill_name 传 `E.skill_info` → 查无此技被拒，`_instance_extract_target` 的 skill 目标分支整链不可达 | 副本内『技能 <名> <目标名>』完全失效（深查 9） |
| 2 | **P1** | instance.py:1348-1404 | `_instance_act` from_state 未传 charging、写回块未写回 `b.charging`，副本无 `st["charging"][qq]` | 副本内玩家蓄力技能（陨石术/大治疗术/蓄力斩等）回合间丢失、永不放（深查 4，违反 §6.3/§8.2 item3） |
| 3 | **P2** | drops.py:307 / instance.py:503-529 | 副本 Boss 本体 rank=1，与 §8.1"Boss(rank2)+爪牙(rank1)"不符；Boss 与爪牙同层，无法形成站位挡刀 | 副本 Boss 队无前/后排结构，目标选择/挡刀语义与设计偏离（深查 3） |
| 4 | **P3** | instance.py:548-553 / 1696 | `_instance_enemies_compact` 把 `st["boss"]=enemies[0]`；Boss 先死爪牙存活时 st["boss"] 变首爪牙，主 Boss 多动落到爪牙 | 边界情形下多动/状态显示指错单位（未崩溃） |
| 5 | **P3** | instance.py:451/502 + 402-413 | `_instance_elite_scale` 只对 elite 主怪生效（当前精英为单怪阵列等价）；若未来精英带爪牙，爪牙不吃缩放 | 与 §8.2"作用于 Boss 队伍全部单位"措辞差异，当前数据豁免 |

> 不再深入核实项：C-3 的 allies 未透传（`b.allies` 副本内未使用，无功能影响）。
