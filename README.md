# 🤖 SS IntelliBot

**SS IntelliBot** is an AI-powered PDF question-answering assistant built using **Streamlit**, **Snowflake Cortex**, and **Snowpark**. It enables users to upload PDF documents and ask context-aware questions, retrieving answers based solely on the content of those documents.

---

## 🚀 Features

- 🧠 **Contextual Q&A from PDFs**  
  Uses Cortex Search Services to retrieve relevant content from uploaded documents.
  
- 📁 **Multi-PDF Support**  
  Supports searching across multiple uploaded files with context snippets from each.

- 🌒 **Dark Mode Toggle**  
  Easily switch between light and dark themes for accessibility.

- 📌 **Pin Responses**  
  Save key responses across sessions.

- 💬 **Chat History**  
  Maintains history for more intelligent follow-up questions.

- 💾 **Session Persistence**  
  Saves and restores conversation state across reloads using local JSON storage.

- 📄 **Debug Mode**  
  Developers can inspect the raw retrieved context for transparency.

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/ss-intellibot.git
cd ss-intellibot

### Install dependencies
pip install -r requirements.txt

### Configure Secrets:
[snowflake]
user = "YOUR_USERNAME"
password = "YOUR_PASSWORD"
account = "YOUR_ACCOUNT"
warehouse = "YOUR_WAREHOUSE"
database = "YOUR_DATABASE"
schema = "YOUR_SCHEMA"
role = "ACCOUNTADMIN"


💡 Usage Guide
Upload PDF(s) using the sidebar.
Select a Cortex Search Service and preferred model.
Ask your question using the chat input.
The assistant will fetch relevant chunks from the uploaded PDFs and respond accordingly.
You can inspect retrieved content in debug mode.

🙋 Authors
Shailesh Rahul
Saumya Shruti

Crafted with ❤️ using Snowflake Cortex & Streamlit.

