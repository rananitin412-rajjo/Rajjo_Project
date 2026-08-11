# market_data.py

import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from datetime import datetime

from alerts_db import get_price_history_list


def get_btc_market_data():
    """CoinGecko se BTC ka current price + 24hr trend data fetch karta hai."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"CoinGecko ticker error: status {response.status_code}, response: {response.text[:200]}")
            return None

        data = response.json()
        market_data = data["market_data"]

        return {
            "price": float(market_data["current_price"]["usd"]),
            "high_24h": float(market_data["high_24h"]["usd"]),
            "low_24h": float(market_data["low_24h"]["usd"]),
            "change_percent": float(market_data["price_change_percentage_24h"])
        }
    except Exception as e:
        print(f"CoinGecko ticker exception: {e}")
        return None


def get_gold_price():
    """Live Gold (XAU/USD) current price fetch karta hai."""
    try:
        url = "https://api.gold-api.com/price/XAU"
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        response = requests.get(url, headers=headers, timeout=8)

        if response.status_code != 200:
            print(f"Gold API error: status {response.status_code}, response: {response.text[:200]}")
            return None

        data = response.json()
        return float(data["price"])
    except Exception as e:
        print(f"Gold API exception: {e}")
        return None


def calculate_indicators_from_prices(prices):
    """Ek price list se RSI, MACD, aur Moving Averages calculate karta hai."""

    if len(prices) < 20:
        return None

    series = pd.Series(prices)
    result = {}

    try:
        rsi = RSIIndicator(close=series, window=14).rsi()
        result["rsi"] = round(rsi.iloc[-1], 2)
    except Exception as e:
        print(f"RSI calculation error: {e}")
        result["rsi"] = None

    try:
        macd_calc = MACD(close=series)
        result["macd"] = round(macd_calc.macd().iloc[-1], 4)
        result["macd_signal"] = round(macd_calc.macd_signal().iloc[-1], 4)
    except Exception as e:
        print(f"MACD calculation error: {e}")
        result["macd"] = None
        result["macd_signal"] = None

    try:
        if len(prices) >= 20:
            sma20 = SMAIndicator(close=series, window=20).sma_indicator()
            result["sma_20"] = round(sma20.iloc[-1], 2)
        else:
            result["sma_20"] = None
    except Exception as e:
        print(f"SMA20 calculation error: {e}")
        result["sma_20"] = None

    try:
        if len(prices) >= 50:
            sma50 = SMAIndicator(close=series, window=50).sma_indicator()
            result["sma_50"] = round(sma50.iloc[-1], 2)
        else:
            result["sma_50"] = None
    except Exception as e:
        print(f"SMA50 calculation error: {e}")
        result["sma_50"] = None

    return result


def get_btc_indicators():
    """CoinGecko ke hourly data se BTC indicators calculate karta hai."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"CoinGecko chart error: status {response.status_code}, response: {response.text[:200]}")
            return None

        data = response.json()
        closes = [point[1] for point in data["prices"]]

        return calculate_indicators_from_prices(closes)
    except Exception as e:
        print(f"CoinGecko chart exception: {e}")
        return None


def get_gold_indicators():
    """Hamare apne stored price history se Gold indicators calculate karta hai."""
    try:
        prices = get_price_history_list("GOLD", limit=100)
        return calculate_indicators_from_prices(prices)
    except Exception as e:
        print(f"Gold indicators exception: {e}")
        return None


def format_indicators(indicators, asset_name):
    """Indicators ko readable text mein format karta hai."""

    if not indicators:
        return f"{asset_name}: Indicators ke liye abhi paryapt data nahi hai.\n"

    text = f"{asset_name} Indicators:\n"

    if indicators.get("rsi") is not None:
        rsi_val = indicators["rsi"]
        if rsi_val >= 70:
            zone = "OVERBOUGHT"
        elif rsi_val <= 30:
            zone = "OVERSOLD"
        else:
            zone = "neutral"
        text += f"- RSI (14): {rsi_val} ({zone})\n"

    if indicators.get("macd") is not None and indicators.get("macd_signal") is not None:
        macd_trend = "bullish (MACD > Signal)" if indicators["macd"] > indicators["macd_signal"] else "bearish (MACD < Signal)"
        text += f"- MACD: {indicators['macd']} | Signal: {indicators['macd_signal']} ({macd_trend})\n"

    if indicators.get("sma_20") is not None:
        text += f"- SMA 20: ${indicators['sma_20']:,.2f}\n"

    if indicators.get("sma_50") is not None:
        text += f"- SMA 50: ${indicators['sma_50']:,.2f}\n"

    return text


def get_market_snapshot():
    """Sab market data + indicators ko ek readable text mein format karta hai."""

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
            f"- 24hr Change: {btc['change_percent']:.2f}% ({trend})\n"
        )
        btc_indicators = get_btc_indicators()
        snapshot += format_indicators(btc_indicators, "BTC") + "\n"
    else:
        snapshot += "BTC/USD: data fetch nahi ho payi abhi\n\n"

    if gold:
        snapshot += f"Gold (XAU/USD):\n- Current: ${gold:,.2f}\n"
        gold_indicators = get_gold_indicators()
        snapshot += format_indicators(gold_indicators, "Gold") + "\n"
    else:
        snapshot += "Gold (XAU/USD): price fetch nahi ho payi abhi\n"

    return snapshot