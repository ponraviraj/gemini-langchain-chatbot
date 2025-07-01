import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Setup environment
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

# Basic LangSmith tracing (optional)
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT or ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Create data folder if not exists
if not os.path.exists("data"):
    os.makedirs("data")

# User login logic
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Enter Unique Name to Start")

    username = st.text_input("Your Name (must be unique):")

    if st.button("Login"):
        user_file = f"data/{username}.json"

        if os.path.exists(user_file):
            st.error("⚠️ Name already taken! Try another.")
        elif username.strip() == "":
            st.warning("Please enter a valid name.")
        else:
            st.session_state.username = username
            st.session_state.logged_in = True
            st.session_state.user_file = user_file
            st.session_state.chat_history = []
            st.success(f"✅ Welcome {username}!")
            st.experimental_rerun()

else:
    # Load memory and model
    st.set_page_config(page_title="Gemini Chat", page_icon="🤖")
    st.title(f"💬 Chat with Gemini - {st.session_state.username}")

    # Load user chat history
    if os.path.exists(st.session_state.user_file):
        with open(st.session_state.user_file, "r") as f:
            st.session_state.chat_history = json.load(f)

    # Display chat history
    for item in st.session_state.chat_history:
        st.markdown(f"🧑‍💻 **You:** {item['user']}")
        st.markdown(f"🤖 **Gemini:** {item['bot']}")

    # Set up Gemini + LangChain
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
    memory = ConversationBufferMemory()

    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        verbose=False
    )

    # Ask input
    user_input = st.text_input("Ask Gemini something...")

    if user_input:
        # If user asks name
        if "what is my name" in user_input.lower():
            response = f"Your name is {st.session_state.username}."
        else:
            response = conversation.predict(input=user_input)

        # Save conversation
        st.session_state.chat_history.append({"user": user_input, "bot": response})
        with open(st.session_state.user_file, "w") as f:
            json.dump(st.session_state.chat_history, f, indent=2)

        st.experimental_rerun()

