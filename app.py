import streamlit as st
import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import random

# Load environment
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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
cursor.execute('''
    CREATE TABLE IF NOT EXISTS scores (
        username TEXT,
        question TEXT,
        correct TEXT,
        user_answer TEXT,
        is_correct INTEGER
    )
''')
conn.commit()

st.set_page_config(page_title="Gemini Quiz Chat", page_icon="🤖")

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
if "quiz_mode" not in st.session_state:
    st.session_state.quiz_mode = False
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0

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

# Quiz generator
def generate_quiz_questions():
    questions = [
        ("What is Python used for?", ["Web Development", "Data Science", "Scripting", "All of the above"], "All of the above"),
        ("Which keyword defines a function in Python?", ["function", "def", "define", "lambda"], "def"),
        ("What data type is the result of 3 / 2 in Python 3?", ["int", "float", "str", "bool"], "float"),
        ("Which of these is a Python web framework?", ["React", "Flask", "Laravel", "Django"], "Django"),
        ("What does 'len()' function return?", ["Length of a list", "Sum", "Max", "None"], "Length of a list"),
    ]
    return random.sample(questions, 3)

# Pages
if st.session_state.page == "auth":
    st.title("🔐 Welcome to Gemini Quiz Chat")
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
    st.title(f"💬 Chat with Gemini - {username}")
    if st.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "auth"
        st.rerun()

    st.toggle("📜 Show chat history", key="show_history")

    if not st.session_state.chat_history:
        cursor.execute("SELECT user_input, bot_response FROM chats WHERE username = ? ORDER BY rowid DESC LIMIT 10", (username,))
        st.session_state.chat_history = list(reversed(cursor.fetchall()))

    if st.session_state.show_history:
        for row in st.session_state.chat_history:
            st.markdown(f"<div style='background-color:#e3f2fd;padding:10px;border-radius:10px;margin-bottom:5px'><b>You:</b> {row[0]}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#fce4ec;padding:10px;border-radius:10px;margin-bottom:10px'><b>Gemini:</b> {row[1]}</div>", unsafe_allow_html=True)

    if not st.session_state.conversation:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
        memory = ConversationBufferMemory()
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory)

    if st.session_state.quiz_mode:
        quiz = st.session_state.quiz_questions[st.session_state.quiz_index]
        st.subheader(f"🧠 Question {st.session_state.quiz_index + 1}:")
        st.write(quiz[0])
        choice = st.radio("Choose an answer:", quiz[1], key=f"quiz_q{st.session_state.quiz_index}")
        if st.button("Submit Answer"):
            correct = quiz[2]
            is_correct = int(choice == correct)
            if is_correct:
                st.success("✅ Correct!")
                st.session_state.quiz_score += 1
            else:
                st.error(f"❌ Wrong. Correct: {correct}")
            cursor.execute("INSERT INTO scores (username, question, correct, user_answer, is_correct) VALUES (?, ?, ?, ?, ?)",
                           (username, quiz[0], correct, choice, is_correct))
            conn.commit()
            st.session_state.quiz_index += 1
            if st.session_state.quiz_index >= len(st.session_state.quiz_questions):
                st.balloons()
                st.success(f"🏁 Quiz completed. Score: {st.session_state.quiz_score}/{len(st.session_state.quiz_questions)}")
                st.session_state.quiz_mode = False
                st.session_state.quiz_questions = []
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
            st.rerun()
    else:
        user_input = st.text_input("Ask Gemini something (or say 'start quiz'):")
        if user_input:
            if "start quiz" in user_input.lower():
                st.session_state.quiz_mode = True
                st.session_state.quiz_questions = generate_quiz_questions()
                st.session_state.quiz_index = 0
                st.rerun()
            else:
                try:
                    response = st.session_state.conversation.predict(input=user_input)
                except Exception:
                    response = "Sorry, something went wrong."
                st.session_state.chat_history.append((user_input, response))
                cursor.execute("INSERT INTO chats (username, user_input, bot_response) VALUES (?, ?, ?)",
                               (username, user_input, response))
                conn.commit()
                st.rerun()
