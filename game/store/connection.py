# -*- coding: utf-8 -*-

"""奥兰迪亚·余烬纪年存储层 - connection：连接管理 + 建表(唯一碰 sqlite 连接的地方)"""
import os
import sqlite3
import threading
from contextlib import contextmanager

from .. import content as C


DB_PATH = os.environ.get(
    "GWEN_GAME_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game_data.db"),
)

# v135 装配期循环解除：connection 不再顶层依赖 content（data._assembly → core →
# smith_stock → db → store.connection → content 未完成初始化）。C_MAP_IDS 改为
# 惰性求值——首次访问时 content 必已完成装配（消费端都在命令层运行期）。
_C_MAP_IDS_CACHE = None


def _map_ids() -> set:
    global _C_MAP_IDS_CACHE
    if _C_MAP_IDS_CACHE is None:
        _C_MAP_IDS_CACHE = set(C.MAP_BY_ID.keys())
    return _C_MAP_IDS_CACHE


# 兼容旧引用（store 层内部使用 C_MAP_IDS 做集合运算）
C_MAP_IDS = _map_ids()

# v105 P1(M01#11)：RLock——get_player 读档惰性升级前需在锁内计算称号加成（title_bonus
# 会再调 get_stats/get_quests/get_inventory 等 store 函数），Lock 不可重入会死锁。
_lock = threading.RLock()


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def atomic():
    """F1 P0-2：单连接 + 单事务的原子写上下文。

    同一进程内经由 _lock 串行化（与其它 store 函数一致），并对并发写加
    BEGIN IMMEDIATE（拿写锁）保证跨连接场景的单事务原子性。
    用法：
        with atomic() as conn:
            conn.execute(...); conn.execute(...)
    块内抛异常 → rollback；正常退出 → commit。返回连接对象供 execute。
    """
    with _lock:
        conn = _connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()


# ================= v103.5 B1-1 建表 SQL 按域拆分 =================
# 原巨型 executescript（317 行 init_db）拆为 3 个常量，init_db 依次执行，行为零变化。
# 加新表：按域加入对应常量（或新建常量），并在 init_db 补 executescript。
_SQL_CORE_TABLES = """
CREATE TABLE IF NOT EXISTS players (
                qq_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 0,
                hp INTEGER,
                mp INTEGER,
                max_hp INTEGER,
                max_mp INTEGER,
                cur_map TEXT DEFAULT 'vila',
                cur_subarea TEXT DEFAULT '',
                equipment TEXT DEFAULT '{}',
                skills TEXT DEFAULT '[]',
                class_tier INTEGER DEFAULT 0,
                attr_pts INTEGER DEFAULT 0,
                attributes TEXT DEFAULT '{"str":0,"agi":0,"int":0,"vit":0}',
                skill_points INTEGER DEFAULT 0,
                learned_skills TEXT DEFAULT '[]',
                hidden_class_unlock TEXT DEFAULT '[]',
                shortcuts TEXT DEFAULT '{}',
                evolve_path INTEGER DEFAULT 0,
                skill_levels TEXT DEFAULT '{}',
                learned_blueprints TEXT DEFAULT '[]',
                lucky_until INTEGER DEFAULT 0,
                stamina INTEGER DEFAULT 100,
                stamina_ts INTEGER DEFAULT 0,
                created_at INTEGER,
                last_active INTEGER,
                race TEXT DEFAULT 'human',
                gender TEXT DEFAULT '',
                faction TEXT DEFAULT '',
                battle_prefs TEXT DEFAULT '{}',
                investigate_date TEXT DEFAULT '',
                investigate_count INTEGER DEFAULT 0
            );CREATE TABLE IF NOT EXISTS inventory (
                qq_id TEXT NOT NULL,
                item_key TEXT NOT NULL,
                item_data TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (qq_id, item_key)
            );CREATE TABLE IF NOT EXISTS quests (
                qq_id TEXT PRIMARY KEY,
                main_quest TEXT,
                main_status TEXT DEFAULT 'pending',
                main_progress TEXT DEFAULT '{}',
                daily TEXT DEFAULT '{}',
                completed_main TEXT DEFAULT '[]',
                side TEXT DEFAULT '{}'
            );CREATE TABLE IF NOT EXISTS battle_state (
                qq_id TEXT PRIMARY KEY,
                monster TEXT NOT NULL,
                state TEXT NOT NULL,
                updated_at INTEGER
            );CREATE TABLE IF NOT EXISTS achievements (
                qq_id TEXT NOT NULL,
                ach_key TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                PRIMARY KEY (qq_id, ach_key)
            );CREATE TABLE IF NOT EXISTS stats (
                qq_id TEXT PRIMARY KEY,
                kills INTEGER DEFAULT 0,
                elite_kills INTEGER DEFAULT 0,
                boss_kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                day_kills INTEGER DEFAULT 0,
                day_date TEXT DEFAULT '',
                visited_areas INTEGER DEFAULT 0,
                inst_clears INTEGER DEFAULT 0,
                party_count INTEGER DEFAULT 0,
                fish_count INTEGER DEFAULT 0,
                gather_count INTEGER DEFAULT 0,
                mine_count INTEGER DEFAULT 0,
                cook_count INTEGER DEFAULT 0,
                alchemy_count INTEGER DEFAULT 0,
                craft_count INTEGER DEFAULT 0,
                enhance_count INTEGER DEFAULT 0,
                enchant_count INTEGER DEFAULT 0,
                world_events INTEGER DEFAULT 0,
                catch_collect INTEGER DEFAULT 0,
                chests_opened INTEGER DEFAULT 0
            );CREATE TABLE IF NOT EXISTS reputation (
                qq_id TEXT NOT NULL,
                faction TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                PRIMARY KEY (qq_id, faction)
            );CREATE TABLE IF NOT EXISTS signin (
                qq_id TEXT PRIMARY KEY,
                last_date TEXT DEFAULT '',
                streak INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0
            );CREATE TABLE IF NOT EXISTS props_use (
                qq_id TEXT PRIMARY KEY,
                used TEXT DEFAULT '{}'
            );CREATE TABLE IF NOT EXISTS fishing (
                qq_id TEXT PRIMARY KEY,
                total INTEGER DEFAULT 0
            );CREATE TABLE IF NOT EXISTS bestiary (
                qq_id TEXT NOT NULL,
                monster TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                PRIMARY KEY (qq_id, monster)
            );CREATE TABLE IF NOT EXISTS visited (
                qq_id TEXT NOT NULL,
                map_id TEXT NOT NULL,
                PRIMARY KEY (qq_id, map_id)
            );CREATE TABLE IF NOT EXISTS visited_subareas (
                qq_id TEXT NOT NULL,
                map_id TEXT NOT NULL,
                sa_id TEXT NOT NULL,
                first_at INTEGER,
                PRIMARY KEY (qq_id, map_id, sa_id)
            );CREATE TABLE IF NOT EXISTS player_groups (
                qq_id TEXT NOT NULL,
                group_id TEXT NOT NULL,
                first_seen INTEGER,
                last_active INTEGER,
                PRIMARY KEY (qq_id, group_id)
            );"""

_SQL_SOCIAL_TABLES = """
CREATE TABLE IF NOT EXISTS world_event (
                id INTEGER PRIMARY KEY,
                etype TEXT NOT NULL,
                starts_at INTEGER,
                ends_at INTEGER,
                data TEXT DEFAULT '{}'
            );CREATE TABLE IF NOT EXISTS event_state (
                key TEXT PRIMARY KEY,
                value TEXT
            );CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                seller TEXT NOT NULL,
                item_key TEXT NOT NULL,
                item_data TEXT NOT NULL,
                price INTEGER NOT NULL,
                listed_at INTEGER
            );CREATE TABLE IF NOT EXISTS party (
                group_id TEXT NOT NULL,
                leader TEXT NOT NULL,
                member TEXT NOT NULL,
                created_at INTEGER,
                PRIMARY KEY (group_id, member)
            );CREATE TABLE IF NOT EXISTS guilds (
                gid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                leader TEXT NOT NULL,
                icon TEXT DEFAULT '🏰',
                desc TEXT DEFAULT '',
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                created_at INTEGER
            );CREATE TABLE IF NOT EXISTS guild_members (
                gid INTEGER NOT NULL,
                qq_id TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at INTEGER,
                contribute INTEGER DEFAULT 0,
                sign_date TEXT DEFAULT '',
                task_date TEXT DEFAULT '',
                task_progress INTEGER DEFAULT 0,
                PRIMARY KEY (gid, qq_id)
            );CREATE TABLE IF NOT EXISTS pets (
                qq_id TEXT PRIMARY KEY,
                pet_key TEXT NOT NULL,
                name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                satiety INTEGER DEFAULT 100,
                bond INTEGER DEFAULT 0,
                last_sat_time INTEGER DEFAULT 0
            );CREATE TABLE IF NOT EXISTS pet_dex (
                qq_id TEXT NOT NULL,
                pet_key TEXT NOT NULL,
                hatched INTEGER DEFAULT 0,
                PRIMARY KEY (qq_id, pet_key)
            );CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qq_id TEXT NOT NULL,
                group_id TEXT DEFAULT '',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'new',
                reply TEXT DEFAULT ''
            );"""

_SQL_PROF_TABLES = """
CREATE TABLE IF NOT EXISTS professions (
                qq_id TEXT PRIMARY KEY,
                gather_lv INTEGER DEFAULT 1,
                gather_exp INTEGER DEFAULT 0,
                mining_lv INTEGER DEFAULT 1,
                mining_exp INTEGER DEFAULT 0,
                fishing_lv INTEGER DEFAULT 1,
                fishing_exp INTEGER DEFAULT 0,
                alchemy_lv INTEGER DEFAULT 1,
                alchemy_exp INTEGER DEFAULT 0,
                craft_lv INTEGER DEFAULT 1,
                craft_exp INTEGER DEFAULT 0,
                cooking_lv INTEGER DEFAULT 1,
                cooking_exp INTEGER DEFAULT 0,
                enhance_lv INTEGER DEFAULT 1,
                enhance_exp INTEGER DEFAULT 0,
                enchant_lv INTEGER DEFAULT 1,
                enchant_exp INTEGER DEFAULT 0,
                fish_king INTEGER DEFAULT 0,
                explore_wandering INTEGER DEFAULT 0
            );"""


def init_db():
    """建表(全局 qq_id 主键)"""
    with _lock:
        conn = _connect()
        try:
            conn.executescript(_SQL_CORE_TABLES)
            conn.executescript(_SQL_SOCIAL_TABLES)
            conn.executescript(_SQL_PROF_TABLES)
            _ensure_legacy_columns(conn)
            conn.commit()
        finally:
            conn.close()


def _ensure_legacy_columns(conn):
    """v103.5 B1-1：老库 ALTER 补列自愈（原 init_db 尾部，拆出便于维护）"""
    # 兼容旧库：players 表补 class_tier 列（转职系统）
    pcols = [r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()]
    if "class_tier" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN class_tier INTEGER DEFAULT 0")
    if "attr_pts" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN attr_pts INTEGER DEFAULT 0")
    if "attributes" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN attributes TEXT DEFAULT '{\"str\":0,\"agi\":0,\"int\":0,\"vit\":0}'")
    if "skill_points" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN skill_points INTEGER DEFAULT 0")
    if "learned_skills" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN learned_skills TEXT DEFAULT '[]'")
    if "hidden_class_unlock" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN hidden_class_unlock TEXT DEFAULT '[]'")
    if "portals" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN portals TEXT DEFAULT '[]'")
    if "skill_bar" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN skill_bar TEXT DEFAULT '[]'")
    if "skill_spent" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN skill_spent INTEGER DEFAULT 0")
    if "shortcuts" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN shortcuts TEXT DEFAULT '{}'")
    if "explore_wandering" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN explore_wandering INTEGER DEFAULT 0")
    if "evolve_path" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN evolve_path INTEGER DEFAULT 0")
    if "skill_levels" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN skill_levels TEXT DEFAULT '{}'")
    if "mounts" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN mounts TEXT DEFAULT '{}'")
    if "learned_blueprints" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN learned_blueprints TEXT DEFAULT '[]'")
    if "lucky_until" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN lucky_until INTEGER DEFAULT 0")
    # v140 波2：副本通关后调查——每日调查次数与日期（跨日归零）
    if "investigate_date" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN investigate_date TEXT DEFAULT ''")
    if "investigate_count" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN investigate_count INTEGER DEFAULT 0")
    # v94 体力系统：动作类行为消耗体力，食物/住宿/自然恢复（老库自愈）
    if "stamina" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN stamina INTEGER DEFAULT 100")
    if "stamina_ts" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN stamina_ts INTEGER DEFAULT 0")
    # 阶段九：种族系统（08 章）——players 表补 race 列（老库自愈）
    if "race" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN race TEXT DEFAULT 'human'")
    # v95.24 性别系统：注册可选性别（男/女），老库自愈
    if "gender" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN gender TEXT DEFAULT ''")
    # v139 职业融合：战前指令偏好（形态预设/终结阈值/蓄力档位）——老库自愈
    if "battle_prefs" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN battle_prefs TEXT DEFAULT '{}'")
    # 阶段九：成就系统（14 章）——stats 表补计数列 + players 表补 equipped_title 列
    scols = [r[1] for r in conn.execute("PRAGMA table_info(stats)").fetchall()]
    for scol in ("visited_areas", "inst_clears", "party_count", "fish_count", "gather_count",
                 "mine_count", "cook_count", "alchemy_count", "craft_count", "enhance_count",
                 "enchant_count", "world_events", "catch_collect", "chests_opened"):
        if scol not in scols:
            conn.execute(f"ALTER TABLE stats ADD COLUMN {scol} INTEGER DEFAULT 0")
    if "equipped_title" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN equipped_title TEXT DEFAULT ''")
    # v84 房屋升级（25 章）：players 表补 deed_lv 列（房产等级，默认 1 级木屋）
    if "deed_lv" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN deed_lv INTEGER DEFAULT 1")
    # v86 子区域（02 章 13 节）：players 表补 cur_subarea 列（当前所在子区域，空=地图默认落点）
    if "cur_subarea" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN cur_subarea TEXT DEFAULT ''")
    # v141 大陆隔离：players 表补 world_id 列（所在大陆 id，默认 mainland=主大陆；副本实例=inst:<uuid>）
    if "world_id" not in pcols:
        conn.execute("ALTER TABLE players ADD COLUMN world_id TEXT DEFAULT 'mainland'")
    # 兼容旧库：feedback 表补 reply 列（意见回复）
    fcols = [r[1] for r in conn.execute("PRAGMA table_info(feedback)").fetchall()]
    if "reply" not in fcols:
        conn.execute("ALTER TABLE feedback ADD COLUMN reply TEXT DEFAULT ''")
    # v66 摆摊：market 表补 map_id 列（NULL/'' = 群市场寄售；有值 = 在该地图摆摊）
    mcols = [r[1] for r in conn.execute("PRAGMA table_info(market)").fetchall()]
    if "map_id" not in mcols:
        conn.execute("ALTER TABLE market ADD COLUMN map_id TEXT DEFAULT ''")
    # v67 双副业体系：professions 表补 activated 列（JSON 数组：已激活副业 key；v167 起无数量上限）
    prcols = [r[1] for r in conn.execute("PRAGMA table_info(professions)").fetchall()]
    if "activated" not in prcols:
        conn.execute("ALTER TABLE professions ADD COLUMN activated TEXT DEFAULT '[]'")
    # 导师进修（19 章第八章）：professions 表补 强化/附魔 独立副业列（8 副业）
    if "enhance_lv" not in prcols:
        conn.execute("ALTER TABLE professions ADD COLUMN enhance_lv INTEGER DEFAULT 1")
        conn.execute("ALTER TABLE professions ADD COLUMN enhance_exp INTEGER DEFAULT 0")
    if "enchant_lv" not in prcols:
        conn.execute("ALTER TABLE professions ADD COLUMN enchant_lv INTEGER DEFAULT 1")
        conn.execute("ALTER TABLE professions ADD COLUMN enchant_exp INTEGER DEFAULT 0")
    # 导师进修：players 表补 apprentices 列（JSON 数组：已拜师副业 key）
    apcols = [r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()]
    if "apprentices" not in apcols:
        conn.execute("ALTER TABLE players ADD COLUMN apprentices TEXT DEFAULT '[]'")
    # v68 地契：players 表补 deed 列（地皮 ID，一人一张）
    pcols2 = [r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()]
    if "deed" not in pcols2:
        conn.execute("ALTER TABLE players ADD COLUMN deed TEXT DEFAULT ''")
    # 24 章宠物系统：pets 表补 last_sat_time 列（饱食度自然衰减时间戳，老库自愈）
    petcols = [r[1] for r in conn.execute("PRAGMA table_info(pets)").fetchall()]
    if "last_sat_time" not in petcols:
        conn.execute("ALTER TABLE pets ADD COLUMN last_sat_time INTEGER DEFAULT 0")
    # v116 阵营国战最小闭环：players 表补 faction 列（玩家可选入籍的四阵营，空串=未加入）。
    # 老库自愈：新建库在 _SQL_CORE_TABLES 已知该列（见 players CREATE），此处仅补存量库。
    pcols_f = [r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()]
    if "faction" not in pcols_f:
        conn.execute("ALTER TABLE players ADD COLUMN faction TEXT DEFAULT ''")


