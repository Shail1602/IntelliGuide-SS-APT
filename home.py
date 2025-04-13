import streamlit as st
#from snowflake.core import Root
from snowflake.cortex import Complete
from snowflake.snowpark.session import Session
import snowflake.connector
import json
import os
import shutil
import tempfile
import fitz
from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import MistralForCausalLM
import pydantic

print("🧠 App using pydantic version:", pydantic.__version__)


APP_NAME = "SS Intelliguide – AI-Powered Travel Intelligence"
st.set_page_config(APP_NAME, page_icon="🌏", layout="wide")
MODELS = ["mistral-large2", "llama3.1-70b", "llama3.1-8b"]


#embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", cache_folder=".cache")

faiss_db = FAISS.load_local("embeddings", embedding_model, allow_dangerous_deserialization=True)

# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# faiss_db = FAISS.load_local("embeddings", embedding_model, allow_dangerous_deserialization=True)

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
# root = Root(session)

TOPICS = ["All Locations", "Europe", "Australia", "New-Zealand", "Asia", "Africa", "South-America", "Antartica", "North-America"]
SESSION_STATE_FILE = "session_state.json"
STAGE_NAME = "@apt_pdf_db.public.apt"

def extract_location_keywords(query):
    # Define all known regions or locations here
    known_locations = ["india", "europe", "japan", "new zealand", "canada", "africa", "peru", "south australia", "vietnam", "kimberley"]
    return [loc.lower() for loc in known_locations if loc.lower() in query.lower()]


@st.cache_resource
def get_local_llm(model_id="sshleifer/tiny-gpt2"):
    try:
        print(f"📦 Attempting to load model from: {model_id}")
        
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=False,  # safer default
            use_fast=False
        )
        print("✅ Tokenizer loaded")

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=False,
            torch_dtype=torch.float32,  # safer than float16 for CPU
            device_map="cpu"  # force CPU for now to avoid GPU crash
        )
        print("✅ Model loaded")

        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        print("✅ Pipeline initialized")
        return tokenizer, pipe

    except Exception as e:
        print("❌ Exception during LLM loading:", str(e))
        raise


try:
    tokenizer, llm_pipe = get_local_llm()
except Exception as e:
    st.error(f"❌ Failed to load local LLM: {str(e)}")
    raise

def auto_summarize(prompt, max_words=1024):
    words = prompt.split()
    if len(words) <= max_words:
        return prompt

    summary_prompt = f"""
    [INST]
    Please summarize the following content to under {max_words} words while retaining key details and structure:
    
    {prompt}
    [/INST]
    """

    return complete(summary_prompt)



def complete(prompt: str) -> str:
    if not prompt or len(prompt.strip()) < 5:
        return "[⚠️ Empty or too short prompt]"

    try:
        result = llm_pipe(prompt, max_new_tokens=512, do_sample=True, temperature=0.7)

        if not result or not isinstance(result, list):
            return "[❌ No result from model]"
        
        output = result[0].get("generated_text", "").strip()
        if "[/INST]" in output:
            return output.split("[/INST]")[-1].strip()
        return output or "[❌ Model returned empty response]"

    except IndexError:
        return "[❌ IndexError: Model output index out of range]"
    except Exception as e:
        return f"[❌ Exception in model: {str(e)}]"


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
            desc_result = session.sql(f"DESC CORTEX SEARCH SERVICE {svc_name};").collect()
            if desc_result:
                try:
                    search_col = desc_result[0]["search_column"]
                except KeyError:
                    search_col = "chunk"
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
    return complete(prompt)


def build_prompt(question):
    context = query_faiss(question)
    return f"""
    [INST]
    You are SS IntelliGuide, a helpful AI assistant with access to APT PDF-based knowledge.
    Use the following context to answer user questions concisely and clearly.

    <context>{context}</context>
    <question>{question}</question>
    [/INST]
    Answer:
    """



# def query_cortex(query, columns=None, filter={}):
#    columns = columns or []
#    db, schema = session.get_current_database(), session.get_current_schema()
#    svc = root.databases[db].schemas[schema].cortex_search_services[st.session_state.selected_cortex_search_service]
    
#    search_col = next(
#        (s["search_column"] for s in st.session_state.service_metadata if s["name"] == st.session_state.selected_cortex_search_service),
#        "chunk"  # fallback
#    )

#    all_columns = list(set(columns + [search_col, "file_url", "relative_path"]))
#    results = svc.search(query, columns=all_columns, filter=filter, limit=st.session_state.num_retrieved_chunks).results

#    def make_context(i, r):
#        file = r.get("relative_path", "unknown")
      
#        chunk = next((v for k, v in r.items() if k.lower() == search_col.lower()), "[Missing chunk]")
#        return f"Context {i+1}: {file}:\n{chunk}"

#    context = "\n\n".join([make_context(i, r) for i, r in enumerate(results)])

#  if st.session_state.debug:
#       st.sidebar.write("🔎 Raw Cortex Result Preview:", results[0] if results else {})
#        st.sidebar.text_area("📄 Context Documents", context, height=300)

 #   return context 

def query_faiss(query: str) -> str:
    docs: list[Document] = faiss_db.similarity_search(query, k=st.session_state.num_retrieved_chunks)
    context = ""
    for i, doc in enumerate(docs):
        file = doc.metadata.get("source", "unknown")
        region = doc.metadata.get("region", "N/A")
        country = doc.metadata.get("country", "N/A")
        context += f"Context {i+1} | File: {file} | Region: {region} | Country: {country}\n{doc.page_content}\n\n"
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
                background-color: linear-gradient(to right, #edf6f9, #d0f0fd);
                color: #000000;
            }
            </style>
        """, unsafe_allow_html=True)


def init_config():
    with st.sidebar:
        st.toggle("🌓 Dark Mode", key="dark_mode", value=False)
        apply_theme()
        st.title("⚙️ Configuration")
        # st.radio("🔍 Use Search From", ["FAISS"], key="search_backend", horizontal=True)
        st.session_state.search_backend = "Cortex"
        if "model_name" not in st.session_state:
            st.session_state.model_name = "mistral-large2"
        #if "selected_cortex_search_service" not in st.session_state:
         #   service_names = [s["name"] for s in st.session_state.service_metadata]
          #  if service_names:
           #     st.session_state.selected_cortex_search_service = service_names[0]
        # st.session_state.service_metadata ="selected_cortex_search_service"
        #st.selectbox("Cortex Search Service", [s["name"] for s in st.session_state.service_metadata], key="selected_cortex_search_service")
        st.button("🧹 Clear Chat", key="clear_conversation")
        st.toggle("🐞 Debug Mode", key="debug", value=False)
        st.toggle("🕘 Use Chat History", key="use_chat_history", value=True)
        st.selectbox("📂 Filter by Topic", TOPICS, key="selected_topic")
        #st.image("https://raw.githubusercontent.com/Shail1602/Inellibot/main/SS%20Intellibot.png", caption="SS IntelliGuide", use_container_width=True)
        st.caption("Ask Smart. Get Smarter.")
        
        with st.expander("🧠 Advanced Options"):
            st.selectbox("Select Model", MODELS, key="model_name")
            st.slider("Context Chunks", 1, 50, 20, key="num_retrieved_chunks")
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

    extracted_text = []
    try:
        with fitz.open(tmp_path) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    extracted_text.append(text.strip())
    except Exception as e:
        st.error(f"Failed to extract text: {e}")
        return
    
    try:
        put_query = f"PUT file://{target_temp_path} {STAGE_NAME}  OVERWRITE=TRUE AUTO_COMPRESS=FALSE"
        cs.execute(put_query)
        cs.execute("USE DATABASE apt_pdf_db")
        cs.execute("USE SCHEMA public")
        cs.execute(f"ALTER STAGE apt_pdf_db.public.apt REFRESH")
        
        for idx, chunk in enumerate(extracted_text):
            chunk_sql = f"""
            INSERT INTO apt_pdf_db.public.docs_chunks_table
            SELECT
                relative_path,
                build_scoped_file_url({STAGE_NAME}, relative_path) AS file_url,
                CONCAT(SPLIT_PART(relative_path, '/', -1), ': ', func.chunk) AS chunk,
                'English' AS language
            FROM (
                SELECT relative_path
                FROM directory({STAGE_NAME})
                WHERE relative_path = ('{file_name}') 
            ),
            TABLE(apt_pdf_db.public.pdf_text_chunker(build_scoped_file_url({STAGE_NAME}, relative_path))) AS func;
            """
            cs.execute(chunk_sql)
            cs.execute("ALTER STAGE apt_pdf_db.public.apt REFRESH")
            cs.execute("""
            CREATE OR REPLACE CORTEX SEARCH SERVICE apt_pdf_db.public.apt_pdf
                ON chunk
                ATTRIBUTES language
                WAREHOUSE = apt_pdf_wh
                TARGET_LAG = '1 minute'
                AS (
                    SELECT
                        chunk,
                        relative_path,
                        file_url,
                        language
                    FROM apt_pdf_db.public.docs_chunks_table
                );
            """)
            st.success(f"✅ Uploaded and Reindexed the file : {file_name}")
            
            os.remove(tmp_path)
            if os.path.exists(target_temp_path):
                os.remove(target_temp_path)       
            if "uploaded_pdf" in st.session_state:
                del st.session_state["uploaded_pdf"]
            
    except Exception as e:
        st.error(f"Failed to upload/index: {e}")
    finally:
        cs.close()
        conn.close()

def upload_to_faiss_vectorstore(uploaded_file):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    file_name = uploaded_file.name.replace(" ", "_")
    folder_path = "pdfs"
    os.makedirs(folder_path, exist_ok=True)
    final_path = os.path.join(folder_path, file_name)
    shutil.copy(tmp_path, final_path)

    try:
        with pdfplumber.open(tmp_path) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=300)
        chunks = splitter.split_text(full_text)
        metadatas = [{"source": f"{folder_path}/{file_name}"}] * len(chunks)

        # Load existing FAISS DB
        try:
            db = FAISS.load_local("embeddings", embedding_model, allow_dangerous_deserialization=True)
            db.add_texts(chunks, metadatas)
        except Exception:
            db = FAISS.from_texts(chunks, embedding_model, metadatas=metadatas)

        db.save_local("embeddings")
        st.success(f"✅ Uploaded and indexed to FAISS: {file_name}")

        os.remove(tmp_path)
        if "uploaded_pdf" in st.session_state:
            del st.session_state["uploaded_pdf"]

    except Exception as e:
        st.error(f"Failed to process and index PDF: {e}")

def handle_uploaded_pdf():
    uploaded_file = st.sidebar.file_uploader("📥 Upload PDF", type=["pdf"], key="pdf_uploader")
    if uploaded_file is not None:
        st.session_state.uploaded_pdf = uploaded_file.name
        st.sidebar.success(f"Uploaded: {uploaded_file.name}")
        upload_to_faiss_vectorstore(uploaded_file)


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
    summary = complete( prompt)
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
    st.markdown("""
                <style>
                .hero {
                    background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e');  /* tropical beach background */
                    background-size: cover;
                    background-position: center;
                    padding: 30px;
                    border-radius: 16px;
                    color: white;
                    font-weight: bold;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                }
                </style>
                """, unsafe_allow_html=True)
    st.markdown("""
                <style>
                    html, body, .stApp {
                        font-family: 'Segoe UI', sans-serif;
                        font-size: 16px;
                        color: #111827;
                    }
                </style>
                """, unsafe_allow_html=True)
    st.markdown("""
                <style>
                    .stChatInput input {
                        background-color: #f0f8ff !important;
                        border: 1px solid #ccc !important;
                        border-radius: 10px !important;
                        padding: 10px !important;
                    }
                </style>
                """, unsafe_allow_html=True)
    st.markdown("""
                <style>
                @keyframes fadeIn {
                    0% { opacity: 0; transform: translateY(20px); }
                    100% { opacity: 1; transform: translateY(0); }
                }
                
                .stApp > div {
                    animation: fadeIn 0.7s ease-in-out;
                }
                </style>
                """, unsafe_allow_html=True)
    st.markdown("""
                <style>
                @keyframes pulse {
                  0% { transform: scale(1); }
                  50% { transform: scale(1.03); }
                  100% { transform: scale(1); }
                }
                </style>
                """, unsafe_allow_html=True)  
    st.markdown("""
            <style>
            .fab {
              position: fixed;
              bottom: 25px;
              right: 30px;
              background: #1f77b4;
              color: white;
              padding: 14px 18px;
              border-radius: 30px;
              font-weight: bold;
              box-shadow: 0 4px 10px rgba(0,0,0,0.25);
              z-index: 999;
              cursor: pointer;
              transition: background 0.3s;
            }
            .fab:hover {
              background: #155a8a;
            }
            </style>
            """, unsafe_allow_html=True)
    st.markdown("""
                <style>
                @keyframes slideDown {
                    from { opacity: 0; transform: translateY(-20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
        
                .header-animate {
                    animation: slideDown 0.7s ease-out;
                }
                </style>
            """, unsafe_allow_html=True)
    st.markdown("""
        <style>
        li:hover {
            color: #00bcd4 !important;
            cursor: pointer;
            transform: scale(1.02);
            transition: all 0.2s ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("""
            <style>
            button[kind="primary"] {
                background-color: #1f77b4 !important;
                color: white !important;
                font-weight: 600;
                font-size: 16px;
                border-radius: 8px;
            }
            button[kind="primary"]:hover {
                background-color: #155a8a !important;
            }
            </style>
            """, unsafe_allow_html=True)

def main():
    st.markdown("""
                <div class='header-animate' style='background: linear-gradient(to right, #e0f7fa, #ffffff);
                    padding: 25px 40px;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    margin-top: 0px;
                    margin-bottom: 5px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;'>
                    <div style='display: flex; align-items: center; gap: 18px;'>
                        <div style='
                            font-size: 46px;
                            line-height: 1;
                            margin-right: 10px;'>
                            🌏
                        </div>
                        <div style='line-height: 1.4;'>
                            <div style='font-size: 22px; font-weight: 700; color: #1f77b4;'>SS IntelliGuide</div>
                            <div style='font-size: 14.5px; color: #444;'>Explore the world with confidence — your AI travel companion for APT tours & adventures.</div>
                         </div>
                    </div>
                    <div>
                        <img src='https://raw.githubusercontent.com/Shail1602/Inellibot/main/dbr.jpg' alt='DB Results' style='height: 50px; border-radius: 8px; box-shadow: 0 0 6px rgba(0,0,0,0.1);'>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    

    add_custom_css()
    #if st.session_state.get("search_backend", "Cortex") == "Cortex":
    # init_service_metadata()
    handle_uploaded_pdf()
    init_config()
    init_messages()

    if len(st.session_state.messages) == 0:
        st.markdown("""
            <div style='
            position: relative;
            background-image: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1470&q=80");
            background-size: cover;
            background-position: center;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            margin-top: 5px;
            margin-bottom: 30px;'>
              <div style='
              background: rgba(0, 0, 0, 0.5);
              color: white;
              padding: 40px 30px;'>
            <h2 style='margin-bottom: 10px; animation: pulse 2s infinite;'>👋 Welcome to SS IntelliGuide!</h2>
            <p style='font-size: 16px;'>Ask any question based on our uploaded brochures:</p>
            <p style='font-size: 15px;'><strong>Brochures Available:</strong> Enchanting Japan, Vietnam & Cambodia, Ancient Kingdoms of Asia, European River Cruises, and more.</p>
            <p style='font-size: 16px; margin-top: 20px;'><strong>Try asking:</strong></p>
                <ul style='list-style: none; padding-left: 0; font-size: 15px; line-height: 1.8;'>
                  <li>🌏 What Signature Experiences are included in the Vietnam & Cambodia tour?</li>
                  <li>🚂 What are the scenic highlights of the Danube River Cruise?</li>
                  <li>🗾 What cities do we visit on the Enchanting Japan tour?</li>
                  <li>🏰 Are Freedom of Choice activities available in Prague?</li>
                  <li>📅 What is the itinerary for the Ancient Kingdoms of Japan and South Korea?</li>
                </ul>
              </div>
            </div>
        """, unsafe_allow_html=True) 

    for i, msg in enumerate(st.session_state.messages):
        css_class = "chat-left" if msg["role"] == "assistant" else "chat-right"
        st.markdown(f"<div class='{css_class}'>{msg['content']}</div>", unsafe_allow_html=True)
        if msg["role"] == "assistant":
            if st.button("⭐ Pin this response", key=f"pin_{i}"):
                st.session_state.pinned_messages.append(msg["content"])
                save_session_state()
                st.success("Pinned!")

    disable_chat = False
    if question := st.chat_input("💬 Ask your question...", disabled=disable_chat):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("SS IntelliGuide is typing..."):
            prompt = build_prompt(question.replace("'", ""))
            reply = complete( prompt)
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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2: 
        if st.button("📂 Browse PDF Brochures", use_container_width=True):
            st.switch_page("pages/PDF Viewer.py")

    st.markdown("""
            <div style='text-align: center; font-size: 13px; color: #888; margin-top: 40px;'>
              SS IntelliGuide • Designed by Shailesh & Saumya
            </div>
            """, unsafe_allow_html=True)
   
if __name__ == "__main__":
    main()
