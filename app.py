import streamlit as st
import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langsmith import traceable

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# LangSmith setup
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
os.environ["LANGCHAIN_ENDPOINT"] = LANGCHAIN_ENDPOINT
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# DB setup
if not os.path.exists("data"):
    os.makedirs("data")

conn = sqlite3.connect("data/gemini_users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        username TEXT,
        user_input TEXT,
        bot_response TEXT
    )
''')
conn.commit()

# App config
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

# Session state
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "show_history" not in st.session_state:
    st.session_state.show_history = True
if "page_number" not in st.session_state:
    st.session_state.page_number = 0

# Auth functions
def login_user(name, password):
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (name, password))
    return cursor.fetchone() is not None

def signup_user(name, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (name, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# LangSmith traceable wrapper
@traceable(name="Gemini Chat Session")
def chat_with_gemini(user_input):
    return st.session_state.conversation.predict(input=user_input)

# Chat UI
if st.session_state.page == "auth":
    st.title("🌈 Welcome to Gemini Neon Chat")
    tab1, tab2 = st.tabs(["🔓 Login", "🆕 Signup"])
    with tab1:
        name = st.text_input("Name", key="login_name")
        pw = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_user(name, pw):
                st.session_state.username = name
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("Invalid credentials")
    with tab2:
        sname = st.text_input("Create Name", key="signup_name")
        spw = st.text_input("Create Password", type="password", key="signup_pass")
        if st.button("Signup"):
            if signup_user(sname, spw):
                st.success("Signup successful! Please login.")
            else:
                st.warning("Username already exists")

elif st.session_state.page == "chat":
    username = st.session_state.username
    st.markdown("""
    <style>
    .chat-box {
        background-color: #0f0f0f;
        color: #39ff14;
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
        box-shadow: 0 0 10px #39ff14;
    }
    .chat-input {
        background-color: #1f1f1f;
        color: #fff;
        border: 2px solid #39ff14;
        border-radius: 10px;
        padding: 10px;
    }
    .neon-title {
        font-size: 30px;
        text-align: center;
        color: #fff;
        text-shadow: 0 0 5px #39ff14, 0 0 10px #39ff14, 0 0 20px #39ff14;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='neon-title'>💬 Gemini Chat with {username}</div>", unsafe_allow_html=True)

    if st.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "auth"
        st.rerun()

    st.toggle("📜 Show last 10 chats", key="show_history")

    if not st.session_state.chat_history:
        cursor.execute("SELECT user_input, bot_response FROM chats WHERE username = ? ORDER BY rowid DESC", (username,))
        st.session_state.chat_history = list(reversed(cursor.fetchall()))

    paginated = st.session_state.chat_history[st.session_state.page_number * 10:(st.session_state.page_number + 1) * 10]

    if st.session_state.show_history:
        for user, bot in paginated:
            st.markdown(f"<div class='chat-box'><b>You:</b> {user}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='chat-box'><b>Gemini:</b> {bot}</div>", unsafe_allow_html=True)

        total_pages = (len(st.session_state.chat_history) - 1) // 10 + 1
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.page_number > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.page_number -= 1
                    st.rerun()
        with col3:
            if st.session_state.page_number < total_pages - 1:
                if st.button("Next ➡️"):
                    st.session_state.page_number += 1
                    st.rerun()

    if not st.session_state.conversation:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY)
        memory = ConversationBufferMemory()
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory, verbose=False)

    user_input = st.text_input("", placeholder="Type your message here...", label_visibility="collapsed", key="chat_input")
    if user_input:
        try:
            response = chat_with_gemini(user_input)
        except Exception as e:
            response = f"Error: {e}"

        st.session_state.chat_history.append((user_input, response))
        cursor.execute("INSERT INTO chats (username, user_input, bot_response) VALUES (?, ?, ?)",
                       (username, user_input, response))
        conn.commit()

        st.rerun()
