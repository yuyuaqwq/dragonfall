# 技能结算管线化重构设计（v176 根治方案）

> 目标：消灭 _player_skill God Method（858→563 仍过长），用"结算上下文 + 阶段方法 + 乘区表"根治
> 设计先行，鱼鱼确认后实施（动引擎核心结算，最高风险档）

## 一、根因诊断

_player_skill 的攻击技能分支本质是**一条 6 阶段流水线**，但用"函数内局部变量顺序传递"实现：

```
[暴击判定] → [乘区装配(13来源)] → [段循环伤害] → [命中效果] → [吸血/资源] → [日志]
```

**为什么变成 God Method**：
1. **乘区 = 13 个局部变量**（frozen/stealth/stack/cond/magic/passive/reaction/affix/elem/...）——
   加新乘区只能在函数中间插一行；乘区之间还有副作用交叉（passive_bonus 被 combo/三连/套装多处累乘）
2. **阶段间靠实例字段飞线**（self._mom_mult/_combo_mult/_combo_ready_used/_sk_af_mult/_hp_cost_bonus 5 个临时字段跨方法传递标签）
3. **版本补丁叠层**：117/565 行是 v 注释（代码内版本历史代替 git）

## 二、根治方案：_AttackCast 结算上下文

### 核心思想
一次攻击结算 = 构造 `_AttackCast` → 依次调用阶段方法 → 取结果。
**所有中间状态挂在 ctx 上**（不再局部变量飞线），**乘区收成 dict**（可插拔、可测、可审计）。

```python
class _AttackCast:
    """一次攻击技能结算上下文（轻量，仅战斗内瞬态）。"""
    __slots__ = ("battle", "st", "est", "player", "info", "kind", "mech",
                 "lv", "skill_name", "target", "logs",
                 # 阶段产物
                 "is_crit", "lucky", "stealth_mult", "effs", "stealth_hit",
                 "mults", "execute_tag", "element", "procs", "reaction_log",
                 "multi", "total", "magi_part", "tags", "mark_done")

    def __init__(self, battle, st, player, info, skill_name, target=None):
        self.battle = battle
        ...
        self.mults = {}          # 乘区表: 来源名 -> 倍率
        self.tags = []           # 伤害标签（斩杀/蓄势/套装…）

    # ---- 阶段 1: 基础 + 暴击判定 ----
    def roll_crit(self): ...

    # ---- 阶段 2: 乘区装配（核心重构点）----
    # 每来源一个方法/数据键, 全部写 self.mults
    def mult_frozen(self): self.mults["frozen"] = ...
    def mult_stack(self): ...
    def mult_passive(self): ...
    def mult_reaction(self): ...   # 反应副作用(AOE/冻结/感电)在各自来源方法内
    def mult_class_bonus(self): ... # 蓄势/连段/三连/套装 —— 替代 5 个 self._*_mult 飞线
    def finalize_pmult(self):
        pmult = E.skill_power_mult(...)
        for v in self.mults.values(): pmult *= v
        return min(pmult, C.SKILL_PMULT_CAP)

    # ---- 阶段 3: 段循环伤害 ----
    def apply_segments(self):
        for seg in range(self.multi): ...

    # ---- 阶段 4: 命中效果（标记/连段/资源词条/吸血）----
    def apply_on_hit(self): ...
```

### 关键设计决策
1. **乘区 dict 化**：`self.mults["frozen"]=1.3` 代替 `frozen_bonus=1.3` 局部变量
   - 加新乘区 = 在装配阶段加一行 `mults["xxx"]=...`（不动段循环/pmult 计算）
   - pmult 计算统一为 `product(mults.values())`（一个循环替代 13 变量手乘）
2. **实例字段飞线消灭**：self._mom_mult 等 5 个 → 存 ctx.mults["momentum"] + ctx.tags
   - 副作用：普攻路径也读这些字段？需查（_player_dmg_mult 或普攻处若读则保留兼容）
3. **阶段方法化**：roll_crit/mult_*/apply_segments/apply_on_hit 各自独立可测
4. **_player_skill 变薄**：~30 行编排（选分支 → 构造 ctx → 调阶段 → 返回 logs）

### 迁移路径（分步，每步门禁绿 + 回归一致）
1. **Step 1**: 建 _AttackCast 骨架（__init__ + mults dict），_player_skill 内先构造 ctx 但还不用
2. **Step 2**: 乘区局部变量 → ctx.mults（纯搬移，pmult 计算改 product）
3. **Step 3**: 段循环 → ctx.apply_segments()
4. **Step 4**: 命中效果 → ctx.apply_on_hit()
5. **Step 5**: _player_skill 瘦身为编排器；删 5 个实例临时字段
6. 每步: 36 门禁 + refactor_regression --compare (4fab93c9433b) + commit

### 风险与护栏
- 最高风险档（引擎核心结算），必须逐 Step 迁移 + 每步全量验证
- 行为零变化目标：mults dict 乘积顺序与原连乘一致（乘法交换律保证相等）
- 普攻/宠物若也读 self._mom_mult 等字段 → Step 5 需同步改（先 grep 确认影响面）
- 迁移期间保留旧方法（_skill_crit_roll/_skill_seg_damage/_skill_passive_dmg_bonus 可先被 ctx 包装或并入）

## 三、预期效果
- _player_skill: 563 → ~40 行（纯编排）
- 新乘区接入成本：改一个数据/加一个 mult_xxx 方法，不碰主流程
- 每个乘区/阶段可独立单测
- v 注释随迁移自然精简（原因写 git，代码留"为什么"）
