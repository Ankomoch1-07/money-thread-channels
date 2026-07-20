#!/usr/bin/env python3
"""fact層：金価格の数値取得（唯一の必須層・断定してよい層）。

無料・キー不要の Yahoo Finance チャートAPIを使う（stooqはJSアンチボットで不可になったため変更）。
  金 = GC=F（COMEX金先物・ほぼスポット）／ USD/JPY = JPY=X
円/g は自前計算：XAU/USD × USD/JPY ÷ 31.1035。
履歴も取れるので is_record_high（最高値圏か）と長期チャート用データもここで賄える。
ここが取れなければ台本の数値が書けないため build_ingest 側で required 扱い（失敗時は停止）。

usage(単体テスト): fact_price.py
"""
from __future__ import annotations
import urllib.request, json, datetime

TROY_OUNCE_G = 31.1035
GOLD_SYMBOL = "GC=F"   # COMEX金先物。ほぼスポットXAU/USD
FX_SYMBOL = "JPY=X"    # USD/JPY

def jpy_per_gram(xau_usd: float, usd_jpy: float) -> float:
    return xau_usd * usd_jpy / TROY_OUNCE_G

def _yahoo_chart(symbol: str, rng: str = "max", interval: str = "1d") -> dict:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?range={rng}&interval={interval}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace"))
    return data["chart"]["result"][0]

def fetch() -> dict:
    """ingest.json .fact スキーマの dict を返す。"""
    gold = _yahoo_chart(GOLD_SYMBOL, rng="max")
    fx = _yahoo_chart(FX_SYMBOL, rng="1mo")

    g_closes = [c for c in gold["indicators"]["quote"][0]["close"] if c is not None]
    g_highs = [h for h in gold["indicators"]["quote"][0]["high"] if h is not None]
    xau_usd = gold["meta"].get("regularMarketPrice") or g_closes[-1]
    usd_jpy = fx["meta"].get("regularMarketPrice") or \
        [c for c in fx["indicators"]["quote"][0]["close"] if c is not None][-1]

    change_pct_1d = round((g_closes[-1] - g_closes[-2]) / g_closes[-2] * 100, 2) if len(g_closes) >= 2 else 0.0
    all_time_high = max(g_highs) if g_highs else xau_usd
    is_record_high = xau_usd >= all_time_high * 0.999   # 0.1%許容で"最高値圏"

    return {
        "xau_usd": round(xau_usd, 2),
        "usd_jpy": round(usd_jpy, 2),
        "jpy_per_gram": round(jpy_per_gram(xau_usd, usd_jpy)),
        "change_pct_1d": change_pct_1d,
        "is_record_high": bool(is_record_high),
        "all_time_high_usd": round(all_time_high, 2),
        "source": f"yahoo:{GOLD_SYMBOL}+{FX_SYMBOL}",
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }

if __name__ == "__main__":
    print(json.dumps(fetch(), ensure_ascii=False, indent=2))
