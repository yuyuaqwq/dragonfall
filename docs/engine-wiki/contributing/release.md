# 贡献指南：版本与分发

> ⚠️ **诚实标注**：引擎**当前还没有独立的版本号、没有 CHANGELOG、没有发布流程**。
> 本页写的是「现状 + 分发前必须过完的清单」，不是既有流程的复述。
> 未取证项列在文末与 [_selfcheck.md](../_selfcheck.md)。

## 现状：引擎怎么被"版本化"

| 层面 | 现状 |
|---|---|
| 插件版本 | `metadata.yaml` 的 `version: 0.105.0`（**这是插件的版本，不是引擎的**） |
| 引擎版本 | **无独立版本号**。引擎的变更以插件版本 + 文档文件名里的编号体现（如 `REFACTOR_v181P4_*`） |
| 仓库 | 引擎与游戏内容**在同一个仓库**（`game/battle2/` 与 `game/data/`、`game/services/` 并列） |
| 分发形态 | 目前是「同仓库源码 + 内容侧共享」；做成 submodule 的方案见 `docs/ENGINE_CONTENT_SPLIT_PLAN.md` §6/§7 |
| CHANGELOG | **无** |
| 兼容性承诺 | **无**（没有 semver 约定、没有弃用期策略） |

## 分发形态的三种候选

| 形态 | 做法 | 适合 |
|---|---|---|
| **拷目录** | 复制 `game/battle2/` 进你的项目，按需改名 | 只需一份、不跟上游 |
| **git submodule** | 把引擎拆成独立仓库，挂 submodule | 跟上游更新 / 提 PR |
| **PyPI 包** | 需要先加 `pyproject.toml` 与 `__version__` | 公共复用 |

前两种**现在就能做**（拷贝已实测跑通：见
[../getting-started/installation.md](../getting-started/installation.md)）；
第三种需要先补下面「分发前清单」的第 1、2 项。

## 分发前必须过的清单

### A. 边界（架构）—— 未完成项

- [x] **反向依赖已断**（原 15 条 `引擎→内容` import 边）—— 门禁
      `tests/test_engine_no_content.py` 可验（commit `d5e323e`，S1）
- [x] **公开 API 面已固化**（26 符号 re-export + 5 个私有符号升公开保别名，S2）
- [x] **通用件已归位**（`formula_expr` / `formation` / `skill_kinds` / `battle_bars` → `battle2/support/`，S3）
- [x] **`game/engine.py` 已拆**（S5'，commit `5eae164`；旧路径留 shim）
- [x] **内容侧单一装配入口已收敛**（S7，commit `50eb8dc`：`apply_game_content`）
- [ ] **引擎包改名**（S4：`game/battle2` → `game/engine`）—— 未做
- [ ] **拆仓库 / submodule**（S8）—— 未做（仓库无 `.gitmodules`）
- [ ] **收口清理过渡 shim**（S9）—— 未做（`game/engine.py` shim 仍在）
- [ ] **语义残留未清**（门禁只是 import 门禁）。未清的 4 项：
  - `support/skill_kinds.py` 的中文枚举值（`skill_kinds.py:27-34`）→ 应改为
    从 `config.kind_of` 注入，或明确标为「参考实现专用」
  - `landing` / `stats` 里的固定效果 key（`death_guard` · `heal_amp_pct` · `heal_down` ·
    `_anti_heal_pct` · `sleep`）
  - `effects.act_apply` 里的 `if key == "reduce"`
  - `battle._check_side_end` 里的 `"player"` 阵营名（`battle.py:515`）
  （完整表见 [../architecture/boundaries.md](../architecture/boundaries.md) 的「边界瑕疵」）
- [ ] **缺失消费方的声明清理**（`on_threshold` / `debuff_scale` / `wake_on_hit` /
      `tag` / `period.type` / `period.per_layer` / `period.dmg_type`）——
      要么实现消费，要么从参考实现的数据里删掉（现在它们会让第三方误以为可用）

### B. 可分发工程性

- [ ] **加版本号**：`game/battle2/__init__.py` 里加 `__version__`，
      或独立仓库的 `pyproject.toml`
- [ ] **加元数据**：Python 版本要求（当前未声明）、许可证、仓库地址
- [ ] **拆出可独立运行的测试**：现在 28 个 `test_battle2_*.py` 里有依赖内容侧
      （`config.load_game_defaults()`）的；分发包需要「零内容」的引擎自测集
      （门禁 `test_engine_no_content.py` 已经是零内容，可作起点）
- [ ] **去掉对仓库路径的假设**：`tests/conftest.py` 顶部的 `PLUGIN_DIR` / `QQBOT_DIR`
      路径推导（`dragonfall/` → `plugins/` → `data/` → `qqbot/`）属于本仓库结构
- [ ] **文档**：本 wiki（`docs/engine-wiki/`）作为引擎仓库的 `docs/`
- [ ] **示例工程**：一个 20 行的可运行 demo（本 wiki 的 README 已给出可跑样例，
      可直接抽成 `examples/`）

### C. 兼容性承诺（建议一次定下）

当前**没有**任何承诺。若要发布，建议至少约定：

| 变更类型 | 承诺 |
|---|---|
| `EVENTS` 元组增删 | **破坏性**（事件名是协议）；删事件要留一个版本的兼容 fire |
| `Battle` 公开方法签名 | 破坏性；加参数只能加在末尾且带默认值 |
| `to_state` 字段 | 加字段 = 兼容（旧档缺字段走默认）；**改字段语义 = 破坏性**（需要迁移） |
| 引擎动词的行为 | 破坏性（内容层依赖语义） |
| 新增 hook | 兼容 |
| `support/` 的函数 | 视为公开（已在 `__init__` 之外被引用），改动需评估 |

## 迁移期的两条实务建议

1. **引擎侧与内容侧分开发版本**。现在插件版本 `0.105.0` 同时覆盖两者，
   导致「引擎改了但内容没跟上」和「内容改了」无法区分。
2. **保留 `docs/ENGINE_CONTENT_SPLIT_PLAN.md` 的 S1–S3 门禁作为回归锚**
   （它每步都有机器可验断言）。拆仓库时把 `tests/test_engine_no_content.py`
   一起搬走 —— 它是分发包的**自证文件**。

## 未取证 / 待确认

- 引擎的实际最低 Python 版本（只有 `__pycache__` 里的 3.11/3.12 痕迹）
- 是否已有计划中的分发形态（spec 提到 submodule，但仓库里**没有** `.gitmodules`）
- 是否存在内部约定的版本号方案（注释里的 `v181` 系列编号是否等价 semver 未知）
- commit 类型约定（无 CONTRIBUTING / 无钩子 —— 见 [conventions.md](conventions.md) §9）

完整清单 → [../_selfcheck.md](../_selfcheck.md)

## 相关

- 边界与迁移方案 → [../architecture/boundaries.md](../architecture/boundaries.md)
- 拿引擎的三种方式 → [../getting-started/installation.md](../getting-started/installation.md)
- 测试与回归 → [setup.md](setup.md)
