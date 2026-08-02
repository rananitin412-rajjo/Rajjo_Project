# app.py

import streamlit as st

from llm import ask_llm, ask_llm_with_image
from personality import SYSTEM_PROMPT
from trading_knowledge import TRADING_KNOWLEDGE

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


# Database setup (ek hi baar chalega)
create_database()
create_journal_table()

st.set_page_config(page_title="Rajjo AI", page_icon="💹", layout="centered")

st.title("💹 Rajjo AI")
st.caption("Your trading mentor & finance companion")

# Session state mein conversation history rakhte hain (Streamlit reload-safe)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\n" + TRADING_KNOWLEDGE
        }
    ]

# Sidebar mein open trades dikhate hain
with st.sidebar:
    st.subheader("📖 Open Trades")
    open_trades = get_open_trades()
    if open_trades:
        for t in open_trades:
            trade_id, asset, direction, entry, sl, target = t
            st.markdown(
                f"**#{trade_id} {asset} {direction.upper()}**\n"
                f"Entry: {entry} | SL: {sl} | Target: {target}"
            )
    else:
        st.write("Koi open trade nahi hai.")

# Purani chat history dikhao (system message chhod ke)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Image upload (optional)
uploaded_image = st.file_uploader("Chart ya screenshot bhejo (optional)", type=["png", "jpg", "jpeg"])

# Naya message input
user_input = st.chat_input("Rana, kuch pucho...")

if user_input:

    # User message show + save
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        if uploaded_image is not None:
            st.image(uploaded_image)

    with st.chat_message("assistant"):
        with st.spinner("Rajjo soch rahi hai..."):

            # Extraction (memory + trade + close) — ek hi call
            open_trades = get_open_trades()
            extracted = extract_all(user_input, open_trades)

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

            # Context build karo
            memory_text = ""
            for category, key, value in get_all_memories():
                memory_text += f"[{category}] {key}: {value}\n"

            market_text = get_market_snapshot()
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

            messages_for_this_call = st.session_state.messages + [live_context]

            if uploaded_image is not None:
                image_bytes = uploaded_image.getvalue()
                reply = ask_llm_with_image(messages_for_this_call, image_bytes, uploaded_image.type)
            else:
                reply = ask_llm(messages_for_this_call)

            st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()