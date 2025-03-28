import streamlit as st
from snowflake.core import Root
from snowflake.cortex import Complete
from snowflake.snowpark.session import Session
import snowflake.connector
import json
import os
import shutil
import tempfile

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
STAGE_NAME = "@cortex_search_tutorial_db.public.fomc"

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
        st.toggle("🌓 Dark Mode", key="dark_mode", value=False)
        apply_theme()
        st.title("⚙️ Configuration")
        st.selectbox("Cortex Search Service", [s["name"] for s in st.session_state.service_metadata], key="selected_cortex_search_service")
        st.button("🧹 Clear Chat", key="clear_conversation")
        st.toggle("🐞 Debug Mode", key="debug", value=False)
        st.toggle("🕘 Use Chat History", key="use_chat_history", value=True)
        st.selectbox("📂 Filter by Topic", TOPICS, key="selected_topic")
        st.image("https://raw.githubusercontent.com/Shail1602/Inellibot/main/SS%20Intellibot.png", caption="SS IntelliBot", use_container_width=True)
        st.caption("Ask Smart. Get Smarter.")
        
        with st.expander("🧠 Advanced Options"):
            st.selectbox("Select Model", MODELS, key="model_name")
            st.slider("Context Chunks", 1, 10, 5, key="num_retrieved_chunks")
            st.slider("Chat History Messages", 1, 10, 5, key="num_chat_messages")

def upload_to_snowflake_stage(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    conn = snowflake.connector.connect(**connection_parameters)
    cs = conn.cursor()
    file_name = os.path.basename(uploaded_file.name).replace(" ", "_")
    staged_path = f"{file_name}" 
    target_temp_path = os.path.join(tempfile.gettempdir(), file_name)
    shutil.copy(tmp_path, target_temp_path)
    staged_file_path = f"fomc/{file_name}"
    st.write("Uploading to:", f"{target_temp_path}")
    st.write("Uploading to:", f"{uploaded_file}")
    st.write("Uploading to:", f"{staged_file_path}")
    try:
        put_query = f"PUT file://{target_temp_path} {STAGE_NAME}/{staged_file_path}  OVERWRITE=TRUE AUTO_COMPRESS=FALSE"
        cs.execute(put_query)

        cs.execute("USE DATABASE cortex_search_tutorial_db")
        cs.execute("USE SCHEMA public")
        chunk_sql = f"""
        INSERT INTO cortex_search_tutorial_db.public.docs_chunks_table
        SELECT
            relative_path,
            build_scoped_file_url({STAGE_NAME}, relative_path) AS file_url,
            CONCAT(SPLIT_PART(relative_path, '/', -1), ': ', func.chunk) AS chunk,
            'English' AS language
        FROM (
            SELECT relative_path
            FROM directory({STAGE_NAME})
            WHERE relative_path ILIKE '{staged_file_path}%' 
        ),
        TABLE(cortex_search_tutorial_db.public.pdf_text_chunker(build_scoped_file_url({STAGE_NAME}, relative_path))) AS func;
        """
        cs.execute(chunk_sql)
        st.success(f"✅ Uploaded and reindexed: {file_name}")
    except Exception as e:
        st.error(f"Failed to upload/index: {e}")
    finally:
        cs.close()
        conn.close()

def handle_uploaded_pdf():
    uploaded_file = st.sidebar.file_uploader("📥 Upload PDF", type=["pdf"], key="pdf_uploader")
    if uploaded_file is not None:
        st.session_state.uploaded_pdf = uploaded_file.name
        st.sidebar.success(f"Uploaded: {uploaded_file.name}")
        upload_to_snowflake_stage(uploaded_file)


def generate_summary():
    full_history = st.session_state.messages
    formatted_history = ""
    for m in full_history:
        role = "User" if m["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {m['content']}\n"
    prompt = f"""
    [INST]
    You are an expert summarizer. Summarize the following chat conversation into 5-7 key bullet points that capture the main ideas and solutions shared by the assistant. Be concise, and do not repeat.
    <chat_history>
    {formatted_history}
    </chat_history>
    Your output should look like:
    - Point 1
    - Point 2
    ...
    [/INST]
    """
    summary = complete(st.session_state.model_name, prompt)
    return summary.strip()


def add_custom_css():
    chat_left_bg = "#f4f4f4" if not st.session_state.get("dark_mode") else "#1e1e1e"
    chat_right_bg = "#dcf4ea" if not st.session_state.get("dark_mode") else "#2e2e2e"
    text_color = "#000000" if not st.session_state.get("dark_mode") else "#fafafa"
    st.markdown(f"""
        <style>
        .chat-left {{
            background-color: {chat_left_bg};
            color: {text_color};
            padding: 14px;
            border-radius: 14px;
            margin: 12px 0;
            text-align: left;
            font-size: 15px;
            border-left: 4px solid #1f77b4;
        }}
        .chat-right {{
            background-color: {chat_right_bg};
            color: {text_color};
            padding: 14px;
            border-radius: 14px;
            margin: 12px 0;
            text-align: right;
            font-size: 15px;
            border-right: 4px solid #2a9d8f;
        }}
        </style>
    """, unsafe_allow_html=True)


def main():
    st.markdown("""<div style='background: linear-gradient(to right, #f2f2f2, #e0f7fa); padding: 25px 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; display: flex; align-items: center; justify-content: center; gap: 20px;'>
    <div style='display: flex; align-items: center; gap: 20px;'>
        <div style='background-color: #7b2cbf; color: white; font-size: 50px; font-weight: bold; width: 90px; height: 90px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(123, 44, 191, 0.7); animation: pulseGlow 2s infinite;'>SS</div>
        <div style='text-align: left;'>
            <div style='font-size: 32px; font-weight: bold; color: #1f77b4;'>SS IntelliBot</div>
            <div style='font-size: 16px; color: #333;'>Precision. Speed. Knowledge. — Your AI companion for data-driven excellence.</div>
            <div style='font-size: 13px; color: #555; font-style: italic; margin-top: 8px;'>👨‍💻 Crafted with expertise by <strong>Shailesh Rahul</strong> & <strong>Saumya Shruti</strong></div>
        </div>
    </div>
    <div>
        <img src='https://raw.githubusercontent.com/Shail1602/Inellibot/main/dbr.jpg' alt='DB Logo' style='height: 100px; border-radius: 8px;'>
        </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    add_custom_css()
    init_service_metadata()
    handle_uploaded_pdf()
    init_config()
    init_messages()

    if len(st.session_state.messages) == 0:
        st.markdown("""<div class='hero' style='margin-top: 10px;'>
            👋 Welcome to SS IntelliBot! Ask any question based on our uploaded documents:
            <br><br>
            <b>Topics Available:</b> Database Concepts, AWS Framework, Python for Beginners,
            Azure, PostgreSQL, Kubernetes, Pro Git, and OWASP.
            <br><br>
            Type your question below to get started!
            <br><br>
            <b>Try asking:</b>
            <ul style='list-style-type: none; padding: 0;'>
                <li>🔍 What is the difference between RDS and Redshift?</li>
                <li>🤖 How do I deploy a model in Kubernetes?</li>
                <li>🔐 What are OWASP Top 10 vulnerabilities?</li>
                <li>🐘 How to connect Python to PostgreSQL?</li>
                <li>☁️ What are key services in AWS Framework?</li>
            </ul>
        </div>""", unsafe_allow_html=True)

    for i, msg in enumerate(st.session_state.messages):
        css_class = "chat-left" if msg["role"] == "assistant" else "chat-right"
        st.markdown(f"<div class='{css_class}'>{msg['content']}</div>", unsafe_allow_html=True)
        if msg["role"] == "assistant":
            if st.button("⭐ Pin this response", key=f"pin_{i}"):
                st.session_state.pinned_messages.append(msg["content"])
                save_session_state()
                st.success("Pinned!")

    disable_chat = not st.session_state.service_metadata
    if question := st.chat_input("💬 Ask your question...", disabled=disable_chat):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("SS IntelliBot is typing..."):
            prompt = build_prompt(question.replace("'", ""))
            reply = complete(st.session_state.model_name, prompt)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_session_state()
            st.markdown(f"<div class='chat-left'>{reply}</div>", unsafe_allow_html=True)

    if st.session_state.messages:
        with st.expander("📌 Pinned Messages"):
            for i, msg in enumerate(st.session_state.pinned_messages):
                st.markdown(f"**Pinned {i+1}:** {msg}")

        with st.expander("📊 Generate Summary"):
            if st.button("Generate Insight Summary"):
                summary = generate_summary()
                st.markdown(f"**🔎 Summary:**\n\n{summary}", unsafe_allow_html=True)

        with st.expander("⬇️ Download Chat History"):
            full_chat = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages])
            st.download_button("Download .txt", full_chat, file_name="chat_history.txt")

        with st.expander("📢 Feedback"):
            st.radio("How helpful was the response?", ["👍 Excellent", "👌 Good", "👎 Needs Improvement"])

if __name__ == "__main__":
    main()
