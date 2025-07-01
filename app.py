import streamlit as st
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langsmith import traceable

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# Check if everything is set
if not all([GOOGLE_API_KEY, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT]):
    st.error("Missing environment variables.")
    st.stop()

# LangSmith setup
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
os.environ["LANGCHAIN_ENDPOINT"] = LANGCHAIN_ENDPOINT
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Streamlit UI
st.set_page_config(page_title="Gemini ChatBot", page_icon="🤖")
st.title("💬 Gemini + LangChain + LangSmith")

# Setup LLM and memory
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)

# Store memory in session so it persists
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory()

# Create conversation chain with memory
conversation = ConversationChain(
    llm=llm,
    memory=st.session_state.memory,
    verbose=False
)

# LangSmith tracing
@traceable(name="Gemini Chat Session")
def chat_with_gemini(user_input):
    return conversation.predict(input=user_input)

# Chat input
user_input = st.text_input("🗣️ Ask Gemini something:")

if user_input:
    with st.spinner("Gemini is thinking..."):
        response = chat_with_gemini(user_input)
        st.markdown(f"🤖 **Gemini:** {response}")
