import streamlit as st
import os
import sys
import json
from dotenv import load_dotenv

# App configuration
st.set_page_config(page_title="Mutual Fund Assistant", page_icon="groww_logo.ico", layout="centered")

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
st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; gap: 10px;">
        <img src="https://assets-netstorage.groww.in/web-assets/bson_storage_files/webtemp/app-logo.svg" height="25">
        <h2 style="margin: 0; padding: 0;">Mutual Fund Assistant</h2>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

# Fetch status
try:
    with open("last_updated.json", "r") as f:
        data = json.load(f)
        st.sidebar.caption(f"**Last Data Update:**\n{data.get('last_updated', 'Unknown')}")
except Exception:
    st.sidebar.caption("**Last Data Update:** Unknown")

# (Suggestions moved to main page)

st.sidebar.markdown("---")
st.sidebar.info("This is an AI assistant to help you understand mutual funds based on scraped data.")

# Main Chat Interface
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        <img src="https://assets-netstorage.groww.in/web-assets/bson_storage_files/webtemp/app-logo.svg" height="40">
        <h1 style="margin: 0; padding: 0;">Mutual Fund Q&A</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show suggestions on main page ONLY if chat history is empty
if len(st.session_state.messages) == 0:
    st.markdown("### Try asking one of these verified questions:")
    suggestions = [
        "What is the expense ratio of Groww Liquid Fund Direct Growth?",
        "What is the risk profile of Groww Overnight Fund Direct Growth?",
        "Tell me the pros and cons of Groww Value Fund Direct Growth",
        "What is the category of Groww Large Cap Fund Direct Growth?",
        "What is the benchmark of Groww Multicap Fund Direct Growth?"
    ]
    
    # Create columns for a grid layout or just stack them
    for suggestion in suggestions:
        if st.button(suggestion, use_container_width=True, type="secondary"):
            st.session_state.submit_suggestion = suggestion
            st.rerun()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar="https://assets-netstorage.groww.in/web-assets/bson_storage_files/webtemp/app-logo.svg"):
            st.markdown(message["content"])
    else:
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
    with st.chat_message("assistant", avatar="https://assets-netstorage.groww.in/web-assets/bson_storage_files/webtemp/app-logo.svg"):
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
