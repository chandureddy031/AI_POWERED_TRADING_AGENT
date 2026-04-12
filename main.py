import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from utils.logger import get_logger
from utils.db import init_db, get_recent
from orchestrator import run_analysis

log = get_logger("main")
app = FastAPI(title="AI Trading Assistant", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ui_path = os.path.join(os.path.dirname(__file__), "ui")
if os.path.exists(ui_path):
    app.mount("/static", StaticFiles(directory=ui_path), name="static")

def clean(obj):
    """Recursively convert numpy types to native Python."""
    if isinstance(obj, dict):   return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, list):   return [clean(i) for i in obj]
    if isinstance(obj, np.bool_):    return bool(obj)
    if isinstance(obj, np.integer):  return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray):  return obj.tolist()
    return obj

@app.on_event("startup")
async def startup(): await init_db()

class AnalysisRequest(BaseModel):
    symbol:       str
    timeframe:    str   = "1h"
    trade_type:   str   = "swing"
    account_size: float = 10000.0
    open_trades:  int   = 0
    invest_amount: float = 1000.0
    leverage:     float = 1.0

@app.get("/")
async def root():
    idx = os.path.join(ui_path, "index.html")
    return FileResponse(idx) if os.path.exists(idx) else {"status":"running"}

@app.post("/api/analyze")
async def analyze(req: AnalysisRequest):
    log.info("POST /api/analyze | %s", req.dict())
    try:
        result = await run_analysis(
            symbol=req.symbol.upper(), timeframe=req.timeframe,
            trade_type=req.trade_type, account_size=req.account_size,
            open_trades=req.open_trades, invest_amount=req.invest_amount,
            leverage=req.leverage,
        )
        return JSONResponse(content={"status":"ok","data": clean(result)})
    except Exception as e:
        log.error("Analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def history(limit: int = 10):
    rows = await get_recent(limit)
    return JSONResponse(content={"status":"ok","data": clean(rows)})

@app.get("/api/health")
async def health(): return {"status":"healthy"}