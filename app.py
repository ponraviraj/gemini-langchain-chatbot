import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Setup
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

# Set LangSmith tracing envs (optional)
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT or ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Streamlit page setup
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

# Create data folder
if not os.path.exists("data"):
    os.makedirs("data")

# Session state initialization
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# Login block
if st.session_state.username is None:
    st.title("🔐 Enter Unique Name to Start")
    username = st.text_input("Your Name (must be unique):")

    if st.button("Login"):
        if not username.strip():
            st.warning("❗ Please enter a valid name.")
        elif os.path.exists(f"data/{username}.json"):
            st.error("⚠️ Name already taken! Try another.")
        else:
            # New user setup
            st.session_state.username = username
            st.session_state.user_file = f"data/{username}.json"
            st.session_state.chat_history = []
            st.success(f"✅ Welcome {username}!")
            # No rerun needed — let it proceed
else:
    # Load history only once
    if os.path.exists(f"data/{st.session_state.username}.json") and not st.session_state.chat_history:
        with open(f"data/{st.session_state.username}.json", "r") as f:
            st.session_state.chat_history = json.load(f)

    # Setup chatbot only once
    if st.session_state.conversation is None:
        memory = ConversationBufferMemory()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=GOOGLE_API_KEY
        )
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory)

    # UI display
    st.title(f"💬 Chat with Gemini - {st.session_state.username}")

    # Show previous conversation
    for chat in st.session_state.chat_history:
        st.markdown(f"🧑‍💻 **You:** {chat['user']}")
        st.markdown(f"🤖 **Gemini:** {chat['bot']}")

    # User input
    user_input = st.text_input("Ask Gemini something:")

    if user_input:
        # Handle "name" questions smartly
        if any(x in user_input.lower() for x in ["what is my name", "who am i", "tell my name"]):
            response = f"Your name is {st.session_state.username}."
        else:
            response = st.session_state.conversation.predict(input=user_input)

        # Save and display
        st.session_state.chat_history.append({
            "user": user_input,
            "bot": response
        })

        with open(f"data/{st.session_state.username}.json", "w") as f:
            json.dump(st.session_state.chat_history, f, indent=2)

        # Show latest reply
        st.markdown(f"🧑‍💻 **You:** {user_input}")
        st.markdown(f"🤖 **Gemini:** {response}")
