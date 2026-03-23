import streamlit as st
import os
import sys
import json
from dotenv import load_dotenv

# App configuration
st.set_page_config(page_title="Mutual Fund Assistant", page_icon="🤖", layout="centered")

# Inject Custom CSS to match the Original UI
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Header (Hide Streamlit menu line) */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background-color: #010409 !important;
        border-right: 1px solid #30363d;
    }
    
    /* Sidebar Text */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #8b949e !important;
    }
    
    /* Assistant Chat Bubble */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: #21262d;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    /* User Chat Bubble */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #1f6feb;
        color: white !important;
        border-radius: 12px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {
        color: white !important;
    }
    
    /* Chat Input Area */
    [data-testid="stChatInput"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
    }
    
    /* Chat Input Text */
    [data-testid="stChatInput"] textarea {
        color: #c9d1d9 !important;
    }
    
    /* Suggestion Buttons */
    div.stButton > button {
        background-color: #161b22 !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
        font-weight: 500 !important;
    }
    div.stButton > button:hover {
        background-color: #30363d !important;
        color: #fff !important;
        border-color: #58a6ff !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Load environment variables (for local testing; Streamlit Cloud uses st.secrets)
load_dotenv()

# Override the environment variable if a Streamlit secret is present
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# Import RAG Core (Note: Ensure dependencies are installed and accessible)
try:
    from phase3_rag_core.rag_query import query_rag
    backend_loaded = True
except ImportError as e:
    st.error(f"Failed to load RAG backend: {e}")
    backend_loaded = False

# Sidebar: Status and Quick Suggestions
st.sidebar.title("Mutual Fund Assistant")
st.sidebar.markdown("---")

# Fetch status
try:
    with open("last_updated.json", "r") as f:
        data = json.load(f)
        st.sidebar.caption(f"**Last Data Update:**\n{data.get('last_updated', 'Unknown')}")
except Exception:
    st.sidebar.caption("**Last Data Update:** Unknown")

st.sidebar.markdown("---")

st.sidebar.markdown("### Suggested Queries")
suggestions = [
    "What is the expense ratio of Groww Liquid Fund Direct Growth?",
    "What is the risk profile of Groww Overnight Fund Direct Growth?",
    "Tell me the pros and cons of Groww Value Fund Direct Growth",
    "What is the category of Groww Large Cap Fund Direct Growth?",
    "What is the benchmark of Groww Multicap Fund Direct Growth?"
]

# When a suggestion is clicked, we can populate the chat input. 
# Streamlit doesn't natively allow updating the physical chat input easily, 
# but we can set a session state variable to trigger a run.
for suggestion in suggestions:
    if st.sidebar.button(suggestion, use_container_width=True, type="secondary"):
        st.session_state.submit_suggestion = suggestion

st.sidebar.markdown("---")
st.sidebar.info("This is an AI assistant to help you understand mutual funds based on scraped data.")

# Main Chat Interface
st.title("🤖 Mutual Fund Q&A")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to handle processing a query
def process_query(prompt: str):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate response
    with st.chat_message("assistant"):
        if not backend_loaded:
            response = "Backend failed to load. Please check logs."
            sources_html = ""
        else:
            with st.spinner("Thinking..."):
                try:
                    answer, sources = query_rag(prompt)
                    
                    if answer.startswith("ERROR:"):
                        response = f"**Error:** {answer}"
                        sources_html = ""
                    else:
                        response = answer
                        
                        # Format sources
                        sources_html = ""
                        if sources and isinstance(sources, list):
                            sources_html = "\n\n**Sources:**\n"
                            unique_sources = list(set(sources))
                            for source in unique_sources:
                                sources_html += f"- [{source.split('/')[-1]}]({source})\n"
                
                except Exception as e:
                    response = f"**Failed to retrieve answer:** {str(e)}"
                    sources_html = ""

        # Display answer
        full_response = response + sources_html
        st.markdown(full_response)
        
    # Add assistant message to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})


# Check if a suggestion was clicked
if "submit_suggestion" in st.session_state:
    prompt = st.session_state.submit_suggestion
    del st.session_state.submit_suggestion
    process_query(prompt)

# Accept user input
else:
    if prompt := st.chat_input("Ask me anything about MF schemes..."):
        process_query(prompt)
