# REFACTOR P0-B：skill_up.py 中文 key 消重（只读侦察 + 迁移方案设计）

> 分支：`wt_p0b`（worktree w7） · 状态：**设计文档，未改任何 game/ 代码**
> 审计出处：ARCHITECTURE_AUDIT 数据层最脏处 §五① —— SKILL_UP 以**中文技能名**作 key，628 个赋值中 160 组同名重复（112 组同名不同值），Python 后定义覆盖前定义，实际生效值靠"最后一行"侥幸。
> 铁律：**行为零变化**。迁移后每个技能实际吃到的成长曲线必须与现状（= SKILL_UP 字典求值后的"最后定义"）完全一致。

---

## 1. 侦察结论（全部经 AST 全量统计，非抽样）

### 1.1 SKILL_UP 规模

| 口径 | 数值 |
|---|---|
| 文件总赋值行（SKILL_UP 字典字面量 key:value 对） | **628** |
| 去重后 distinct key | **468** |
| 只出现 1 次的 key | 308 |
| 重名 key 组数（出现 ≥2 次） | **160** |
| 重名组内的赋值总数 | 320（160×2，**无 3 连击**：不存在 ≥3 次同 key） |
| 重名组**值不同**（冲突，后覆盖前 = 行为被覆盖方） | **112** |
| 重名组**值相同**（冗余重复，无行为影响） | **48** |

- 每个重名 key 均恰有 **2 个赋值**；无 3+ 组。
- 冲突组的两个赋值**永远一个来自 v83–v139 手工区（L24–355）、一个来自 v153 脚本重做区（L356–651）**，无 v153 内部自撞、无 v180 补配区（L652–656）撞车。统计：112 冲突 + 48 同值全部为 `{pre153, v153+}` 跨区对。
- 也就是说：**"最后一行覆盖"不是偶然——v153 重做脚本在文件末尾整体刷了一遍技能成长，凡是 v153 保留的技能名，旧区配置全被 v153 区覆盖**。今天线上实际生效值 = v153+ 区那一份（除 5 个 v180 补配项在 L654–655 再次覆盖 L650–651 的龙息之怒/骷髅海系）。这是**蓄意的整表重平衡**，不是随手重复。

### 1.2 重名 key 的"归属"画像（对照现行 skills.py 全表）

对每个重名 key 反查当前三张技能表（PLAYER_SKILLS 61 + BRANCH_SKILLS 238 + TUTOR_SKILLS 6 = 305 个技能），结论：

- **160/160 重名 key 都有且仅有 1 个现行 occupant**（基础 39 / 分支 121 / 导师 0）。
- 冲突 112 组：基础 23 组（如 冰锥/圣光弹/雷击/挥砍/火球术/冥想……） + 分支 89 组（万毒噬心/元素裁决/星轨锁定/哀歌……）。
- **0 个重名 key 是"纯死配置"**——每个重名 key 都映射到现行某个技能。被覆盖的旧值只是该技能在 v153 前的旧成长，v153 已按新数值体系统一重刷。
- 现行 305 技能名的**名字空间全局唯一**（player/branch/tutor 三表之间 0 重名），所以**当下**按名字查不会歧义——脏点全部是**潜在**的：文件内 160 组重复制造"读代码无法判断谁生效"，且任何新增同名技能（基础/分支/导师/怪物共用名）会静默互相污染。

### 1.3 key 到底对应谁：完整查询链

```
玩家技能升级/详情/列表 UI 输入（中文名 / 序号 / sk_id）
   │
   ▼
engine.skill_info(class_name, name)          # engine.py:963
   ├─ C.resolve('skills', name)               # 只对 PLAYER_SKILLS(61) + TUTOR_SKILLS(6) 建过索引（_SKILL_FLAT）
   │     ├─ 基础技：name→sk_id 命中 → _sk_table[sk_id]
   │     ├─ 导师技：命中 → TUTOR_SKILLS[cls][sk_id]
   │     └─ 分支技：resolve 未命中（原样返回中文名）→ 遍历 _br_table 分支字典
   │            若中文名 ∈ 分支叶 dict（叶 key 即中文名）→ 命中
   └─ info dict（带 'name' 中文名字段 + 'lv' 学习等级）
   │
   ▼
engine._skill_up(info)                        # engine.py:765 —— 唯一 SKILL_UP 消费入口
   ├─ v180 隔离：info 无 'lv'（怪技能/宠物/NPC 引用）→ 返回 {}（不查表）
   └─ 有 'lv' → C.SKILL_UP.get(info['name'])   # ★ key = 技能显示中文名
   │
   ▼ 9 个成长 helper 全部只经 _skill_up 拿配置：
   skill_max_level / skill_power_mult / skill_flat_value /
   skill_cond_mult / skill_mech_val / skill_lifesteal_pct / skill_buff_turns
```

- **SKILL_UP 的 key = info['name']（技能显示名），不区分段（基础/分支/导师共用同一名字空间）。** 三表现行 0 重名 + v180 的 lv 隔离是当前"不炸"的两道保险。
- 存库侧（store/players.py:150–155）：`learned_skills` 存原始输入（中文名/sk_id 混合），读出时 `display('skills')` 把 sk_id 还原中文名；`skill_levels` 写时 resolve 成 sk_id、读时 display 回中文名。**分支技能不在 resolve('skills') 索引内**（_SKILL_FLAT 只含基础+导师），所以分支名全程中文原样走。

### 1.4 现行行为 = 字典求值后的"最后定义"，已程序化验证

- 用 AST 依源码顺序逐条求值 628 项 → 得到有效字典（468 键）→ 对 305 现行技能名覆盖率 **100%（缺配 0）**。
- 冲突组最后一行全部落在 v153+ 区（除 v180 补配 2 组落在 L654/655），与"文件末尾整表重刷"一致。
- **基线 = 该 468 键有效字典**。迁移的任何方案，只要保证"每个现行技能名查到的配置 == 此字典中该名对应值"，行为即零变化。

---

## 2. 引擎/消费改动面（把 key 从"中文名"换成"稳定 id"需要动什么）

### 2.1 唯一 SKILL_UP 入口与派生 helper

| 函数 | 位置 | 说明 |
|---|---|---|
| `_skill_up(info)` | engine.py:765–774 | **唯一查表点**。改 key 方案下唯一需要改语义的地方：`SKILL_UP.get(info['name'])` → `SKILL_UP.get(<稳定id>, …)`。id 来源见 §4 |
| `skill_max_level` | engine.py:786 | 消费 `_skill_up().max`（无配 default 5） |
| `skill_power_mult` | engine.py:881 | 消费 `_skill_up().p`（无配 = 1.0，v180 起无默认成长） |
| `skill_flat_value` | engine.py:889 | 消费 `_skill_up().flat_*`（缺省回落常量） |
| `skill_cond_mult` | engine.py:924 | 消费 `_skill_up().c`（无配默认 0.05） |
| `skill_mech_val` | engine.py:933 | 消费 `_skill_up().m`（无配默认 2） |
| `skill_lifesteal_pct` | engine.py:941 | 消费 `_skill_up().l`（无配 0） |
| `skill_buff_turns` | engine.py:911 | 内部再调 `skill_max_level(info)` |

### 2.2 helper 的消费调用面（game/ 内全部调用点）

- **battle.py（战斗热路径）**：`skill_power_mult` L6042/6044/6872/7067；`skill_buff_turns` L6247/6418/7186；`skill_lifesteal_pct` L6411；`skill_mech_val` L7177；`skill_flat_value` L7223；`skill_cond_mult` L7331；另有 `skill_level_of` L7144、`skill_info` 查表多处、`skill_by_key` 怪引用玩家技 v177 管线（L7633 `_lookup_skill_info`）。
- **commands/player.py（学习/升级/详情 UI）**：`skill_max_level` L1405/1736；`skill_upgrade_cost` L1516/1740/1761；`skill_power_mult` L1681；`skill_buff_turns` L1683；`skill_cond_mult` L1685；`skill_mech_val` L1693；`skill_lifesteal_pct` L1697；写库路径 L1588（learned 存**原始输入**）、L1747（skill_levels 存 resolve 后 sk_id）。
- **commands/combat.py（技能列表/成长预览）**：L1328–1367 全部成长维度渲染 + L1395 满级展示；`_player_skill_table`/`_branch_skills_for` L1224–1262（玩家可见技能表 = sk_id 键 ∪ 中文名键 ∪ sk_id 键 三段合并，序号由 dict 顺序决定——**注意：若分支叶 key 由中文名改成 id，序号展示位次不变但列表 key 域变化**）。
- **commands/instance.py**：L3105/3109（伙伴/塔战斗回血用 `skill_buff_turns`/`skill_power_mult`，后者**未传 info** → 走默认，与 SKILL_UP 无关）。
- **core/battle_mech.py**：`skill_buff_turns` 25+ 处（buff 刻数），多数带 `info=`；L111 一次不带 info（默认值）。
- **scripts/**（离线数值/文案工具）：`build_matrix/build_matrix.py`、`skill_scan.py`、`strength_matrix_report.py`、`gen_skill_exprs.py`、`numeric_lib/*`、`v112_tome_smoke.py`、`_tmp_calib_v2.py` 直接 import engine helper 算成长/预览——迁移后它们拿到的仍是 engine 公开函数结果，**只要 engine 对外签名不变就无需改**（除非直接读 SKILL_UP 原样）。
- **tests/**：`test_commands_skills.py` 等 30+ 用例断言升级/成长数值——是行为零变化的天然回归网（`scripts/run_numeric_tests.py` 门禁，见 dragonfall-game 铁律）。
- **其他数据消费方（无 lv，不受 SKILL_UP 影响，但受"名字空间"牵连）**：monsters.py `MONSTER_SKILLS` 205 条**全部无 lv**（v180 隔离点）；wild_npcs.py `teach_skills` 教旧版基础技名（战争践踏/冰霜新星/狩猎终章/暗影处刑/破晓之拳等 12 处，经 `E.skill_info` 查——v153 后多数已查不到返回 None，属历史残留）；pets.py/affixes.py/equip_roster.py 中同名 token 是宠物自带技/词缀/装备名，**不经过 skill_info 链路**。

### 2.3 改 key 的雷区（决定方案取舍）

1. **branch 叶 key = 中文名**（238 个）。engine/commands 到处用 `for sk, info in branches.items()`、`skill_name in skills`、`skill_items[idx-1]`（序号查看依赖 dict 顺序 + key 即玩家输入可匹配对象）。若 BRANCH_SKILLS 叶 key 全改 sk_id，所有"玩家输入中文名 → 查表"路径都要在 resolve 索引之外**再补一层分支名→id 映射**，且 `_player_skill_table` 序号模式返回的 key 会从中文名变 id → UI 输出要跟着改（玩家看到列表项 key 被拿去 `skill_info`/`技能升级` 匹配）。
2. **存储层双轨**：learned_skills 存原始输入、skill_levels 存 resolve(id) 读回 display(name)。分支不在索引 → 分支永远中文。改成 id-key 不影响 DB（存量玩家存档是中文名/ID 混合，load 时 display 转换只对索引内有效——分支原样保留，天然兼容）。
3. **显示名 ≠ 名字空间唯一**的未来新增：任何新技能只要显示名撞现存名，SKILL_UP 中文 key 就静默偷配置——这是"新增技能必须动引擎/数据混乱"的根源（审计 §五①）。
4. **怪物技能隔离靠 `lv is None`**，不是靠 key——key 换成 id 后隔离逻辑不变（怪技仍无 lv）。

---

## 3. 候选方案

### 方案 A：SKILL_UP 全改稳定 id key + 三张技能表同步给分支生成 id（侵入大）

- SKILL_UP key → `sk_xxx`：基础/导师直接用现有 sk_id（67 个）；分支 238 个用 `pinyin_id(中文名)` 生成（前缀 `sk_`，与现有 pinyin 体系一致，core/index.py 工具现成）。
- BRANCH_SKILLS 叶 key 同步从中文名 → sk_id，并给每个叶 info 保留 `name` 字段（显示用）。
- `_skill_up` 改为按 info 携带的 id 查（info 加 `sid` 字段 or 查表时由调用方 resolve）。
- **改名雷区全踩**：序号模式 key 域变化、分支叶遍历处 `skill_name in skills` 失效（resolve 只覆盖基础+导师）、全仓 branch 遍历代码要逐个适配。v177 `_SKILL_KEY_INDEX` 缓存的 key 域也变。收益是"一步到位"。

**结论：侵入面横跨 engine/commands/battle 的 key 语义，改 key 即改玩家可见接口语义，风险远超收益，且分支 id 为纯新增第三套 key 体系（player 已 sk_、branch 中文名、tutor sk_），过渡期三套并存反而更乱。** 不推荐单独执行。

### 方案 B：SKILL_UP 保留中文 key，消重成"每名一条"（文件内去重）

- 依 §1.4 基线：468 个 distinct key 中，冲突组取**最后一行**（= 现行生效值），同值组删旧留新 → 628 行 → 468 行（每技能一条，删 160 条被覆盖行）。
- 文件内不再有同名；但 key 仍是中文名 → **"新增技能撞名即污染"的根因未除**（未来加一个中文名相同的分支/导师/基础技，照样覆盖）。且 163 个孤儿 key（v153 前已删技能的旧配置，无现行 occupant）继续留在表里当噪音。
- 若顺带删 163 孤儿：需论证无任何 live info 可达（§2.2 已查：monsters 无 lv、wild_npc teach 的旧名查不到 info、pets/affixes 不经链路）→ 可删，行为零变化。但**删了之后 SKILL_UP 不再覆盖旧名字**——任何"未来用旧名建技能"会直接没配置（而不是像现在吃到残留旧值），属于把隐性 bug 转显性，方向对但依赖"未来无同名"的自觉。
- **优点：纯数据文件改动（+ 一条防重言注释），引擎零改动，UI/存储零影响，行为 100% 保持（按定义）。**

### 方案 C：加 alias 归属层 —— SKILL_UP 条目加 owner/归属 id，engine 精确匹配（根治）

- SKILL_UP 结构从 `{中文名: cfg}` 演进为「**每条配置显式带归属**」：

```python
SKILL_UP = {
    # 形态示意（落地按实施小节定稿）
    "sk_zhan_ge": {"name": "战歌", "max": 3},              # 基础/导师：key=现有 sk_id
    "sk_branch_ai_ge": {"name": "哀歌", "p": 12, "max": 5},  # 分支：key=生成的稳定 sk_branch_* id
}
SKILL_NAME_INDEX = {...}   # 中文名 → id（构建时由技能表自动生成，含 305 现名 + 防御性报重）
```

- engine `_skill_up(info)`：
  - info 携带稳定 id（**基础/导师 = 现存 sk_id；分支 = 生成的 sk_branch_id**）→ 直接 `SKILL_UP.get(id)`；查不到再回落 `SKILL_UP.get(name)`（兼容期/防御）。
  - id 来源不加字段也行：`_skill_up` 内用 info['name'] + 表归属反查 id——但 info 本身就在三表中，反查成本 O(1) 缓存。
- 引擎对外 9 个 helper 签名不变；**改动收敛在 `_skill_up` 一个函数 + 数据文件结构**。
- 消重动作 = 方案 B 的 628→468 去重 + 163 孤儿清理（孤儿本就不该喂给任何 live info）。
- **行为零变化验证链**：迁移后 `SKILL_UP[id]` 与基线 468 键逐名对拍（脚本断言：每个现行技能名 → 新 id → cfg == 基线 cfg）。

**推荐：C（alias/归属层根治）+ 执行时先做 B 的去重步骤（628→468 一行不丢语义），再做 id-key + 归属断言。** 理由：
1. 唯一根治"同名即污染"：配置 key 脱离显示名，未来新增技能即使中文撞名，只要 id 不同就互不干扰；
2. 引擎改动收敛在 `_skill_up` 一个函数（+ 索引构建），对外 helper/UI/存储签名全不变 → 消费面（§2.2 全部调用点）零改动；
3. 分支 id 只在**数据层**新增（不侵入 BRANCH_SKILLS 叶 key、不动玩家可见序号接口）——绕过方案 A 的所有雷区；
4. 冲突"最后一行"语义变成显式 owner 归属，可加启动断言：任何 `SKILL_UP` 条目若 owner 查无此 id、或两个 id 共用一个中文名 → 启动即炸（把隐性污染变显性）；
5. 存量 DB 玩家存档天然兼容（中文名/ID 混合，读回时 display 只对索引内有效，分支原样）。

---

## 4. 落地步骤（供实施 agent，本任务不改代码）

### Step 0：基线快照（必须先做）
```python
# 独立脚本：AST 顺序求值 628 项 → 468 键有效字典 → 对 305 现行技能名逐名断言：
#   名→cfg 与迁移后 名→id→cfg 完全一致。跑 numeric_tests 全绿作总闸。
```

### Step 1：数据层去重（628→468，行为不变）
- 冲突 112 组：保留**最后一行**（全部为 v153+/v180 区的现行值）；同值 48 组：删早留晚（同值，无语义差）。
- 163 孤儿 key 删除（§2.2 已证无 live 可达路径；防回归：删前跑 numeric_tests + 全仓 grep 复核无引用）。
- 保留顶部注释说明 key 语义演进（v102.4 → v153 → P0-B）。
- 该步单独可提交、可上线：**引擎零改动、纯数据文件、行为按定义不变**——先把"读代码无法判断谁生效"的脏点清掉。

### Step 2：id-key + 归属（方案 C 主体）
- 技能表侧无需改结构：基础/导师 id = 现存 sk_id；分支 id = 生成 `sk_`+pinyin_id（305 名拼音仅 1 撞：`守歌`/`收割`→`sk_shou_ge`，见下）。
- SKILL_UP key 改 id，条目带 `"name": 中文名`（保留可读性/校验）。
- `_skill_up` 单点改：`SKILL_UP.get(id_of(info))`，`id_of` = info 内新字段 or 查归属索引（构建期由 _assembly 装配）。
- 分支 id 撞车处理（必须显式）：
  - `守歌`(基础 sk_shou_ge) vs `收割`(分支)：pinyin 均 `shou_ge` → 生成规则加**段前缀**：基础/导师 `sk_<pinyin>`（沿用现名），分支 `sk_br_<pinyin>` → `sk_br_shou_ge` 唯一。全量复核无第二撞。
- 启动自检（可选增强）：SKILL_UP 中每 key 必须能反查到一个 live 技能，否则 ImportError——防 163 类孤儿再生。

### Step 3：回归
- `scripts/run_numeric_tests.py` 全绿（数值门禁铁律）；`tests/test_commands_skills.py`（升级/满级/成长曲线断言）；
- 用 Step 0 对拍脚本断言 305 名 → cfg 与基线逐项相等（这是"行为零变化"的机器证明，不能只靠测试通过）；
- 手工冒烟：技能学习/升级/详情/战斗各 1 条（基础技、分支技、导师技各一）。

### 改动文件清单（实施时）
| 文件 | 改动 |
|---|---|
| `game/data/skill_up.py` | 628→468 去重 + 删 163 孤儿 + key 改稳定 id + 条目带 name + 段前缀撞车消解（Step1/2 数据侧） |
| `game/data/_assembly.py` | （如走索引反查）`build_index("skills", _SKILL_FLAT)` 不动；新增分支名→sk_br_id 映射装配（或 SKILL_UP 内联注释表） |
| `game/engine.py` | 仅 `_skill_up`（765–774）单点改 id 查询 + 兼容回落；9 个 helper 签名不动 |
| `game/commands/player.py` `commands/combat.py` `battle.py` `core/battle_mech.py` `commands/instance.py` | **预期零改动**（消费的是 engine 公开 helper）——回归确认即可 |
| `game/data/monsters.py` `wild_npcs.py` 等 | **预期零改动**（lv 隔离/无 info 路径天然不触发 SKILL_UP） |
| `docs/REFACTOR_P0B_skill_up_dedup.md` | 本档 + 实施后补迁移记录 |
| scripts/tests | 新增对拍脚本（Step0/Step3）+ 保留既有数值门禁 |

### 为什么不是 A 单独执行 / B 单独收尾
- A：分支叶 key 改 id 会把"玩家输入中文名"全链路（序号模式、`skill_name in skills`、`_player_skill_table` key 域）拖下水，UI 与存储语义全变，改动面横跨三模块且无行为收益（C 用数据层 id + 单点查询达到同样根治）。
- B：能立刻清掉"同名重复"视觉脏点且引擎零改动——**建议作为 Step 1 先行落地**（低风险快速止血），但它不防"未来同名"；根治必须 C 的 id 归属。所以推荐 = B 先止血 → C 根治，两步各自可独立提交回滚。

---

## 5. 附录

### 5.1 冲突组样例（112 组全量口径：key = 旧区行 vs v153+ 行，现行生效 = 后者）

| key | 旧区行(值) | v153+ 行(现行生效) | 现行 occupant |
|---|---|---|---|
| 战歌 | L29 `{p:0,c:0.05,m:2,max:3}` | L483 `{max:3}` | 基础/cls_shi_ren/sk_zhan_ge |
| 冰锥 | L50 `{p:12,c:0.05,max:5}` | L389 `{p:12,max:5}` | 基础/cls_fa_shi/sk_bing_zhui |
| 圣光弹 | L56 `{p:12,c:0.05,max:5}` | L525 `{p:10,max:5}` | 基础/cls_mu_shi |
| 雷击 | L102 `{p:12,c:0.05,max:5}` | L634 `{p:12,max:5}` | 基础/cls_fa_shi |
| 万毒噬心 | L106 `{p:10,c:0.08,max:3}` | L357 `{p:10,max:5}` | 分支/cls_ci_ke/T3/毒刃者 |
| 哀歌 | L32 `{p:10,c:0.05,m:2,max:5}` | L418 `{p:12,max:5}` | 分支/cls_shi_ren/T1/挽歌者 |
| 元素裁决 | L178 `{p:10,c:0.08,max:3}` | L383 `{p:10,max:3}` | 分支/cls_fa_shi/T3 |
| 星轨锁定 | L344 `{p:10,c:0.05,max:5}` | L496 `{max:3}` | 分支/cls_you_xia/T3 |
| 骷髅海 | L263 `{p:10,max:5}` | L647 `{max:1}` | 分支/cls_mu_shi/T3 |
| 龙息之怒 | L232 `{p:10,c:0.08,m:2,max:5}` | L651 `{p:10,max:5}` | 分支/cls_zhan_shi/T2 |

（112 组全量表见数据侧脚本产物：冲突键全部满足"旧区行 L<356、v153+/v180 行 L≥356"，无例外的 3+ 组、无同区内撞。）

### 5.2 48 组"同值重复"名单（删早留晚即可，无行为差）
（实施脚本可直接从基线对拍输出；此处列代表：安眠曲、安魂曲、圣光惩戒、气力裂空、生命圣域、破城锤、致命连射、连环拳、风暴之舞、疾风骤雨、终结·处刑、终结·暗影绞杀、猎网陷阱、穿心箭、穿云箭、直拳、破甲斩、旋风斩、震地击 等 —— 全量以脚本 assert 为准，不手抄。）

### 5.3 163 孤儿 key 的性质
- 全部是 v153 前**已从技能表删除/更名**的技能名（旧 6 基础职业部分技能：战争践踏/淬毒/冰霜新星/元素爆发/无畏冲击/林语印记/狩猎终章/暗影处刑/破晓之拳/龙爪/龙息/即兴弹唱/鼓舞/伴奏/蓄力斩…… 及旧隐藏职业被动等）。
- 现行可达性（§2.2 全仓复核）：monsters 205 条无 lv（v180 隔离）→ 不查 SKILL_UP；wild_npcs teach_skills 教的旧名经 `E.skill_info` 现查不到 info → 返回 None，**不产生 info dict**；pets/affixes/equip_roster 同名 token 为宠物自带技/词缀/装备名，不经引擎链路 → **无任何 live 路径能把孤儿名送进 `_skill_up`** → 删除行为零变化。
- 引擎 docstring 提到"怪技能撞名 14 个（圣光弹/雷击/龙爪…）"中的 龙爪 正属此列——怪物侧靠 lv 隔离已不触发，SKILL_UP 里残留的 龙爪 配置是死行。

### 5.4 pinyin id 撞车清单（分支 id 生成必须处理）
- `守歌`(基础，现 sk_shou_ge) 与 `收割`(分支 刺客 T1)：pinyin 皆 `shou_ge`。
- 消解：分支统一 `sk_br_` 前缀（`sk_br_shou_ge`），与基础/导师 `sk_` 前缀天然分域；全 305 名复核无第二撞。

---

*（本档由 wt_p0b worktree 只读侦察产出；SKILL_UP 未改动、game/ 未改动。下一步实施前请跑 Step 0 基线对拍脚本并把产物附本档。）*
