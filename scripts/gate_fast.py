#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""门禁**快速档**：按「这次改了哪些文件」只跑相关门禁，把全量门禁挪到批收口那一次。

为什么有它（今晚实测的耗时结构）
--------------------------------
```
一条 dsh 线的时长 ~ 改动量 x **门禁轮数**；实测 ~70% 时间花在验证上：
  · 一轮门禁 ~ 2 分钟（文案 55s + 数值 24s + v87 + v104 + tlogs + v185 ...）
  · 全量 272 文件跑一遍 ~ 5 分钟
p4pf 那批 36 个壳 x 每壳 7 道门禁 = 2 小时 47 分（最慢的一条）
⇒ 本工具：按改动面**只跑相关门禁**；全量留到批收口（`--full`）。
```

用法
----
```
python scripts/gate_fast.py --changed <path> [<path> ...]   # 指定改动文件
python scripts/gate_fast.py --changed auto                  # 自动探测（git status + 与 --baseline 比）
python scripts/gate_fast.py --full                          # 跑全量（= 手工那套 7 道 + 定向补强 + 两条全量）
python scripts/gate_fast.py --self-check                    # 校验映射表没有「无门禁覆盖」的盲区
```
辅助开关（不改变上面四个语义）：
```
--plan            只算选中集合、不执行（回放/审阅用；打印选中与跳过两段）
--list            打印映射表全文（门禁 <-> 覆盖 glob <-> 实测耗时）
--emit-map        以 markdown 打印映射表（写报告用）
--gates a,b,c     只跑指定门禁（人工复现手工那套 7 道时用）
--json PATH       另存机器可读结果
--dry-run         等价于 --plan
--sandbox DIR     沙箱适配：TEMP/TMP/LOCALAPPDATA 重定向 + PYTHONPATH 注入 DIR\\_env
--host/--framework/--python/--baseline/--db-dir/--timeout   路径与超时覆盖
```

行为要求（逐条对齐作业书 §1）
------------------------------
```
(1) 映射表**显式写在脚本里**：每条门禁 -> 覆盖路径 glob + 实测耗时（见 GATES）。
    覆盖路径口径：包内 content/** · 宿主 game/** · tests/** · editor/** · docs/** · 引擎 saintess_engine/**
(2) 选中规则 = 改动文件 ∩ 门禁覆盖 glob；**并额外跑 cheap 冒烟**（引擎能加载 + 包能 import）
(3) 结束打印**两段**：`✅ 已跑：<清单 + 各自耗时>` / `⏭️ 已跳过：<清单 + 原因> -> 批收口请跑 --full`
(4) 退出码：已跑的门禁有红 -> 非零；全绿 -> 0；**跳过的门禁不影响退出码**（但必须在上面的两段里醒目列出）
(5) `--self-check`：仓库里所有「可被改动的路径」逐个过映射表，没有门禁覆盖的列出来
    （要么补映射，要么在 NO_GATE 里显式标注「此路径无门禁覆盖，理由=...」）
```

红线（不许降低验证强度）
------------------------
* 跳过的门禁**只影响提示，不影响退出码**；但两段打印里必须逐条列出、并指到 `--full`。
* `--changed` **不选** tier=full 的两条全量门禁（272 / 55 文件）——它们只在 `--full` 跑；
  这条规则本身也会在「已跳过」里逐条打印，不做静默省略。
* 只改 docs 这类非行为面时，输出必须**明示**「跳过了全部行为门禁」。
* cheap 冒烟**永远跑**（它是「引擎能加载 + 包能 import」的最低保险，与改动面无关）。

沙箱注意
--------
Windows 沙箱下两条已知坑会让门禁**假红**（详见 `overnight/B18-QUEUE-gwen.md` 落地姿势 0/1/1b）：
  0. `tempfile.mkdtemp` 用 `os.mkdir(path, 0o700)` -> 拿不到写 ACE -> 走临时目录的门禁全假红。
     本脚本用 `--sandbox DIR` 注入 `DIR/_env/sitecustomize.py`（只替换 mkdtemp 的 mode，不碰仓内文件）。
  1b. 行尾：引擎仓 = LF / 插件镜像 = CRLF；对拍前先 `diff -q --strip-trailing-cr`。
这两个开关**只影响沙箱**，真仓 / CI 不需要。
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time

# --------------------------------------------------------------------------------------
# 0. 常量与默认路径
# --------------------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HOST_ROOT = os.path.dirname(HERE)                      # scripts/ 的上级 = 宿主插件仓根
DEFAULT_FRAMEWORK_DIR = "C:/Users/yuyu/framework-engine"       # 与仓内其它门禁同一默认口径
DEFAULT_PYTHON = "C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe"
DEFAULT_TIMEOUT = 1200

#: 手工那套 7 道（今晚 p4pf 实测那套）——`--full` 的对照基准。
MANUAL_CANON = ["v87", "v104", "texts", "numeric", "tlogs", "adm", "run185"]
MANUAL_CANON_EVIDENCE = (
    "p4pf/out/gates_final.log（2026-09-14 21:59 实测：v87 242/0 · v104 314/0 · 文案 63/63 · "
    "数值 18/18 · tlogs 21/21 · v185 准入 85/85 · v185 遍历 30/30，总判全绿）"
)

#: `--full` 相对手工那套多出来的门禁 -> 为什么要多跑（逐条解释，见 `--full` 对照表）。
FULL_EXTRA_REASONS = {
    "import_closure": "手工那套没有它：IMPGATE 门禁（包内 import 面自洽）只在引擎仓 run_all 里，"
                      "而今晚 C2<->C4 的 _host_content 错位正是它抓到的那一类（见三个历史事件回放 ①）。",
    "egg83": "手工那套没有它：改 event_templates/reward 取件口时，这条是当场炸 ImportError 的定点门禁之一。",
    "evt97_03": "手工那套没有它：同上，事件模板导入面/行为冻结的定点门禁。",
    "re97_05": "手工那套没有它：rule_engine 猴补面失效（PATCHAUDIT/INTFIX §7-U1）就是它报的红。",
    "mech_ports": "手工那套没有它：包内 content/mech/** 的端口门禁（P4 批次 36 个壳搬的正是这层）。",
    "export_sync": "手工那套没有它：包内 content/data|rules 与域清单/schema 的同步门禁（域声明改动的主要抓手）。",
    "texts_specs": "手工那套没有它：文案真源 <-> 宿主镜像 <-> 投影 texts.json 的三方同步门禁（文案 63/63 不查这三份的一致性）。",
    "domain_owner": "手工那套没有它：域 owner/tier 门禁（B15 的 commands 域 owner 红项就是它报的）。",
    "pkg_coverage": "手工那套没有它：域清单/落点/孤儿文件门禁（FIXDECL 的 text_specs 域声明红项就是它报的）。",
    "terminal": "手工那套没有它：终态复合门禁（宿主 <=2k 行 / 零包知识 / 包内覆盖等 6 条，转调引擎骨架）。",
    "editor_domains": "手工那套没有它：引擎侧「包声明域 <-> 有效域表」门禁（域声明改动的定点门禁）。",
    "editor_decl_domains": "手工那套没有它：声明式域门禁（域声明/落点改动的定点门禁）。",
    "editor_large_pkg": "手工那套没有它：大包（73 域 / 9000+ 条）装载门禁（域声明改动后的冒烟）。",
    "editor_schemas": "手工那套没有它：包内 schema <-> 数据条目门禁（改 schema/数据条目时先红的那条）。",
    "wiki_refs": "手工那套没有它：引擎 wiki 行号引用自检（改 docs/ 才是它选中的唯一理由）。",
    "host_test_self": "手工那套没有它：改测试本体时最少要跑它自己（否则改测试等于没验证）。",
    "fw_test_self": "手工那套没有它：同上（引擎仓侧）。",
    "patch_surface": "手工那套没有它：PATCHAUDIT ④ 的常驻哨兵（宿主壳改写静默 no-op 扫描），"
                     "正是历史事件②那一类的长期看门人。",
    "host_runall": "手工那套没有它：这是**全量**（272 文件 ~5 分钟），按设计只在批收口跑，不进 --changed。",
    "fw_runall": "手工那套没有它：引擎仓全量（55 文件），同上，只在批收口跑。",
    "smoke_engine": "手工那套没有它：cheap 冒烟，永远跑（引擎能加载）。",
    "smoke_pkg_import": "手工那套没有它：cheap 冒烟，永远跑（包能 import）。",
}

#: 「无门禁覆盖」的显式标注：glob -> 理由。`--self-check` 只对**既不被门禁覆盖、
#: 也不在这张表里**的路径报红（这就是它的牙）。**不许用它掩盖真缺口** —— 每条都要能说出理由。
NO_GATE = [
    # ---- 宿主插件仓 ----
    ("host:main.py", "宿主进程入口（AstrBot 启动装配），无独立门禁；装配面由 terminal + runall 间接覆盖"),
    ("host:metadata.yaml", "插件平台清单（AstrBot 元数据），非行为面，无门禁覆盖"),
    ("host:ARCHITECTURE.md", "宿主架构文档，无门禁覆盖（文档漂移靠人审）"),
    ("host:DEVELOPMENT.md", "宿主开发文档，无门禁覆盖（同上）"),
    ("host:README.md", "宿主 README，无门禁覆盖"),
    ("host:docs/**", "宿主文档目录，无门禁覆盖（B18 队列里那批文档滞后项靠人审 + 单开小活）"),
    ("host:design/**", "宿主设计稿目录（策划案/设计文档），无门禁覆盖"),
    ("host:data/**", "宿主平台数据目录（非源码；AstrBot 运行时数据）"),
    ("host:schema/**", "宿主侧 schema 副本目录，无门禁覆盖（真源 schema 在引擎仓，由 editor_schemas 覆盖）"),
    ("host:tools/**", "宿主一次性排查/审计脚本，无门禁覆盖"),
    ("host:playthrough_cmd*.txt", "人工playthrough 指令清单，无门禁覆盖"),
    ("host:test_*.db*", "测试库文件（运行时产物），无门禁覆盖"),
    ("host:_b14_*", "B14 波次留下的测试库/产物，无门禁覆盖"),
    ("host:scripts/balance_data/**", "数值平衡数据（脚本输入），无门禁覆盖"),
    ("host:scripts/*.md", "脚本目录里的历史报告/说明，无门禁覆盖"),
    ("host:scripts/playtest_*.json", "playtest 回环状态文件，无门禁覆盖"),
    ("host:scripts/data/**", "脚本数据目录，无门禁覆盖"),
    ("host:scripts/build_matrix/**", "数值矩阵构建产物，无门禁覆盖"),
    ("host:scripts/economy_lib/**", "经济模拟库（离线工具），无门禁覆盖"),
    ("host:scripts/numeric_lib/**", "数值工具库（离线工具），无门禁覆盖"),
    ("host:scripts/_retired/**", "已退役导出器（归档），无门禁覆盖"),
    ("host:scripts/*.ps1", "宿主一次性运维脚本，无门禁覆盖"),
    ("host:scripts/*.sh", "宿主一次性运维脚本，无门禁覆盖"),
    ("host:tests/__init__.py", "测试包标记文件，无门禁覆盖"),
    ("host:tests/conftest.py", "测试夹具/DB 引导（所有测试共享）；它自身的改动无定向门禁，靠 runall 暴露"),
    ("host:tests/shim_astrbot/**", "astrbot 行为等价替身（run_all 的提速 shim），非产品码，无门禁覆盖"),
    ("host:tests/data/**", "测试用数据资产（t2i 模板等），无门禁覆盖"),
    ("host:tests/numeric_sim.py", "数值测试的共享模拟器（被 test_numeric_* 引用）"),
    ("host:tests/b20_qq_ref.py", "B20 试玩的 QQ 侧参考实现（对照用），无门禁覆盖"),
    ("host:tests/smoke_*.py", "冒烟脚本（非 test_*.py，run_all 不收编；历史遗留）"),
    ("host:tests/_*", "测试私有夹具/冻结基准（_cmd_registry / _command_table_freeze / _battle_settlement_snapshot / "
                      "_ports_freeze_gen 等）：随对应测试一起被读，自身单改无定向门禁"),
    ("host:tests/pytest_shim/**", "pytest 兼容 shim，无门禁覆盖"),
    ("host:scripts/**", "宿主 scripts/ 下的**其它**脚本：一次性排查/审计/生成器（audit_*/scan_*/gen_*/sim_*/"
                        "playtest*/loopback*/verify_*/v*_*.py 等），多数是一次性活、不进任何门禁；"
                        "★ 被登记为门禁本体的那几个（check_domain_owner / verify_package_coverage / "
                        "check_terminal_state / run_numeric_tests / mirror_tlogs）已经在门禁覆盖里（门禁自覆盖），"
                        "不会落到这条标注上"),
    ("host:scripts/*.txt", "脚本目录里的历史输出（playthrough_out / regression_report），无门禁覆盖"),
    ("host:__init__.py", "宿主插件包标记（AstrBot 插件入口标记），无门禁覆盖"),
    # ---- 引擎仓 ----
    ("fw:tests/js/**", "引擎测试用的前端 JS 夹具（form_widgets_test 等），无 Python 门禁覆盖"),
    ("fw:tests/conftest.py", "引擎测试夹具，无门禁覆盖"),
    ("fw:tests/_domain_fixtures.py", "引擎测试夹具（非 test_*.py，run_all 不直接跑），无门禁覆盖"),
    ("fw:tests/run_all.py", "引擎仓全量运行器本体：改它由人工跑一次 fw_runall（--full）验证，自身无定向门禁"),
    ("fw:games/*/README.md", "包 README（历史盘点），无门禁覆盖"),
    ("fw:examples/**/*.md", "示例包 README，无门禁覆盖"),
    ("fw:README.md", "引擎仓 README，无门禁覆盖"),
    ("fw:docs/**", "引擎文档（非 engine-wiki 部分）无门禁覆盖；engine-wiki/** 由 wiki_refs 覆盖"),
    ("fw:tools/**", "引擎离线工具，无门禁覆盖"),
    ("fw:schemas/**", "引擎通用 schema 由 editor_schemas 间接覆盖（见该门禁 covers）"),
    ("fw:examples/minimal-game/**", "示例包：由 fw_runall 的 minimal-game 冒烟覆盖（--full 才跑）"),
    ("fw:games/my_game/**", "引擎自带迷你示例包（非本产品包）：由 import_closure / fw_runall 覆盖"),
    ("fw:tests/_domain_fixtures.py", "引擎测试夹具（非 test_*.py，run_all 不直接跑），无门禁覆盖"),
    ("fw:tests/conftest.py", "引擎测试 conftest，无门禁覆盖"),
    ("fw:editor/web/**", "编辑器前端静态资源，无门禁覆盖（B20 只跑了 test_editor_play 的 HTTP 面）"),
    ("fw:editor/UI_DESIGN.md", "编辑器 UI 设计文档，无门禁覆盖"),
    ("fw:editor/README.md", "编辑器 README，无门禁覆盖（FIXDECL 曾按人审改它）"),
    ("fw:.gitignore", "VCS 忽略清单，无门禁覆盖"),
    ("host:.gitignore", "VCS 忽略清单，无门禁覆盖"),
    ("host:.gitmodules", "子模块清单，无门禁覆盖"),
]

#: 「可被改动的路径」扫描时**排除**的目录/文件名（不是盲区掩盖：--self-check 会把它们单独打印出来）
EXCLUDE_DIRS = {
    ".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", ".mypy_cache",
    ".ruff_cache", ".runtmp", ".idea", ".vscode", "dist", "build",
}
EXCLUDE_NAME_RE = re.compile(
    r"(\.pyc$|\.pyo$|\.db$|\.db-|\.db\.|\.sqlite$|\.bak|\.orig$|\.rej$|~$|\.pref|\.mutbak$"
    r"|\.b14bak$|\.log$|\.zip$|\.png$|\.jpg$|\.jpeg$|\.gif$|\.ico$|\.exe$|\.dll$|\.so$|\.lock$"
    r"|^\.loopback|^\.spy_|^playtest_loop_state)"
)
INTERESTING_EXT = {
    ".py", ".json", ".md", ".yaml", ".yml", ".js", ".css", ".html", ".txt", ".sh", ".ps1", ".ts",
}


# --------------------------------------------------------------------------------------
# 1. 映射表（**显式**：门禁 -> 覆盖路径 glob + 实测耗时）
# --------------------------------------------------------------------------------------
#
# `covers` 口径（每条都必须能说出「这个门禁读/断言的是这些文件」）：
#   host:<rel>  宿主插件仓（dragonfall/）内的相对路径
#   fw:<rel>    引擎仓（GWEN_FRAMEWORK_DIR 指向的框架仓）内的相对路径
# glob：`*` 不跨 `/`，`**` 跨层级；`*` 单独一条 = 全部路径。
#
# `cost` = **本机实测**秒数（2026-09-15，沙箱副本、py=uv astrbot python；
# 7 道核心门禁的数值与 p4pf/out/gates_final.log 的实测同量级）。
# `tier`：core/engine = 行为门禁；docs = 文档层；smoke = cheap 冒烟；full = 全量。
# `selectable=False` 的门禁**不参与 --changed 选中**（只有 --full 跑），并在「已跳过」里逐条说明。


class Gate(object):
    __slots__ = ("gid", "title", "repo", "cwd", "argv", "covers", "cost", "tier",
                 "selectable", "needs_db", "why", "dyn_changed", "measure_file",
                 "baseline_red")

    def __init__(self, gid, title, repo, cwd, argv, covers, cost, tier,
                 selectable=True, needs_db=True, why="", dyn_changed=False,
                 measure_file=None, baseline_red=None):
        self.gid = gid
        self.title = title
        self.repo = repo            # 门禁登记在哪个仓（决定默认 cwd 与 --full 的分组）
        self.cwd = cwd              # "host" | "fw" | "fw_tests"
        self.argv = argv            # 相对 cwd 的参数（argv[0] = 脚本）
        self.covers = covers
        self.cost = cost
        self.tier = tier
        self.selectable = selectable
        self.needs_db = needs_db
        self.why = why
        #: True = 命令按**改动文件**现搭（「改哪个测试就跑哪个测试」），argv 只是模板
        self.dyn_changed = dyn_changed
        self.measure_file = measure_file
        #: 已登记基线红：{"pat": <输出里必须出现的原文片段>, "cite": <出处>, "all": True}
        self.baseline_red = baseline_red


GATES = [
    # ================= 核心 7 道（手工那套；MANUAL_CANON）= =================
    Gate(
        "v87", "命令注册矩阵（同 pattern 多注册仅限豁免组）", "host", "host",
        ["tests/test_v87_command_matrix.py"],
        ["host:game/commands/**", "host:game/content.py",
         "fw:games/*/content/commands.py", "fw:games/*/content/cmds_*.py",
         "fw:games/*/content/data/commands.json"],
        0.13, "core",
        why="AST 扫宿主 game/commands/** 的 @declared/@filter.regex 注册面；包内命令表同源。",
    ),
    Gate(
        "v104", "命令系统（声明/优先级/守卫/回执 314 断言）", "host", "host",
        ["tests/test_v104_commands_system.py"],
        ["host:game/commands/**", "host:game/content.py", "host:game/data/cmd_config.json",
         "fw:games/*/content/commands.py", "fw:games/*/content/cmds_*.py",
         "fw:games/*/content/data/commands.json"],
        2.51, "core",
        why="真跑命令系统：注册表 + 优先级 + 守卫 + 回执；读 game/commands/** 与包内命令表。",
    ),
    Gate(
        "texts", "文案表 63/63（真源 content/data/text_specs.json + 宿主 game/core/texts.py）", "host", "host",
        ["tests/test_texts_table.py"],
        ["host:game/core/texts.py", "host:game/data/text_specs.json",
         "host:game/commands/**", "host:game/core/instance_gate.py",
         "fw:games/*/content/texts.py", "fw:games/*/content/data/text_specs.json",
         "fw:games/*/content/data/texts.json"],
        65.2, "core",
        why="63 条文案逐格比对；含宿主命令层 T.text/T.static AST 计数（副本准入 WIRED 域）。",
    ),
    Gate(
        "numeric", "数值 18 文件（公式/曲线/掉落统一/掉落矩阵）", "host", "host",
        ["scripts/run_numeric_tests.py"],
        ["host:game/core/**", "fw:saintess_engine/**", "fw:games/*/content/rules/**"],
        28.1, "core",
        why="转调 tests/test_numeric_*.py 18 个文件；吃引擎公式 + content/rules 数值表 + game/core 曲线。",
    ),
    Gate(
        "tlogs", "tlogs 单源 21/21（真源包内 content/data/tlogs.json）", "host", "host",
        ["tests/test_tlogs_single_source.py"],
        ["host:game/data/tlogs.json", "host:game/tlog_setup.py",
         "host:scripts/mirror_tlogs.py", "fw:games/*/content/data/tlogs.json"],
        1.68, "core",
        why="断言「真源=包内 content/data/tlogs.json / 镜像=宿主 game/data/tlogs.json / 读点只有 tlog_setup.py 一处」。",
    ),
    Gate(
        "adm", "v185 副本准入 85/85（含源码级 AST 门禁）", "host", "host",
        ["tests/test_v185_instance_admission.py"],
        ["host:game/commands/instance*.py", "host:game/core/instance_gate.py",
         "host:game/core/texts.py", "host:game/commands/base.py",
         "fw:games/*/content/cmds_instance*.py", "fw:games/*/content/flow/instance_gate.py",
         "fw:games/*/content/flow/instance_battle.py"],
        8.19, "core",
        why="副本准入 85 项 + 对 game/core/instance_gate.py 的源码级断言（>=11 T.text / >=16 T.static）。",
    ),
    Gate(
        "run185", "v185 副本行为冻结 30/30（接线路由/合成房间战）", "host", "host",
        ["tests/test_v185_instance_run.py"],
        ["host:game/commands/instance.py", "host:game/commands/instance_battle.py",
         "host:game/commands/combat.py", "host:game/commands/world.py",
         "host:tests/_v185run_baseline.json",
         "fw:games/*/content/cmds_instance*.py", "fw:games/*/content/flow/**",
         "fw:games/*/content/combat_cmds.py"],
        2.34, "core",
        why="真跑一条副本流程，把逐步命令输出 + battle.state 快照与冻结基准逐字比对。",
    ),

    # ================= 定向补强（三个历史事件各自的门禁）=================
    Gate(
        "import_closure", "包内 import 面自洽（AST，含函数体内延迟 import）", "fw", "fw_tests",
        ["test_package_import_closure.py"],
        ["fw:games/*/**/*.py", "fw:examples/*/**/*.py"],
        1.53, "engine",
        why="历史事件①：content/event_templates.py 的 `from .reward import _host_content` 被打断就是它点名的。",
    ),
    Gate(
        "egg83", "v83 探索彩蛋（猴补面 roll_poi/roll_wild_encounter/roll_explore_egg）", "host", "host",
        ["tests/test_v83_explore_egg.py"],
        ["host:game/commands/combat.py", "host:game/commands/exploration.py", "host:game/content.py",
         "host:game/core/event_templates.py",
         "fw:games/*/content/combat_cmds.py", "fw:games/*/content/exploration.py",
         "fw:games/*/content/wild.py", "fw:games/*/content/pois.py",
         "fw:games/*/content/event_templates.py"],
        1.90, "core",
        why="历史事件①：C2<->C4 错位落地前就是它（+ v97_03）当场炸 ImportError —— 它的 import 链"
            "（conftest -> 宿主包 -> content.event_templates）经过 event_templates，故 event_templates 也算它的依赖面。",
    ),
    Gate(
        "evt97_03", "v97_03 事件模板（注册表 + 落库 + 猴补面 roll_explore_event）", "host", "host",
        ["tests/test_v97_03_event_templates.py"],
        ["host:game/core/event_templates.py", "host:game/commands/combat.py",
         "fw:games/*/content/event_templates.py", "fw:games/*/content/data/event_templates.json"],
        1.74, "core",
        why="历史事件①：同上（事件模板取件口错位的定点门禁）。",
    ),
    Gate(
        "re97_05", "v97_05 规则引擎（猴补面 _is_time + RULES 同源）", "host", "host",
        ["tests/test_v97_05_rule_engine.py"],
        ["host:game/core/rule_engine.py", "host:game/data/rules.py",
         "fw:games/*/content/rule_engine.py", "fw:games/*/content/catalog_b143.py",
         "fw:games/*/content/rules/game_config.json"],
        3.3, "core",
        why="历史事件②：宿主编写 `game.core.rule_engine._is_time` 归一化时钟失效（猴补面失效）时它夜间必红。",
        baseline_red={"pat": "77 通过 / 1 失败",
                      "cite": "INTFIX out/W-INTFIX.md §7-U1（夜间必红：宿主壳 game/core/rule_engine.py:30 的 "
                              "_is_time 是 import 期引用拷贝，覆盖不到包内实现 content/rule_engine.py）—— "
                              "既有缺陷、主修法在宿主 game/**，与本工具无关；白天自动变绿（78/0）",
                      "all": True},
    ),
    Gate(
        "mech_ports", "包内 content/mech 端口门禁", "host", "host",
        ["tests/test_package_mech_ports.py"],
        ["host:game/core/**", "fw:games/*/content/mech/**"],
        1.81, "engine",
        why="P4 批次 36 个壳搬进包内的机械/端口面（mech/**）与宿主薄壳的一致性。",
    ),
    Gate(
        "export_sync", "包内数据 <-> 域清单/落点/schema 同步", "host", "host",
        ["tests/test_export_package_sync.py"],
        ["fw:games/*/content/data/*.json", "fw:games/*/content/rules/*.json",
         "fw:games/*/game.json", "fw:games/*/editor/domains.json", "fw:games/*/schemas/**",
         "host:game/data/**"],
        1.71, "engine",
        why="逐条过包内 schema + 域清单 <-> 数据文件落点；改域声明/数据条目必跑。",
    ),
    Gate(
        "texts_specs", "文案真源 <-> 宿主镜像 <-> 投影 texts.json 三方同步", "host", "host",
        ["tests/test_texts_specs_sync.py"],
        ["host:game/data/text_specs.json", "host:game/core/texts.py",
         "fw:games/*/content/data/text_specs.json", "fw:games/*/content/data/texts.json",
         "fw:games/*/content/texts.py"],
        1.18, "engine",
        why="文案规格表的三方一致性（texts 63/63 不查这三份是否同源）。",
    ),
    Gate(
        "domain_owner", "域 owner/tier 门禁（72+ 域全标注 + 标注自洽）", "host", "host",
        ["scripts/check_domain_owner.py", "--check"],
        ["fw:games/*/editor/domains.json", "fw:games/*/game.json", "fw:games/*/content/**/*.py"],
        0.48, "engine",
        why="历史事件③：B15 的 commands 域 owner（engine->package）红项就是它报的。",
    ),
    Gate(
        "pkg_coverage", "域清单/落点/孤儿文件门禁（包内覆盖）", "host", "host",
        ["scripts/verify_package_coverage.py", "--check"],
        ["fw:games/*/editor/domains.json", "fw:games/*/game.json",
         "fw:games/*/content/data/*.json", "fw:games/*/content/rules/*.json"],
        1.59, "engine",
        why="历史事件③：FIXDECL 的「存在未声明的域文件：content/data/text_specs.json」就是它报的。",
    ),
    Gate(
        "terminal", "终态复合门禁（宿主<=2k 行 / 零包知识 / 包内覆盖 6 条）", "host", "host",
        ["scripts/check_terminal_state.py", "--check"],
        ["host:game/**", "fw:games/*/content/**", "fw:saintess_engine/**"],
        2.9, "engine",
        why="转调引擎骨架 + 包内覆盖 + 宿主规模/零包知识；改行为面时的整体口径闸。",
        baseline_red={"pat": "未达标 2 条",
                      "cite": "终态目标 ①（宿主 12,556 行 > 2,000 行）②（零包知识 172 处 > 0）**未达标** —— "
                              "这两条是 B19b 的终态目标，不是本波回归（fixdecl out/W-FIXDECL.md §4.1："
                              "「①② 是作业书自己认定仍在的未达标项，整体 exit 1 属预期」）；③④⑤⑥ 达标",
                      "all": True},
    ),

    Gate(
        "patch_surface", "宿主壳改写「静默 no-op」哨兵（PATCHAUDIT ④ 常驻）", "host", "host",
        ["tests/test_patch_surface.py"],
        ["host:tests/**", "host:game/**/*.py"],
        2.8, "core",
        why="历史事件②的**常驻哨兵**：扫 tests/**（含 conftest）里每条对宿主名字的改写，逐条判"
            "「有效 / 静默 no-op」，新增未登记的失效改写直接报红（`--self-test` 自带牙）。"
            "★ 本线快照（宿主 0ee4557）比它进仓的提交（5384351）早一版，故在快照上它是红的 —— "
            "见下面 baseline_red 的归因；当前真仓上应为绿。",
        baseline_red={"pat": "失效改写（静默 no-op）",
                      "cite": "本线快照早于宿主提交 5384351（PATCHAUDIT：修 test_v97_05 的猴补面失效，"
                              "把改写打到包内 content.rule_engine._is_time，夜间 78/0）；"
                              "该哨兵正是在**修复前**的树上报红（1 条 = test_v97_05 的 `RE._is_time`），"
                              "属快照漂移、非本次改动引入；当前真仓（5384351）上应复绿。",
                      "all": True},
    ),
    # ================= 引擎侧 editor 门禁 =================
    Gate(
        "editor_domains", "引擎侧 包声明域 <-> 有效域表（85/85）", "fw", "fw_tests",
        ["test_editor_package_domains.py"],
        ["fw:games/*/editor/domains.json", "fw:games/*/game.json",
         "fw:games/*/content/data/*.json", "fw:games/*/content/rules/*.json", "fw:editor/**"],
        3.01, "engine",
        why="历史事件③的引擎侧定点门禁：域数不写死，按「内置 ∪ 包声明」的集合关系判。",
    ),
    Gate(
        "editor_decl_domains", "声明式域门禁（28/28）", "fw", "fw_tests",
        ["test_editor_declarative_domains.py"],
        ["fw:games/*/editor/**", "fw:editor/**", "fw:games/*/schemas/**"],
        0.30, "engine",
        why="声明式扩展面（domains.json 的 kind/schema/primary 等字段口径）。",
    ),
    Gate(
        "editor_large_pkg", "大包装载门禁（32/0）", "fw", "fw_tests",
        ["test_editor_large_package.py"],
        ["fw:games/*/content/data/*.json", "fw:games/*/content/rules/*.json",
         "fw:games/*/editor/domains.json", "fw:editor/**"],
        2.38, "engine",
        why="73 域 / 9000+ 条的大包装载冒烟；域声明或数据条目改动后必跑。",
    ),
    Gate(
        "editor_schemas", "包内 schema <-> 数据条目（38/38）", "fw", "fw_tests",
        ["test_editor_package_schemas.py"],
        ["fw:games/*/schemas/**", "fw:schemas/**", "fw:games/*/content/data/*.json"],
        1.91, "engine",
        why="逐条过包内 schema；改 schema 或数据条目先红的那条。",
    ),
    Gate(
        "wiki_refs", "引擎 wiki 行号引用自检（drift 0）", "fw", "fw_tests",
        ["test_wiki_refs.py"],
        ["fw:docs/engine-wiki/**", "fw:games/*/docs/**", "fw:editor/**"],
        0.21, "docs",
        why="文档层门禁：改 wiki/文档时校验文内行号引用不漂移（FIXDECL 改 wiki 后靠它复绿）。",
    ),

    # ================= 「改哪个测试就跑哪个测试」（动态命令）=================
    Gate(
        "host_test_self", "宿主仓自测：改动哪个 tests/test_*.py 就直接跑它", "host", "host",
        ["tests/test_v87_command_matrix.py"],
        ["host:tests/test_*.py"],
        1.5, "core", dyn_changed=True, measure_file="tests/test_v87_command_matrix.py",
        why="改测试本体（不是产品代码）时，最少要跑的就是它自己；命令按本次命中的改动文件现搭"
            "（一个文件一次 python tests/<file>.py，私有库）。",
    ),
    Gate(
        "fw_test_self", "引擎仓自测：改动哪个 tests/test_*.py 就直接跑它", "fw", "fw_tests",
        ["tests/test_wiki_refs.py"],
        ["fw:tests/test_*.py"],
        0.5, "engine", dyn_changed=True, measure_file="tests/test_wiki_refs.py",
        why="同上（引擎仓侧）；cwd = <fw>/tests，与 tests/run_all.py 同姿势。",
    ),

    # ================= 全量（只在 --full 跑）=================
    Gate(
        "host_runall", "宿主全量 run_all_tests.py（272 文件 ~5 分钟）", "host", "host",
        ["scripts/run_all_tests.py"],
        ["*"],
        194.9, "full", selectable=False, needs_db=False,
        why="全量回归：改动面无关，按设计只在批收口（--full）跑。沙箱副本实测 272 文件 / 263 通过 / 9 失败 / 194.9s，"
            "9 红 = 7 已登记基线红（INTFIX §4.4 基线 265/7 的同一批）+ v97_05 夜红（同上）+ test_texts_table 冷库态红"
            "（fresh DB 62/63、温库 63/63，已实测归因，见 W-GATEFAST §4）。",
    ),
    Gate(
        "fw_runall", "引擎仓全量 tests/run_all.py（55 文件）", "fw", "fw",
        ["tests/run_all.py"],
        ["*"],
        97.3, "full", selectable=False, needs_db=False,
        why="引擎仓全量（含 minimal-game 冒烟）：沙箱副本实测 54 文件 / 54 通过 / 0 失败 / 97.3s（全绿）。"
            "同上，只在批收口跑。",
    ),

    # ================= cheap 冒烟（永远跑）=================
    Gate(
        "smoke_engine", "cheap 冒烟：引擎能加载", "fw", "fw",
        ["-c", "__SMOKE_ENGINE__"],
        ["*"], 0.17, "smoke", needs_db=False,
        why="最低保险：saintess_engine 能 import（引擎坏了后面所有门禁都无意义）。",
    ),
    Gate(
        "smoke_pkg_import", "cheap 冒烟：包能 import", "fw", "fw",
        ["-c", "__SMOKE_PKG__"],
        ["*"], 0.35, "smoke", needs_db=False,
        why="最低保险：包内 content 包能 import（含 content.rule_engine / event_templates 这类易断点）。",
    ),
]

GATES_BY_ID = {g.gid: g for g in GATES}

SMOKE_CODE = {
    "__SMOKE_ENGINE__": (
        "import sys; sys.path.insert(0, {fw!r}); import saintess_engine as E; "
        "print('SMOKE-ENGINE-OK names=%d' % len(dir(E)))"
    ),
    "__SMOKE_PKG__": (
        "import sys; sys.path.insert(0, {fw!r}); sys.path.insert(0, {pkg!r}); "
        "import content; import content.rule_engine; import content.event_templates; "
        "print('SMOKE-PKG-OK path=%s' % content.__path__[0])"
    ),
}


# --------------------------------------------------------------------------------------
# 2. glob 匹配与路径归一
# --------------------------------------------------------------------------------------

def glob_to_re(pat):
    """把覆盖 glob 编译成正则：`*` 不跨 `/`，`**` 跨层级（`**/` 可匹配零层）。"""
    out = []
    i, n = 0, len(pat)
    while i < n:
        c = pat[i]
        if pat.startswith("**/", i):
            out.append(r"(?:.*/)?")
            i += 3
        elif pat.startswith("**", i):
            out.append(r".*")
            i += 2
        elif c == "*":
            out.append(r"[^/]*")
            i += 1
        elif c == "?":
            out.append(r"[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("".join(out) + r"\Z")


_GLOB_CACHE = {}


def path_matches(pattern, repo, rel):
    """pattern = '<repo>:<glob>' 或 '*'（全部）。"""
    if pattern == "*":
        return True
    prep, _, g = pattern.partition(":")
    if prep != repo:
        return False
    rx = _GLOB_CACHE.get(g)
    if rx is None:
        rx = _GLOB_CACHE[g] = glob_to_re(g)
    return bool(rx.match(rel))


def covers_hit(gate, changed):
    """返回 (命中的改动文件列表, 命中的覆盖 glob 列表)。

    改动文件按 `coverage_keys` 展开（宿主仓的 `framework/<rel>` == 引擎仓 `<rel>`），
    这样「在宿主仓里看到 framework/... 被改」与「引擎仓 ... 被改」选出同一批门禁。
    """
    files, globs = [], []
    for repo, rel in changed:
        hit = False
        for r, p in coverage_keys(repo, rel):
            for pat in gate.covers:
                if path_matches(pat, r, p):
                    globs.append(pat)
                    hit = True
                    break
            if hit:
                break
        if hit:
            files.append("%s:%s" % (repo, rel))
    return files, sorted(set(globs))


def norm_rel(p):
    p = p.strip().strip('"').strip("'").replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def normalize_changed(raw, host_root, fw_root):
    """把用户给的各种写法归一成 [(repo, rel), ...]。

    接受：`host:<rel>` / `fw:<rel>` / `framework:<rel>` / `engine:<rel>` /
        绝对路径（落哪个仓就归哪个仓；`<host>/framework/**` 归 fw）/
        `framework/<rel>`（宿主侧写法）/ 裸相对路径（先按存在性判，再按目录特征判）。
    返回 (changed, notes)：notes 记录归一过程中的提示（不静默丢东西）。
    """
    host_root = os.path.abspath(host_root).replace("\\", "/")
    fw_root = os.path.abspath(fw_root).replace("\\", "/")
    out, notes = [], []
    for item in raw:
        p = norm_rel(item)
        if not p:
            continue
        low = p.lower()
        repo = rel = None
        for prefix, r in (("host:", "host"), ("fw:", "fw"), ("framework:", "fw"), ("engine:", "fw")):
            if low.startswith(prefix):
                repo, rel = r, p[len(prefix):]
                break
        if repo is None:
            cand = os.path.abspath(p).replace("\\", "/")
            if cand.lower().startswith(fw_root.lower() + "/"):
                repo, rel = "fw", cand[len(fw_root) + 1:]
            elif cand.lower().startswith(host_root.lower() + "/framework/"):
                repo, rel = "fw", cand[len(host_root) + len("/framework/"):]
            elif cand.lower().startswith(host_root.lower() + "/"):
                repo, rel = "host", cand[len(host_root) + 1:]
            elif low.startswith("framework/"):
                repo, rel = "fw", p[len("framework/"):]
            else:
                host_p = os.path.join(host_root, p)
                fw_p = os.path.join(fw_root, p)
                if os.path.exists(host_p):
                    repo, rel = "host", p
                elif os.path.exists(fw_p):
                    repo, rel = "fw", p
                else:
                    top = p.split("/", 1)[0]
                    repo = "fw" if top in (
                        "saintess_engine", "editor", "schemas", "games", "examples") else "host"
                    notes.append("路径不存在，按目录特征归到 %s：%s" % (repo, p))
        if not rel:
            notes.append("跳过空路径：%r" % (item,))
            continue
        rel = norm_rel(rel)
        if os.path.isdir(os.path.join(host_root if repo == "host" else fw_root, rel)):
            notes.append("路径是目录（已保留为前缀匹配）：%s:%s" % (repo, rel))
        out.append((repo, rel))
    # 去重保序
    seen, uniq = set(), []
    for repo, rel in out:
        if (repo, rel) not in seen:
            seen.add((repo, rel))
            uniq.append((repo, rel))
    return uniq, notes


def detect_changed(host_root, fw_root, baseline=None):
    """`--changed auto`：git status（含未跟踪） + 与基线比（--baseline / $GATEFAST_BASELINE）。"""
    changed, notes = [], []
    for repo, root in (("host", host_root), ("fw", fw_root)):
        if not os.path.isdir(os.path.join(root, ".git")) and not os.path.exists(os.path.join(root, ".git")):
            notes.append("%s 仓没有 .git，跳过 auto 探测：%s" % (repo, root))
            continue
        try:
            pr = subprocess.run(["git", "-C", root, "status", "--porcelain"],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        except OSError as e:
            notes.append("%s 仓 git 调用失败：%s" % (repo, e))
            continue
        if pr.returncode != 0:
            notes.append("%s 仓 git status 返回 %s" % (repo, pr.returncode))
        for line in (pr.stdout or "").splitlines():
            if len(line) < 4:
                continue
            body = line[3:].strip()
            if " -> " in body:                      # rename
                body = body.split(" -> ", 1)[1]
            body = norm_rel(body.strip('"'))
            if not body or body == "framework" and repo == "host":
                continue                            # 子模块指针：fw 仓自己会被扫到
            changed.append(("host" if repo == "host" else "fw", body))
        base = baseline
        if base:
            try:
                pr2 = subprocess.run(["git", "-C", root, "diff", "--name-only", base],
                                     capture_output=True, text=True, encoding="utf-8", errors="replace")
                if pr2.returncode == 0:
                    for line in (pr2.stdout or "").splitlines():
                        line = norm_rel(line)
                        if line:
                            changed.append(("host" if repo == "host" else "fw", line))
                else:
                    notes.append("%s 仓 git diff %s 返回 %s" % (repo, base, pr2.returncode))
            except OSError as e:
                notes.append("%s 仓 git diff 调用失败：%s" % (repo, e))
    # 目录条目展开：git status 里的目录（未跟踪目录）展开成文件
    expanded, seen = [], set()
    for repo, rel in changed:
        root = host_root if repo == "host" else fw_root
        full = os.path.join(root, rel)
        if os.path.isdir(full):
            for p in iter_repo_paths(root):
                if p == rel or p.startswith(rel.rstrip("/") + "/"):
                    key = (repo, p)
                    if key not in seen:
                        seen.add(key)
                        expanded.append(key)
            continue
        key = (repo, rel)
        if key not in seen:
            seen.add(key)
            expanded.append(key)
    return expanded, notes


# --------------------------------------------------------------------------------------
# 3. 可改动路径扫描（--self-check 用）
# --------------------------------------------------------------------------------------

def iter_repo_paths(root):
    """列出「可被改动的路径」（相对路径，posix 风格）。排除项见 EXCLUDE_DIRS / EXCLUDE_NAME_RE。"""
    res = []
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in EXCLUDE_DIRS and not d.startswith(".run_all_workers")]
        for fn in filenames:
            if EXCLUDE_NAME_RE.search(fn):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in INTERESTING_EXT:
                continue
            full = os.path.join(dirpath, fn)
            res.append(os.path.relpath(full, root).replace("\\", "/"))
    return sorted(res)


def gate_self_path(g):
    """门禁**自己**的脚本路径（改哪个门禁本体 -> 那个门禁要被选中）。"""
    if not g.argv or g.argv[0].startswith("-"):
        return None
    if g.cwd == "host":
        return ("host", g.argv[0])
    if g.cwd == "fw_tests":
        return ("fw", "tests/" + g.argv[0])
    if g.cwd == "fw":
        return ("fw", g.argv[0])
    return None


def coverage_keys(repo, rel):
    """算覆盖时用的等价键：宿主仓的 `framework/<rel>` 就是引擎仓的 `<rel>`（子模块镜像）。"""
    keys = [(repo, rel)]
    if repo == "host" and rel.startswith("framework/"):
        keys.append(("fw", rel[len("framework/"):]))
    return keys


def coverage_gates():
    """参与「覆盖判定」的门禁 = 能被 --changed 选中的那些。

    **不许**把 `covers=['*']` 的全量/冒烟门禁算进来 —— 它们的覆盖面是「全部路径」，
    算进来会让 self-check 恒绿（牙就没了）。全量门禁按设计只在 --full 跑，不构成覆盖。
    """
    return [g for g in GATES if g.selectable and g.tier != "smoke"]


def self_check(host_root, fw_root):
    """返回 (covered, annotated, blind, scanned_counts)。blind = 既无门禁覆盖也无标注的路径。"""
    covered, annotated, blind = [], [], []
    counts = {}
    cov_gates = coverage_gates()
    for repo, root in (("host", host_root), ("fw", fw_root)):
        paths = iter_repo_paths(root)
        counts[repo] = len(paths)
        for rel in paths:
            gates = []
            for r, p in coverage_keys(repo, rel):
                gates += [g.gid for g in cov_gates
                          if any(path_matches(c, r, p) for c in g.covers)]
            for g in cov_gates:                       # 门禁本体自覆盖
                if gate_self_path(g) == (repo, rel):
                    gates.append(g.gid)
            if gates:
                covered.append(("%s:%s" % (repo, rel), sorted(set(gates))))
                continue
            notes = []
            for r, p in coverage_keys(repo, rel):
                notes += [why for pat, why in NO_GATE if path_matches(pat, r, p)]
            if notes:
                annotated.append(("%s:%s" % (repo, rel), notes))
            else:
                blind.append("%s:%s" % (repo, rel))
    return covered, annotated, blind, counts


# --------------------------------------------------------------------------------------
# 4. 执行
# --------------------------------------------------------------------------------------

def resolve_python(explicit=None):
    for cand in (explicit, os.environ.get("GWEN_PYTHON"), DEFAULT_PYTHON):
        if cand and os.path.exists(cand):
            return os.path.abspath(cand)
    return sys.executable


def resolve_roots(args):
    host = os.path.abspath(args.host or os.environ.get("GATEFAST_HOST") or DEFAULT_HOST_ROOT)
    if args.framework:
        fw, src = os.path.abspath(args.framework), "--framework"
    elif os.environ.get("GWEN_FRAMEWORK_DIR"):
        fw, src = os.path.abspath(os.environ["GWEN_FRAMEWORK_DIR"]), "$GWEN_FRAMEWORK_DIR"
    else:
        fw, src = os.path.abspath(DEFAULT_FRAMEWORK_DIR), "默认 %s" % DEFAULT_FRAMEWORK_DIR
    if not os.path.isdir(fw):
        sub = os.path.join(host, "framework")
        if os.path.isdir(sub):
            fw, src = sub, "<host>/framework 回退"
    return host, fw, src


def gate_cwd(gate, host_root, fw_root):
    if gate.cwd == "host":
        return host_root
    if gate.cwd == "fw":
        return fw_root
    if gate.cwd == "fw_tests":
        return os.path.join(fw_root, "tests")
    if gate.cwd.startswith("abs:"):
        return gate.cwd[4:]
    return host_root


def build_env(gate, python, host_root, fw_root, db_dir, sandbox, py_path_extra):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["GWEN_FRAMEWORK_DIR"] = fw_root
    env["GATEFAST_HOST"] = host_root
    if gate.needs_db:
        env["GWEN_GAME_DB"] = os.path.join(db_dir, "gf_%s.db" % gate.gid)
    pp = env.get("PYTHONPATH", "")
    parts = []
    if sandbox:
        parts.append(os.path.join(os.path.abspath(sandbox), "_env"))
    if py_path_extra:
        parts.append(os.path.abspath(py_path_extra))
    if parts:
        env["PYTHONPATH"] = os.pathsep.join(parts + ([pp] if pp else []))
    if sandbox:
        sb = os.path.abspath(sandbox)
        os.makedirs(os.path.join(sb, "tmp", "Temp"), exist_ok=True)
        env["LOCALAPPDATA"] = os.path.join(sb, "tmp")
        env["TEMP"] = os.path.join(sb, "tmp", "Temp")
        env["TMP"] = os.path.join(sb, "tmp", "Temp")
    return env


def gate_argv(gate, python, host_root, fw_root, argv_override=None):
    if argv_override is not None:                       # 动态自测门禁：跑命中的那个测试文件
        repo, rel = argv_override.split(":", 1)
        root = host_root if repo == "host" else fw_root
        return [python, os.path.join(root, rel)]
    argv = list(gate.argv)
    if argv and argv[0] == "-c":
        code = SMOKE_CODE[argv[1]]
        pkg = os.path.join(fw_root, "games", "orlandia")
        return [python, "-c", code.format(fw=fw_root, pkg=pkg)]
    cwd = gate_cwd(gate, host_root, fw_root)
    return [python, os.path.join(cwd, argv[0])] + argv[1:]


def run_gate(gate, python, host_root, fw_root, db_dir, sandbox, py_path_extra, timeout,
             argv_override=None):
    os.makedirs(db_dir, exist_ok=True)
    cwd = gate_cwd(gate, host_root, fw_root)
    argv = gate_argv(gate, python, host_root, fw_root, argv_override)
    env = build_env(gate, python, host_root, fw_root, db_dir, sandbox, py_path_extra)
    t0 = time.time()
    try:
        pr = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
        out = (pr.stdout or "") + (pr.stderr or "")
        rc, timed_out = pr.returncode, False
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        rc, timed_out = -9, True
    except OSError as e:
        out, rc, timed_out = "无法启动门禁：%s" % e, -1, False
    dt = time.time() - t0
    last = ""
    for ln in reversed([l.strip() for l in out.splitlines() if l.strip()]):
        if re.match(r"^[=\-_~*#\s]+$", ln):
            continue
        last = ln
        break
    return {
        "gid": gate.gid, "title": gate.title, "cmd": " ".join(argv), "cwd": cwd,
        "rc": rc, "ok": rc == 0, "timed_out": timed_out, "seconds": round(dt, 2),
        "last": last, "output": out, "detail": argv_override or "",
    }


def classify_baseline_red(gate, res):
    """已登记基线红：门禁红了，但输出里出现登记过的原文片段 -> 不是本次改动引入的。"""
    br = getattr(gate, "baseline_red", None)
    if not br or res["ok"]:
        return None
    if br.get("pat") and br["pat"] in (res.get("output") or ""):
        return {"pat": br["pat"], "cite": br.get("cite", ""), "all": bool(br.get("all"))}
    return None


# --------------------------------------------------------------------------------------
# 5. 打印
# --------------------------------------------------------------------------------------

def _h(title):
    print("")
    print("=" * 78)
    print(title)
    print("=" * 78)


def print_plan_header(host_root, fw_root, fw_src, python, changed, mode, notes):
    _h("GATEFAST 门禁快速档  ·  gate_fast.py")
    print("宿主插件仓 host      : %s" % host_root)
    print("引擎仓     framework : %s   (来源: %s)" % (fw_root, fw_src))
    print("解释器     python    : %s" % python)
    print("模式       mode      : %s" % mode)
    print("")
    if changed:
        print("本次改动 %d 个文件：" % len(changed))
        for repo, rel in changed:
            print("   %s:%s" % (repo, rel))
    else:
        print("本次改动 0 个文件（--changed 为空）")
    for n in notes:
        print("   [note] %s" % n)


def print_two_sections(ran, skipped, behavior_ran, total_seconds):
    """作业书 §1(3) 要求的两段：✅ 已跑 / ⏭️ 已跳过。"""
    print("")
    print("-" * 78)
    print("✅ 已跑：%d 道，合计 %.1fs" % (len(ran), total_seconds))
    if ran:
        for r in ran:
            flag = "✅" if r["ok"] else ("⏱️" if r["timed_out"] else "❌")
            extra = ("  <%s>" % r["detail"]) if r.get("detail") else ""
            base = "  [基线红]" if r.get("baseline_red") else ""
            print("   %s %-18s %7.2fs  rc=%-3s  %s%s%s"
                  % (flag, r["gid"], r["seconds"], r["rc"], r["title"], extra, base))
    else:
        print("   （无）")
    print("")
    print("-" * 78)
    print("⏭️ 已跳过：%d 道（跳过原因 = 覆盖面不含本次改动）→ **批收口请跑 --full**" % len(skipped))
    for s in skipped:
        print("   ⏭️ %-18s [%s] %s" % (s["gid"], s["reason_kind"], s["reason"]))
    print("-" * 78)
    # 醒目提示：只改非行为面时，必须明说「跳过了全部行为门禁」
    skipped_behavior = [s for s in skipped if s["tier"] in ("core", "engine")]
    if not behavior_ran:
        print("")
        print("⚠️  ⚠️  ⚠️  本次改动跳过了全部行为门禁（core/engine 层 %d 道）—— "
              "覆盖面不含任何行为面改动。" % len(skipped_behavior))
        print("⚠️  ⚠️  ⚠️  这批改动**没有**被任何行为门禁验证过；合并/落地前请自行判断，"
              "批收口务必跑 --full。")
    print("")
    print("退出码口径：只有「已跑」的门禁影响退出码；上面每一条「已跳过」都不影响退出码，"
          "但已在清单里逐条列出。")


def print_full_comparison(ran_ids):
    """--full 与「手工那套 7 道」并排对照 + 差异逐条解释。"""
    _h("--full 对照：与手工那套（7 道）并排")
    print("手工那套（今晚 p4pf 每壳跑的那 7 道）证据：%s" % MANUAL_CANON_EVIDENCE)
    print("")
    print("  #   手工那套        --full 清单                                 关系")
    maxlen = max(len(g.gid) for g in GATES) if GATES else 8
    for i, gid in enumerate(MANUAL_CANON, 1):
        mark = "✅ 同一条" if gid in ran_ids else "❗ 本次未跑"
        print("  %-3d %-15s %-*s %s" % (i, gid, maxlen + 2, gid, mark))
    print("")
    extras = [g for g in GATES if g.gid not in MANUAL_CANON]
    print("  --full 多出 %d 道（逐条解释为什么多跑）：" % len(extras))
    for g in extras:
        print("   ➕ %-18s %s" % (g.gid, FULL_EXTRA_REASONS.get(g.gid, g.why or "（未登记理由）")))
    print("")
    print("  等价性口径：手工那套 ⊂ --full（上面每一道都在 --full 的清单里）；--full 的**多出部分**")
    print("  全部是「定向补强 + 文档层 + 两条全量 + cheap 冒烟」，逐条理由见上表。若只要手工那套，")
    print("  用：--gates %s" % ",".join(MANUAL_CANON))


def print_map_markdown():
    print("| # | 门禁 id | 覆盖路径 glob | 实测耗时 (s) | tier | 参选 --changed | 说明 |")
    print("|---|---|---|---|---|---|---|")
    for i, g in enumerate(GATES, 1):
        covs = "<br>".join("`%s`" % c for c in g.covers)
        print("| %d | `%s` | %s | %.2f | %s | %s | %s |" % (
            i, g.gid, covs, g.cost, g.tier, "是" if g.selectable else "**否（只 --full）**",
            g.title.replace("|", "/")))


# --------------------------------------------------------------------------------------
# 6. main
# --------------------------------------------------------------------------------------

def select_gates(changed, only_ids=None):
    """返回 (selected, skipped)。skipped 每项带 reason_kind / reason。"""
    selected, skipped = [], []
    for g in GATES:
        if only_ids is not None:
            if g.gid in only_ids:
                selected.append((g, ["--gates 指定"], ["--gates"]))
            else:
                skipped.append({"gid": g.gid, "tier": g.tier, "reason_kind": "未选中",
                                "reason": "--gates 未指定该门禁"})
            continue
        hits, globs = covers_hit(g, changed)
        if not g.selectable:
            skipped.append({
                "gid": g.gid, "tier": g.tier, "reason_kind": "全量门禁",
                "reason": "按设计只在 --full 跑（covers=%s，覆盖全部路径，进 --changed 会让每轮都变全量）"
                          % ",".join(g.covers)})
            continue
        if hits:
            selected.append((g, hits, globs))
        else:
            skipped.append({
                "gid": g.gid, "tier": g.tier, "reason_kind": "覆盖面不含本次改动",
                "reason": "covers=%s —— 本次改动 0 命中" % ",".join(g.covers)})
    return selected, skipped


def cmd_self_check(args, host_root, fw_root):
    covered, annotated, blind, counts = self_check(host_root, fw_root)
    _h("--self-check：映射表盲区校验")
    print("扫描「可被改动的路径」：host %d 条 · fw %d 条（已排除 .git/__pycache__/*.db/*.log 等，见脚本常量）"
          % (counts.get("host", 0), counts.get("fw", 0)))
    print("")
    print("门禁覆盖     ：%d 条路径" % len(covered))
    print("显式无覆盖标注：%d 条路径（NO_GATE，逐条带理由）" % len(annotated))
    print("盲区（未覆盖且未标注）：%d 条" % len(blind))
    print("")
    if blind:
        print("❌ 盲区清单（必须补映射，或在 NO_GATE 里显式标注理由）：")
        for b in blind:
            print("   ❌ %s" % b)
    else:
        print("✅ 无盲区：每条可改动路径要么被门禁覆盖，要么在 NO_GATE 里有显式理由。")
    print("")
    print("── 显式标注「此路径无门禁覆盖」的清单（%d 组 glob）──" % len(NO_GATE))
    for pat, why in NO_GATE:
        n = sum(1 for p, _ in annotated if path_matches(pat, *p.split(":", 1)))
        print("   · %-40s 命中 %4d 条  <= %s" % (pat, n, why))
    if args.verbose:
        print("")
        print("── 覆盖明细（%d 条）──" % len(covered))
        for p, gates in covered:
            print("   %-60s <- %s" % (p, ",".join(gates)))
    if blind:
        return 3
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        add_help=True,
        description="门禁快速档：按改动面只跑相关门禁（全量留到 --full）")
    ap.add_argument("--changed", nargs="*", default=None,
                    help="改动文件；`auto` = git status + 与 --baseline 比")
    ap.add_argument("--full", action="store_true", help="跑全量（手工那套 7 道 + 定向补强 + 两条全量）")
    ap.add_argument("--self-check", action="store_true", help="校验映射表没有「无门禁覆盖」的盲区")
    ap.add_argument("--gates", default=None, help="只跑指定门禁（逗号分隔）")
    ap.add_argument("--plan", action="store_true", help="只算选中集合、不执行")
    ap.add_argument("--dry-run", action="store_true", help="同 --plan")
    ap.add_argument("--list", action="store_true", help="打印映射表全文")
    ap.add_argument("--emit-map", action="store_true", help="以 markdown 打印映射表")
    ap.add_argument("--json", default=None, help="另存机器可读结果")
    ap.add_argument("--host", default=None, help="宿主插件仓根（默认脚本上级目录）")
    ap.add_argument("--framework", default=None, help="$GWEN_FRAMEWORK_DIR 覆盖")
    ap.add_argument("--python", default=None, help="跑门禁的解释器")
    ap.add_argument("--baseline", default=None, help="--changed auto 时的 git 基线（rev）")
    ap.add_argument("--db-dir", default=None, help="门禁私有库目录（默认 <temp>/gate_fast_db）")
    ap.add_argument("--sandbox", default=None,
                    help="沙箱适配目录：注入 <DIR>/_env 到 PYTHONPATH 并重定向 TEMP/TMP/LOCALAPPDATA")
    ap.add_argument("--py-path", default=None, help="额外追加到子进程 PYTHONPATH")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="单条门禁超时秒")
    ap.add_argument("--allow-baseline-red", action="store_true",
                    help="退出码按「新增红」口径计（已登记基线红不阻塞）；默认**关**，即任一红都非零退出")
    ap.add_argument("--verbose", action="store_true", help="打印覆盖明细/门禁输出尾")
    args = ap.parse_args(argv)

    if args.list:
        for g in GATES:
            print("%-18s %-8s %-6s cost=%-7.2f %s" % (g.gid, g.repo, g.tier, g.cost, g.title))
            print("   covers: %s" % ", ".join(g.covers))
            print("   why   : %s" % g.why)
        return 0
    if args.emit_map:
        print_map_markdown()
        return 0

    host_root, fw_root, fw_src = resolve_roots(args)
    python = resolve_python(args.python)
    db_dir = args.db_dir or os.path.join(os.path.abspath(args.sandbox or os.getcwd()), "gate_fast_db")

    if args.self_check:
        return cmd_self_check(args, host_root, fw_root)

    only_ids = None
    if args.gates:
        only_ids = [s.strip() for s in args.gates.split(",") if s.strip()]
        unknown = [g for g in only_ids if g not in GATES_BY_ID]
        if unknown:
            print("❌ --gates 里有未知门禁：%s（可用 --list 看清单）" % ",".join(unknown))
            return 2

    changed, notes = [], []
    if args.changed is not None:
        if len(args.changed) == 1 and args.changed[0] == "auto":
            baseline = args.baseline or os.environ.get("GATEFAST_BASELINE")
            changed, notes = detect_changed(host_root, fw_root, baseline)
            mode = "changed=auto（git status%s）" % (" + diff vs %s" % baseline if baseline else "")
        else:
            changed, notes = normalize_changed(args.changed, host_root, fw_root)
            mode = "changed=显式 %d 个路径" % len(args.changed)
    elif args.full or only_ids is not None:
        mode = "full" if args.full else "--gates"
    else:
        print("❌ 必须给 --changed <paths> / --changed auto / --full / --self-check 之一")
        return 2

    print_plan_header(host_root, fw_root, fw_src, python, changed, mode, notes)

    skipped = []
    if args.full or only_ids is not None:
        selected = [(g, ["--full" if args.full else "--gates"], ["--full" if args.full else "--gates"])
                    for g in GATES if (only_ids is None or g.gid in only_ids)]
    else:
        selected, skipped = select_gates(changed, only_ids)

    plan = []
    for g, hits, globs in selected:
        if g.dyn_changed:
            # 只认真正形如 `<repo>:<rel>` 的命中项；--full/--gates 模式没有改动面 -> 用代表文件跑一次
            use = [h for h in hits if ":" in h] or ["%s:%s" % (g.repo, g.measure_file)]
            for h in use:
                plan.append((g, [h], globs, h))
        else:
            plan.append((g, hits, globs, None))

    _h("选中集合（%d 道）" % len(plan))
    for g, hits, globs, ov in plan:
        print("   · %-18s [%s] 命中 %d：%s" % (g.gid, g.tier, len(hits),
                                              ",".join(hits) if hits else "(--full)"))
    if not plan:
        print("   （空）")

    def dump_json(ran_items):
        if not args.json:
            return
        with io.open(args.json, "w", encoding="utf-8") as fh:
            json.dump({
                "host_root": host_root, "framework_root": fw_root, "framework_source": fw_src,
                "python": python, "mode": mode, "plan_only": bool(args.plan or args.dry_run),
                "changed": ["%s:%s" % (r, p) for r, p in changed],
                "ran": ran_items, "skipped": skipped,
                "manual_canon": MANUAL_CANON, "manual_canon_evidence": MANUAL_CANON_EVIDENCE,
                "gates": [{"gid": g.gid, "covers": g.covers, "cost": g.cost, "tier": g.tier,
                           "selectable": g.selectable, "title": g.title} for g in GATES],
            }, fh, ensure_ascii=False, indent=2)
        print("   机器可读结果已写：%s" % args.json)

    if args.plan or args.dry_run:
        ran_stub = [{"gid": g.gid, "title": g.title, "seconds": 0.0, "rc": "-", "ok": True,
                     "tier": g.tier, "hits": hits, "covers_hit": globs, "plan_only": True,
                     "detail": ov or ""}
                    for g, hits, globs, ov in plan]
        behavior = [g for g, _, _, _ in plan if g.tier in ("core", "engine")]
        print_two_sections(ran_stub, skipped, behavior, 0.0)
        if args.full:
            print_full_comparison([g.gid for g, _, _, _ in plan])
        print("")
        print("[--plan] 未执行任何门禁。")
        dump_json(ran_stub)
        return 0

    results, baseline_reds = [], []
    for g, hits, globs, ov in plan:
        print("")
        print(">>> 跑 %s%s：%s" % (g.gid, (" [%s]" % ov) if ov else "", g.title))
        r = run_gate(g, python, host_root, fw_root, db_dir,
                     args.sandbox, args.py_path, args.timeout, argv_override=ov)
        r["tier"] = g.tier
        r["hits"] = hits
        br = classify_baseline_red(g, r)
        r["baseline_red"] = br
        if br:
            baseline_reds.append((g, r, br))
        results.append(r)
        flag = "✅" if r["ok"] else ("⏱️" if r["timed_out"] else "❌")
        tag = "  [已登记基线红，非本次引入]" if br else ""
        print("    %s rc=%s  用时 %.2fs%s" % (flag, r["rc"], r["seconds"], tag))
        if br:
            print("       依据：%s" % br["cite"])
        if r["last"]:
            print("    末行：%s" % r["last"])
        if not r["ok"] or args.verbose:
            tail = [l for l in r["output"].strip().splitlines() if l.strip()][-25:]
            print("    ── 输出尾 ──")
            for ln in tail:
                print("      " + ln)

    total = sum(r["seconds"] for r in results)
    behavior_ran = [r for r in results if r["tier"] in ("core", "engine")]
    print_two_sections(results, skipped, behavior_ran, total)
    if args.full:
        print_full_comparison([r["gid"] for r in results])

    red = [r for r in results if not r["ok"]]
    new_red = [r for r in red if not r.get("baseline_red")]
    if baseline_reds:
        print("")
        print("ℹ️ 已登记基线红 %d 道（非本次改动引入，逐条带出处）：" % len(baseline_reds))
        for g, r, br in baseline_reds:
            print("   · %-14s %s" % (g.gid, br["cite"]))
    if red:
        print("")
        print("❌ 已跑的门禁里有 %d 道红（其中 %d 道是已登记基线红、%d 道是**新增红**）：%s"
              % (len(red), len(red) - len(new_red), len(new_red),
                 ", ".join(r["gid"] for r in new_red) if new_red else "（新增红 = 空）"))
        if args.allow_baseline_red:
            print("    --allow-baseline-red：退出码按「新增红」口径计（=%s）" % (1 if new_red else 0))
    else:
        print("")
        print("✅ 已跑的门禁全绿（跳过的 %d 道不影响退出码，但请在批收口跑 --full）" % len(skipped))

    dump_json(results)
    if red:
        return 1 if (new_red or not args.allow_baseline_red) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
