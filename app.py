import streamlit as st
import os
import json
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

# Setup
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

if not os.path.exists("data"):
    os.makedirs("data")

users_file = "data/users.json"
if not os.path.exists(users_file):
    with open(users_file, "w") as f:
        json.dump({}, f)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# ------------------- AUTH -------------------
if st.session_state.page == "auth":
    st.title("🔐 Welcome to Gemini Chat")

    tabs = st.tabs(["🔓 Login", "🆕 Signup"])

    with open(users_file, "r") as f:
        users = json.load(f)

    with tabs[0]:
        login_name = st.text_input("Name", key="login_name")
        login_pass = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            if login_name in users and users[login_name] == login_pass:
                st.session_state.username = login_name
                st.session_state.page = "chat"
            else:
                st.error("❌ Invalid credentials")

    with tabs[1]:
        signup_name = st.text_input("Create Name", key="signup_name")
        signup_pass = st.text_input("Create Password", type="password", key="signup_pass")

        if st.button("Signup"):
            if signup_name in users:
                st.warning("⚠️ Username already exists.")
            elif not signup_name or not signup_pass:
                st.warning("❗ Both fields are required.")
            else:
                users[signup_name] = signup_pass
                with open(users_file, "w") as f:
                    json.dump(users, f, indent=2)

                user_file = f"data/{signup_name}.json"
                with open(user_file, "w") as f:
                    json.dump([], f)

                st.success("✅ Signup successful! Please login.")

# ------------------- CHAT -------------------
elif st.session_state.page == "chat":
    username = st.session_state.username
    user_file = f"data/{username}.json"

    st.title(f"💬 Chat with Gemini - {username}")
    if st.button("🚪 Logout"):
        st.session_state.page = "auth"
        st.session_state.username = ""
        st.session_state.chat_history = []
        st.session_state.conversation = None
        st.experimental_rerun()

    # Load chat history (once)
    if os.path.exists(user_file) and not st.session_state.chat_history:
        with open(user_file, "r") as f:
            st.session_state.chat_history = json.load(f)

    # Setup model and memory
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

        # Save chat
        st.session_state.chat_history.append({"user": user_input, "bot": response})
        with open(user_file, "w") as f:
            json.dump(st.session_state.chat_history, f, indent=2)

        # Show only last message
        st.markdown(f"🧑‍💻 **You:** {user_input}")
        st.markdown(f"🤖 **Gemini:** {response}")
