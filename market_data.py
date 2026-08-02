# market_data.py

import requests
from datetime import datetime


def get_btc_market_data():
    """Binance se BTC ka current price + 24hr trend data fetch karta hai."""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        headers = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()

        return {
            "price": float(data["lastPrice"]),
            "high_24h": float(data["highPrice"]),
            "low_24h": float(data["lowPrice"]),
            "change_percent": float(data["priceChangePercent"])
        }
    except Exception:
        return None


def get_gold_price():
    """Live Gold (XAU/USD) current price fetch karta hai."""
    try:
        url = "https://api.gold-api.com/price/XAU"
        headers = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        return float(data["price"])
    except Exception:
        return None


def get_market_snapshot():
    """Sab market data ko ek readable text mein format karta hai."""

    btc = get_btc_market_data()
    gold = get_gold_price()

    fetch_time = datetime.now().strftime("%I:%M:%S %p")

    snapshot = f"LIVE MARKET DATA (fetched at {fetch_time}):\n\n"

    if btc:
        trend = "UP 📈" if btc["change_percent"] > 0 else "DOWN 📉"
        snapshot += (
            f"BTC/USD:\n"
            f"- Current: ${btc['price']:,.2f}\n"
            f"- 24hr High: ${btc['high_24h']:,.2f}\n"
            f"- 24hr Low: ${btc['low_24h']:,.2f}\n"
            f"- 24hr Change: {btc['change_percent']:.2f}% ({trend})\n\n"
        )
    else:
        snapshot += "BTC/USD: data fetch nahi ho payi abhi\n\n"

    if gold:
        snapshot += (
            f"Gold (XAU/USD):\n"
            f"- Current: ${gold:,.2f}\n"
            f"- (24hr trend data abhi available nahi hai is source se)\n"
        )
    else:
        snapshot += "Gold (XAU/USD): price fetch nahi ho payi abhi\n"

    return snapshot