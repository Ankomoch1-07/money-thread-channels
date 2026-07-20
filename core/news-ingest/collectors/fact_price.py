#!/usr/bin/env python3
"""fact層：金価格の数値取得（唯一の必須層・断定してよい層）。

XAU/USD と USD/JPY を価格APIから取得し、円/g を自前計算する。
まずは無料枠(goldapi.io / metalpriceapi 等)で検証。日次1リクエスト＋キャッシュで枠を節約。
API失敗時は WebSearch フォールバック（discovery経由）に委譲する想定。
ここが取れなければ台本の数値が書けないため、build_ingest 側で required=True 扱い。
"""
from __future__ import annotations

TROY_OUNCE_G = 31.1035  # 1 troy oz = 31.1035 g

def jpy_per_gram(xau_usd: float, usd_jpy: float) -> float:
    """円/g = XAU/USD × USD/JPY ÷ 31.1035"""
    return xau_usd * usd_jpy / TROY_OUNCE_G

def fetch(provider: str = "goldapi.io", api_key: str | None = None) -> dict:
    """価格APIから XAU/USD・USD/JPY を取得して fact dict を返す（TODO: 実API接続）。

    戻り値の形は NEWS_INGEST.md の ingest.json .fact スキーマに一致させる:
      {xau_usd, usd_jpy, jpy_per_gram, change_pct_1d, is_record_high, source, fetched_at}
    """
    raise NotImplementedError(
        "無料枠API(goldapi.io等)へ接続。取得後 jpy_per_gram() で円/g算出、"
        "過去N日高値と比較して is_record_high を判定する"
    )

if __name__ == "__main__":
    # 算出ロジックだけ手元確認できるようにしておく
    demo = jpy_per_gram(2700.0, 150.0)
    print(f"demo 円/g (XAU/USD=2700, USD/JPY=150) = {demo:.0f}")
