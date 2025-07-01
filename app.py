import streamlit as st
import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Database setup
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

# Streamlit app config
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

# Session state initialization
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# Utility functions
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

# ---------- AUTH PAGE ----------
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

    # Logout Button
    if st.button("🚪 Logout"):
        st.session_state.page = "auth"
        st.session_state.username = ""
        st.session_state.chat_history = []
        st.session_state.conversation = None
        st.rerun()

    # Load model if not already
    if st.session_state.conversation is None:
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",  # Or gemini-pro based on availability
                google_api_key=GOOGLE_API_KEY,
            )
            memory = ConversationBufferMemory()
            st.session_state.conversation = ConversationChain(llm=llm, memory=memory)
        except Exception as e:
            st.error(f"❌ Failed to initialize Gemini model: {e}")
            st.stop()

    # Input for asking Gemini
    user_input = st.text_input("Ask Gemini something:")
    if user_input:
        try:
            if "your name" in user_input.lower():
                response = f"Your name is {username}."
            else:
                response = st.session_state.conversation.predict(input=user_input)

            # Save in memory + DB
            st.session_state.chat_history.append({"user": user_input, "bot": response})
            cursor.execute("INSERT INTO chats (username, user_input, bot_response) VALUES (?, ?, ?)",
                           (username, user_input, response))
            conn.commit()

            # Display just the response
            st.markdown(f"🤖 **Gemini:** {response}")

        except Exception as e:
            st.error(f"❌ Gemini error: {e}")
