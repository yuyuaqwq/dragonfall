# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年AstrBot 插件主入口 —— 薄装配层（重构后）

命令处理器已按领域拆至 game/commands/（Mixin 模式）：
  PlayerCmds / WorldCmds / CombatCmds / EconomyCmds / SocialCmds / MiscCmds
本文件只保留：插件生命周期 + 后台任务 + Mixin 装配。

★ R3（2026-09-15）：AstrBot 指令注册**改为宿主驱动**
----------------------------------------------------
指令注册不再依赖 `game/commands/**` 的 `@declared` 装饰器（那份是待删树），
而由宿主 `host/registration.py` 从**包内声明表**（引擎 `Package.command_declarations()`）
逐条注册（`register_commands()`，在 `AstrMain.__init__` 装配）。见 out/W-R3.md：
删掉 `game/commands/**` 后 import 仍通过、但注册 194 → 0 的静默哑掉态由本批关闭。

`Main`（Mixin 汇编）与 `_fix_handler_module_paths()` 是**过渡态遗留**：测试侧
`tests/conftest.py` 仍取 `main.Main`（P5D 正在改口到 `tests/_engine_harness.py`），
删壳（P5C）后本文件这两处一并消失。`_LEGACY_SHELLS=False` 时（删壳预演/终态）
本文件照样能 import、能注册、能跑命令。
"""
import glob
import threading
import logging

from astrbot.api import star  # 仅 AstrMain 壳需要（生产命中真实 astrbot；测试命中 tests/shim_astrbot）

from .game import db

#: 过渡态遗留壳是否在位（删壳预演 / P5C 终态 = False）。**只在删壳预演时才会 False**。
try:
    from .game.commands import (
        PlayerCmds, WorldCmds, CombatCmds, EconomyCmds, SocialCmds, MiscCmds,
        InstanceCmds, GmCmds, ExplorationCmds,  # v115 探索进度指令
        JobGuideCmds,  # v130.2g 『职业』速查指令
        CollectionCmds,  # v140 波2 『收藏册』指令
        WeeklyCmds, TowerCmds,  # v169.2 周常悬赏『周常』/修炼爬塔『爬塔』
        EventMenuCmds,  # v140 波3.7 『今日事件/事件』指令
    )
    _LEGACY_SHELLS = True
except ImportError:                                            # 删壳预演 / 终态
    _LEGACY_SHELLS = False


def _fix_handler_module_paths():
    """修复 Mixin 重构后 handler 模块路径问题（必须保留的 hack，勿删）。

    AstrBot 通过 handler.handler_module_path 在 star_map 中精确查找插件实例
    （star_manager: star_map[path]=metadata，path=插件主模块；分发时
    star_map.get(handler.handler_module_path) 精确匹配），而 Mixin 拆分后
    handler 注册为 game.commands.* 子模块路径（注册时取 handler.__module__），
    与 Main 类所在的 main 模块不匹配，导致全部指令 handler 被过滤、
    消息全部落入 LLM 回复。

    官方机制仅有 LLM tools 的子模块重映射（star_manager 加载插件时对
    llm_tools 执行 ft.handler_module_path = metadata.module_path），对指令
    handler 无子模块→主模块映射，故本 hack 无法移除；若未来 AstrBot
    改为前缀匹配/官方支持子模块映射，可删除本函数（届时下方
    matched==0 告警会提示）。

    这里在插件加载完成后，把本插件所有 handler 的模块路径统一改写到
    main 模块（__name__），保证 star_map 能正确关联到 Main 实例。
    失败绝不静默：输出 ERROR 日志（后果=全部指令落入 LLM），并附带
    注册表同步校验（P3）差集日志。
    """
    _LOGGER = logging.getLogger(__name__)
    if not _LEGACY_SHELLS:
        # 删壳预演 / 终态：旧壳树已不在 —— 注册由 host/registration.py 驱动，
        # 注册出来的 handler 的 __module__ 本来就是本模块（无需改写）。
        _LOGGER.info(
            "过渡态遗留壳不在位（删壳预演/终态）：跳过旧路径 handler 路径改写；"
            "AstrBot 指令注册由 host/registration.py 驱动。")
        return
    try:
        from astrbot.core.star.star_handler import star_handlers_registry

        pkg = __name__.rsplit(".", 1)[0]  # data.plugins.dragonfall
        matched = 0
        for h in star_handlers_registry._handlers:
            if h.handler_module_path and h.handler_module_path.startswith(pkg + "."):
                h.handler_module_path = __name__
                matched += 1
        if matched == 0:
            # 注册机制若变化导致 0 命中，必须大声告警而非静默失效
            _LOGGER.warning(
                "handler 模块路径改写命中 0 个 handler：Mixin 子模块 handler 将无法"
                "关联 Main 实例，指令会全部落入 LLM 回复。请检查 AstrBot 版本兼容性；"
                "若官方已支持子模块映射，可删除本 hack。"
            )
        else:
            _LOGGER.info("已改写 %d 个 handler 模块路径 -> %s", matched, __name__)

        # ---- P3 注册表同步校验：已注册公开 handler 名 vs _registry 静态表键 ----
        from .game.commands._registry import COMMAND_REGEX

        # 私有 handler（_ 前缀，如 _maint_gate）按 base.py v96 设计不进静态表，
        # 两侧统一排除，只校验公开指令名
        table_keys = {k for k in COMMAND_REGEX if not k.startswith("_")}
        registered = {
            h.handler_name
            for h in star_handlers_registry._handlers
            if h.handler_module_path == __name__ and not h.handler_name.startswith("_")
        }
        missing = sorted(table_keys - registered)  # 表有、实际未注册
        extra = sorted(registered - table_keys)    # 实际注册、表里没有
        if not missing and not extra:
            _LOGGER.info(
                "注册表同步校验通过：%d 静态键 ↔ %d 已注册公开 handler",
                len(table_keys), len(registered),
            )
        else:
            _LOGGER.warning(
                "注册表同步校验发现漂移：表缺 %d 键 %s；表多 %d 键 %s。"
                "请同步 game/commands/_registry.py（半自动维护，见该文件头注释）。",
                len(missing), missing, len(extra), extra,
            )
    except Exception:
        _LOGGER.error(
            "handler 模块路径改写/注册表校验失败——指令将全部落入 LLM 回复，"
            "请立即检查 AstrBot 版本兼容性", exc_info=True
        )

_fix_handler_module_paths()


def _weekly_reward_selfcheck():
    """★ 启动自检（fail-closed）：周常达标发奖的宿主注入面必须在位。

    背景（RPT 实测的静默失效）：`game/services/weekly_progress.py` 这个注入点消失后，
    包内 `content/flow/weekly_progress.py::_grant_rewards` 取不到宿主 `reward.grant_reward`，
    而 `weekly_bump_kill` 的旧宽容兜底会把它吞掉 ⇒ **玩家达标不发奖、进度不落库、零日志**。
    按「fail-closed 优先」口径：启动时就大声报错，绝不静默。

    * 通过 → INFO 一行留痕（可见地证明链路在位）；
    * 失败 → ERROR + **抛**（拒绝带着静默坏掉的发奖链路启动）。

    幂等（模块 import 期调一次；`Main.__init__` 再调一次，热重载/多次实例化都安全）。
    """
    _LOGGER = logging.getLogger(__name__)
    try:
        from content.flow import weekly_progress as _WP
    except Exception:
        _LOGGER.error("周常发奖启动自检失败：包内 content.flow.weekly_progress 不可导入", exc_info=True)
        raise
    try:
        _LOGGER.info(_WP.selfcheck())
    except Exception as exc:
        _LOGGER.error(
            "周常发奖启动自检失败：%s —— 缺注入时玩家达标会静默不发奖，故拒绝启动（fail-closed）。"
            "请在宿主装配处调 content.flow.weekly_progress.bind_host(db, grant_reward)。", exc)
        raise


if _LEGACY_SHELLS:
    # 过渡态：旧壳 import 期已经跑过包 bootstrap（宿主注入面 bind_host 已扇出），
    # 与 P5′ 1.0b 的口径一致；终态（旧壳不在位）由 register_commands() 在装配期调同一次自检。
    _weekly_reward_selfcheck()


# ---- v92 文件转发体验通道 ----
# 后台线程监控 scripts/playthrough_cmd.txt：读到命令 → 进程内构造 fake 事件
# → _run_shortcut 转发给真实 handler → 结果追加写 scripts/playthrough_out.txt。
# 身份固定 gm_playtest（私聊），GM 指令自然放行；完全在 AstrBot 进程内，无跨进程锁。
import asyncio
import os
import threading
import time as _time

_PLAYTEST_QQ = "gm_playtest"  # 体验专用身份（QQ 不存在的测试号）
_PLAY_CMD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "playthrough_cmd.txt")
_PLAY_OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "playthrough_out.txt")
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__)) + os.sep + "scripts"


def _loopback_files():
    """所有待处理命令文件（含多身份 playthrough_cmd_<ident>.txt），按名排序保证主通道优先。"""
    return sorted(glob.glob(os.path.join(_SCRIPTS_DIR, "playthrough_cmd*.txt")))


def _out_file_for(cmd_path: str) -> str:
    """命令文件对应的输出文件：playthrough_cmd.txt → playthrough_out.txt；带身份 → playthrough_out_<ident>.txt。"""
    name = os.path.basename(cmd_path)
    if name == "playthrough_cmd.txt":
        return _PLAY_OUT_FILE
    ident = name[len("playthrough_cmd_"):-len(".txt")]
    return os.path.join(_SCRIPTS_DIR, f"playthrough_out_{ident}.txt")


class _LoopbackEvent:
    """模拟 AstrBot 消息事件（私聊，测试身份）。"""

    def __init__(self, msg: str, sender_id: str = None, group_id: str = None):
        self.message_str = msg
        self._sender = sender_id or _PLAYTEST_QQ
        # v95.1：多号联测支持——带身份通道进统一测试群，可组队/开副本；主通道保持 private（GM 权限）
        self._group_id = group_id or "private"
        self._stopped = False            # P5A：平台 gate（`_maint_gate`）的 stop_event 语义

    def get_group_id(self):
        return self._group_id

    def get_sender_id(self):
        return self._sender

    def get_self_id(self):
        # v101.28s：合并转发节点 uin 用（bot 自身 QQ = NapCat 3473145972，
        # 前端显示为"格温"发送的聊天记录）
        return "3473145972"

    def get_message_str(self):
        return self.message_str

    def plain_result(self, text):
        return text

    def stop_event(self):
        """v96 停服 gate / 翻页快捷键用：标记「本事件不再向下传播」。"""
        self._stopped = True

    async def send(self, message):
        return message


def _file_loopback_start():
    """启动文件转发监控线程（幂等，AstrBot 与测试脚本共用同一 Main 时只起一次）。"""
    if getattr(_file_loopback_start, "_started", False):
        return
    _file_loopback_start._started = True

    def worker():
        # v94.1 修复：AstrBot 热重载（watchfiles）会重新执行本模块 → 防多 worker 竞态。
        # 锁文件记录 PID；已有存活 worker 则本线程直接退出（旧 worker 处理逻辑相同）。
        lock_path = os.path.join(_SCRIPTS_DIR, ".loopback_worker.lock")
        try:
            if os.path.exists(lock_path):
                with open(lock_path, "r", encoding="utf-8") as f:
                    old_pid = int(f.read().strip() or "0")
                if old_pid > 0:
                    try:
                        os.kill(old_pid, 0)  # 存活检查
                        return  # 已有 worker 在跑，本线程退出
                    except OSError:
                        pass  # 旧进程已死，抢占
            with open(lock_path, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
        except Exception:
            # q11：锁失败不阻塞（极端情况容忍多 worker），留痕便于排查
            logging.getLogger(__name__).warning(
                "loopback worker 锁文件读写失败（容忍多 worker 继续）", exc_info=True
            )
        while True:
            try:
                for cmd_path in _loopback_files():
                    if os.path.exists(cmd_path):
                        with open(cmd_path, "r", encoding="utf-8") as f:
                            cmd = f.read().strip()
                        try:
                            os.remove(cmd_path)
                        except OSError:
                            pass
                        if cmd:
                            _dispatch(cmd, _out_file_for(cmd_path))
            except Exception:
                # q11：单轮轮询失败不中断线程，留痕便于定位
                logging.getLogger(__name__).warning(
                    "loopback worker 单轮轮询失败（已跳过，1s 后重试）", exc_info=True
                )
            _time.sleep(1.0)

    def _dispatch(cmd: str, out_file: str):
        """P5A：本通道 = **引擎 host 通道**（`adapter_qq` 三函数 + inject）。

        v55 轮口径保留：main 通道也进统一测试群 gm_test_group（#47b 需要 2 真人组队打副本，
        main 在 private 群无法与 gm_test_group 的小蓝组队 —— party/副本按 group_id 隔离）；
        GM 权限不受影响（gm_ 前缀身份恒放行）。

        与改造前的差异（**有意**，见 out/W-P5A.md）：
          · 执行面从「宿主注册表 `Main._run_shortcut`」改成「引擎通道 `EngineChannel.collect_event`」
            （包内声明路由 → 守卫 → `Env` → 包内处理器 → 逐段回话）；
          · 于是也不再需要「提交主事件循环」那一步（引擎通道自带 async 桥，见
            `host/adapter_qq.py::run_sync`）；平台发送在引擎通道的 loop 上完成。
        """
        lines = [f"\n{'='*50}\n▶ 『{cmd}』"]
        try:
            channel = engine_channel()
            ev = _LoopbackEvent(cmd, _ident_of(out_file), "gm_test_group")
            lines.extend(str(seg) for seg in channel.collect_event(ev))
        except Exception as e:
            lines.append(f"❌ 异常: {type(e).__name__}: {e}")
            logging.getLogger(__name__).error(
                "引擎 host 通道转发失败（命令=%r）", cmd, exc_info=True)
        _append_out("\n".join(lines), out_file)

    def _ident_of(out_file: str) -> str:
        """输出文件反推身份：主通道 → gm_playtest；带身份 → 文件名中的 ident。"""
        name = os.path.basename(out_file)
        if name == "playthrough_out.txt":
            return _PLAYTEST_QQ
        return name[len("playthrough_out_"):-len(".txt")]

    def _append_out(text: str, out_file: str = None):
        with open(out_file or _PLAY_OUT_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    t = threading.Thread(target=worker, daemon=True, name="file-loopback")
    t.start()


def _event_state_cleanup_once():
    """v104 M24 P2-5：启动时清理流失玩家残留的 event_state 键（>30 天未活跃）。
    幂等（多实例/热重载只跑一次）；仅清五类后缀键，talkflags_ 等持久键不动。"""
    if getattr(_event_state_cleanup_once, "_started", False):
        return
    _event_state_cleanup_once._started = True
    try:
        from .game.store.world import cleanup_stale_event_state
        n = cleanup_stale_event_state()
        if n:
            logging.getLogger(__name__).info("已清理 %d 个流失玩家残留 event_state 键", n)
        # v141 大陆回收（P0-3，2026-08-30 审计）：启动兜底清理超龄大陆实例
        # （内存 dict + DB event_state 孤儿键，24h 默认；幂等）
        try:
            from .game.core.worlds import cleanup_stale_instances
            _nw = cleanup_stale_instances()
            if _nw:
                logging.getLogger(__name__).info("已清理 %d 个超龄大陆实例", _nw)
        except Exception:
            logging.getLogger(__name__).warning(
                "大陆实例清理跳过（异常不影响启动）", exc_info=True
            )
    except Exception:
        logging.getLogger(__name__).warning(
            "event_state 残留键清理跳过（DB 未就绪或异常，不影响启动）", exc_info=True
        )


if _LEGACY_SHELLS:

    class Main(
        PlayerCmds,
        WorldCmds,
        CombatCmds,
        EconomyCmds,
        SocialCmds,
        MiscCmds,
        InstanceCmds,
        GmCmds,
        ExplorationCmds,  # v115 探索进度指令
        JobGuideCmds,  # v130.2g 『职业』速查指令
        CollectionCmds,  # v140 波2 『收藏册』指令
        WeeklyCmds, TowerCmds,  # v169.2 周常悬赏『周常』/修炼爬塔『爬塔』
        EventMenuCmds,  # v140 波3.7 『今日事件/事件』指令
    ):
        """奥兰迪亚·余烬纪年核心游戏类（v117.5 起平台无关，不再继承 astrbot star.Star）。

        astrbot 接入由文件末尾 AstrMain 壳完成（命令装饰器经 game/commands/_platform
        双注册进 astrbot 注册表；本类零 astrbot 依赖）。迁移到其他平台：
        把 game/ 包 + 本类搬走，另写目标平台的薄壳即可。

        ★ R3：本类是**过渡态遗留**（P5C 删除）——生产分发已改由 `host/registration.py`
        驱动的引擎通道承担；测试侧 `tests/conftest.py` 仍取本类（P5D 改口中）。
        """

        def __init__(self, context=None) -> None:
            self.context = context
            # v101.28q：记录主事件循环——loopback worker 线程里的 handler 执行必须提交到主 loop，
            # 否则 await Quart websocket（aiocqhttp bot API）会跨 loop 挂死（gm_窥探 投递卡住的根因）
            try:
                self._main_loop = asyncio.get_event_loop()
            except RuntimeError:
                self._main_loop = None
            # v93 修复：仅真实 AstrBot 实例注册回环通道（测试脚本 Main(None) 会覆盖类变量 → 通道查 test 库）
            if context is not None:
                Main._loopback_instance = self  # v92: 文件转发通道拿当前实例
            db.init_db()
            # ★ P5′ 1.0b：周常发奖注入面启动自检（幂等；缺注入 → 当场报错，绝不静默不发奖）
            _weekly_reward_selfcheck()
            # v104 M24 P2-5：启动时清理流失玩家残留 event_state 键（幂等，见 _event_state_cleanup_once）
            _event_state_cleanup_once()
            # v92: 文件转发体验通道——后台线程监控命令文件，
            # 在 AstrBot 进程内把命令转发给游戏引擎（真实 handler 链路），结果写回文件。
            # 用途：格温（Hermes）写 playthrough_cmd.txt → 进程内执行 → playthrough_out.txt 读结果，
            # 绕开跨进程 sqlite 锁竞争，以玩家身份逐条体验完整流程。
            # v94.1 修复：仅真实 AstrBot 实例启动 worker——测试脚本 Main(None) 若启动 worker，
            # 会抢走回环指令并在测试进程里报"未找到 Main 实例"（与 #40 同类问题）。
            if context is not None:
                _file_loopback_start()
            # v36: 广播任务已停用（意见改为 cron 汇总报告给鱼鱼，不回复玩家）

else:
    #: 删壳预演 / 终态：旧壳树不在位，`main.Main` 不再存在（测试侧已改口 `_engine_harness`）。
    Main = None


# ============================================================================
# 引擎 host 通道（P5A）
# ----------------------------------------------------------------------------
# 契约真源：`framework/docs/engine-wiki/reference/host-api.md`
#   （三函数 / ctx 七字段 / 六钩子 / `Env` 字段表 / 命令通道 / `inject` 一个 dict 两处用）
# 形状真源：`overnight/B19a_HOST_CONTRACT_DESIGN.md` §2.1（宿主终态文件清单）
#
# 本批（P5A）**不动旧路径**：AstrBot 生产分发仍走 `game/commands/**` 的 194 个壳
# （P5C 才删壳 + 把生产分发切到本通道）。本通道供 **loopback 测试通道** 与对拍脚本驱动，
# 用来证明「宿主靠 `host/adapter_qq.py`（三函数）+ `inject` 跑通命令，且与旧路径逐字节相同」。
#
# 宿主面五件（`host/**`）：adapter_qq（三函数 + 钩子）· _platform · _identity ·
# store_factory（库路径 + 连接 + 单进程锁 + 存档半边取用口）· log_setup / tlog_setup。
# ============================================================================

import json as _json  # noqa: E402

from saintess_engine.host import Host as _EngineHostBase  # noqa: E402

from .host import adapter_qq as _adapter_qq  # noqa: E402
from .host import store_factory as _store_factory  # noqa: E402
from .host import _platform  # noqa: E402
from .host import registration as _registration  # noqa: E402
from .host.shell import HostShell as _HostShell  # noqa: E402

#: 包目录配置项（环境变量优先；插件配置文件同名键次之）
_PACKAGE_CFG_ENV = "GWEN_PACKAGE_DIR"
_PACKAGE_CFG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def resolve_package_dir(package_dir: str = None):
    """包目录（`game.json` 所在）—— **只从配置来**；代码里不写死任何包名。

    配置来源（按序）：
      ① 显式入参（测试 / 对拍脚本）；
      ② 环境变量 `GWEN_PACKAGE_DIR`；
      ③ 插件配置 `<插件根>/config.json` 的 `package_dir`（相对路径按插件根解析）。

    都没有 → 记 ERROR 并返回 `None`（引擎通道**不启动**：fail-closed —— 换包 = 换配置 + 重启进程，
    宿主的可替换性要求「包路径」不许在代码里猜）。
    """
    raw = str(package_dir or os.environ.get(_PACKAGE_CFG_ENV) or "").strip()
    if not raw:
        try:
            with open(_PACKAGE_CFG_FILE, encoding="utf-8") as fh:
                raw = str((_json.load(fh) or {}).get("package_dir") or "").strip()
        except OSError:
            raw = ""
        except ValueError:
            logging.getLogger(__name__).error(
                "插件配置不是合法 JSON：%s（包目录取不到 → 引擎通道不启动）", _PACKAGE_CFG_FILE)
            raw = ""
    if not raw:
        logging.getLogger(__name__).error(
            "未配置包目录（环境变量 %s 或 %s 的 package_dir）——引擎 host 通道不启动。"
            "换包 = 换配置 + 重启进程（一个进程一个包）。", _PACKAGE_CFG_ENV, _PACKAGE_CFG_FILE)
        return None
    if not os.path.isabs(raw):
        raw = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), raw))
    return raw


class EngineHost(_EngineHostBase):
    """引擎 host 的宿主子类 —— 只加三处宿主侧必需面（**引擎一行未改**）。

    ① `env.state["shell"]`：包内取宿主面的**唯一过渡能力口**（包内 `content/guards.py` 与
       `cmds_*.py` 都经它取 `_strip_cmd` / `_player` / `_tip` / `_is_gm` / `_broadcast` …）。
       本类只负责把调用方给的宿主壳透传进 `Env.state`（与旧桥 `game/commands/_host_bridge.py`
       的 `state={"shell": host_shell}` 同形同值 ⇒ 包内行为逐字不变）。
    ② async 处理器：包内战斗族处理器是 `async def`（返回 `list[str]`），引擎 `_as_replies`
       不 await ⇒ 会把协程对象当回话投出去。本类在 `_as_replies` 里 await / 收 async 流
       （编辑器试玩通道 `editor/play_worker.py` 已有同款先例）。
    ③ 新玩家**不代造档**：引擎缺省会给一份「最小档」；本包策略是「先注册」（包内没有
       `initial_save`）—— 代造档会让包侧 `player` 守卫失效、还会凭空落一行玩家档。
       故：包**没有**声明 `initial_save` ⇒ 空档（由包内 `player` 守卫按**包内文案**拦截）。
    """

    def __init__(self, *args, shell=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.shell = shell

    # ---- ① 宿主壳能力口 ----
    def build_env(self, key, spec, ctx, player, *, raw=None):
        env = super().build_env(key, spec, ctx, player, raw=raw)
        if self.shell is not None:
            env.state["shell"] = self.shell
        return env

    # ---- ② async 处理器 ----
    @staticmethod
    def _as_replies(out) -> list:
        """处理器返回值 → 文本段（`str` / list / 生成器 / `None` 都收）。

        与引擎原实现的**唯一差异**：**空串段保留**。包内排版空行是 `raw("")`（`content/commands.py`
        `render_panel` → 空串段），旧路径 `_BRIDGE.run` 的 `"\\n".join` 会把它变成空行；引擎原实现
        在 `_as_replies` 里把空串滤掉，等价于**吃掉空行** ⇒ 两条通道的成品文本不再逐字节相同。
        这里只滤 `None`（保真）；空串是否投递由投递侧决定（见 `handle`：收集面保真、平台面不空发）。
        """
        if hasattr(out, "__await__") or hasattr(out, "__anext__"):
            out = _adapter_qq.run_sync(out)
        if out is None:
            return []
        if isinstance(out, str):
            return [out]
        if isinstance(out, (list, tuple, set)):
            return [str(x) for x in out if x is not None]
        if hasattr(out, "__iter__") and not isinstance(out, (dict, bytes)):
            return [str(x) for x in out if x is not None]
        return [str(out)]

    # ---- ③ 新玩家建档策略 + 逐段投递 ----
    def accept(self, ctx: dict, spec=None) -> None:
        """一条消息：读档（含「不代造档」策略）→ 指定声明或引擎路由 → **逐段投递**。

        与引擎原实现的两处差异（理由见本类文档串）：
          · 新玩家不代造档（包没声明 `initial_save` ⇒ 空档，由包侧 `player` 守卫拦截）；
          · 投递走 `adapter.say`（**不经** `Host.say` 的 `if text:` 过滤）：空串段是包内排版空行，
            收集面必须保真（对拍/回放），平台面由适配器 `say` 自己决定不空发。

        `spec` 显式给出时按该声明执行（适配器对**不可见声明**的路由落点，见
        `host/adapter_qq.py::route_plan`）；缺省 = 引擎可见路由。
        """
        ctx = ctx or {}
        uid = str(ctx.get("uid") or "")
        to = {"uid": uid, "group_id": ctx.get("group_id")}
        text = str(ctx.get("text") or "").strip()
        player = self.load_player(uid)
        if player is None:
            if self.pkg is not None and self.pkg.entry_fn("initial_save") is not None:
                player = self.pkg.initial_save(uid, ctx, id_key=self.id_key) or {}
                if not isinstance(player, dict):
                    player = {}
                if player:                       # 建档是引擎级副作用（新档必须落库一次）
                    self.save_player(uid, player)
            else:
                player = {}                      # 包要求先注册 → 空档（`player` 守卫拦截）
        if spec is not None:
            replies = self.invoke(spec, ctx, player)
        else:
            replies = self.route(ctx, player, text)
        for part in replies:
            self.adapter.say(to, part)

    def handle(self, ctx: dict) -> None:
        """引擎契约的 `handle`（= `accept` 的缺省形态：走引擎可见路由）。"""
        self.accept(ctx)


class EngineShell(_HostShell):
    """引擎通道的**宿主壳** —— 终态宿主壳 `host/shell.py::HostShell`（P5C 交付）的宿主子类。

    ★ R3：本类**不再继承** `Main`（`game/commands/**` 的 Mixin 汇编，待删树）——删掉那棵树
    之后 `import main` / 建通道 / 注册 / 跑命令都必须照常。宿主壳的通用那一半（分页 / 剥参 /
    认人 / 读档 / 广播 / 平台 gate / 平台例外 4 条）在 `host/shell.py`，内容那一半转引包内真源。

    `game/commands/**` 里 `shortcut_trigger` / `page_flip` / `gm_play` 的正文会调
    `self._run_shortcut(event, text)` 把消息转给另一条指令执行 —— 本类把这一步接到
    `EngineChannel.collect_event`（`ctx` 由同一平台事件重建，`text` = 重建后的指令文本），
    于是「5 条平台例外」也走在引擎通道上（§11.3 / P5A 作业书 §2③）。
    """

    _engine_channel = None

    def bind_engine_channel(self, channel) -> None:
        self._engine_channel = channel

    async def _run_shortcut(self, event, text: str):
        """转发另一条指令执行 —— **改走引擎通道**（P5A §2③），并保留框架转发的换文语义。

        与 `saintess_engine.command.router.run_shortcut` 同款：转发期间**临时把事件的
        `message_str` 换成重建后的指令文本**，结束后还原（否则包内处理器经 `env.raw`
        取到的还是原消息，参数解析会错 —— 实测：`n3` → 转发『前往 3』时拿到 `n3`）。
        """
        channel = self._engine_channel
        if channel is None:
            raise RuntimeError(
                "引擎通道未装配：EngineShell._run_shortcut 需要 bind_engine_channel() ——拒绝静默走旧路径")
        had = hasattr(event, "message_str")
        orig = getattr(event, "message_str", None)
        try:
            if had:
                event.message_str = text
            for seg in channel.collect_event(event, text=text):
                yield seg
        finally:
            if had:
                event.message_str = orig


class EngineChannel:
    """引擎通道装配 + 驱动口（宿主唯一「跑一条消息」入口）。

        channel = EngineChannel(package_dir)      # package_dir **由配置给**
        channel.boot()                            # 加载包（bind/inject）→ 建表 → 绑存档半边
        channel.collect_event(event)              # 平台事件 → 引擎通道 → 回话段（list[str]）

    `collect_event` / `collect_ctx` 的顺序 = 平台门 → 平台例外命令 → 引擎路由：

        ① 平台 gate（`_maint_gate`）：命停服 → 本次不路由、零回话；
        ② 平台例外（`gm_play` / `gm_spy` / `shortcut_trigger` / `page_flip`）：交给适配器派发
           （包内没有也不应有处理器；转发经 `EngineShell._run_shortcut` 回到本通道）；
        ③ 其余：`Host.handle(ctx)`（引擎按**包内声明**路由 → 守卫 → `Env` → 包内处理器）。
    """

    def __init__(self, package_dir: str, *, context=None, shell=None, sink=None, seed=None,
                 inject=None):
        self.package_dir = package_dir
        self.store = _store_factory.store()
        self.shell = shell if shell is not None else EngineShell()
        self.shell.bind_engine_channel(self)
        self.adapter = _adapter_qq.QQAdapter(
            store=self.store, shell=self.shell, context=context, sink=sink, seed=seed)
        self.host = EngineHost(self.adapter, package_dir, shell=self.shell,
                               inject=inject if inject is not None else _store_factory.inject_handles(),
                               id_key="uid")
        self.pkg = None

    def boot(self):
        """加载包（→ 包侧 `bind_host(**inject)`，import 命令模块**之前**）+ 建表 + 绑存档口。

        ★ R3：另加两处**声明驱动**接线（都是宿主件、零包知识，值全部来自包内声明表）：
          · `_GameCmdFilter` 的「游戏指令正则」供体（停服 gate 的命中判定）；
          · `HostShell._static_source`（命令转发的静态兜底表）。
        """
        self.pkg = self.host.boot()
        _store_factory.bind_store(self.pkg)          # 存档半边（`content/persistence`）
        self.store.init()                            # 建表 / 迁移（幂等）
        self.adapter.attach(pkg=self.pkg, host=self.host)
        self.shell.bind_package(self.pkg)            # 宿主壳取包内半边的落点
        _platform._GameCmdFilter.set_pattern_source(
            lambda: _registration.declaration_patterns(self.pkg))
        _HostShell._static_source = lambda: _registration.static_handlers(self.pkg)
        _HostShell._STATIC_HANDLERS = None           # 换包 / 重载 → 旧缓存作废
        return self.pkg

    def dispatch_declaration(self, key: str, event, text: str = None) -> list:
        """**按声明 key** 跑一条指令 → 回话段（`list[str]`）—— 注册驱动 handler 的执行体。

        与 `collect_ctx` 的区别：**不重新路由**，直接执行这条声明（旧壳 `_BRIDGE.run(self, key, …)`
        同义）。AstrBot 已按正则把消息分发到本 key 的 handler，重路由会引入第二套命中口径。
        三段：① 平台 gate（`_maint_gate`）→ 零回话；② 平台例外四条 → 宿主壳实现；
        ③ 其余 → `Host.accept(ctx, spec)`（守卫 → `Env` → 包内处理器）。
        """
        ctx = self.adapter.to_ctx(event, text=text)
        self.adapter.begin(ctx)
        if key == _adapter_qq.GATE_KEY:
            self.adapter.gate(ctx)
            return []
        out: list = []
        with self.adapter.collecting(out):
            if key in _adapter_qq.PLATFORM_ROUTES:
                out.extend(self.adapter.platform_replies(key, ctx))
            else:
                spec = self.host.commands.get(key)
                if spec is None:
                    raise KeyError(
                        "包内声明表没有 key=%r ——注册驱动的 pattern 与声明表不同源？" % (key,))
                self.host.accept(ctx, spec)
        return out

    def collect_ctx(self, ctx: dict) -> list:
        """一条消息 → 回话段（`list[str]`，元素顺序 = 投递顺序）。

        三段式（§11.3）：① 平台 gate（`_maint_gate`，停服拦截时零回话）→
        ② 适配器那半路由（平台例外四条 / 不可见声明）→ ③ 引擎可见路由。
        """
        self.adapter.begin(ctx)
        out: list = []
        with self.adapter.collecting(out):
            if self.adapter.gate(ctx):
                return []                            # 停服拦截：不路由、零回话
            plan = self.adapter.route_plan(ctx.get("text") or "")
            if plan is not None and plan[0] == "platform":
                out.extend(self.adapter.platform_replies(plan[1].key, ctx))
            elif plan is not None and plan[0] == "invoke":
                self.host.accept(ctx, plan[1])       # 不可见声明 → 包内处理器
            else:
                self.host.accept(ctx)                # 引擎可见路由
        return out

    def collect_event(self, event, text: str = None) -> list:
        """平台事件 → 回话段（`text` 显式给出 = 快捷/翻页重建的指令文本）。"""
        return self.collect_ctx(self.adapter.to_ctx(event, text=text))


#: 进程唯一引擎通道（loopback 测试通道用；对拍脚本可自行 `EngineChannel(...)` 另建）
_ENGINE_CHANNEL = {"channel": None}


def engine_channel(package_dir: str = None, **kwargs) -> EngineChannel:
    """取（或建）进程唯一引擎通道。配置缺包目录 → **抛**（调用方决定怎么报，绝不静默）。"""
    channel = _ENGINE_CHANNEL["channel"]
    if channel is None:
        resolved = resolve_package_dir(package_dir)
        if not resolved:
            raise RuntimeError(
                "引擎 host 通道未配置包目录（%s / %s.package_dir）——拒绝猜包名"
                % (_PACKAGE_CFG_ENV, _PACKAGE_CFG_FILE))
        channel = EngineChannel(resolved, **kwargs)
        channel.boot()
        _ENGINE_CHANNEL["channel"] = channel
    return channel


def register_commands(package_dir: str = None, *, module_path: str = None) -> int:
    """★ R3：**AstrBot 指令注册**入口（声明驱动）——返回注册条数。

    流程（fail-closed，任一步失败都抛，绝不静默留一个「注册 0 条」的哑机器人）：

        ① 起（或取）引擎通道（包目录**由配置给**）→ 加载包 → 声明表就位；
        ② `reset_plugin_handlers`：接管本插件名下旧 handler（过渡态 `game/commands/**`
           的 `@declared` 装饰器仍在 import 期注册 —— 不清掉就会两套并存、每条消息跑两遍）；
        ③ `register_from_declarations`：包内声明 × 1 → AstrBot 正则 handler × 1；
        ④ 自检：注册条数 == 包内声明条数（不等 → 抛）。

    `module_path` 缺省 = 本模块（AstrBot `star_map` 按它精确关联插件实例）。
    """
    channel = engine_channel(package_dir)
    _weekly_reward_selfcheck()      # 终态：注入面自检挪到装配期（同一 fail-closed 语义）
    target = str(module_path or __name__)
    _registration.bind_dispatcher(channel.dispatch_declaration)
    cleared = _registration.reset_plugin_handlers(target)
    count = _registration.register_from_declarations(channel.pkg, module_path=target)
    expected = _registration.declaration_count(channel.pkg)
    logging.getLogger(__name__).info(
        "AstrBot 指令注册（声明驱动）：清旧 %d 条 → 注册 %d 条 / 声明 %d 条（module_path=%s）",
        cleared, count, expected, target)
    if count != expected:
        raise RuntimeError(
            "注册条数 %d != 包内声明条数 %d ——注册驱动有漏（拒绝带着哑掉的指令表启动）"
            % (count, expected))
    return count


def registration_teeth_probe(module_path: str = None) -> tuple:
    """**门禁牙齿**用探针：清掉本插件 handler → 旁路注册驱动 → 数一遍。

    返回 `(cleared, registered, remaining)`：`registered` == 0 而 `remaining` == 0
    ⇒ 「旁路驱动必须报红」成立（`tests/test_command_registration.py` 用它做有牙实测）。
    """
    target = str(module_path or __name__)
    cleared = _registration.reset_plugin_handlers(target)
    return cleared, 0, count_plugin_handlers(target)


def count_plugin_handlers(module_path: str = None) -> int:
    """本插件在 AstrBot 注册表里的指令 handler 条数（门禁量尺）。"""
    target = str(module_path or __name__)
    try:
        from astrbot.core.star.star_handler import star_handlers_registry as _reg
    except Exception:                                            # noqa: BLE001
        return -1
    return sum(1 for md in getattr(_reg, "_handlers", ())
               if str(getattr(md, "handler_module_path", "") or "") == target)


# ================= astrbot 插件壳（v117.5 解耦后薄层） =================
# ★ R3 起：指令注册由宿主 `host/registration.py` 驱动（`AstrMain.__init__` → `register_commands()`），
# 不再依赖 `game/commands/_platform` 的装饰器双注册。
# 本壳仍做两件事：① 提供 class X(star.Star) 让 astrbot 发现插件（main.py 是固定入口）；
# ② context 翻译——核心回复数据类（MessageChain/Plain/Node/Nodes）→ astrbot 类型。
# 平台类型真源 = 宿主 `host/_platform.py`（P5C 交付），**不再 import 待删树**。
from .host import _platform as _pf  # noqa: E402


def _to_astrbot_node(node):
    """核心 Node → astrbot Node（OneBot 合并转发节点）。"""
    from astrbot.core.message.components import Node as ANode
    from astrbot.core.message.components import Nodes as ANodes
    from astrbot.core.message.components import Plain as APlain

    content = []
    for comp in node.content:
        if isinstance(comp, _pf.Plain):
            content.append(APlain(comp.text))
        elif isinstance(comp, _pf.Node):
            content.append(_to_astrbot_node(comp))
        elif isinstance(comp, _pf.Nodes):
            content.append(ANodes([_to_astrbot_node(n) for n in comp.nodes]))
        else:
            content.append(comp)
    return ANode(uin=node.uin, name=node.name, content=content)


def _to_astrbot_chain(chain):
    """核心 MessageChain → astrbot MessageChain。"""
    from astrbot.core.message.components import Nodes as ANodes
    from astrbot.core.message.components import Plain as APlain
    from astrbot.core.message.message_event_result import MessageChain as AChain

    out = []
    for comp in chain.chain:
        if isinstance(comp, _pf.Plain):
            out.append(APlain(comp.text))
        elif isinstance(comp, _pf.Node):
            out.append(_to_astrbot_node(comp))
        elif isinstance(comp, _pf.Nodes):
            out.append(ANodes([_to_astrbot_node(n) for n in comp.nodes]))
        else:
            out.append(comp)
    return AChain(out)


class _ContextProxy:
    """把核心 MessageChain 翻译成 astrbot MessageChain 后转发（其余属性透传）。"""

    def __init__(self, real):
        self._real = real

    def send_message(self, target, chain):
        return self._real.send_message(target, _to_astrbot_chain(chain))

    def __getattr__(self, name):
        return getattr(self._real, name)


class AstrMain(star.Star, EngineShell):
    """astrbot 插件壳：继承**终态宿主壳** `EngineShell`（`host/shell.py::HostShell` 子类）。

    ★ R3：本类**不再继承** `Main`（待删的 Mixin 汇编）——AstrBot 装载插件时实例化本类，
    实例化期间调 `register_commands()` 完成「包内声明 → AstrBot handler」注册（star_manager
    的 handler 绑定发生在实例化**之后**，故注册时机正确），并注入 context 翻译代理。

    注册失败**当场抛**（fail-closed）：宁可不启动，也不带着 0 条注册的哑指令表上线。
    """

    def __init__(self, context=None, **kwargs):
        proxy = _ContextProxy(context) if context is not None else None
        EngineShell.__init__(self, context=proxy)
        register_commands(module_path=__name__)


def is_game_command(msg: str) -> bool:
    """v134.1 私聊延迟修复：判断消息是否为本插件能处理的游戏指令。

    供 AstrBot RateLimitStage（only_llm 模式）调用：命中任一注册指令
    pattern → 该消息走规则匹配秒回，跳过限流；未命中 → 走 LLM 才限流。

    ★ R3：判定口径从待删的 `game/commands/_registry.COMMAND_REGEX` 改口到**宿主注册驱动**
    （`host/registration.py::is_game_command`，正则池 = 包内声明表，注册时刷新）——删壳后
    这条判定照常有效（否则 only_llm 模式下游戏指令会被限流 stall）。
    """
    return _registration.is_game_command(msg)
