import streamlit as st
import time
from SmartBudgetAI.chat_engine import handle_user_message

# Page Config
st.set_page_config(
    page_title="SmartBudget AI", 
    page_icon="💰",
    layout="centered"
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
    }
    .stChatInputContainer {
        padding-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("💰 SmartBudget AI")
st.caption("Your Financial Assistant (Powered by Llama 3.2 Local)")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize User ID (Mock for now, easy to swap later)
USER_ID = 1

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle User Input
if prompt := st.chat_input("Type a message (e.g., 'Lent John 50' or 'Spot Alex 20')"):
    # 1. Show User Message
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Get Bot Response (The Backend Logic)
    # We show a spinner because the LLM fallback might take ~10-20s
    with st.spinner("Thinking..."):
        response = handle_user_message(prompt, user_id=USER_ID)
    
    if response is None:
        response = "⚠️ Error: The bot returned nothing. Please check chat_engine.py."
    

    # 3. Show Bot Response
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

    # 4. Notification Logic (The Pop-up)
    # This detects the "Signal" from executor.py
    if "settled" in response.lower() or "closed" in response.lower():
        st.toast("✅ Loan successfully settled!", icon="🎉")
        st.balloons()
    
    # 5. Force UI Update (Optional, keeps things snappy)
    time.sleep(0.1)
