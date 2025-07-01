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
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT or ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Set page
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

# SQLite DB Setup
if not os.path.exists("data"):
    os.makedirs("data")

conn = sqlite3.connect("data/gemini_users.db")
c = conn.cursor()

# Create user table
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
""")

# Create chat table
c.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        username TEXT,
        user_msg TEXT,
        bot_msg TEXT
    )
""")
conn.commit()

# Session states
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "username" not in st.session_state:
    st.session_state.username = ""
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# ------------------- AUTH -------------------
def login_user(name, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (name, password))
    return c.fetchone()

def signup_user(name, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (name, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

if st.session_state.page == "auth":
    st.title("🔐 Welcome to Gemini Chat")
    tabs = st.tabs(["🔓 Login", "🆕 Signup"])

    with tabs[0]:
        login_name = st.text_input("Name", key="login_name")
        login_pass = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", key="login_button"):
            user = login_user(login_name, login_pass)
            if user:
                st.session_state.username = login_name
                st.session_state.page = "chat"
                st.experimental_rerun()
            else:
                st.error("❌ Invalid credentials")

    with tabs[1]:
        signup_name = st.text_input("Create Name", key="signup_name")
        signup_pass = st.text_input("Create Password", type="password", key="signup_pass")

        if st.button("Signup", key="signup_button"):
            if not signup_name or not signup_pass:
                st.warning("❗ Both fields required.")
            elif signup_user(signup_name, signup_pass):
                st.success("✅ Signup successful. Please login.")
            else:
                st.warning("⚠️ Username already exists.")

# ------------------- CHAT -------------------
elif st.session_state.page == "chat":
    username = st.session_state.username
    st.title(f"💬 Chat with Gemini - {username}")

    if st.button("🚪 Logout"):
        st.session_state.page = "auth"
        st.session_state.username = ""
        st.session_state.conversation = None
        st.experimental_rerun()

    # Setup model
    if st.session_state.conversation is None:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=GOOGLE_API_KEY
        )
        memory = ConversationBufferMemory()
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory)

    user_input = st.text_input("Ask Gemini something:")

    if user_input:
        if "your name" in user_input.lower():
            response = f"Your name is {username}."
        else:
            response = st.session_state.conversation.predict(input=user_input)

        # Store in SQLite
        c.execute("INSERT INTO chat_history (username, user_msg, bot_msg) VALUES (?, ?, ?)",
                  (username, user_input, response))
        conn.commit()

        # Show last message
        st.markdown(f"🧑‍💻 **You:** {user_input}")
        st.markdown(f"🤖 **Gemini:** {response}")
