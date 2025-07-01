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

# Database Setup
if not os.path.exists("database"):
    os.makedirs("database")

conn = sqlite3.connect("database/chat_data.db", check_same_thread=False)
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

# Page config
st.set_page_config(page_title="Gemini Chat", page_icon="💬")

# Session state init
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "username" not in st.session_state:
    st.session_state.username = ""
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "page_number" not in st.session_state:
    st.session_state.page_number = 0
if "show_history" not in st.session_state:
    st.session_state.show_history = True

# Helper functions
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

# AUTH PAGE
if st.session_state.page == "auth":
    st.title("Gemini Chat")
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        name = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(name, pw):
                st.session_state.username = name
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        sname = st.text_input("Create Username")
        spw = st.text_input("Create Password", type="password")
        if st.button("Signup"):
            if signup_user(sname, spw):
                st.success("Signup successful. Please log in.")
            else:
                st.warning("Username already exists")

# CHAT PAGE
elif st.session_state.page == "chat":
    st.title(f"💬 Chat with Gemini - {st.session_state.username}")

    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "auth"
        st.rerun()

    if not st.session_state.conversation:
        memory = ConversationBufferMemory(return_messages=True)
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY)
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory)

    if not st.session_state.chat_history:
        cursor.execute("SELECT user_input, bot_response FROM chats WHERE username = ? ORDER BY rowid DESC", (st.session_state.username,))
        st.session_state.chat_history = list(reversed(cursor.fetchall()))

    with st.container():
        st.toggle("Show last 10 chats", key="show_history")
        if st.session_state.show_history:
            chats = st.session_state.chat_history[st.session_state.page_number * 10:(st.session_state.page_number + 1) * 10]
            for u, b in chats:
                st.markdown(f"**You:** {u}")
                st.markdown(f"**Gemini:** {b}")

            total_pages = (len(st.session_state.chat_history) - 1) // 10 + 1
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.session_state.page_number > 0:
                    if st.button("Previous"):
                        st.session_state.page_number -= 1
                        st.rerun()
            with col3:
                if st.session_state.page_number < total_pages - 1:
                    if st.button("Next"):
                        st.session_state.page_number += 1
                        st.rerun()

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("", placeholder="Ask something...")
        submitted = st.form_submit_button("Send")
        if submitted and user_input:
            try:
                response = st.session_state.conversation.predict(input=user_input)
            except Exception as e:
                response = f"Error: {e}"

            st.session_state.chat_history.insert(0, (user_input, response))
            cursor.execute("INSERT INTO chats (username, user_input, bot_response) VALUES (?, ?, ?)",
                           (st.session_state.username, user_input, response))
            conn.commit()
            st.rerun()
