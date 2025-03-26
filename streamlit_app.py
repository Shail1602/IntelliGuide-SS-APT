import streamlit as st
from snowflake.core import Root
from snowflake.cortex import Complete
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.session import Session

APP_NAME = "SS IntelliBot"
st.set_page_config(APP_NAME, page_icon="🤖", layout="wide")
MODELS = ["mistral-large2", "llama3.1-70b", "llama3.1-8b"]

import snowflake.connector

# ✅ Establish Snowpark session (only one session)
connection_parameters = {
    "user": st.secrets["snowflake"]["user"],
    "password": st.secrets["snowflake"]["password"],
@@ -23,6 +21,11 @@
session = Session.builder.configs(connection_parameters).create()
root = Root(session)

TOPICS = [
    "All Topics", "Database Concepts", "AWS Framework", "Python for Beginners",
    "Azure", "PostgreSQL", "Kubernetes", "Pro Git", "OWASP"
]

def init_messages():
    if "pinned_messages" not in st.session_state:
        st.session_state.pinned_messages = []
@@ -39,28 +42,20 @@ def init_service_metadata():
            metadata.append({"name": svc_name, "search_column": search_col})
        st.session_state.service_metadata = metadata

TOPICS = ["All Topics", "Database Concepts", "AWS Framework", "Python for Beginners", "Azure", "PostgreSQL", "Kubernetes", "Pro Git", "OWASP"]

def handle_uploaded_pdf():
    uploaded_file = st.sidebar.file_uploader("📥 Upload PDF", type=["pdf"], key="pdf_uploader")
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
              @keyframes pulseGlow {
  0% { box-shadow: 0 0 8px rgba(123, 44, 191, 0.5); }
  50% { box-shadow: 0 0 20px rgba(123, 44, 191, 1); }
  100% { box-shadow: 0 0 8px rgba(123, 44, 191, 0.5); }
}
            </style>
        """, unsafe_allow_html=True)
    else:
@@ -70,23 +65,17 @@ def apply_theme():
                background-color: #f2f2f2;
                color: #000000;
            }
              @keyframes pulseGlow {
  0% { box-shadow: 0 0 8px rgba(123, 44, 191, 0.5); }
  50% { box-shadow: 0 0 20px rgba(123, 44, 191, 1); }
  100% { box-shadow: 0 0 8px rgba(123, 44, 191, 0.5); }
}
            </style>
        """, unsafe_allow_html=True)


def init_config():
    with st.sidebar:
        st.toggle("🌓 Dark Mode", key="dark_mode", value=False)
        st.toggle("🌃 Dark Mode", key="dark_mode", value=False)
        apply_theme()
        st.title("⚙️ Configuration")
        st.selectbox("Cortex Search Service", [s["name"] for s in st.session_state.service_metadata], key="selected_cortex_search_service")
        st.button("🧹 Clear Chat", key="clear_conversation")
        st.toggle("🐞 Debug Mode", key="debug", value=False)
        st.toggle("🚿 Debug Mode", key="debug", value=False)
        st.toggle("🕘 Use Chat History", key="use_chat_history", value=True)
        st.selectbox("📂 Filter by Topic", TOPICS, key="selected_topic")

@@ -95,24 +84,8 @@ def init_config():
            st.slider("Context Chunks", 1, 10, 5, key="num_retrieved_chunks")
            st.slider("Chat History Messages", 1, 10, 5, key="num_chat_messages")

        with st.expander("🧾 Session Info"):
            st.write(st.session_state)

def query_cortex(query, columns=[], filter={}):
    db, schema = session.get_current_database(), session.get_current_schema()
    svc = root.databases[db].schemas[schema].cortex_search_services[st.session_state.selected_cortex_search_service]
    results = svc.search(query, columns=columns, filter=filter, limit=st.session_state.num_retrieved_chunks).results
    search_col = next(s["search_column"] for s in st.session_state.service_metadata if s["name"] == st.session_state.selected_cortex_search_service).lower()
    context = "\n\n".join([f"Context {i+1}: {r[search_col]}" for i, r in enumerate(results)])
    if st.session_state.debug:
        st.sidebar.text_area("📄 Context Documents", context, height=300)
    return context

def get_chat_history():
    return st.session_state.messages[-st.session_state.num_chat_messages:-1]

def complete(model, prompt):
    return Complete(model, prompt).replace("$", "\$")
    return Complete(model, prompt, session=session).replace("$", "\$")

def summarize_chat(chat_history, question):
    prompt = f"""
@@ -124,6 +97,19 @@ def summarize_chat(chat_history, question):
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
@@ -143,174 +129,28 @@ def build_prompt(question):
    """
    return prompt

def add_custom_css():
    chat_left_bg = "#f4f4f4" if not st.session_state.get("dark_mode") else "#1e1e1e"
    chat_right_bg = "#dcf4ea" if not st.session_state.get("dark_mode") else "#2e2e2e"
    text_color = "#000000" if not st.session_state.get("dark_mode") else "#fafafa"
    st.markdown("""
        <style>
        .chat-left {
            background-color: {chat_left_bg};
            color: {text_color};
            padding: 14px;
            border-radius: 14px;
            margin: 12px 0;
            text-align: left;
            font-size: 15px;
            border-left: 4px solid #1f77b4;
            position: relative;
        }
        .chat-left::before {
            content: "🌐";
            position: absolute;
            left: -40px;
            top: 0;
            width: 30px;
            height: 30px;
        }
        .chat-right {
            background-color: {chat_right_bg};
            color: {text_color};
            padding: 14px;
            border-radius: 14px;
            margin: 12px 0;
            text-align: right;
            font-size: 15px;
            border-right: 4px solid #2a9d8f;
            position: relative;
        }
        .chat-right::after {
            content: "🧑‍💻";
            position: absolute;
            right: -30px;
            top: 0;
            font-size: 24px;
        }
        .hero {
    background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
    padding: 35px;
    border-radius: 16px;
    margin-top: 40px;
    text-align: center;
    font-size: 20px;
    font-weight: 600;
    color: #00332f;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 0.3s ease-in-out;
    animation: fadeIn 1s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
        </style>
    """, unsafe_allow_html=True)

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


def main():
    if st.session_state.get("pinned_messages"):
        with st.expander("📌 Pinned Messages"):
            for i, msg in enumerate(st.session_state.pinned_messages):
                st.markdown(f"**Pinned {i+1}:** {msg}")
    handle_uploaded_pdf()
    st.markdown("""
    <div style='background: linear-gradient(to right, #f2f2f2, #e0f7fa); padding: 25px 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; display: flex; align-items: center; justify-content: center; gap: 20px;'>
        <div style='background-color: #7b2cbf; color: white; font-size: 40px; font-weight: bold; width: 90px; height: 90px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(123, 44, 191, 0.7); animation: pulseGlow 2s infinite;'>SS</div>
        <div style='text-align: left;'>
            <div style='font-size: 32px; font-weight: bold; color: #1f77b4;'>SS IntelliBot</div>
            <div style='font-size: 16px; color: #333;'>Precision. Speed. Knowledge. — Your AI companion for data-driven excellence.</div>
            <div style='font-size: 13px; color: #555; font-style: italic; margin-top: 8px;'>👨‍💻 Crafted with expertise by <strong>Shailesh Rahul</strong> & <strong>Saumya Shruti</strong> 🚀</div>
        </div>
    </div>
""", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    add_custom_css()
    init_service_metadata()
    init_config()
    init_messages()
    handle_uploaded_pdf()

    st.title("SS IntelliBot")

    if len(st.session_state.messages) == 0:
      st.markdown("""
        <div class='hero' style='margin-top: 10px;'>
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
        </div>
        """, unsafe_allow_html=True)
        st.info("Start by asking a question from the available topics.")

    for msg in st.session_state.messages:
        css_class = "chat-left" if msg["role"] == "assistant" else "chat-right"
        st.markdown(f"<div class='{css_class}'>{msg['content']}</div>", unsafe_allow_html=True)

    disable_chat = not st.session_state.service_metadata
    if question := st.chat_input("💬 Ask your question...", disabled=disable_chat):
    if question := st.chat_input("🔍 Ask your question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.markdown(f"<div class='chat-right'>{question}</div>", unsafe_allow_html=True)

        with st.spinner("SS IntelliBot is typing..."):
            typing_placeholder = st.empty()
            typing_placeholder.markdown("<i>SS IntelliBot is typing...</i>", unsafe_allow_html=True)
            prompt = build_prompt(question.replace("'", ""))
            prompt = build_prompt(question)
            reply = complete(st.session_state.model_name, prompt)
            typing_placeholder.empty()
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.markdown(f"<div class='chat-left'>{reply}</div>", unsafe_allow_html=True)
            if st.button("⭐ Pin this response", key=f"pin_{len(st.session_state.messages)}"):
                st.session_state.pinned_messages.append(reply)
                st.success("Pinned!")

        st.session_state.messages.append({"role": "assistant", "content": reply})

    if len(st.session_state.messages) > 0:
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
