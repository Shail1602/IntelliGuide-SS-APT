import streamlit as st
from snowflake.core import Root
from snowflake.cortex import Complete
from snowflake.snowpark.session import Session
import json
import os

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

    if not context.strip() or all("[Missing chunk]" in c for c in context.split("\n\n")):
        return f"""
        [INST]
        The user asked: \"{question}\" but no relevant context was found in the uploaded PDF documents.
        Please respond: \"I'm sorry, the provided context does not contain any information about '{question}'.\"
        [/INST]
        """

    return f"""
    [INST]
    You are SS IntelliBot, a helpful AI assistant with access to PDF-based knowledge.
    Only answer the user's question using the <context> and <chat_history> provided.
    If you cannot find relevant context, say so clearly.

    <chat_history>{chat_text}</chat_history>
    <context>{context}</context>
    <question>{question}</question>
    [/INST]
    Answer:
    """


def query_cortex(query, columns=None, filter={}):
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
