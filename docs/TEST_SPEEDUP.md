# 测试运行加速指南（v117 起）

全量回归从 ~9 分钟压到 ~1.5~2 分钟的关键文档。新同学/协作者先读这篇，再读 DEVELOPMENT.md §5。

## 1. 怎么跑最快

```bash
# 日常全量（推荐）：默认按核数自适应并行（4~16 路）
python scripts/run_all_tests.py

# 跳过已知坏测试（重构期间省 5s/个）
python scripts/run_all_tests.py --skip=test_v98_04_battle_registry.py

# 开发期单测（不进全量）
python scripts/run_all_tests.py --file=test_v94_stamina.py --fail-fast

# 兜底：旧行为（纯串行 + 共享 test_game_data.db，~9 分钟）
python scripts/run_all_tests.py --serial
```

实测耗时（149 文件，24 核/32G 机器，2026-08）：

| 方式 | 耗时 | 说明 |
|---|---|---|
| 旧版串行（真实 astrbot，共享库） | ~9 分钟 | 弃用，仅 --serial --real-astrbot 兜底 |
| 并行 + 真实 astrbot（--real-astrbot） | ~105s | 8~16 路 |
| **并行 + shim astrbot（默认）** | **~27s** | v117.5，见 §2.5 |

### 2.5 shim astrbot 与解耦（v117.5）

游戏命令层原本 import 的 astrbot 符号经审计全部是「注册副作用装饰器（返回原函数）+
类型标注 + 简单数据类」，v117.5 已分两步解耦：

1. **核心平台抽象 `game/commands/_platform.py`**：10 个 commands Mixin 改为 import
   项目自有平台模块（`filter.regex` 等语法原样保留，只换 import 来源）；装饰器
   **双注册**——同时注册核心注册表与真实 astrbot 注册表（生产可用时），保证迁移
   中间态生产行为不变。
2. **main.py 壳化**：核心 `Main` 类零 astrbot 依赖；`AstrMain(star.Star, Main)` 薄壳
   负责 astrbot 插件发现 + context 翻译（核心 MessageChain → astrbot 类型）。

`tests/shim_astrbot/` 是行为等价的 astrbot 替身，现在只服务于 main.py 壳的
`from astrbot.api import star`（测试命中替身省 import 开销，全量 27s）。

- **自动生效**：runner 子进程 env 注入；conftest 顶部也注入（手动单跑同样提速）。
- **对照验证**：`--real-astrbot`（runner）或 `GWEN_NO_SHIMMED_ASTRBOT=1`（手动单跑）
  退回真实 astrbot；改 shim/壳后必须两种模式结果一致（见 §6）。
- **生产安全**：真实 AstrBot 进程不会加载替身（只有测试进程的 PYTHONPATH 命中）；
  生产行为与原实现等价（声明驱动注册：`AstrMain` → `register_commands()` → `host/registration.py`）。
- 迁移到新平台：复用 `host/**` + 引擎通道，写目标平台的薄壳（照 `AstrMain`）。

## 2. 为什么以前慢、现在能快

**慢的根源**：每个测试文件 = 独立 Python 子进程；每个进程要 import 完整插件链
（`main → game.commands（158 个 handler）→ astrbot.api → astrbot.core.star/provider → google.genai + openai SDK`），
**仅 astrbot SDK 链就要 ~2.8s/进程**，游戏自身模块只占 ~0.3s；旧 runner 纯串行，且所有测试
共用 `test_game_data.db`、互相 `clean_db` 污染，**被迫串行**。

**并行安全的机制**（scripts/run_all_tests.py）：

1. **每文件独立私有库**：runner 给每个子进程设置 `GWEN_GAME_DB=tests/.run_all_workers/test_game_data_w<i>.db`；conftest 用 `setdefault` 尊重外层 env，测试拿到的就是自己的库 → 互不污染。
2. **空白 schema 模板**：每轮跑先用 `init_db()` 建一次模板（只 import game.store，~0.3s），各文件复制一份 → 表结构齐全、零残留（比旧共享库更干净，项目本就往私有库方向走）。
3. **串行槽**：硬编码共享 `test_game_data.db` 的文件（目前只有 `test_v101_28_food_hot.py`）自动进串行槽先跑；未来新增同款文件会被正则自动识别。
4. 失败时只打该文件 stdout/stderr 尾部 30 行，并行不刷屏。

## 3. 并行扩展性实测（为什么 16 路不是 2 倍）

并发 import 基准（每进程 import 完整插件链 ~4s）：

| 并发数 | 整批 wall | 结论 |
|---|---|---|
| 1 | 4.1s | 基线 |
| 4 | 4.2s | 近乎完美扩展 |
| 8 | 5.4s | 仍接近线性 |
| 16 | 11.1s | **撞上共享瓶颈**（所有进程同时读同一份 site-packages，大概率 Windows Defender 实时扫描序列化） |

→ 本机 8~16 路耗时几乎一样（112s vs 105s）。想再压到 1 分钟内，唯一现实手段是
**给 Windows Defender 加排除项**（设置 → 病毒和威胁防护 → 排除项，加
`C:\Users\yuyu\AppData\Roaming\uv\tools\astrbot` 与插件目录），排除后 16 路有望真正线性扩展。
（已实测确认瓶颈不在游戏代码——`game/data/` 大字典模块 import 合计仅 ~10ms。）

## 4. 参数速查

| 参数 | 作用 |
|---|---|
| `--jobs=N` | 并行路数，默认 `max(4, min(16, 核数))`；本机 8~16 均可 |
| `--serial` | 旧行为：纯串行 + 共享库 |
| `--file=xxx.py` | 只跑单文件（旧逻辑、共享库，行为不变） |
| `--fail-fast` | 出第一个失败即不再调度新文件（在途的跑完） |
| `--skip=a.py,b.py` | 跳过已知坏测试（逗号分隔，可重复） |
| `--real-astrbot` | 退回真实 astrbot（对照验证 shim 用，较慢） |
| 环境变量 `GWEN_NO_SHIMMED_ASTRBOT=1` | 手动单跑时退回真实 astrbot |

## 5. 新测试守则（否则会坑到并行）

1. **禁止直接赋值 `os.environ["GWEN_GAME_DB"]` 指向共享 `test_game_data.db`**（不认外层 env，会进串行槽拖慢全量）；要隔离库用 `setdefault` 指自己的私有库，或直接用 conftest 默认。
2. **概率/随机逻辑必须 `random.seed()` 固定**（DEVELOPMENT.md 铁律；v94 教训：探索随机触发采集事件额外扣体力 → 偶发假红）。
3. 测试必须确定性：不依赖真实时钟（patch 固定时段）、清 battle 状态、等级提到威慑线等，见 DEVELOPMENT.md §5。
4. 不要依赖其他测试文件留下的 DB 残留——并行下每个文件拿到的是零残留新库。

## 6. 失败排查流程

1. 看 ❌ 文件后面的 stdout/stderr 尾部输出（runner 自动打印 30 行）。
2. 单文件复现：`python scripts/run_all_tests.py --file=test_xxx.py`（共享库路径）。
3. 若单文件过、全量偶发挂：怀疑随机/时钟依赖 → 按 §5.2/5.3 修测试，别改 runner。
4. 想对照旧行为：`--serial` 跑一遍，若同样挂则是测试/代码问题，与并行无关。

## 7. 并行改造验证记录（v117）

- 第一版并行（空库不建表）→ test_v64_passive 挂 `no such table: players` → 加模板库机制修复。
- test_v94_stamina 偶发假红（无 seed）→ 补 `random.seed(42)` 修复。
- test_v98_04_battle_registry 旧断言未跟随战斗重构（mark 层数迁移），旧流程同样挂，属在途工作，用 `--skip=` 过渡。
- 四轮全量：118s / 116s / 112s / 105s，最终 148/149（唯一失败为上述在途测试，跳过即全绿）。
- 曾评估「测试进程注入假 astrbot 模块跳过 SDK import」：astrbot 装饰器体系与游戏代码深度耦合
  （filter.regex 150+ 处、star_handlers_registry 静态表校验、MessageChain/Node/Plain 构造），
  保真成本/漂移风险过高，否决。
