import streamlit as st
from snowflake.core import Root
from snowflake.cortex import Complete
from snowflake.snowpark.session import Session
import json
import os
import fitz  # For extracting PDF text

APP_NAME = "SS IntelliBot"
st.set_page_config(APP_NAME, page_icon="🤖", layout="wide")
MODELS = ["mistral-large2", "llama3.1-70b", "llama3.1-8b"]

# Snowflake session config
connection_parameters = {
    "user": st.secrets["snowflake"]["user"],
    "password": st.secrets["snowflake"]["password"],
    "account": st.secrets["snowflake"]["account"],
    "warehouse": st.secrets["snowflake"]["warehouse"],
    "database": st.secrets["snowflake"]["database"],
    "schema": st.secrets["snowflake"]["schema"],
    "role": st.secrets["snowflake"].get("role", "ACCOUNTADMIN")
}

session = Session.builder.configs(connection_parameters).create()
root = Root(session)

TOPICS = ["All Topics", "Database Concepts", "AWS Framework", "Python for Beginners", "Azure", "PostgreSQL", "Kubernetes", "Pro Git", "OWASP"]
SESSION_STATE_FILE = "session_state.json"


def complete(model, prompt):
    return Complete(model, prompt, session=session).replace("$", "\$")


def save_session_state():
    with open(SESSION_STATE_FILE, "w") as f:
        json.dump({
            "messages": st.session_state.get("messages", []),
            "pinned_messages": st.session_state.get("pinned_messages", [])
        }, f)


def load_session_state():
    if os.path.exists(SESSION_STATE_FILE):
        with open(SESSION_STATE_FILE, "r") as f:
            state = json.load(f)
            st.session_state["messages"] = state.get("messages", [])
            st.session_state["pinned_messages"] = state.get("pinned_messages", [])


def init_messages():
    if "messages" not in st.session_state:
        load_session_state()
        st.session_state.setdefault("messages", [])
        st.session_state.setdefault("pinned_messages", [])
    if st.session_state.get("clear_conversation"):
        st.session_state.messages = []
        save_session_state()


def init_service_metadata():
    if "service_metadata" not in st.session_state:
        services = session.sql("SHOW CORTEX SEARCH SERVICES;").collect()
        metadata = []
        for s in services:
            svc_name = s["name"]
            search_col = session.sql(f"DESC CORTEX SEARCH SERVICE {svc_name};").collect()[0]["search_column"]
            metadata.append({"name": svc_name, "search_column": search_col})
        st.session_state.service_metadata = metadata


def get_chat_history():
    return st.session_state.messages[-st.session_state.num_chat_messages:-1]


def summarize_chat(chat_history, question):
    prompt = f"""
    [INST]
    Extend the user question using the chat history.
    <chat_history>{chat_history}</chat_history>
    <question>{question}</question>
    [/INST]
    """
    return complete(st.session_state.model_name, prompt)


def build_prompt(question):
    chat_history = get_chat_history() if st.session_state.use_chat_history else []
    chat_text = "\n".join([msg["content"] for msg in chat_history if msg["role"] == "user"])
    summary = summarize_chat(chat_text, question) if chat_history else question
    context = query_cortex(summary)
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


def query_cortex(query, columns=None, filter={}):
    if "local_pdf_context" in st.session_state:
        return st.session_state.local_pdf_context[:5000]

    columns = columns or []
    db, schema = session.get_current_database(), session.get_current_schema()
    svc = root.databases[db].schemas[schema].cortex_search_services[st.session_state.selected_cortex_search_service]
    search_col = next(s["search_column"] for s in st.session_state.service_metadata if s["name"] == st.session_state.selected_cortex_search_service)
    all_columns = list(set(columns + [search_col, "file_url", "relative_path"]))
    results = svc.search(query, columns=all_columns, filter=filter, limit=st.session_state.num_retrieved_chunks).results

    def make_context(i, r):
        file = r.get("relative_path", "unknown")
        chunk = r.get(search_col.lower(), "[Missing chunk]")
        return f"Context {i+1}: {file}:\n{chunk}"

    context = "\n\n".join([make_context(i, r) for i, r in enumerate(results)])

    if st.session_state.debug:
        st.sidebar.text_area("📄 Context Documents", context, height=300)
    return context


def handle_uploaded_pdf():
    uploaded_file = st.sidebar.file_uploader("📥 Upload PDF", type=["pdf"], key="pdf_uploader")
    if uploaded_file is not None:
        st.session_state.uploaded_pdf = uploaded_file.name
        st.sidebar.success(f"Uploaded: {uploaded_file.name}")

        # Extract text using PyMuPDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        pdf_text = ""
        for page in doc:
            pdf_text += page.get_text()
        st.session_state.local_pdf_context = pdf_text


def main():
    st.title("🤖 SS IntelliBot")
    init_messages()
    init_service_metadata()
    handle_uploaded_pdf()

    if "model_name" not in st.session_state:
        st.session_state.model_name = MODELS[0]
    if "num_retrieved_chunks" not in st.session_state:
        st.session_state.num_retrieved_chunks = 5
    if "num_chat_messages" not in st.session_state:
        st.session_state.num_chat_messages = 5
    if "debug" not in st.session_state:
        st.session_state.debug = False
    if "use_chat_history" not in st.session_state:
        st.session_state.use_chat_history = True

    st.sidebar.title("🛠 Configuration")
    st.sidebar.selectbox("Model", MODELS, key="model_name")
    st.sidebar.slider("Context Chunks", 1, 10, 5, key="num_retrieved_chunks")
    st.sidebar.slider("Chat History Messages", 1, 10, 5, key="num_chat_messages")

    if len(st.session_state.messages) == 0:
        st.markdown("""
        👋 Welcome to SS IntelliBot! Ask a question based on your uploaded PDF or indexed documents.
        Try asking:
        - What is the difference between RDS and Redshift?
        - How do I deploy a model in Kubernetes?
        - What are OWASP Top 10 vulnerabilities?
        """)

    for i, msg in enumerate(st.session_state.messages):
        role = "🧠" if msg["role"] == "assistant" else "🙋"
        st.markdown(f"**{role} {msg['role'].capitalize()}:** {msg['content']}")

    if question := st.chat_input("💬 Ask your question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("Thinking..."):
            prompt = build_prompt(question.replace("'", ""))
            reply = complete(st.session_state.model_name, prompt)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_session_state()
            st.markdown(f"**🧠 Assistant:** {reply}")

if __name__ == "__main__":
    main()
