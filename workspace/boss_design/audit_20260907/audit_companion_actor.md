收到，停止继续读代码，基于已审计内容整理最终报告。

---

# 随从/召唤物/宠物 actor 化残余专用路径审计报告（battle.py 及关联文件）

**审计对象**：`C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/battle.py`（10143 行，v180-C 后）

**总体判断**：v180-C 已将召唤物（kind=summon）与宠物（kind=pet）统一收进 `self.companions`，并配套了 guard/auto_act/untargetable/hidden 字段——但**引擎层大量消费点仍是"按身份读 self.pet / self.summons 专用容器"的专用路径**，字段驱动只是"装进同一个列表"，没有真正被通用逻辑按字段消费。4 个方向的问题如下。

---

## 一、按 kind/tid/身份/名字特判的残余（应字段驱动）

**1. battle.py:9141 清理死亡随从 —— kind=pet 特判（低危，但暴露"pet 无 hp 字段"的设计裂缝）**
```python
for c in list(self.companions):
    if c.get("kind") == "pet" or "hp" not in c:   # ← 按 kind 特判
        continue
    if c.get("hp", 0) <= 0:
        ... self.companions.remove(c)
```
- **类型**：kind 特判残余（且与 `_pet_ensure_actor` 注释宣称"字段即能力"矛盾）。
- **影响**：说明宠物 actor **没有 hp 容器**（只有 level/satiety），一旦未来给宠物配 hp（随从通用受击），此处自动失效；同时宠物纯靠 kind 白名单免于误清，若未来出现第三种无 hp 实体又要再加特判。
- **建议**：清理条件改按**字段**判定：`if c.get("untargetable"): continue`（不可选中=非受击单位）或统一给宠物 actor 补 `hp: None/1` 并用 `untargetable` 表达不可受击。

**2. battle.py:9055 `_summon_entity` —— tid=="skeleton" 特判**
```python
if tid == "skeleton":
    for _pn_sk, _ps_sk in self._proc_pm(player)["proc"].get("skeleton_cap", []):
        _summon_limit = ...
```
- **类型**：tid 特判残余（v169.7 骷髅海）。
- **影响**：加新召唤物模板想带"上限提升被动"必须再写 `if tid==xxx`；与随从数据驱动哲学相悖。
- **建议**：`skeleton_cap` 被动数据配 `tid/summons` 键（如 `{"tid":"skeleton"}`），此处改为"被动声明的 tid == 当前 tid"匹配循环，去掉 `if tid=="skeleton"` 硬编码。

**3. battle.py:4698/9821/9818 & battle_mech.py:2081/2093 —— skeleton tid / 名称含"骷髅" 特判**
```python
# battle.py:4698 _undead_count
if s.get("hp",0)>0 and (s.get("tid")=="skeleton" or "骷髅" in str(s.get("name",""))):
# battle.py:9821 death_contract（牧师死灵线）祭品池
_skels = [s for s in self.summons if s.get("tid")=="skeleton" and ...]
# battle_mech.py:2081/2093 bone_rush/sacrifice
skels = [s for s in ... if s.get("tid")=="skeleton" and ...]
```
- **类型**：tid/名字特判残余（亡灵语义散在 4+ 处）。
- **影响**：所有"亡灵系随从"判定各自维护一份"骷髅=亡灵"的口径（skeleton 硬编码 + 中文名关键词匹配），新增亡灵类随从（幽魂/僵尸召唤物）不会自动被识别；`_undead_count` 还混算敌方怪（`名含亡灵/骷髅/僵尸/幽灵` 关键词），**语义全部靠名字字符串，不是字段**。
- **建议**：随从 actor 增加 `tags: ["undead","skeleton"]` 或数据模板加 `undead: True` 字段，消费点统一 `if "undead" in s.get("tags",[])`；`_undead_count` 的敌方侧同理改读敌方单位 `tags`/`is_undead` 字段（数据在 monster 模板加字段），彻底去中文名匹配。

**4. battle.py:9806-9812 `_death_pact` —— `self.companions.pop()` 裸 pop 尾部**
```python
if actor["hp"]<=0 and self.summons and not self._death_pact_used:
    ...
    fallen = self.companions.pop()    # ← 无任何筛选
```
- **类型**：身份/容器特判残余（依赖"列表尾部=召唤物"的旧布局假设）。v180-C 宠物 actor 也进 companions 后，若宠物排在尾部（`_pet_ensure_actor` 先于后续召唤追加），此 pop **可能牺牲宠物 actor 而非召唤物**。下方 9814 的 death_contract 分支已改 `[c for c in self.companions if c.get("kind")=="summon"]` 正确筛选，**两条链不一致**。
- **影响**：潜在会牺牲宠物/非召唤实体（虽然宠物无 hp、本分支检查 `self.summons` 非空才进，但 pop 的对象可能与检查集合不符）。低概率 bug，逻辑上必须修。
- **建议**：与 9814 同款改为 `_sacrifice_pool = [c for c in self.companions if c.get("kind")=="summon"]; fallen = _sacrifice_pool.pop()`，或统一收口成一个 `_companion_sacrifice()` helper。

**5. battle.py:355-364 `_th_passive_heal`（tick handler）—— battle.summons 特判**
```python
if battle.summons:
    for _pn,_ps in _pm.get("focus_regen_summon", []):
        ...  # 森之共鸣：召唤物在场专注充能
```
- **类型**：容器特判残余（读 `battle.summons` 兼容视图而非按字段扫 companions）。
- **影响**：`focus_regen_summon`（游侠·森之共鸣）只能被 kind=summon 激活；若未来加"宠物在场也充能"类被动需另写条件。低危但语义仍是身份判断。
- **建议**：改扫 `companions` 里 `kind != "pet"` 或带 `counts_as_summon` 字段者，或直接数据配 `companion_kind:["summon"]`。

---

## 二、`_companion_act` 只支持 basic_atk vs 宠物 8 种 skill_type（核心冲突）

**1. 宠物技能仍走独立 `_pet_skill_turn` + `PET_SKILL_EFFECTS` 注册表（battle.py:7721-7746, 112-213），完全未收编进 companions auto_act**

宠物 actor 化后，**宠物行为仍是专用路径**：
- `_th_pet_act`（642-671）→ `battle._pet_skill_turn(...)`（7721）→ 读 `self.pet`（**不是 actor 参数**）→ `PET_POOL` 查 pet_key → `PET_SKILL_EFFECTS[stype]` 分发 8 个 handler（atk_pct/matk_pct/lifesteal/pierce/heal_pct/buff_atk/crit_up/block）。
- 而 companions 的通用触发点 `_companions_trigger("player_act")`（3096-3097）只被**召唤物**的 `auto_act`（basic_atk）命中——**宠物身上没有 auto_act，即使有，`_companion_act`(9100-9116) 也只认 `basic_atk` 一种 act.type**，`heal_owner/buff_owner` 分支只是 9117 行的注释占位（"未来扩展"）。

- **冲突点**：`_pet_skill_turn` 内部 handler 全部以 `player`（主人）为治疗/增益目标、`battle._player_stats(player)` 取面板、`battle._damage_enemy(..., attacker=battle.pet)` 打伤害——**本质是"主人的挂件技能"而非"actor 自己的行为"**。8 种 skill_type 效果 = 攻击×N/魔攻×N/吸血/破防/回血/加攻/加暴击/挡刀，是 8 个"随从技能效果"，与 auto_act 想表达的"随从每 N 刻做一件事"高度同构，**是同一语义的两套实现**。
- **能收编吗**：可以——把 `PET_POOL` 的 skill_type/skill_value/skill_interval 翻译成 `auto_act = {trigger:"interval", interval:N, act:{type:skill_type, value:...}}`，`_companion_act` 按 act.type 分发到通用实现（basic_atk 已有；heal_owner 用玩家管线 `_skill_heal`；buff_owner 写 owner buffs；lifesteal/pierce 等走 `_damage_enemy`+`attacker=actor`），间隔调度复用 v179 tick 卡（`_th_pet_act` 已示范 interval 卡模式）。**建议**：至少先加 `act.type=heal_owner/buff_owner` 两个通用分支把 heal_pct/buff_atk/crit_up 收编（3/8 效果），伤害系可后置；block（影袭）应并入 guard 体系（见第三节）。

**2. `_pet_skill_dmg` 里 `attacker=battle.pet`（battle.py:138）+ 玩家面板取攻击力**
```python
st = battle._player_stats(player)          # 用主人面板算伤害
dmg = E.calc_damage(int(st["atk"]*pdef["skill_value"]), est.get("def",0))
real = battle._damage_enemy(dmg, logs, attacker=battle.pet or None)
```
- **类型**：宠物技能非 actor 化（伤害数值用主人面板，仅归属/被动挂宠物）。
- **影响**：宠物攻击伤害跟主人成长而非宠物自身（若将来宠物有等级面板则不成立）；乘区虽已传 attacker=宠物，但**基础伤害取主人 atk/matk**——"宠物 actor 化"只化了伤害归属，没化数值来源。
- **建议**：数值改读宠物 actor 自身（`actor.get("atk")`/宠物模板 atk 比例），或维持设计"宠物伤害=主人面板×系数"并显式注释（鱼鱼拍板点）。

**3. `_pet_buff_vals` 旁路状态（battle.py:199-212 + 7384-7389 消费）**
```python
# _psk_buff_atk/_psk_crit_up
_pbv = getattr(battle, "_pet_buff_vals", {}); _pbv["atk"]=...; battle._pet_buff_vals = _pbv
# _apply_buffs（7386-7389）
if attr in ("atk","crit"):
    _pv = getattr(self, "_pet_buff_vals", {}).get(attr)
```
- **类型**：宠物专用旁路状态（buff 强度不随 buff 数据存，靠 battle 级 dict 临时拼装）。
- **影响**：非序列化状态（若断线恢复，宠物 buff_atk 强度丢失只剩 2 刻标记）；且 `buff_atk`/`crit_up` 技能名与 `BUFF_MULT`/`_apply_buffs` 通用增益键语义重合，本质应直接写 `player["buffs"]["atk_up"]` 并用通用 `_apply_buffs` 乘区。宠物技能收编 auto_act 后此旁路应消失（buff 数值写进 act.data，由通用 buff 结算读取）。
- **建议**：`act:{type:"buff_owner", buff:"atk_up", value:0.30, turns:2}` → `_companion_act` 通用分支直接写 owner buffs（数值放 actor auto_act 配置，随 actor 序列化），删 `_pet_buff_vals`。

---

## 三、guard 挡刀：pet 专用 `_pet_block_check` 与 companions 通用 `_guard_redirect_check` 双轨重复

**1. 双函数并存（battle.py:7785 `_pet_block_check` / 9217 `_guard_redirect_check`），调用点 battle.py:10074/10082 串行两段**
```python
# _damage_actor 内（10073-10082）
if _is_player:
    dmg = self._pet_block_check(dmg, logs)        # ① 宠物专用（mode=absorb，拦截整段伤害→0）
    if dmg <= 0: ... return 0
    dmg = self._guard_redirect_check(dmg, logs)   # ② 随从通用（mode=redirect，按随从 def 转伤）
```
- **类型**：挡刀双轨（语义同"随从/宠物替主人挡刀"，实现两套：absorb 宠物整伤拦截 vs redirect 召唤物转移承受按 def 结算）。
- **影响**：
  - `_pet_block_check` 仍直接读 `self.pet`（**不是扫 companions**），守卫条件含 `pet["level"]`/`pet["satiety"]`——宠物即使已在 companions 里，挡刀仍走**专用小灶**，且宠物 guard 配置（`_pet_ensure_guard` 写的 `mode:"absorb"`）只在 `_pet_block_check` 被读，**companions 通用挡刀扫描 `_guard_redirect_check`(9225) 只认 `mode=="redirect"` 且来自 `self.summons`**——pet actor 的 guard 字段对通用逻辑不可见（被 summons 过滤掉了）。
  - 双函数对"挡刀后伤害=0 还是转移按 def 结算"语义不一致（absorb 直接 return 0 不给随从扣血日志；redirect 要扣随从 hp），未来加第三种挡刀模式又要第三函数。
- **建议**：
  - 短期：`_guard_redirect_check` 的候选池从 `self.summons` 改为**扫 `self.companions`**（任意 side=player 带 guard 字段者），并支持 `mode:"absorb"`（整伤吸收、按 guard.cooldown 冷却——`_pet_block_check` 的 interval 语义现成可搬）；`_pet_block_check` 收编为"companion 里 kind=pet 的 guard 消费"或删除、挡刀统一走 `_guard_redirect_check`。
  - 中期：把 `_pet_ensure_guard`（block 宠物转配 guard）的逻辑改为在 `_pet_ensure_actor` 内一并完成（宠物 actor 化 = 补 kind/side/buffs/guard 一步到位），`_pet_block_check` 的冷却状态 `_guard_last_at` 随 actor 序列化（已在 pet dict 上，收编后仍在 actor 上，天然兼容）。

---

## 四、kind=pet actor 的治疗广播/增益/AOE 误伤面（hidden/untargetable 未被消费）

**1. `hidden` 字段零消费、`untargetable` 字段零消费（全引擎 grep 证实）**
- `hidden` 只被写入（7692）和注释提及（7677）——**没有任何显示层/命令层读取它来跳过宠物显示**（命令层 combat.py 的战场显示走 `e_minions`/enemies，companions 不进战场显示，所以 hidden 是"未来字段"，但按鱼鱼哲学应尽早被消费或在显示管线接入）。
- `untargetable` 只被写入（7693）+注释（7678）——**敌方目标选择 `_pick_enemy_target`(1258)/instance 的 `_instance_enemy_one_act`(3331)/formation.select_target 全部不检查 untargetable**。当前宠物不进 allies/enemies 阵列所以敌人打不到它（不是字段保护，是**没进目标池**）；一旦未来随从受击/入阵列，untargetable 必须被 formation 消费。**注释声称的"敌人选目标跳过它"实际未接线。**

**2. 治疗广播不覆盖 companions —— 反而"安全"但语义不对称**
- 单机"全队回血"类（`_th_echo_heal` 510-512 扫 `battle.allies`、`_set_miracle_team_heal` 4843-4845 扫 `self.allies`、副本 `_apply_team_effect` 3080-3088 扫 `st["members"]`）**都只扫玩家 allies，不扫 companions**——所以宠物/召唤物现在不会被治疗广播奶到（低影响，当前宠物无 hp 容器无所谓，但**召唤物也没有**，与 v151 注释"召唤物吃 AOE/吃增益"矛盾——见下）。
- 副本 `_instance_act`(2618) 每次给 Battle 传 `pet` + `allies`=玩家快照；`_pet_ensure_actor` 只在 `_now<=0` 的 __init__ 挂点与 from_state 补挂执行，**companions 列表在副本 Battle 瞬态构造间不持久**（每次行动重建），宠物 actor 每行动重建一次（幂等可接受），但召唤物（若有）在副本不会跨行动存活——副本身份与单机不对称。

**3. AOE 类误伤面：反向 —— 召唤物"吃 AOE"字段 `eats_aoe` 从未被消费（全引擎 grep：只被写入）**
- `eats_aoe` 只在 `_spawn_companion` 装配(9023/9077)与 SUMMONS 数据(summons.py 31/40/51/62)出现，**没有任何 AOE/敌方技能按它结算**。敌方 AOE（`_aoe_damage` 8724 只对 `self.enemies` 结算，玩家侧召唤物根本不在 enemies 里）→ **藤蔓守卫等 eats_aoe 召唤物实际永远吃不到 AOE**，v151 语义（"吃 AOE"是弱点设计）静默失效。真正会"误伤"的是另一方向：若把 companions 并入敌方 AOE 目标池（未来若做随从受击），没有 eats_aoe 过滤的随从会被 AOE 打到——字段语义与实现方向相反。

**4. 增益广播同理只覆盖玩家（`_apply_team_effect` 副本侧 3104-3112 扫 st["p_buffs"] 玩家表）**——companions 的 buffs 容器（`_pet_ensure_actor` 7691 与 `_spawn_companion` 9019 都就位了）实际没有任何增益来源会写它，除非显式传 actor。字段就位但零消费面，属于"actor 化只完成了容器化"。

**5. 序列化缺口（to_state/from_state）—— companions 主体不可恢复**
- `to_state` 只序列化 `"summons": self.summons`（1084，仅召唤物兼容视图）；`from_state` 恢复 `b.summons = st["summons"]`（1342）——**kind=pet 的 companion 不进 `st["summons"]`，靠 `st["pet"]` 单独走**（1069/1295）。宠物 actor 的 guard/`_guard_last_at`/buffs 在 pet dict 上随 `pet` 序列化，OK；但**如果宠物 actor 上有任何 companions 特有状态（buffs 未来被增益写入），序列化不会经 companions 路径保存**。召唤物 actor 经 summons 视图序列化（dict 副本，非引用），恢复后由 setter 重建。当前可用，但 companions 统一容器与序列化仍是"两条老路"，未来加第三类 companion（如真·队友宠物随从）序列化会漏。
- tick_effects 序列化 actor_ref（1120-1132）只认 `"player"` 或 enemies uid——**宠物 actor（companions 成员）作为 tick 卡 actor 时序列化会落空**（pet_act 卡 uid 专用不依赖 actor_ref，可侥幸；但若未来给 companions 挂通用 tick 卡则丢）。

---

## 问题清单汇总（按优先级）

| # | 位置 | 问题 | 类型 | 建议 |
|---|---|---|---|---|
| P0 | battle.py:9809 `self.companions.pop()` | 死亡契约牺牲品裸 pop 尾部，宠物 actor 进 companions 后可能牺牲宠物（与 9814 分支不一致） | 身份特判残留/潜在 bug | 同 9814 改为筛选 `kind=="summon"` 池 |
| P0 | battle.py:7721-7746 + 112-213 | 宠物 8 种 skill_type 仍走 `_pet_skill_turn`/`PET_SKILL_EFFECTS` 专用注册表，与 companions `auto_act` 双轨；`_companion_act`(9100) 只认 basic_atk，heal_owner/buff_owner 是注释占位 | 双轨/未收编 | PET_POOL → auto_act 数据翻译，`_companion_act` 加 act.type 通用分支（heal_owner/buff_owner 先收编 heal_pct/buff_atk/crit_up 3 类） |
| P0 | battle.py:7785+10074 vs 9217+10082 | 挡刀 pet 专用 `_pet_block_check` 与通用 `_guard_redirect_check` 并存串行；pet guard（mode=absorb）不在通用候选池（通用池只扫 summons+redirect） | 双轨重复 | 通用挡刀改扫 `self.companions`+支持 mode=absorb，删/收编 `_pet_block_check` |
| P1 | battle.py:4698/9821/9818 + battle_mech.py:2081/2093 + 9055 | skeleton tid / "骷髅"名字关键词 / 亡灵关键词 4+ 处散落特判 | tid/名字特判残留 | 随从/怪模板加 `tags`/`undead` 字段，消费点改字段 |
| P1 | battle.py:9141 `c.get("kind")=="pet"` | 死亡清理按 kind 特判（宠物无 hp 容器裂缝） | kind 特判残留 | 改按 `untargetable`/hp 字段 |
| P1 | battle.py:138+7661+7721 | 宠物伤害数值用主人面板（仅归属 actor 化）；`_pet_buff_vals`(199-212/7386-7389) 旁路非序列化 | 数值未 actor 化 | 数值读宠物自身或显式拍板；buff 值随 auto_act/actor 数据 |
| P2 | 全引擎 grep | `hidden`/`untargetable`/`eats_aoe` 三个字段只写不读 | 字段未消费 | 敌选目标/显示层/AOE 结算接线（formation 消费 untargetable；AOE 按 eats_aoe 结算或删除字段） |
| P2 | battle.py:1022/1032+1084+1342 | `summons` 兼容视图/序列化仍是 kind 过滤的双轨；companions 本体不进序列化（pet 走 st["pet"] 另路）；tick actor_ref 不认 companions | 序列化/视图双轨 | 统一序列化 companions（含 kind 标注），tick actor_ref 支持 companion 引用 |
| P2 | battle.py:355/510/4843 | `battle.summons`/`allies` 特判扫描（召唤物在场/全队回血只扫玩家） | 容器特判 | 语义收口：要不要奶随从是设计决策，别靠容器巧合 |

**文件：** 未改任何代码（审计指令）。主要问题集中在 battle.py（上述行号），关联 battle_mech.py:650-660/924-929（敌方 summon 机制走 `_summon_minions` 敌方侧，与玩家侧 companions 无冲突，但敌方 minion 也是独立 e_minions/enemies 双轨，同类问题可在后续审计覆盖）。