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

# LangSmith (optional)
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT or ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# App config
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

# Create data folder
if not os.path.exists("data"):
    os.makedirs("data")

# Load or init user credentials
users_file = "data/users.json"
if os.path.exists(users_file):
    with open(users_file, "r") as f:
        users = json.load(f)
else:
    users = {}

# Session state init
if "page" not in st.session_state:
    st.session_state.page = "auth"
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# ---------- AUTH PAGE ----------
if st.session_state.page == "auth":
    st.title("🔐 Welcome to Gemini Chat")

    tab1, tab2 = st.tabs(["🔓 Login", "🆕 Signup"])

    with tab1:
        login_name = st.text_input("Name", key="login_name")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_name in users and users[login_name] == login_pass:
                st.session_state.username = login_name
                st.session_state.page = "chat"
                st.success("✅ Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid name or password")

    with tab2:
        signup_name = st.text_input("Create Name", key="signup_name")
        signup_pass = st.text_input("Create Password", type="password", key="signup_pass")
        if st.button("Signup"):
            if signup_name in users:
                st.warning("⚠️ Name already exists, choose another.")
            elif not signup_name or not signup_pass:
                st.warning("❗ Both fields are required.")
            else:
                users[signup_name] = signup_pass
                with open(users_file, "w") as f:
                    json.dump(users, f, indent=2)
                with open(f"data/{signup_name}.json", "w") as f:
                    json.dump([], f)
                st.success("✅ Signup successful! You can login now.")

# ---------- CHAT PAGE ----------
elif st.session_state.page == "chat":
    username = st.session_state.username
    user_file = f"data/{username}.json"

    # Load chat history once
    if os.path.exists(user_file) and not st.session_state.chat_history:
        with open(user_file, "r") as f:
            st.session_state.chat_history = json.load(f)

    # Load model
    if st.session_state.conversation is None:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
        memory = ConversationBufferMemory()
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory)

    # UI
    st.title(f"💬 Chat with Gemini - {username}")
    logout_btn = st.button("🚪 Logout")
    if logout_btn:
        st.session_state.page = "auth"
        st.session_state.username = None
        st.session_state.chat_history = []
        st.session_state.conversation = None
        st.experimental_rerun()

    # Display previous chats
    for chat in st.session_state.chat_history:
        st.markdown(f"🧑‍💻 **You:** {chat['user']}")
        st.markdown(f"🤖 **Gemini:** {chat['bot']}")

    # Input and response
    user_input = st.text_input("Ask Gemini something:")

    if user_input:
        if any(x in user_input.lower() for x in ["what is my name", "who am i"]):
            response = f"Your name is {username}."
        else:
            response = st.session_state.conversation.predict(input=user_input)

        st.session_state.chat_history.append({"user": user_input, "bot": response})
        with open(user_file, "w") as f:
            json.dump(st.session_state.chat_history, f, indent=2)

        st.markdown(f"🧑‍💻 **You:** {user_input}")
        st.markdown(f"🤖 **Gemini:** {response}")
