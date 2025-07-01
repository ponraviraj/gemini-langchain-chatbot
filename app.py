import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Load env variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

# Set LangSmith envs (optional)
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT or ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Ensure data folder exists
if not os.path.exists("data"):
    os.makedirs("data")

# Setup page
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

# Session setup
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Login Section
if not st.session_state.username:
    st.title("🔐 Enter Unique Name to Start")
    username_input = st.text_input("Your Name (must be unique):")

    if st.button("Login"):
        if not username_input.strip():
            st.warning("❗ Please enter a valid name.")
        elif os.path.exists(f"data/{username_input}.json"):
            st.error("⚠️ Name already taken! Try another.")
        else:
            # Set session
            st.session_state.username = username_input
            st.session_state.user_file = f"data/{username_input}.json"
            st.success(f"✅ Welcome {username_input}!")
            st.rerun()

# Chat Section
if st.session_state.username:
    st.title(f"💬 Chat with Gemini - {st.session_state.username}")

    # Load previous chat history
    user_file = f"data/{st.session_state.username}.json"
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            st.session_state.chat_history = json.load(f)

    # Display old chats
    for msg in st.session_state.chat_history:
        st.markdown(f"🧑‍💻 **You:** {msg['user']}")
        st.markdown(f"🤖 **Gemini:** {msg['bot']}")

    # Gemini model
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
    memory = ConversationBufferMemory()
    conversation = ConversationChain(llm=llm, memory=memory)

    # Input box
    user_input = st.text_input("Ask Gemini something:")

    if user_input:
        if any(q in user_input.lower() for q in ["your my name", "who am i", "what is my name"]):
            response = f"Your name is {st.session_state.username}."
        else:
            response = conversation.predict(input=user_input)

        # Display and save
        st.markdown(f"🤖 **Gemini:** {response}")
        st.session_state.chat_history.append({"user": user_input, "bot": response})

        with open(user_file, "w") as f:
            json.dump(st.session_state.chat_history, f, indent=2)

        st.rerun()
