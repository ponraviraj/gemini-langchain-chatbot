import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

# LangSmith (optional)
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT or ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Setup data folder
if not os.path.exists("data"):
    os.makedirs("data")

# Streamlit page setup
st.set_page_config(page_title="Gemini Chat", page_icon="🤖")

# Login logic
if "username" not in st.session_state:
    st.session_state.username = None

if not st.session_state.username:
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
                st.session_state.chat_history = []
                st.success(f"✅ Welcome {username}!")
                st.stop()  # Safely exit to reload session
    st.stop()  # Stop if not logged in

# ✅ After login
st.title(f"💬 Chat with Gemini - {st.session_state.username}")

# Load chat history
if os.path.exists(st.session_state.user_file):
    with open(st.session_state.user_file, "r") as f:
        st.session_state.chat_history = json.load(f)

# Display past chats
for item in st.session_state.chat_history:
    st.markdown(f"🧑‍💻 **You:** {item['user']}")
    st.markdown(f"🤖 **Gemini:** {item['bot']}")

# LLM setup
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory)

# Input box
user_input = st.text_input("Ask Gemini something...")

if user_input:
    # Respond to name questions dynamically
    if any(keyword in user_input.lower() for keyword in ["your my name", "who am i", "what is my name"]):
        response = f"Your name is {st.session_state.username}."
    else:
        response = conversation.predict(input=user_input)

    # Save chat history
    st.session_state.chat_history.append({"user": user_input, "bot": response})
    with open(st.session_state.user_file, "w") as f:
        json.dump(st.session_state.chat_history, f, indent=2)

    st.markdown(f"🤖 **Gemini:** {response}")
