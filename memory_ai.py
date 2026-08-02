# memory_ai.py

import json
from llm import ask_llm


def extract_all(text, open_trades):
    """Ek hi call mein memory, new trade, aur trade-close — teeno check karta hai."""

    trades_list = ""
    if open_trades:
        for t in open_trades:
            trade_id, asset, direction, entry, sl, target = t
            trades_list += f"#{trade_id}: {asset} {direction} | Entry: {entry} | SL: {sl} | Target: {target}\n"
    else:
        trades_list = "No open trades."

    prompt = f"""
You are an AI that analyzes a user message and extracts THREE possible things
in a single JSON response.

Return ONLY valid JSON, nothing else, in this exact structure:

{{
    "memory": null OR {{"category": "...", "key": "...", "value": "..."}},
    "new_trade": null OR {{"asset": "...", "direction": "buy/sell", "entry_price": number, "stop_loss": number, "target": number, "reasoning": "..."}},
    "close_trade": null OR {{"trade_id": number, "outcome": "win/loss/breakeven", "note": "..."}}
}}

RULES:

1. "memory" - only if the user shares a LASTING personal fact (name, city, hobby,
   goal, preference, etc.) that would be useful to remember long-term. Otherwise null.

2. "new_trade" - only if user is clearly logging a NEW trade with asset, direction,
   and at least one of entry/SL/target. Otherwise null.

3. "close_trade" - only if user is clearly closing/exiting one of these OPEN trades:
{trades_list}
   Match to the correct trade_id from the list above. Otherwise null.

A message can trigger zero, one, two, or all three fields. Most casual messages
(questions, chit-chat) will have all three as null.

Examples:

User: "My name is Rana"
Output: {{"memory": {{"category": "personal", "key": "name", "value": "Rana"}}, "new_trade": null, "close_trade": null}}

User: "I bought BTC at 64500, SL 63800, target 66000 because of support bounce"
Output: {{"memory": null, "new_trade": {{"asset": "BTC", "direction": "buy", "entry_price": 64500, "stop_loss": 63800, "target": 66000, "reasoning": "support bounce"}}, "close_trade": null}}

User: "haan close kar do, SL hit ho gaya"
Output: {{"memory": null, "new_trade": null, "close_trade": {{"trade_id": (pick correct id from open trades list), "outcome": "loss", "note": "SL hit"}}}}

User: "What's the RSI of gold?"
Output: {{"memory": null, "new_trade": null, "close_trade": null}}

Now analyze this message.

User:
{text}
"""

    reply = ask_llm([
        {
            "role": "user",
            "content": prompt
        }
    ])

    try:
        return json.loads(reply)
    except Exception:
        return {
            "memory": None,
            "new_trade": None,
            "close_trade": None
        }