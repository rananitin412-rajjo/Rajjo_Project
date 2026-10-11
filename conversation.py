# conversation.py

from personality import SYSTEM_PROMPT
from trading_knowledge import TRADING_KNOWLEDGE, INDEPENDENT_ANALYSIS_RULE

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT + "\n\n" + TRADING_KNOWLEDGE + "\n\n" + INDEPENDENT_ANALYSIS_RULE
    }
]