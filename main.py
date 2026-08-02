# main.py

from llm import ask_llm
from conversation import messages

from memory import (
    create_database,
    save_memory,
    get_all_memories
)

from memory_ai import extract_all
from market_data import get_market_snapshot

from trade_journal import (
    create_journal_table,
    add_trade,
    close_trade,
    get_journal_summary,
    get_open_trades
)


create_database()
create_journal_table()

print("=" * 40)
print("          RAJJO AI")
print("=" * 40)

while True:

    user = input("\nRana : ")

    if user.lower() in ["exit", "quit", "bye"]:
        print("\nRajjo : Bye Rana ❤️")
        break

    messages.append(
        {
            "role": "user",
            "content": user
        }
    )

    # Ek hi call mein memory + new trade + trade close — sab check ho jaata hai
    open_trades = get_open_trades()
    extracted = extract_all(user, open_trades)

    memory = extracted.get("memory")
    if memory:
        save_memory(
            memory.get("category"),
            memory.get("key"),
            memory.get("value")
        )

    new_trade = extracted.get("new_trade")
    if new_trade:
        add_trade(
            new_trade.get("asset"),
            new_trade.get("direction"),
            new_trade.get("entry_price"),
            new_trade.get("stop_loss"),
            new_trade.get("target"),
            new_trade.get("reasoning")
        )

    close_info = extracted.get("close_trade")
    if close_info:
        close_trade(
            close_info.get("trade_id"),
            close_info.get("outcome")
        )

    # Memory text
    memory_text = ""
    for category, key, value in get_all_memories():
        memory_text += f"[{category}] {key}: {value}\n"

    # Live market data
    market_text = get_market_snapshot()

    # Trade journal
    journal_text = get_journal_summary()

    live_context = {
        "role": "system",
        "content": (
            "Yeh Rana ke baare mein stored memory hai. Sirf tab use karo jab relevant ho.\n\n"
            f"{memory_text}\n\n"
            "Yeh abhi ke live market prices hain. Agar Rana price ya market ke "
            "baare mein pooche to inhi actual numbers ka use karo.\n\n"
            f"{market_text}\n\n"
            "Yeh Rana ki trade journal hai. Agar Rana apni trades, performance, "
            "ya history ke baare mein pooche to isi data ka use karo.\n\n"
            f"{journal_text}"
        )
    }

    messages_for_this_call = messages + [live_context]

    reply = ask_llm(messages_for_this_call)

    print("\nRajjo :", reply)

    messages.append(
        {
            "role": "assistant",
            "content": reply
        }
    )