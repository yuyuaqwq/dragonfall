# -*- coding: utf-8 -*-

"""《剑与魔法》存储层 - connection：连接管理 + 建表(唯一碰 sqlite 连接的地方)"""
import os
import sqlite3
import threading

from .. import content as C


DB_PATH = os.environ.get(
    "GWEN_GAME_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game_data.db"),
)

C_MAP_IDS = set(C.MAP_BY_ID.keys())

_lock = threading.Lock()


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建表(全局 qq_id 主键)"""
    with _lock:
        conn = _connect()
        try:
            conn.executescript("""
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
                created_at INTEGER,
                last_active INTEGER,
                race TEXT DEFAULT 'human'
            );
            CREATE TABLE IF NOT EXISTS inventory (
                qq_id TEXT NOT NULL,
                item_key TEXT NOT NULL,
                item_data TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (qq_id, item_key)
            );
            CREATE TABLE IF NOT EXISTS quests (
                qq_id TEXT PRIMARY KEY,
                main_quest TEXT,
                main_status TEXT DEFAULT 'pending',
                main_progress TEXT DEFAULT '{}',
                daily TEXT DEFAULT '{}',
                completed_main TEXT DEFAULT '[]',
                side TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS battle_state (
                qq_id TEXT PRIMARY KEY,
                monster TEXT NOT NULL,
                state TEXT NOT NULL,
                updated_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS achievements (
                qq_id TEXT NOT NULL,
                ach_key TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                PRIMARY KEY (qq_id, ach_key)
            );
            CREATE TABLE IF NOT EXISTS stats (
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
                catch_collect INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS reputation (
                qq_id TEXT NOT NULL,
                faction TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                PRIMARY KEY (qq_id, faction)
            );
            CREATE TABLE IF NOT EXISTS signin (
                qq_id TEXT PRIMARY KEY,
                last_date TEXT DEFAULT '',
                streak INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS props_use (
                qq_id TEXT PRIMARY KEY,
                used TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS fishing (
                qq_id TEXT PRIMARY KEY,
                total INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS bestiary (
                qq_id TEXT NOT NULL,
                monster TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                PRIMARY KEY (qq_id, monster)
            );
            CREATE TABLE IF NOT EXISTS visited (
                qq_id TEXT NOT NULL,
                map_id TEXT NOT NULL,
                PRIMARY KEY (qq_id, map_id)
            );
            CREATE TABLE IF NOT EXISTS player_groups (
                qq_id TEXT NOT NULL,
                group_id TEXT NOT NULL,
                first_seen INTEGER,
                last_active INTEGER,
                PRIMARY KEY (qq_id, group_id)
            );
            CREATE TABLE IF NOT EXISTS world_event (
                id INTEGER PRIMARY KEY,
                etype TEXT NOT NULL,
                starts_at INTEGER,
                ends_at INTEGER,
                data TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS event_state (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                seller TEXT NOT NULL,
                item_key TEXT NOT NULL,
                item_data TEXT NOT NULL,
                price INTEGER NOT NULL,
                listed_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS party (
                group_id TEXT NOT NULL,
                leader TEXT NOT NULL,
                member TEXT NOT NULL,
                created_at INTEGER,
                PRIMARY KEY (group_id, member)
            );
            CREATE TABLE IF NOT EXISTS guilds (
                gid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                leader TEXT NOT NULL,
                icon TEXT DEFAULT '🏰',
                desc TEXT DEFAULT '',
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                created_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS guild_members (
                gid INTEGER NOT NULL,
                qq_id TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at INTEGER,
                contribute INTEGER DEFAULT 0,
                sign_date TEXT DEFAULT '',
                task_date TEXT DEFAULT '',
                task_progress INTEGER DEFAULT 0,
                PRIMARY KEY (gid, qq_id)
            );
            CREATE TABLE IF NOT EXISTS pets (
                qq_id TEXT PRIMARY KEY,
                pet_key TEXT NOT NULL,
                name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                satiety INTEGER DEFAULT 100,
                bond INTEGER DEFAULT 0,
                last_sat_time INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS pet_dex (
                qq_id TEXT NOT NULL,
                pet_key TEXT NOT NULL,
                hatched INTEGER DEFAULT 0,
                PRIMARY KEY (qq_id, pet_key)
            );
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qq_id TEXT NOT NULL,
                group_id TEXT DEFAULT '',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'new',
                reply TEXT DEFAULT ''
            );
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
                fish_king INTEGER DEFAULT 0
            );
            """)
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
            # 阶段九：种族系统（08 章）——players 表补 race 列（老库自愈）
            if "race" not in pcols:
                conn.execute("ALTER TABLE players ADD COLUMN race TEXT DEFAULT 'human'")
            # 阶段九：成就系统（14 章）——stats 表补计数列 + players 表补 equipped_title 列
            scols = [r[1] for r in conn.execute("PRAGMA table_info(stats)").fetchall()]
            for scol in ("visited_areas", "inst_clears", "party_count", "fish_count", "gather_count",
                         "mine_count", "cook_count", "alchemy_count", "craft_count", "enhance_count",
                         "enchant_count", "world_events", "catch_collect"):
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
            # 兼容旧库：feedback 表补 reply 列（意见回复）
            fcols = [r[1] for r in conn.execute("PRAGMA table_info(feedback)").fetchall()]
            if "reply" not in fcols:
                conn.execute("ALTER TABLE feedback ADD COLUMN reply TEXT DEFAULT ''")
            # v66 摆摊：market 表补 map_id 列（NULL/'' = 群市场寄售；有值 = 在该地图摆摊）
            mcols = [r[1] for r in conn.execute("PRAGMA table_info(market)").fetchall()]
            if "map_id" not in mcols:
                conn.execute("ALTER TABLE market ADD COLUMN map_id TEXT DEFAULT ''")
            # v67 双副业上限：professions 表补 activated 列（JSON 数组：已激活副业 key）
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
            conn.commit()
        finally:
            conn.close()


