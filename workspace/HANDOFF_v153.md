# v153 职业重做 · 交接文档（2026-09-01 深夜）

> 鱼鱼睡前交代：按 v153 重做职业（适配 CTB 时刻制引擎）；玩家技能已重置，旧技能直接删；
> 严格数据驱动；可开子 agent 但先分析好；配套内容对齐；回合制遗留数值审计；文案要好。

## ✅ 已完成并提交（git master）

### 1. v153 技能表落库（4c833c8 + 后续修复）
- **294 技能全部落库**：7 职业 × 42（基础 8 + A线 17 + B线 17），`game/data/skills_v153.py`
- 生成器：`scripts/gen_skills_v153.py`（从 docs/CLASS_MECHANICS_v153.md 解析 → 引擎技能表）
- 基础技能 key = `sk_` + 拼音；分支技能 key = 中文名（v151 惯例）
- 字段：lv/mp/power(=base)/kind/cast/cd/hits/mech/cond/desc + 职业专属（focus_cost/faith/shaken_gain）
- **cond 全填充**（stacks/mult 从正则组解析，0 残留 None）

### 2. 职业定义（classes.py）
- 新增 **第 7 职业吟游诗人 cls_shi_ren**（咏叹/挽歌两线，staff 武器，后排）
- 转职改名：法师 元素法师→元素使、奥秘法师→奥术学者/奥术大师/奥秘主宰；
  游侠 林语者→森语者、自然行者→自然守望者、疾风猎手→狂风之猎；
  牧师 B 线→死灵祭司/亡魂引渡者/黯灵君主；拳师 磐岩壁垒→不破之壁
- **cast_atk/cast_defend/cast_flee 全部 7 职业补录**（C-12，§0.3 表）

### 3. 引擎机制接线（416e96b + ca25567）
- **元素印记**：fire_mark/ice_mark/thunder_mark + 结算反应（蒸发×1.3/超载AOE/冻结/感电）✅ 实测验证
- **诗人旋律**：melody/melody_chant/melody_finale（驻留 + 强度层 + 终章）✅ 实测验证
- **磐核爆发**：guard_core_burst（消耗全部磐核 ×(1+0.7×核)）
- **牧师信念负载**（C-18）：四档（清醒/专注/透支/过载）+ 每刻 −0.7 + 过载触发
- **狂暴维持浮点**：maintain_cost 0.6（C-13 破绽衰减 4→1.7）
- **15 个缺失 mech handler 全部补齐**（战意兑现/终结技/猎印/诅咒/骸骨/毒爆/诗人削弱/腐蚀）
- **游侠专注流量制**：energy regen 30→18（每刻 +18）

### 4. desc 文案精写（6198d72）
- **294 条全部精写**（7 子 agent 并行，v151 风格生动文案）
- 样例："长剑划出利落的弧光——造成 82% 物理伤害，命中积攒 1 点战意"

### 5. skill_up 升级曲线（8d02fe9）
- **294 技能独立配置**（p/c/m/max 按类型：输出 p12/max5、大招 p10/max3、被动 max1、增益 max3）

### 6. P4 配套内容
- 转职对话 24 处更新（dialogues.py）+ 诗人导师 NPC + 诗人就职入口
- builds.py 7 职业 × 21 套流派重写（126 引用 0 坏引用）
- 技能书坏引用修复（毒爆术→荆棘爆、安眠曲→诗人）
- 召唤物补全：火元素/雷元素（summons.py）

### 7. 策划案同步（design/new_world 09_职业体系.md）
- §2 职业定位总览更新为 7 职业 + v153 说明

## 🔧 验证结果
- 引擎加载 294 技能 OK，skill_info 全部可查
- 核心机制实测：战士战意、法师元素蒸发、诗人旋律、游侠专注 ✅
- **全量回归 221/222**（test_v137_dungeon 单独跑绿 = 共享库 DB 污染 flaky，v151 已知）
- **数值门禁 8/8 全绿**（含 v133 峰值红线）
- **34 个测试文件全部适配完成**（3 子 agent + 主 agent 收尾）

## 📋 待办

### 🔴 P7 被动机制接线（最大遗留：53 个被动全不生效）
- **现状**：v153 的 53 个被动技能已生成 dict 格式（不崩），但引擎 `_passive_map` 只消费 14 个 proc
  （counter_attack/heal/dodge_up 等），其余 40+ 个（zhan_yi_crit/arcane_intuition/element_core/
  counter_chance/melody_duet 等）**引擎无消费点 → 被动效果不生效**（学了只是占位）
- **需接线清单**（53 个）：见 gen_skills_v153.py 的 MECH_RULES passive 段
- **挂点分类**：伤害倍率类（zhan_yi_crit/poison_all_up/speed_ratio_dmg 等）→ _set_skill_dmg_mult；
  受击类（counter_chance/reflect/tenacity）→ _damage_player；战斗开始类（focus_full_on_kill）；
  每刻类（arcane_intuition/undead_faith）→ _turn_start
- 这是 v153 机制完整性的最大缺口，需逐个接线

### P6 测试适配（已基本完成，待全量回归确认）
- task-0 完成 11 个（已提交 0a14408）；task-1/task-2 完成 23 个（未提交，在工作区）
- 需主 agent 提交 + 跑全量回归

### P4 剩余配套
- 诗人专属装备/套装（当前用 staff 通用装备）
- 装备词条 chi（气）资源残留（v153 拳师废弃 chi → 词条静默失效，需审计）

### P5 回合制遗留审计
- "回合"文本已由 v152 清零；装备 turns 按刻制转换已完成
- 需继续：chi 资源词条、装备效果在新体系下的语义核对

### 上线
- AstrBot 重启验证（NapCat 3473145972）
- 双仓库 push（dragonfall + design/new_world）

## 🔧 环境
- 项目根：C:/Users/yuyu/qqbot/data/plugins/dragonfall（git: master，v153 共 10 commits）
- 设计仓库：design/new_world/
- 回归：`python scripts/run_all_tests.py --serial`
- 技能生成：`python scripts/gen_skills_v153.py`（改数据后重跑 + apply_v153_descs.py 回填 desc）
