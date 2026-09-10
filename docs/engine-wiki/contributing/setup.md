# 贡献指南：开发环境与跑测试

本页面向**改引擎的人**（不是用引擎的人）。用引擎请从
[../getting-started/installation.md](../getting-started/installation.md) 开始。

## 环境

| 项 | 值 | 出处 |
|---|---|---|
| 解释器（引擎单测） | 任意 **Python 3.11/3.12**（引擎只用标准库） | `game/battle2/__pycache__/` 里并存 `cpython-311` / `cpython-312` |
| 解释器（**全量回归**） | **必须** AstrBot 的 uv python（带 `pypinyin`）：<br/>`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe` | `scripts/run_all_tests.py:52` |
| 第三方依赖（引擎） | **零** | 见 [../getting-started/installation.md](../getting-started/installation.md) |
| 静态检查配置 | **无**（无 flake8/ruff/black/mypy/pyproject/setup.py） | `ls` 核实 |

工作目录假设：`<plugin>/` = `data/plugins/dragonfall/`。

## 三种跑法

### ① 单个测试文件（最快，开发期用这个）

```bash
cd <plugin>
python tests/test_battle2_n4_schedule.py
```

每个测试文件都是**可独立运行的脚本**，末尾 `sys.exit(1 if FAIL else 0)`。
常见输出：

```
=== N4 battle2 CTB 调度测试 ===
  ✅ dot_next 登记 1.0
...
=== 结果 PASS=42 FAIL=0 ===
```

### ② 引擎纯度门禁（改引擎后**必跑**）

```bash
python tests/test_engine_no_content.py
```

它做 AST 静态分析（不 import 运行），断言 6 类内容（零反向边 / 零动态 import /
零 kind 字面量 / 注入面存在 / 26 符号门面 / 内容层零私有符号引用）。
exit=0 全绿。**这条红了就等于破坏了引擎的可分发性。**

### ③ 全量回归

```bash
python scripts/run_all_tests.py [--file tests/test_xxx.py] [--fail-fast]
                                [--jobs=N] [--serial]
                                [--skip=test_xxx.py[,test_yyy.py]] [--real-astrbot]
```

（`scripts/run_all_tests.py:5-6`）

机制（`scripts/run_all_tests.py:9-25`）：

- 每个测试文件 = **独立子进程 + 独立私有 DB**（`tests/.run_all_workers/` 下）
- 每轮先 `init_db` 建一次空白 schema 模板，各文件复制一份 → 表结构齐全且零残留
- 默认并行（按核数自适应 4~16），`--serial` 恢复串行（约 9 分钟）
- 默认注入 `tests/shim_astrbot`（行为等价的 astrbot 替身，全量 ~105s → ~27s）
- **串行槽**：硬编码共享库或自己私有库的文件先跑（`SERIAL_SLOT`，`:65-68`）

两条纪律（`scripts/run_all_tests.py:22-24`）：

1. **必须用 uv python**（否则缺 `pypinyin` 会挂）
2. **跑全量期间不要改源文件**（避免中间态误判）

### 测试规模参考（本次核实）

- `tests/test_*.py` 共 **245** 个文件
- 其中 battle2 相关 **28** 个（`tests/test_battle2_*.py`）
- 引擎专项：`test_engine_no_content.py`（门禁）· `test_battle2_coverage.py`（覆盖）
  · `test_battle2_n3_effects.py`（效果系统）· `test_battle2_n4_schedule.py`（调度）
  · `test_battle2_n5_serialize.py`（存档）· `test_battle2_n8_events.py`（事件总线）
  · `test_battle2_n10_*`（落地各段：吸血/防御/反伤/元素/承伤属性/初始 ct/食物）

## 测试脚手架（`tests/conftest.py`）

**新测试请从 conftest 复用，不要手抄模板**（`conftest.py:2-6` 原文）：

```python
from conftest import FakeEvent, run, clean_db, make_player, TEST_DB, PLUGIN_DIR
```

`conftest.py` 自动做三件事（`:24-38`）：

1. `GWEN_GAME_DB` → 独立测试库（**绝不触碰生产 `game_data.db`**）；
   用 `setdefault`，所以你可以预置自己的私有库名（`test_<名>.db`）
2. `GWEN_TEST_MODE=1`（测试模式下未知条件键直接 raise，防假绿）
3. 把 `qqbot/` 与插件根加进 `sys.path`

另：默认 shim astrbot（`GWEN_NO_SHIMMED_ASTRBOT=1` 退回真实 astrbot，对照验证用）。

⚠️ `tests/` 里还有大量 `_probe_*.py` / `_audit_*.py` / `_*.txt` 历史产物，
它们**不是测试**。`scripts/run_all_tests.py` 里有 `RETIRED_PROBES` 名单把退役探针排除。

## 引擎单测的最小写法（不拉整份内容）

引擎可以**零内容**跑（`game/battle2` 是自洽的）：

```python
import os, sys, random
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)

from game.battle2 import Battle, make_actor, config
from game.battle2 import formulas as F

# 最小装配（否则伤害恒 0 —— 见 getting-started/first-battle.md）
config.mount(formulas=F, kinds={...}, basic_fallback={...},
             skill_flat_fn=lambda: {...}, formula_skeleton_fn=lambda: {...})

random.seed(1234)      # 伤害有 ±15% 波动，精确断言必须定种子
```

> ⚠️ 但注意：`import game.battle2` 会触发 `game/__init__.py` 的惰性装配注册
> （`game/bootstrap.py:196`），首次读 hook 就会把 `game.content` 拉进来。
> 所以要**真正零内容**测试，请把引擎目录拷成独立包
> （[../getting-started/installation.md](../getting-started/installation.md) 的实测做法）。

## 改引擎的流程

```
1. 读完 architecture/（尤其 design-decisions.md 的 10 条 ADR）
2. 改代码
3. python tests/test_engine_no_content.py        ← 门禁必须先绿
4. python tests/test_battle2_<相关>.py           ← 相关专项
5. python scripts/run_all_tests.py               ← 全量（用 uv python）
6. 若动了公开 API 面 → 同步 5 个私有别名的门禁断言（tests/test_engine_no_content.py:97-103）
7. 若动了序列化 → 加一条旧档迁移断言
```

## 相关

- 代码约定 → [conventions.md](conventions.md)
- 版本与分发 → [release.md](release.md)
- 给自己的内容写断言 → [../guides/testing.md](../guides/testing.md)
