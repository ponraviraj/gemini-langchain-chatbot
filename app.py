import streamlit as st
import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Load environment
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Create folders and database
if not os.path.exists("data"):
    os.makedirs("data")
conn = sqlite3.connect("data/gemini_users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL)')
cursor.execute('CREATE TABLE IF NOT EXISTS chats (username TEXT, user_input TEXT, bot_response TEXT)')
conn.commit()

# Streamlit config
st.set_page_config(page_title="Gemini Chat", page_icon="🤖", layout="centered")

# Session state
if "page" not in st.session_state: st.session_state.page = "auth"
if "username" not in st.session_state: st.session_state.username = ""
if "conversation" not in st.session_state: st.session_state.conversation = None
if "show_history" not in st.session_state: st.session_state.show_history = True
if "latest_chats" not in st.session_state: st.session_state.latest_chats = []

# Helper functions
def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone() is not None

def signup_user(username, password):
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_last_10_chats(username):
    cursor.execute("SELECT user_input, bot_response FROM chats WHERE username=? ORDER BY rowid DESC LIMIT 10", (username,))
    return list(reversed(cursor.fetchall()))

def store_chat(username, user_msg, bot_msg):
    cursor.execute("INSERT INTO chats VALUES (?, ?, ?)", (username, user_msg, bot_msg))
    conn.commit()

# Auth Page
if st.session_state.page == "auth":
    st.title("🔐 Welcome to Gemini Chat")
    login_tab, signup_tab = st.tabs(["🔓 Login", "🆕 Signup"])

    with login_tab:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.username = username
                st.session_state.page = "chat"
                # Load memory
                memory = ConversationBufferMemory(return_messages=True)
                chat_data = get_last_10_chats(username)
                for u, b in chat_data:
                    memory.chat_memory.add_user_message(u)
                    memory.chat_memory.add_ai_message(b)
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)
                st.session_state.conversation = ConversationChain(llm=llm, memory=memory)
                st.session_state.latest_chats = chat_data
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    with signup_tab:
        new_user = st.text_input("Create Username")
        new_pass = st.text_input("Create Password", type="password")
        if st.button("Signup"):
            if signup_user(new_user, new_pass):
                st.success("✅ Signup successful, login now.")
            else:
                st.warning("⚠️ Username already exists")

# Chat Page
elif st.session_state.page == "chat":
    st.title(f"💬 Gemini - {st.session_state.username}")
    if st.button("🚪 Logout"):
        st.session_state.page = "auth"
        st.session_state.username = ""
        st.session_state.conversation = None
        st.session_state.latest_chats = []
        st.rerun()

    # Show/hide chat history
    with st.expander("🕘 Show/Hide Chat History", expanded=st.session_state.show_history):
        for user_msg, bot_msg in st.session_state.latest_chats:
            st.markdown(f"""
            <div style="background-color:#e1f5fe;padding:10px;border-radius:10px;margin-bottom:5px">
                <b>You:</b> {user_msg}
            </div>
            <div style="background-color:#f1f8e9;padding:10px;border-radius:10px;margin-bottom:10px">
                <b>Gemini:</b> {bot_msg}
            </div>
            """, unsafe_allow_html=True)

    # Input box at the bottom
    st.markdown("---")
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask something:", placeholder="Type your message here...")
        submit = st.form_submit_button("Send")

        if submit and user_input.strip():
            with st.spinner("Gemini is thinking..."):
                response = st.session_state.conversation.predict(input=user_input)
                store_chat(st.session_state.username, user_input, response)
                st.session_state.latest_chats.append((user_input, response))
                if len(st.session_state.latest_chats) > 10:
                    st.session_state.latest_chats.pop(0)
                st.rerun()  # refresh UI with new message
