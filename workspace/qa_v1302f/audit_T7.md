# T7 · 被动节拍器改版×6 全链路审计（鹰眼/战争咆哮/磐石体/墓穴护甲/神圣坚韧/魔力贯穿）——v130.2f

审计日期：2026-08-26 | 依据：framework.md 铁律（只查不改）
验证手段：read_file / search_files / git show 39eeb11（改版 diff）/ 官方直跑 `python tests/test_v1302f_job_quality.py`（52 passed / 0 failed / 0 skipped）
+ 独立行为验证 `workspace/qa_v1302f/t7_sim.py`（27 passed / 0 failed，独立私有临时库，不碰生产库）

---

## 〇、改版事实（commit 39eeb11，数据层 6 处）

| 被动 | 改版前 | 改版后 | desc |
|---|---|---|---|
| 鹰眼（游侠 lv38） | stat crit +3%（生效） | proc mark_extra chance 0.15 | 攻击时15%概率额外叠1印记(与追踪印记叠加) |
| 战争咆哮（战士 lv55） | stat atk +8% 战斗开始 | proc res_gain_bonus | 攻击命中时怒气额外+1 |
| 磐石体（拳师 lv25） | dmg_taken 0.05 + 死字段 chi:1 | dmg_taken 0.05 + res_gain 1 | 受击减伤5%，受击时气+1（desc 补全） |
| 神圣坚韧（牧师 lv25） | dmg_taken_heal 20%×5% | dmg_taken 0.05 + res_gain 1 | 受击减伤5%，受击时信仰+1 |
| 墓穴护甲（暗影神谕线基础） | stat phys_reduce +5% | dmg_taken 0.05 + res_gain 1 | 受击减伤5%，受击时悼咏+1（觉醒即得） |
| 魔力贯穿（时咒线基础） | stat pene_magi +5% | proc attack_res res=time_sand gain=1 | 攻击命中时时间之沙+1（时间节拍加速） |

消费端均为 v104/v113 已有挂点复用（本轮零引擎新增）：mark_extra→battle.py:3388；res_gain_bonus/attack_res→battle.py:2282/2286；dmg_taken+res_gain→battle.py:4831-4849。

## 一、逐被动结论

### 1. 鹰眼（mark_extra 0.15）——**P1：改版把生效被动换成了永不可触发的死被动**
- **消费点存在**：battle.py:3388-3390（`for _pn, _ps in _procs.get("mark_extra", [])` → `random.random()<chance` → `extra_layers+=1`）。
- **渠道死穴**：消费点位于 `if element and E.ELEMENT_MARKS.get(element)` 分支（3385）——元素印记只在「施放带 element 的技能」时挂载。**全库静态证明**：PLAYER/BRANCH/TUTOR/HIDDEN 四表带 element 的技能 100% 属于 cls_fa_shi（法师系）；游侠（cls_you_xia）零 element 技能 → 鹰眼/追踪印记的消费点在游侠渠道**永不可达**（行为实测：游侠施放林语印记 → 元素印记 0 层；猎杀标记走 mech mark 另一系统 1 层，与元素印记无关）。
- **独立叠加**：✔ 消费循环逐条目独立 roll（白盒实测对称性：鹰眼中/追踪中→+2 层；仅鹰眼中/仅追踪中→各 +1 层），0.15+0.3 加法叠加、desc「与追踪印记叠加」字面成立——但双双无效。
- **历史**：v64（82009ec）引入追踪印记时只有数据、无消费端（git 验证），其挂靠的 v2.0 元素印记路径 14+ 版本从未被游侠触发；v130.2f 把原本生效的暴击+3% 换成该死壳 → **本次改版自造「被动消失」**。
- **desc 核对**：「攻击时15%概率额外叠1印记」——普攻/技能攻击渠道均无印记消费点，名实不符。

### 2. 战争咆哮（res_gain_bonus）——**P1：渠道只落地 1/3，「怒气全渠道+1」意图落空**（若按 desc 字面＝普攻口径则降 P2）
- **消费点**：battle.py:2282-2284，位于 `_resource_on_attack`（普攻命中渠道）——全引擎唯一消费点；`_resource_on_skill`（2298-2348）与受击段（4968-4985）均无 res_gain_bonus。
- **实测三渠道**：普攻命中 rage=1(on_attack)+1=2 ✔；技能命中 rage=2(on_skill，未加成)；受击 rage=1(on_hit，未加成)。合成渠道（on_skill=2）与受击渠道（on_hit=1）是战士怒气两大来源，均吃不到加成。
- **设计意图白纸黑字**：test_v1302f_job_quality.py 文档头「战争咆哮 res_gain_bonus 怒气全渠道+1」（§14.3 #1）——官方测试只断言普攻渠道（+2），绿灯掩盖了缺口。
- **desc**：「攻击命中时怒气额外+1」与实现字面自洽，但未表达「任意命中/全渠道」承诺。
- **叠加面 ⚠️**：同键邻居 狂战之魂/气力之心（战士/拳师二转）数据为 `{"res_gain_bonus": 1}` **非 proc 格式** → `_passive_map`（battle.py:2101-2107 只认 ps["proc"]/ps["stat"]）不收纳 → **实测 战争咆哮+狂战之魂 普攻只有 +2（预期 +3）**，狂战之魂「怒气获取+1」为死字段（遗留，非本轮改版；直接破坏「同渠道叠加」预期）。

### 3. 磐石体（dmg_taken 0.05 + res_gain 1）——**P2（满溢口径）+ P3（满值日志）**
- **消费点**：battle.py:4831-4849（受击路径），rpct=0.05>0 进入减伤结算 ✔（实测 受击 50 → 减伤 int(50×0.05)=2，dmg 48）；res_gain=1 → 气+1 ✔（拳师 on_hit=0，纯被动加成，与 desc 一致）；无 cond 放行 ✔。
- **叠加**：与磐石之心（5%）同渠道 → 实测减伤 4 点（各自按原 dmg 计、加法合算 = 10%）✔ 一致。
- **继承**：✔ 基础被动带进转职线（同职业 class 不变；攻线 T1 实测仍在被动汇总）；跨职业传承清空旧技能（player.py:861-863/881-882），隐藏线觉醒即得线级被动按 lv≤level 全授予 —— 无越权残留。
- **P2 满溢口径**：res_gain 走 `E.core_resource_gain` 直调（4848）——带上限但**绕过 `_res_gain_class` 的 overflow_shield 管线**。实测满 10 气受击：+1 蒸发（气=10、盾=0），而同场受击 if on_hit>0 会转盾（墓穴护甲侧实测同一次受击 on_hit 1 点转盾 5、被动 1 点蒸发——同资源双口径）。core_resources.py:71 明确承诺拳师 overflow_shield → 满资源态行为与承诺不符（守护姿态 res_gain 2 同段代码同样受影响）。
- **desc**：「受击减伤5%，受击时气+1」✔ 一致（v130.2f 顺带补全了旧 desc 截断）。

### 4. 墓穴护甲（dmg_taken 0.05 + res_gain 1，cls_hymn）——**P2（满溢口径）+ P3（满值日志）**
- **消费点同段**：受击 → 悼咏 1(on_hit 基础)+1(被动)=2 ✔ + 减伤 2 点 ✔（实测）。
- **继承**：✔ 觉醒即得（传承 grant lv≤level）；旧牧师被动跨线不残留（实测无越权）。
- **P2 满溢口径**：canticle 声明 overflow_shield=True（core_resources.py:109）——实测满 10 悼咏受击：on_hit 溢出转盾 5、墓穴护甲 +1 蒸发；与亡灵祭仪（走 `_res_gain_class` 转盾）同资源两条管线口径不一。
- **desc** ✔ 一致。

### 5. 神圣坚韧（dmg_taken 0.05 + res_gain 1，cls_mu_shi）——**P3 级（代码卫生）+ 主行为 ✔**
- **消费点同段**：受击 → 信仰 1(on_hit 基础)+1(被动)=2 ✔ + 减伤 2 点 ✔（实测）。faith 无 overflow_shield → 无满溢口径问题。
- **改版遗留**：旧 `dmg_taken_heal` 消费端 battle.py:5006-5012 成**死分支**（全库无技能挂载，实测空），注释仍称「被动·神圣坚韧——受击按概率回血」（过时，未来按注释加回该型被动会静默复活旧机制）。
- **desc** ✔ 一致。

### 6. 魔力贯穿（attack_res time_sand +1）——**P1：渠道错位，「施法命中+1沙」落空**（若按 desc 字面=普攻口径则降 P2）
- **消费点**：battle.py:2286-2288，位于 `_resource_on_attack`（普攻命中渠道）——全引擎唯一 attack_res 消费点。
- **实测**：普攻命中 → time_sand=1（on_attack=0+贯穿 1）✔；**施法命中 → time_sand=1（on_skill=1，贯穿未加成）**。
- **设计意图白纸黑字**：test 文档头「魔力贯穿 attack_res 施法命中+1 沙」；core_resources.py:89-90「施法 +1(on_skill)（时间节拍加速）」——时咒线是法系线，施法是主行动、普攻是次要行动 → 被动核心收益渠道错位，实际近乎无效（施法渠道本就有 on_skill+1 兜底）。
- **desc**：「攻击命中时时间之沙+1」字面与实现自洽、与意图不符。
- 无叠加对象（唯一 attack_res 被动）；寒霜亲和因 element 字符串槽崩溃风险被设计决策排除（test 文档 195-200），本被动为数值槽无此风险。

## 二、P0-P3 清单

| 级别 | 现象 | 文件:行号证据 | 影响 |
|---|---|---|---|
| **P0** | 无（无崩溃/数据污染/资源复制；官方 52 + 行为 27 断言全绿） | — | — |
| **P1-1** | 鹰眼改版=死被动：mark_extra 消费点只在元素印记路径（施法带 element 技能），全库 element 技能仅限法师系，游侠零触发路径；v130.2f 把生效的暴击+3% 换成了从未生效的追踪印记同款死壳 | skills.py 鹰眼 passive；battle.py:3385-3394（消费点，`element and ELEMENT_MARKS` 守卫）；全库扫描：element 技能 100% 属 cls_fa_shi；v64 起追踪印记即有数据无消费端（82009ec） | 游侠双印记被动（鹰眼 15%/追踪印记 30%）技能点白花、面板承诺 0 收益；策划按 desc 认知完全落空 |
| **P1-2** | 战争咆哮渠道只实现 1/3：res_gain_bonus 仅在 `_resource_on_attack`（普攻命中）消费；技能命中（on_skill=2）与受击（on_hit=1）渠道无加成，与测试文档「怒气全渠道+1」（§14.3 #1）不符；官方测试仅断言普攻渠道（+2），绿灯掩盖缺口 | battle.py:2282-2284（唯一消费点）；2298-2348 `_resource_on_skill` 无消费；4968-4985 受击段无消费；tests/test_v1302f_job_quality.py:247-263（仅普攻断言） | 战士怒气主力渠道（技能/受击）收益落空，改版承诺「攒怒更快」效果减半以上 |
| **P1-3** | 魔力贯穿渠道错位：attack_res 仅在 `_resource_on_attack`（普攻命中）消费；时咒线为法系主施法线，设计意图「施法命中+1沙」（测试文档头 + core_resources 注释）未落地 → 被动实际近乎无效（普攻渠道极少使用） | battle.py:2286-2288（唯一消费点）；core_resources.py:87-95（时咒 on_skill=1「施法+1」）；tests/test_v1302f_job_quality.py:201-207（仅配置断言） | 「时间节拍加速」承诺落空，被动=空挂 |
| **P2-1** | dmg_taken 系受击 res_gain 绕过 overflow_shield：磐石体/墓穴护甲/守护姿态 满资源时被动 +1/+2 溢出直接蒸发（`E.core_resource_gain` 平顶），而同资源 on_hit/亡灵祭仪 走 `_res_gain_class` 转盾 —— 实测满悼咏同一次受击：on_hit 溢出转盾 5、墓穴护甲 +1 蒸发 | battle.py:4842-4849（直调 E.core_resource_gain）；610-630 `_res_gain_class`（带 overflow_shield）；core_resources.py:26,71,109（承诺转盾）；t7_sim 实测 | 满资源稳态下承诺收益丢失、与「满溢转盾」设计口径不一致（金身/坦克流常态） |
| **P2-2 ⚠️** | 狂战之魂/气力之心「资源获取+1」为死字段：数据 `{"res_gain_bonus": 1}` 非 proc 格式，`_passive_map` 不收纳（实测 咆哮+狂战之魂 普攻=2 非 3）——遗留问题非本轮引入，但直接破坏「与战争咆哮同渠道叠加」的玩家预期 | skills.py 狂战之魂/气力之心 passive；battle.py:2096-2108 `_passive_map`（只认 proc/stat 键） | 二转被动空挂、叠加预期落空；需策划确认格式修复 |
| **P3-1** | dmg_taken 系满值日志无闸门：资源已满时仍无条件打印「受击获取 X 点资源（key 10）」 | battle.py:4849 | 满值反馈误导 |
| **P3-2** | 神圣坚韧改版遗留死代码+过时注释：dmg_taken_heal 消费端无任何技能挂载（实测空），注释仍称「被动·神圣坚韧——受击按概率回血」 | battle.py:5006-5012 | 代码卫生；未来按注释加回同型被动会静默复活旧机制 |
| **P3-3** | battle_conds.py 注释「（首回合，战争咆哮）」过时（战争咆哮已改 proc，不再用 battle_start cond） | battle_conds.py:262 | 注释误导 |
| **P3-4** | 提交信息「被动节拍器×5」实际 6 个（鹰眼/战争咆哮/磐石体/墓穴护甲/神圣坚韧/魔力贯穿） | commit 39eeb11 message | 口头记录不一致（旁证：测试文档头的 ×6 换成了寒霜亲和=设计决策排除项） |

## 三、与既有测试/断言冲突检查
- `test_v1302f_job_quality.py` 52 断言全绿（含 6 被动配置断言 + 磐石体受击回气 + 战争咆哮普攻 +2）——不冲突，但战争咆哮/魔力贯穿的行为断言只覆盖了「实现渠道」，未覆盖设计意图渠道（P1-2/P1-3 正是绿灯下的缺口）。
- `test_v64_passive.py` / `test_v106_1_attributes.py`（本提交改动 3/8 行）：鹰眼/追踪印记相关断言已随改版适配，无冲突；v64 断言仅查 passive 字段格式。
- 行为验证 27/27 全绿（t7_sim.py）：渠道矩阵 / 叠加 / 满溢 / 继承 / 死代码全部按预期判定。

## 四、体验/风险总结
改版 6 个被动里，**受击系 3 个（磐石体/墓穴护甲/神圣坚韧）减伤+回资源主链路健康**（减伤 5% 结算、res_gain 叠加于 on_hit 基础之上、同渠道加法叠加、继承无越权、desc 全一致），仅满资源边缘有转盾口径不一致（P2，金身/坦克流常态触发）。**攻击系 3 个全部有渠道问题**：鹰眼=死被动（P1，改版自造）、战争咆哮=渠道 1/3（P1）、魔力贯穿=渠道错位（P1）——共同根因是**改版只挂数据、复用旧消费点，未核对消费点渠道与设计意图（施法/全渠道）是否匹配**；官方测试对这三项只做了配置断言或单渠道断言，无法拦截。修复方向：① mark_extra 消费点挂到游侠猎杀标记（mech mark）路径或明确废弃；② res_gain_bonus/attack_res 在 `_resource_on_skill` 与受击段补消费（对齐「全渠道/施法命中」意图）或改 desc 明确普攻口径；③ 狂战之魂/气力之心数据格式修 proc 化；④ res_gain 改走 `_res_gain_class` 对齐转盾管线。

## 五、验证脚本
- `workspace/qa_v1302f/t7_sim.py`（27 断言，只读、独立私有临时库）：渠道矩阵（普攻/施法/受击×6 被动）、element 全表扫描、独立 roll 白盒、同渠道叠加、满溢转盾口径、继承矩阵、死代码/注释残留。
- `workspace/qa_v1302f/t7_dump_passives.py`（真 key 被动 dump 辅助）。