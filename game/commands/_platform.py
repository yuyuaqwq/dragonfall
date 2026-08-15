# -*- coding: utf-8 -*-
"""游戏核心平台抽象（v117.5 解耦 astrbot 的第一步）。

game/commands 各 Mixin 原本 import astrbot 的符号，经审计全部是：
  1) 注册副作用装饰器（@filter.regex / @filter.custom_filter，返回原函数）
  2) 类型标注（AstrMessageEvent）
  3) 简单数据类（MessageChain / Plain / Node / Nodes）
  4) 注册表遍历（star_handlers_registry / EventType / RegexFilter / CustomFilter）

本模块提供等价实现，语义照抄 astrbot 真实现（site-packages 同路径文件），并做
「双注册」：装饰器同时注册到核心注册表与真实 astrbot 注册表（生产可用时），
保证迁移中间态生产行为不变；测试环境（无 astrbot 或命中 tests/shim_astrbot）
只注册核心表。

将来迁移到其他平台：只需把本模块的注册表翻译成目标平台的命令系统。
"""
import enum
import re
from dataclasses import dataclass, field

# ================= 事件协议 =================


class AstrMessageEvent:
    """核心事件协议（仅类型标注，运行时为鸭子类型）。

    运行时事件对象需提供：
      get_message_str() / get_sender_id() / get_group_id() / get_self_id()
      plain_result(text) / stop_event() / send(message)
      message_str（可读写属性）
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_message_str(self):
        return getattr(self, "message_str", "")

    def get_group_id(self):
        return getattr(self, "_g", "")

    def get_sender_id(self):
        return getattr(self, "_q", "")

    async def send(self, message):
        return message


# ================= 回复数据类（序列化格式照抄 astrbot 真实现） =================


class BaseMessageComponent:
    type = "component"

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def toDict(self):
        """OneBot 段格式：{"type": 小写类型, "data": {非空字段}}（照抄真实现）。"""
        data = {}
        for k, v in self.__dict__.items():
            if k == "type" or v is None:
                continue
            if k == "_type":
                k = "type"
            data[k] = v
        return {"type": self.type.lower(), "data": data}

    async def to_dict(self) -> dict:
        return self.toDict()


class Plain(BaseMessageComponent):
    type = "Plain"

    def __init__(self, text: str, convert: bool = True, **_):
        self.text = text

    def toDict(self):
        # OneBot 标准 text 段：aiocqhttp 对 astrbot Plain 有 isinstance 特判输出
        # {"type":"text",...}，核心类走兜底分支（segment.toDict()），直接输出最终格式。
        return {"type": "text", "data": {"text": self.text}}

    async def to_dict(self) -> dict:
        return self.toDict()


class Node(BaseMessageComponent):
    """群合并转发节点（OneBot node 段）。"""

    type = "Node"

    def __init__(self, content=None, **kw):
        if isinstance(content, Node):
            content = [content]
        if content is None:
            content = kw.pop("content", [])
        self.content = content
        self.id = kw.pop("id", 0)  # 忽略
        self.name = kw.pop("name", "")  # qq昵称
        self.uin = kw.pop("uin", "0")  # qq号
        self.seq = kw.pop("seq", "")  # 忽略
        self.time = kw.pop("time", 0)  # 忽略

    async def to_dict(self) -> dict:
        data_content = []
        for comp in self.content:
            if isinstance(comp, (Plain, Node, Nodes)):
                data_content.append(await comp.to_dict())
            else:
                data_content.append(comp.toDict())
        return {
            "type": "node",
            "data": {
                "user_id": str(self.uin),
                "nickname": self.name,
                "content": data_content,
            },
        }


class Nodes(BaseMessageComponent):
    """群合并转发（OneBot 多条 node 的 messages 容器）。"""

    type = "Nodes"

    def __init__(self, nodes: list, **_):
        self.nodes = nodes

    def toDict(self):
        return {"messages": [n.toDict() for n in self.nodes]}

    async def to_dict(self) -> dict:
        return {"messages": [await n.to_dict() for n in self.nodes]}


class MessageChain:
    """消息链：chain 组件列表 + message() 链式追加（照抄真实现字段与方法）。"""

    def __init__(self, chain=None):
        self.chain = list(chain) if chain else []
        self.use_t2i_ = None
        self.use_markdown_ = None
        self.type = None

    def message(self, text: str):
        self.chain.append(Plain(text))
        return self

    def get_plain_text(self) -> str:
        return " ".join(c.text for c in self.chain if isinstance(c, Plain))

    def __str__(self):
        return self.get_plain_text()


# ================= 过滤器 =================


class HandlerFilter:
    def filter(self, event, cfg) -> bool:
        raise NotImplementedError


class RegexFilter(HandlerFilter):
    def __init__(self, regex):
        self.regex = re.compile(regex)
        self.regex_str = self.regex.pattern

    def filter(self, event, cfg) -> bool:
        return bool(self.regex.search(event.get_message_str().strip()))


class CustomFilter(HandlerFilter):
    def __init__(self, raise_error: bool = True, **kwargs) -> None:
        self.raise_error = raise_error

    def filter(self, event, cfg) -> bool:
        raise NotImplementedError


class CustomFilterOr(CustomFilter):
    def __init__(self, filter1, filter2) -> None:
        super().__init__()
        self.filter1 = filter1
        self.filter2 = filter2

    def filter(self, event, cfg) -> bool:
        return self.filter1.filter(event, cfg) or self.filter2.filter(event, cfg)


class CustomFilterAnd(CustomFilter):
    def __init__(self, filter1, filter2) -> None:
        super().__init__()
        self.filter1 = filter1
        self.filter2 = filter2

    def filter(self, event, cfg) -> bool:
        return self.filter1.filter(event, cfg) and self.filter2.filter(event, cfg)


# ================= 注册表（语义照抄 astrbot） =================


class EventType(enum.Enum):
    AdapterMessageEvent = enum.auto()
    OnAstrBotLoadedEvent = enum.auto()
    OnPlatformLoadedEvent = enum.auto()


@dataclass
class StarHandlerMetadata:
    event_type: EventType
    handler_full_name: str
    handler_name: str
    handler_module_path: str
    handler: callable
    event_filters: list
    desc: str = ""
    extras_configs: dict = field(default_factory=dict)
    enabled: bool = True


class StarHandlerRegistry:
    def __init__(self):
        self._handlers: list[StarHandlerMetadata] = []

    def append(self, md: StarHandlerMetadata) -> None:
        self._handlers.append(md)
        # 与真实现一致：按 priority 降序排序（priority 越大越先被 _find_handler 命中）
        self._handlers.sort(
            key=lambda h: h.extras_configs.get("priority", 0),
            reverse=True,
        )

    def get_handler_by_full_name(self, full_name: str):
        for md in self._handlers:
            if md.handler_full_name == full_name:
                return md
        return None

    def get_handlers_by_event_type(self, event_type: EventType):
        return [h for h in self._handlers if h.event_type == event_type]


star_handlers_registry = StarHandlerRegistry()


# ================= 命令装饰器 =================


def get_handler_full_name(awaitable) -> str:
    return f"{awaitable.__module__}_{awaitable.__name__}"


def get_handler_or_create(handler, event_type, dont_add=False, **kwargs):
    handler_full_name = get_handler_full_name(handler)
    md = star_handlers_registry.get_handler_by_full_name(handler_full_name)
    if md:
        return md
    md = StarHandlerMetadata(
        event_type=event_type,
        handler_full_name=handler_full_name,
        handler_name=handler.__name__,
        handler_module_path=handler.__module__,
        handler=handler,
        event_filters=[],
    )
    if handler.__doc__:
        md.desc = handler.__doc__.strip()
    if "desc" in kwargs:
        md.desc = kwargs["desc"]
        del kwargs["desc"]
    md.extras_configs = kwargs
    if not dont_add:
        star_handlers_registry.append(md)
    return md


def _dual_register(awaitable, kind: str, *args, **kwargs):
    """双注册：把装饰器完整效果（filter.regex(pat)(func)）同步转发给真实 astrbot。

    生产：handler 照旧注册进 astrbot 注册表，迁移中间态行为不变；
    测试：无 astrbot 或命中 shim，此处静默跳过/无害注册。
    """
    try:
        from astrbot.api.event import filter as _af

        getattr(_af, kind)(*args, **kwargs)(awaitable)
    except Exception:
        import traceback

        traceback.print_exc()


def register_regex(regex, **kwargs):
    def decorator(awaitable):
        md = get_handler_or_create(awaitable, EventType.AdapterMessageEvent, **kwargs)
        md.event_filters.append(RegexFilter(regex))
        _dual_register(awaitable, "regex", regex, **kwargs)
        return awaitable

    return decorator


def register_custom_filter(custom_type_filter, *args, **kwargs):
    custom_filter = custom_type_filter
    raise_error = args[0] if args else True
    if not isinstance(custom_filter, (CustomFilterAnd, CustomFilterOr)):
        custom_filter = custom_filter(raise_error)

    def decorator(awaitable):
        md = get_handler_or_create(awaitable, EventType.AdapterMessageEvent, **kwargs)
        md.event_filters.append(custom_filter)
        _dual_register(awaitable, "custom_filter", custom_type_filter, *args, **kwargs)
        return awaitable

    return decorator


def register_command(command_name=None, sub_command=None, alias=None, **kwargs):
    """占位：dragonfall 未使用 astrbot 的 command 体系，保留接口兼容。"""

    def decorator(awaitable):
        get_handler_or_create(awaitable, EventType.AdapterMessageEvent, **kwargs)
        return awaitable

    return decorator


def register_command_group(command_group_name=None, sub_command=None, alias=None, **kwargs):
    def decorator(obj):
        return obj

    return decorator


class _FilterNS:
    """兼容现有代码 @filter.regex(...) 语法的命名空间（filter 来源改为本模块）。"""

    def regex(self, *args, **kwargs):
        return register_regex(*args, **kwargs)

    def custom_filter(self, *args, **kwargs):
        return register_custom_filter(*args, **kwargs)

    def command(self, *args, **kwargs):
        return register_command(*args, **kwargs)

    def command_group(self, *args, **kwargs):
        return register_command_group(*args, **kwargs)


filter = _FilterNS()
