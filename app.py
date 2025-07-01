import streamlit as st
import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Load API key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Database
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

# Streamlit App config
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

# Session states
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "username" not in st.session_state:
    st.session_state.username = ""
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# Helper: Login
def login_user(name, password):
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (name, password))
    return cursor.fetchone() is not None

# Helper: Signup
def signup_user(name, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (name, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Helper: Load user chat history from DB
def load_chat_history(username):
    cursor.execute("SELECT user_input, bot_response FROM chats WHERE username = ?", (username,))
    return cursor.fetchall()

# Auth Page
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

                # Load full chat history into memory
                chat_history = load_chat_history(name)
                memory = ConversationBufferMemory(return_messages=True)

                # Reconstruct memory from DB
                for user_msg, bot_msg in chat_history:
                    memory.chat_memory.add_user_message(user_msg)
                    memory.chat_memory.add_ai_message(bot_msg)

                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=GOOGLE_API_KEY,
                )
                st.session_state.conversation = ConversationChain(llm=llm, memory=memory)
                st.rerun()
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

# Chat Page
elif st.session_state.page == "chat":
    username = st.session_state.username
    st.title(f"💬 Chat with Gemini - {username}")

    # Logout
    if st.button("🚪 Logout"):
        st.session_state.page = "auth"
        st.session_state.username = ""
        st.session_state.conversation = None
        st.rerun()

    # Input box
    user_input = st.text_input("Ask Gemini something:")

    if user_input:
        try:
            # Send to Gemini
            response = st.session_state.conversation.predict(input=user_input)

            # Store in DB
            cursor.execute("INSERT INTO chats (username, user_input, bot_response) VALUES (?, ?, ?)",
                           (username, user_input, response))
            conn.commit()

            # Show only last bot response
            st.markdown(f"🤖 **Gemini:** {response}")

        except Exception as e:
            st.error(f"❌ Gemini error: {e}")
