import streamlit as st
import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Load env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# DB Setup
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

# Streamlit session setup
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

if "page" not in st.session_state:
    st.session_state.page = "auth"
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "skip_rerun" not in st.session_state:
    st.session_state.skip_rerun = False

# ---------- AUTH PAGE ----------
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

if st.session_state.page == "auth":
    st.title("🔐 Welcome to Gemini Chat")

    tab1, tab2 = st.tabs(["🔓 Login", "🆕 Signup"])

    with tab1:
        name = st.text_input("Name", key="login_name")
        pw = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_user(name, pw):
                st.session_state.username = name
                st.session_state.page = "chat"
                st.session_state.skip_rerun = True
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password")

    with tab2:
        sname = st.text_input("Create Name", key="signup_name")
        spw = st.text_input("Create Password", type="password", key="signup_pass")
        if st.button("Signup"):
            if not sname or not spw:
                st.warning("⚠️ Both fields required")
            elif signup_user(sname, spw):
                st.success("✅ Signup successful! Please login.")
            else:
                st.warning("⚠️ Username already exists")

# ---------- CHAT PAGE ----------
elif st.session_state.page == "chat":
    username = st.session_state.username
    st.title(f"💬 Chat with Gemini - {username}")

    if st.button("🚪 Logout"):
        st.session_state.page = "auth"
        st.session_state.username = ""
        st.session_state.chat_history = []
        st.session_state.conversation = None
        st.session_state.skip_rerun = True
        st.experimental_rerun()

    # Load chat history once
    if not st.session_state.chat_history:
        cursor.execute("SELECT user_input, bot_response FROM chats WHERE username = ?", (username,))
        st.session_state.chat_history = [{"user": row[0], "bot": row[1]} for row in cursor.fetchall()]

    # Initialize conversation
    if st.session_state.conversation is None:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # ✅ VALID Gemini model name
            google_api_key=GOOGLE_API_KEY,
        )
        memory = ConversationBufferMemory()
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory)

    # Show last response
    if st.session_state.chat_history:
        last = st.session_state.chat_history[-1]
        st.markdown(f"🧑‍💻 **You:** {last['user']}")
        st.markdown(f"🤖 **Gemini:** {last['bot']}")

    # Input box
    user_input = st.text_input("Ask Gemini something:")
    if user_input:
        if "your name" in user_input.lower():
            response = f"Your name is {username}."
        else:
            try:
                response = st.session_state.conversation.predict(input=user_input)
            except Exception as e:
                st.error("❌ Gemini model failed to respond.")
                st.stop()

        st.session_state.chat_history.append({"user": user_input, "bot": response})
        cursor.execute("INSERT INTO chats (username, user_input, bot_response) VALUES (?, ?, ?)",
                       (username, user_input, response))
        conn.commit()

        st.experimental_rerun()

# Avoid multiple rerun loops
if st.session_state.get("skip_rerun"):
    st.session_state.skip_rerun = False
