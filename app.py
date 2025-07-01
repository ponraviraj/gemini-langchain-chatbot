import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Load .env
load_dotenv()

# Set keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

# LangSmith setup (optional)
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT or ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Create folder for user data
if not os.path.exists("data"):
    os.makedirs("data")

# Page config
st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖")

# Login screen
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Enter Unique Name to Start")

    username = st.text_input("Your Name (must be unique):")

    if st.button("Login"):
        if not username.strip():
            st.warning("❗ Please enter a valid name.")
        else:
            user_file = f"data/{username}.json"
            if os.path.exists(user_file):
                st.error("⚠️ Name already taken! Try another.")
            else:
                st.session_state.username = username
                st.session_state.user_file = user_file
                st.session_state.logged_in = True
                st.session_state.chat_history = []
                st.experimental_rerun()

# Main chatbot UI
else:
    st.title(f"💬 Welcome, {st.session_state.username}!")

    # Load user chat history if exists
    if os.path.exists(st.session_state.user_file):
        with open(st.session_state.user_file, "r") as f:
            st.session_state.chat_history = json.load(f)

    # Show previous chats
    for chat in st.session_state.chat_history:
        st.markdown(f"🧑‍💻 **You:** {chat['user']}")
        st.markdown(f"🤖 **Gemini:** {chat['bot']}")

    # Setup LLM and memory
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GOOGLE_API_KEY
    )

    conversation = ConversationChain(
        llm=llm,
        memory=st.session_state.memory,
        verbose=False
    )

    # Ask input
    user_input = st.text_input("Ask Gemini something...")

    if user_input:
        # Predict reply
        response = conversation.predict(input=user_input)

        # Save to history
        st.session_state.chat_history.append({"user": user_input, "bot": response})
        with open(st.session_state.user_file, "w") as f:
            json.dump(st.session_state.chat_history, f, indent=2)

        st.experimental_rerun()
