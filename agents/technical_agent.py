"""
agents/technical_agent.py - Upgraded with 40+ patterns, SMC/ICT, Price Action, Fibonacci
"""
import pandas as pd
import numpy as np
import ta
from utils.logger import get_logger
from utils.llm_client import llm_json

log = get_logger("technical_agent")

def fibonacci_levels(df):
    high = df["high"].tail(100).max()
    low  = df["low"].tail(100).min()
    diff = high - low
    return {
        "0.0":   round(low,4), "0.236": round(low+0.236*diff,4),
        "0.382": round(low+0.382*diff,4), "0.5": round(low+0.5*diff,4),
        "0.618": round(low+0.618*diff,4), "0.705": round(low+0.705*diff,4),
        "0.786": round(low+0.786*diff,4), "1.0": round(high,4),
        "1.272": round(high+0.272*diff,4), "1.618": round(high+0.618*diff,4),
        "ote_zone": [round(low+0.62*diff,4), round(low+0.79*diff,4)],
    }

def swing_points(df, w=5):
    highs, lows = [], []
    for i in range(w, len(df)-w):
        if df["high"].iloc[i] == df["high"].iloc[i-w:i+w+1].max():
            highs.append({"idx":i,"price":float(df["high"].iloc[i])})
        if df["low"].iloc[i] == df["low"].iloc[i-w:i+w+1].min():
            lows.append({"idx":i,"price":float(df["low"].iloc[i])})
    return highs, lows

def detect_bos_choch(df):
    highs, lows = swing_points(df)
    price = float(df["close"].iloc[-1])
    r = {"bos_bullish":False,"bos_bearish":False,"choch_bullish":False,"choch_bearish":False,
         "last_swing_high":highs[-1]["price"] if highs else None,
         "last_swing_low":lows[-1]["price"] if lows else None}
    if highs and price > highs[-1]["price"]: r["bos_bullish"] = True
    if lows  and price < lows[-1]["price"]:  r["bos_bearish"] = True
    if len(highs)>=2 and len(lows)>=2:
        if lows[-1]["idx"]>highs[-1]["idx"] and r["bos_bullish"]: r["choch_bullish"]=True
        if highs[-1]["idx"]>lows[-1]["idx"] and r["bos_bearish"]: r["choch_bearish"]=True
    return r

def detect_order_blocks(df):
    r = df.tail(50).reset_index(drop=True)
    bull_obs, bear_obs, breakers = [], [], []
    for i in range(1, len(r)-2):
        c, n = r.iloc[i], r.iloc[i+1]
        if c["close"]<c["open"] and n["close"]>n["open"] and (n["close"]-n["open"])>(c["open"]-c["close"])*0.5:
            valid = float(df["close"].iloc[-1]) > c["low"]
            mit   = float(df["close"].iloc[-1]) < c["low"]
            bull_obs.append({"high":round(float(c["open"]),4),"low":round(float(c["close"]),4),"valid":valid,"mitigated":mit})
            if mit: breakers.append({"type":"breaker_bull","level":round(float(c["open"]),4)})
        if c["close"]>c["open"] and n["close"]<n["open"] and (n["open"]-n["close"])>(c["close"]-c["open"])*0.5:
            valid = float(df["close"].iloc[-1]) < c["high"]
            mit   = float(df["close"].iloc[-1]) > c["high"]
            bear_obs.append({"high":round(float(c["close"]),4),"low":round(float(c["open"]),4),"valid":valid,"mitigated":mit})
            if mit: breakers.append({"type":"breaker_bear","level":round(float(c["close"]),4)})
    return {"bullish_obs":bull_obs[-3:],"bearish_obs":bear_obs[-3:],"breaker_blocks":breakers[-2:]}

def detect_fvg(df):
    fvgs=[]
    r=df.tail(80).reset_index(drop=True)
    for i in range(1,len(r)-1):
        p,n=r.iloc[i-1],r.iloc[i+1]
        price=float(df["close"].iloc[-1])
        if n["low"]>p["high"]:
            fvgs.append({"type":"bullish_fvg","top":round(float(n["low"]),4),"bottom":round(float(p["high"]),4),"filled":price<=n["low"]})
        if n["high"]<p["low"]:
            fvgs.append({"type":"bearish_fvg","top":round(float(p["low"]),4),"bottom":round(float(n["high"]),4),"filled":price>=n["high"]})
    return [f for f in fvgs if not f["filled"]][-5:]

def detect_liquidity(df):
    tol=float(df["close"].iloc[-1])*0.003
    h=df["high"].tail(30); l=df["low"].tail(30)
    return {"buy_side_liquidity":round(float(h.max()),4),
            "sell_side_liquidity":round(float(l.min()),4),
            "equal_highs":[round(float(x),4) for x in h if abs(x-h.max())<tol][:3],
            "equal_lows":[round(float(x),4) for x in l if abs(x-l.min())<tol][:3],
            "inducement":round(float(h.nlargest(2).iloc[-1]),4) if len(h)>=2 else None}

def detect_sr(df):
    highs,lows=swing_points(df,w=8)
    price=float(df["close"].iloc[-1])
    res=[round(h["price"],4) for h in highs[-6:]]
    sup=[round(l["price"],4) for l in lows[-6:]]
    return {"resistance_levels":sorted(set(res),reverse=True)[:4],
            "support_levels":sorted(set(sup))[:4],
            "nearest_resistance":min((r for r in res if r>price),default=None),
            "nearest_support":max((s for s in sup if s<price),default=None)}

def detect_candlestick_patterns(df):
    patterns=[]
    r=df.tail(5).reset_index(drop=True)
    def B(c): return abs(c["close"]-c["open"])
    def UW(c): return c["high"]-max(c["close"],c["open"])
    def LW(c): return min(c["close"],c["open"])-c["low"]
    for i in range(len(r)):
        c=r.iloc[i]; b=B(c); uw=UW(c); lw=LW(c); rng=c["high"]-c["low"]
        if rng==0: continue
        if b<=rng*0.1: patterns.append({"pattern":"doji","bias":"neutral"})
        if lw>=b*2 and uw<=b*0.5 and c["close"]>c["open"]: patterns.append({"pattern":"hammer","bias":"bullish"})
        if uw>=b*2 and lw<=b*0.5 and c["close"]<c["open"]: patterns.append({"pattern":"shooting_star","bias":"bearish"})
        if c["close"]>c["open"] and b>=rng*0.85: patterns.append({"pattern":"marubozu_bull","bias":"bullish"})
        if c["close"]<c["open"] and b>=rng*0.85: patterns.append({"pattern":"marubozu_bear","bias":"bearish"})
        if i>0:
            p=r.iloc[i-1]
            if p["close"]<p["open"] and c["close"]>c["open"] and c["close"]>p["open"] and c["open"]<p["close"]:
                patterns.append({"pattern":"bullish_engulfing","bias":"bullish"})
            if p["close"]>p["open"] and c["close"]<c["open"] and c["close"]<p["open"] and c["open"]>p["close"]:
                patterns.append({"pattern":"bearish_engulfing","bias":"bearish"})
            if p["close"]<p["open"] and c["close"]>c["open"] and c["open"]<p["low"] and c["close"]>(p["open"]+p["close"])/2:
                patterns.append({"pattern":"piercing_line","bias":"bullish"})
            if p["close"]>p["open"] and c["close"]<c["open"] and c["open"]>p["high"] and c["close"]<(p["open"]+p["close"])/2:
                patterns.append({"pattern":"dark_cloud_cover","bias":"bearish"})
        if i>=2:
            p1,p2=r.iloc[i-2],r.iloc[i-1]
            if p1["close"]<p1["open"] and B(p2)<B(p1)*0.3 and c["close"]>c["open"] and c["close"]>(p1["open"]+p1["close"])/2:
                patterns.append({"pattern":"morning_star","bias":"bullish"})
            if p1["close"]>p1["open"] and B(p2)<B(p1)*0.3 and c["close"]<c["open"] and c["close"]<(p1["open"]+p1["close"])/2:
                patterns.append({"pattern":"evening_star","bias":"bearish"})
            if all(r.iloc[j]["close"]>r.iloc[j]["open"] for j in [i-2,i-1,i]):
                patterns.append({"pattern":"three_white_soldiers","bias":"bullish"})
            if all(r.iloc[j]["close"]<r.iloc[j]["open"] for j in [i-2,i-1,i]):
                patterns.append({"pattern":"three_black_crows","bias":"bearish"})
    return patterns

def detect_chart_patterns(df):
    patterns=[]
    close=df["close"].values; high=df["high"].values; low=df["low"].values
    n=len(close)
    if n<30: return patterns
    highs,lows=swing_points(df,w=8)
    # Head & Shoulders
    if len(highs)>=3:
        h=highs[-3:]
        if h[1]["price"]>h[0]["price"] and h[1]["price"]>h[2]["price"] and abs(h[0]["price"]-h[2]["price"])/h[1]["price"]<0.03:
            patterns.append({"pattern":"head_and_shoulders","bias":"bearish","head":h[1]["price"],"neckline":round(min(lows[-2]["price"] if len(lows)>=2 else low[-1],float(low[-1])),4)})
    # Inv H&S
    if len(lows)>=3:
        l=lows[-3:]
        if l[1]["price"]<l[0]["price"] and l[1]["price"]<l[2]["price"] and abs(l[0]["price"]-l[2]["price"])/l[1]["price"]<0.03:
            patterns.append({"pattern":"inv_head_and_shoulders","bias":"bullish","head":l[1]["price"]})
    # Double Top/Bottom
    if len(highs)>=2:
        h1,h2=highs[-2]["price"],highs[-1]["price"]
        if abs(h1-h2)/h1<0.02 and float(close[-1])<min(h1,h2)*0.99:
            patterns.append({"pattern":"double_top","bias":"bearish","level":round((h1+h2)/2,4)})
    if len(lows)>=2:
        l1,l2=lows[-2]["price"],lows[-1]["price"]
        if abs(l1-l2)/l1<0.02 and float(close[-1])>max(l1,l2)*1.01:
            patterns.append({"pattern":"double_bottom","bias":"bullish","level":round((l1+l2)/2,4)})
    # Bull/Bear Flag
    if n>=30:
        pole = (close[-20]-close[-30])/close[-30]
        cons = (max(close[-10:])-min(close[-10:]))/close[-10]
        if pole>0.05 and cons<0.03: patterns.append({"pattern":"bull_flag","bias":"bullish","breakout":round(float(max(close[-10:])),4)})
        pole2 = (close[-30]-close[-20])/close[-30]
        if pole2>0.05 and cons<0.03: patterns.append({"pattern":"bear_flag","bias":"bearish","breakdown":round(float(min(close[-10:])),4)})
    # Triangles
    if len(highs)>=2 and len(lows)>=2:
        if abs(highs[-1]["price"]-highs[-2]["price"])/highs[-1]["price"]<0.015 and lows[-1]["price"]>lows[-2]["price"]:
            patterns.append({"pattern":"ascending_triangle","bias":"bullish","resistance":round(highs[-1]["price"],4)})
        if abs(lows[-1]["price"]-lows[-2]["price"])/lows[-1]["price"]<0.015 and highs[-1]["price"]<highs[-2]["price"]:
            patterns.append({"pattern":"descending_triangle","bias":"bearish","support":round(lows[-1]["price"],4)})
    # Wedges
    if len(highs)>=3 and len(lows)>=3:
        if highs[-1]["price"]>highs[-2]["price"]>highs[-3]["price"] and lows[-1]["price"]>lows[-2]["price"]>lows[-3]["price"]:
            if (lows[-1]["price"]-lows[-3]["price"])>(highs[-1]["price"]-highs[-3]["price"]):
                patterns.append({"pattern":"rising_wedge","bias":"bearish"})
        if highs[-1]["price"]<highs[-2]["price"]<highs[-3]["price"] and lows[-1]["price"]<lows[-2]["price"]<lows[-3]["price"]:
            if (lows[-3]["price"]-lows[-1]["price"])>(highs[-3]["price"]-highs[-1]["price"]):
                patterns.append({"pattern":"falling_wedge","bias":"bullish"})
    return patterns

def compute_indicators(df):
    close=df["close"]; high=df["high"]; low=df["low"]; vol=df["volume"]
    ind={}
    try:
        for p in [9,21,50,200]: ind[f"ema_{p}"]=round(float(ta.trend.ema_indicator(close,window=p).iloc[-1]),4)
        for p in [10,20,50]: ind[f"sma_{p}"]=round(float(ta.trend.sma_indicator(close,window=p).iloc[-1]),4)
        ind["rsi_14"]=round(float(ta.momentum.RSIIndicator(close,14).rsi().iloc[-1]),2)
        ind["rsi_7"]=round(float(ta.momentum.RSIIndicator(close,7).rsi().iloc[-1]),2)
        macd=ta.trend.MACD(close)
        ind["macd"]=round(float(macd.macd().iloc[-1]),4)
        ind["macd_sig"]=round(float(macd.macd_signal().iloc[-1]),4)
        ind["macd_hist"]=round(float(macd.macd_diff().iloc[-1]),4)
        bb=ta.volatility.BollingerBands(close,20)
        ind["bb_upper"]=round(float(bb.bollinger_hband().iloc[-1]),4)
        ind["bb_mid"]=round(float(bb.bollinger_mavg().iloc[-1]),4)
        ind["bb_lower"]=round(float(bb.bollinger_lband().iloc[-1]),4)
        ind["bb_width"]=round(float(bb.bollinger_wband().iloc[-1]),4)
        ind["atr_14"]=round(float(ta.volatility.AverageTrueRange(high,low,close,14).average_true_range().iloc[-1]),4)
        st=ta.momentum.StochasticOscillator(high,low,close)
        ind["stoch_k"]=round(float(st.stoch().iloc[-1]),2)
        ind["stoch_d"]=round(float(st.stoch_signal().iloc[-1]),2)
        ind["cci_20"]=round(float(ta.trend.CCIIndicator(high,low,close,20).cci().iloc[-1]),2)
        ind["adx_14"]=round(float(ta.trend.ADXIndicator(high,low,close,14).adx().iloc[-1]),2)
        ind["mfi_14"]=round(float(ta.volume.MFIIndicator(high,low,close,vol,14).money_flow_index().iloc[-1]),2)
        ind["williams_r"]=round(float(ta.momentum.WilliamsRIndicator(high,low,close,14).williams_r().iloc[-1]),2)
        ind["vwap"]=round(float((close*vol).cumsum().iloc[-1]/vol.cumsum().iloc[-1]),4)
        ind["vol_ratio"]=round(float(vol.iloc[-1]/vol.rolling(20).mean().iloc[-1]),2)
        ind["current_price"]=round(float(close.iloc[-1]),4)
        ind["price_change_pct"]=round(float((close.iloc[-1]-close.iloc[-2])/close.iloc[-2]*100),3)
        ind["trend"]="uptrend" if ind["ema_21"]>ind["ema_50"] else "downtrend" if ind["ema_21"]<ind["ema_50"] else "sideways"
        ind["resistance"]=round(float(high.tail(50).max()),4)
        ind["support"]=round(float(low.tail(50).min()),4)
        rsi_s=ta.momentum.RSIIndicator(close,14).rsi()
        ind["bearish_divergence"]=bool(close.iloc[-1]>close.iloc[-5] and rsi_s.iloc[-1]<rsi_s.iloc[-5])
        ind["bullish_divergence"]=bool(close.iloc[-1]<close.iloc[-5] and rsi_s.iloc[-1]>rsi_s.iloc[-5])
    except Exception as e:
        log.error("Indicator error: %s",e)
    return ind

def project_profit(entry, sl, tp, invest, leverage):
    if not all([entry,sl,tp,invest]): return {}
    pos=invest*leverage; qty=pos/entry
    profit=(tp-entry)*qty; loss=abs(entry-sl)*qty
    return {"invest_usd":invest,"leverage":leverage,"position_size":round(pos,2),
            "qty":round(qty,6),"projected_profit_usd":round(profit,2),
            "projected_loss_usd":round(loss,2),"roi_pct":round(profit/invest*100,2),
            "rr_ratio":round(profit/loss,2) if loss>0 else 0}

async def run(df, symbol, timeframe, trade_type, invest_amount=1000.0, leverage=1.0):
    log.info("technical_agent.run | %s %s %s invest=%.2f lev=%.1f",symbol,timeframe,trade_type,invest_amount,leverage)
    ind=compute_indicators(df); bos=detect_bos_choch(df); obs=detect_order_blocks(df)
    fvgs=detect_fvg(df); liq=detect_liquidity(df); sr=detect_sr(df)
    fibs=fibonacci_levels(df); cpats=detect_candlestick_patterns(df); chpats=detect_chart_patterns(df)
    entry=ind.get("current_price",0)
    sl=sr.get("nearest_support",entry*0.98) or entry*0.98
    tp=sr.get("nearest_resistance",entry*1.03) or entry*1.03
    proj=project_profit(entry,sl,tp,invest_amount,leverage)

    system="You are a professional SMC/ICT + Price Action analyst. Return ONLY valid JSON."
    user=f"""
Symbol:{symbol} TF:{timeframe} Type:{trade_type}
Indicators:{ind}
BOS/CHoCH:{bos}
Order Blocks:{obs}
FVGs:{fvgs}
Liquidity:{liq}
SR:{sr}
Fibonacci:{fibs}
Candlestick Patterns:{cpats}
Chart Patterns:{chpats}

Provide complete analysis. Be HONEST with confidence (low confluence=low score).
Return JSON:
{{
  "technical_signal":"bullish|bearish|neutral",
  "confidence":<0.0-1.0 HONEST>,
  "confluence_count":<int>,
  "trend":"<uptrend|downtrend|sideways>",
  "smc_analysis":{{"bos":<bool>,"choch":<bool>,"premium_discount":"<zone>","active_ob":"<desc>","key_fvg":"<desc>","ote_zone":{fibs.get("ote_zone")}}},
  "key_levels":{{"resistance_levels":{sr.get("resistance_levels")},"support_levels":{sr.get("support_levels")},"fib_618":{fibs.get("0.618")},"fib_382":{fibs.get("0.382")},"buy_side_liq":{liq.get("buy_side_liquidity")},"sell_side_liq":{liq.get("sell_side_liquidity")}}},
  "active_patterns":["<pat1>","<pat2>","<pat3>"],
  "strategies":[{{"name":"<n>","bias":"bullish|bearish","valid":true,"entry":<f>,"stop_loss":<f>,"target":<f>,"rr_ratio":<f>,"rationale":"<why>"}}],
  "next_5_candles":{{"prediction":"up|down|sideways","expected_move_pct":<f>,"key_level_to_watch":<f>,"confidence":<0.0-1.0 HONEST>}},
  "profit_projection":{proj},
  "summary":"<3 sentence synthesis>"
}}
"""
    result=await llm_json(system,user)
    result.update({"raw_indicators":ind,"raw_bos_choch":bos,"raw_order_blocks":obs,
                   "raw_fvgs":fvgs,"raw_liquidity":liq,"raw_sr":sr,"raw_fibonacci":fibs,
                   "candlestick_patterns":cpats,"chart_patterns":chpats,"profit_projection":proj})
    log.info("technical_agent done | signal=%s conf=%.2f",result.get("technical_signal"),result.get("confidence",0))
    return result
