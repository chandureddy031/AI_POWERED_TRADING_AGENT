import json, aiosqlite, os, numpy as np
from config import DB_PATH
from utils.logger import get_logger

log = get_logger("db")
os.makedirs("data", exist_ok=True)

class _Enc(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.bool_,)): return bool(o)
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        return super().default(o)

async def init_db():
    log.info("Initialising database at %s", DB_PATH)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, timeframe TEXT,
            trade_type TEXT, result TEXT, created DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        await db.commit()
    log.info("DB ready")

async def save_analysis(symbol, timeframe, trade_type, result):
    log.info("Saving analysis for %s %s", symbol, timeframe)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO analyses (symbol,timeframe,trade_type,result) VALUES (?,?,?,?)",
            (symbol, timeframe, trade_type, json.dumps(result, cls=_Enc))
        )
        await db.commit()

async def get_recent(limit=10):
    log.debug("Fetching %d recent analyses", limit)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM analyses ORDER BY created DESC LIMIT ?", (limit,))
        rows = await cur.fetchall()
    return [dict(r) for r in rows]