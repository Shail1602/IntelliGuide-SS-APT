import streamlit as st
from snowflake.core import Root
from snowflake.cortex import Complete
from snowflake.snowpark.session import Session

APP_NAME = "SS IntelliBot"
st.set_page_config(APP_NAME, page_icon="🤖", layout="wide")
MODELS = ["mistral-large2", "llama3.1-70b", "llama3.1-8b"]

# ✅ Establish Snowpark session (only one session)
connection_parameters = {
    "user": st.secrets["snowflake"]["user"],
    "password": st.secrets["snowflake"]["password"],
    "account": st.secrets["snowflake"]["account"],
    "warehouse": st.secrets["snowflake"]["warehouse"],
    "database": st.secrets["snowflake"]["database"],
    "schema": st.secrets["snowflake"]["schema"],
    "role": st.secrets["snowflake"]["role"]
}

session = Session.builder.configs(connection_parameters).create()
root = Root(session)

TOPICS = [
    "All Topics", "Database Concepts", "AWS Framework", "Python for Beginners",
    "Azure", "PostgreSQL", "Kubernetes", "Pro Git", "OWASP"
]

def init_messages():
    if "pinned_messages" not in st.session_state:
        st.session_state.pinned_messages = []
    if st.session_state.get("clear_conversation") or "messages" not in st.session_state:
        st.session_state.messages = []

def init_service_metadata():
    if "service_metadata" not in st.session_state:
        services = session.sql("SHOW CORTEX SEARCH SERVICES;").collect()
        metadata = []
        for s in services:
            svc_name = s["name"]
            search_col = session.sql(f"DESC CORTEX SEARCH SERVICE {svc_name};").collect()[0]["search_column"]
            metadata.append({"name": svc_name, "search_column": search_col})
        st.session_state.service_metadata = metadata

def handle_uploaded_pdf():
    uploaded_file = st.sidebar.file_uploader("📅 Upload PDF", type=["pdf"], key="pdf_uploader")
    if uploaded_file is not None:
        st.session_state.uploaded_pdf = uploaded_file.name
        st.sidebar.success(f"Uploaded: {uploaded_file.name}")

def apply_theme():
    if st.session_state.get("dark_mode"):
        st.markdown("""
            <style>
            body, .stApp {
                background-color: #0e1117;
                color: #fafafa;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            body, .stApp {
                background-color: #f2f2f2;
                color: #000000;
            }
            </style>
        """, unsafe_allow_html=True)

def init_config():
    with st.sidebar:
        st.toggle("🌃 Dark Mode", key="dark_mode", value=False)
        apply_theme()
        st.title("⚙️ Configuration")
        st.selectbox("Cortex Search Service", [s["name"] for s in st.session_state.service_metadata], key="selected_cortex_search_service")
        st.button("🧹 Clear Chat", key="clear_conversation")
        st.toggle("🚿 Debug Mode", key="debug", value=False)
        st.toggle("🕘 Use Chat History", key="use_chat_history", value=True)
        st.selectbox("📂 Filter by Topic", TOPICS, key="selected_topic")

        with st.expander("🧠 Advanced Options"):
            st.selectbox("Select Model", MODELS, key="model_name")
            st.slider("Context Chunks", 1, 10, 5, key="num_retrieved_chunks")
            st.slider("Chat History Messages", 1, 10, 5, key="num_chat_messages")

def complete(model, prompt):
    return Complete(model, prompt, session=session).replace("$", "\$")

def summarize_chat(chat_history, question):
    prompt = f"""
    [INST]
    Extend the user question using the chat history.
    <chat_history>{chat_history}</chat_history>
    <question>{question}</question>
    [/INST]
    """
    return complete(st.session_state.model_name, prompt)

def get_chat_history():
    return st.session_state.messages[-st.session_state.num_chat_messages:-1]

def query_cortex(query, columns=[], filter={}):
    db, schema = session.get_current_database(), session.get_current_schema()
    svc = root.databases[db].schemas[schema].cortex_search_services[st.session_state.selected_cortex_search_service]
    results = svc.search(query, columns=columns, filter=filter, limit=st.session_state.num_retrieved_chunks).results
    search_col = next(s["search_column"] for s in st.session_state.service_metadata if s["name"] == st.session_state.selected_cortex_search_service).lower()
    context = "\n\n".join([f"Context {i+1}: {r[search_col]}" for i, r in enumerate(results)])
    if st.session_state.debug:
        st.sidebar.text_area("📄 Context Documents", context, height=300)
    return context

def build_prompt(question):
    chat_history = get_chat_history() if st.session_state.use_chat_history else []
    chat_text = "\n".join([msg["content"] for msg in chat_history if msg["role"] == "user"])
    summary = summarize_chat(chat_text, question) if chat_history else question
    context = query_cortex(summary, columns=["chunk", "file_url", "relative_path"], filter={"@and": [{"@eq": {"language": "English"}}]})
    prompt = f"""
    [INST]
    You are SS IntelliBot, a helpful AI assistant with access to PDF-based knowledge.
    Use the provided <context> and <chat_history> to answer user questions.
    Respond clearly, briefly, and helpfully.

    <chat_history>{chat_text}</chat_history>
    <context>{context}</context>
    <question>{question}</question>
    [/INST]
    Answer:
    """
    return prompt

def main():
    init_service_metadata()
    init_config()
    init_messages()
    handle_uploaded_pdf()

    st.title("SS IntelliBot")

    if len(st.session_state.messages) == 0:
        st.info("Start by asking a question from the available topics.")

    for msg in st.session_state.messages:
        css_class = "chat-left" if msg["role"] == "assistant" else "chat-right"
        st.markdown(f"<div class='{css_class}'>{msg['content']}</div>", unsafe_allow_html=True)

    if question := st.chat_input("🔍 Ask your question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("SS IntelliBot is typing..."):
            prompt = build_prompt(question)
            reply = complete(st.session_state.model_name, prompt)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.markdown(f"<div class='chat-left'>{reply}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
