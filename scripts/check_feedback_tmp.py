import sqlite3
import os

base = r'C:\Users\yuyu\qqbot\data\plugins\dragonfall'
for name in ['game_data.db', 'test_game_data.db', 'game_data.db.bak_v48', 'game_data.db.bak_v30', 'game_data.db.bak_v7']:
    path = os.path.join(base, name)
    print(f'=== {name} (size={os.path.getsize(path)}) ===')
    try:
        conn = sqlite3.connect(path)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print('tables:', tables)
        if 'feedback' in tables:
            total = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
            new = conn.execute("SELECT COUNT(*) FROM feedback WHERE status='new'").fetchone()[0]
            print(f'feedback total={total}, new={new}')
            for r in conn.execute("SELECT id, qq_id, group_id, content, created_at, status FROM feedback ORDER BY id ASC LIMIT 10").fetchall():
                print('  ', r)
        conn.close()
    except Exception as e:
        print('ERR:', e)
