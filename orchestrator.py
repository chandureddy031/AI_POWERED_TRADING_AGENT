"""
orchestrator.py - 6-phase async agent pipeline
"""
import asyncio
from utils.logger import get_logger
from utils.db import save_analysis
from utils.alerts import maybe_alert
import agents.data_agent as data_agent
import agents.identifier_agent as identifier_agent
import agents.fundamental_agent as fundamental_agent
import agents.news_agent as news_agent
import agents.technical_agent as technical_agent
import agents.strategy_agent as strategy_agent
import agents.risk_agent as risk_agent
import agents.decision_agent as decision_agent

log = get_logger("orchestrator")

async def run_analysis(symbol, timeframe, trade_type,
                       account_size=10000.0, open_trades=0,
                       invest_amount=1000.0, leverage=1.0):
    log.info("="*60)
    log.info("ORCHESTRATOR START | %s %s %s invest=%.2f lev=%.1f",
             symbol,timeframe,trade_type,invest_amount,leverage)

    # Phase 1: OHLCV
    log.info("Phase 1: OHLCV fetch")
    df = await asyncio.to_thread(data_agent.fetch_ohlcv, symbol, timeframe)
    log.info("OHLCV rows: %d", len(df))

    # Phase 2: identifier + news (parallel)
    log.info("Phase 2: identifier + news")
    id_res, news_res = await asyncio.gather(
        identifier_agent.run(symbol, trade_type),
        news_agent.run(symbol)
    )

    # Phase 3: fundamental + technical (parallel)
    log.info("Phase 3: fundamental + technical")
    fund_res, tech_res = await asyncio.gather(
        fundamental_agent.run(symbol, id_res.get("asset_type","stock")),
        technical_agent.run(df, symbol, timeframe, trade_type, invest_amount, leverage)
    )

    # Phase 4: strategy
    log.info("Phase 4: strategy")
    strat_res = await strategy_agent.run(tech_res, symbol, timeframe, trade_type)

    # Phase 5: risk
    log.info("Phase 5: risk")
    risk_res = await risk_agent.run(strat_res, fund_res, symbol, account_size, open_trades)

    # Phase 6: decision
    log.info("Phase 6: decision")
    decision = await decision_agent.run(
        symbol=symbol, timeframe=timeframe, trade_type=trade_type,
        identifier=id_res, fundamental=fund_res, news=news_res,
        technical=tech_res, strategy=strat_res, risk=risk_res,
    )

    full = {"decision":decision,"identifier":id_res,"fundamental":fund_res,
            "news":news_res,"technical":tech_res,"strategy":strat_res,"risk":risk_res}
    await save_analysis(symbol, timeframe, trade_type, full)
    await maybe_alert(decision)
    log.info("DONE | action=%s conf=%.4f", decision.get("action"), decision.get("confidence",0))
    return full
