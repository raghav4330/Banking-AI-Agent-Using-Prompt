"""
app.py - Simple Streamlit UI for Banking AI Agent with Guardrails.
"""

import streamlit as st
from agent import banking_agent
from banking_tools import execute_transfer
from models import PendingTransfer

# 1. Page title: Banking AI Agent with Guardrails
st.set_page_config(page_title="Banking AI Agent with Guardrails")
st.title("Banking AI Agent with Guardrails")

# 2. Authenticated user and customer_id stored strictly by the application
CUSTOMER_ID = "C001"
AUTHENTICATED_USER = "Rahul Sharma"

# Show authenticated user
st.subheader(f"Authenticated User: {AUTHENTICATED_USER}")
st.caption(f"Customer ID: {CUSTOMER_ID} (Managed by Application)")

# 3. Session state for conversation history and pending transfer
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_transfer" not in st.session_state:
    st.session_state.pending_transfer = None

# 4. Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 5. Display pending transfer confirmation using Confirm and Cancel buttons
if st.session_state.pending_transfer:
    pending = st.session_state.pending_transfer
    amount = pending["amount"]
    receiver = pending["receiver"]

    st.warning(f"You are about to transfer ₹{amount:g} to {receiver}. Confirm?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm"):
            # Application calls execute_transfer() — never triggered by raw LLM output.
            # authenticated_customer_id is passed for defense-in-depth authorization.
            result = execute_transfer(
                customer_id=CUSTOMER_ID,
                amount=amount,
                receiver=receiver,
                authenticated_customer_id=CUSTOMER_ID,
            )
            st.session_state.pending_transfer = None

            if result.get("success"):
                reply = (
                    f"Transfer successful! Transferred ₹{amount:g} to {receiver}. "
                    f"New balance: ₹{result.get('new_balance'):,.2f}."
                )
            else:
                reply = f"Transfer failed: {result.get('message')}"

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    with col2:
        if st.button("Cancel"):
            # Discard the pending transfer
            st.session_state.pending_transfer = None
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Transfer of ₹{amount:g} to {receiver} was cancelled.",
                }
            )
            st.rerun()

# 6. Chat input connected to banking_agent()
if prompt := st.chat_input("Enter your message..."):
    # Append user input to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Connect chat input to banking_agent() using application-controlled customer_id
    response = banking_agent(prompt, customer_id=CUSTOMER_ID)

    # Check if a pending transfer was returned
    if isinstance(response, PendingTransfer) or (
        isinstance(response, dict) and response.get("status") == "PENDING_CONFIRMATION"
    ):
        st.session_state.pending_transfer = dict(response)
        assistant_msg = (
            f"Transfer request prepared: ₹{response['amount']:g} to {response['receiver']}. "
            "Please confirm or cancel using the buttons above."
        )
    else:
        assistant_msg = str(response)

    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
    st.rerun()
