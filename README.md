# 🤖 SS IntelliBot

**SS IntelliBot** is an AI-powered PDF question-answering assistant built using **Streamlit**, **Snowflake Cortex**, and **Snowpark**. It allows users to upload PDF documents and ask context-aware questions—getting answers based **solely** on the content of those documents.

---

## 👨‍💻 AUTHORS: Crafted With Passion by:  
**Shailesh Rahul** & **Saumya Shruti**


## 🚀 Features

| Feature                        | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| 🧠 **Contextual Q&A**         | Answers only from uploaded PDFs using Snowflake Cortex Search               |
| 📁 **Multi-PDF Support**       | Upload and query across multiple documents                                  |
| 🌒 **Dark Mode Toggle**        | Switch between light and dark themes                                        |
| 📌 **Pin Responses**           | Star key responses to view later, even across sessions                      |
| 💬 **Chat History**            | Keeps track of your interactions for better context                         |
| 💾 **Session Persistence**     | Saves messages and pins in a local `.json` file for reload continuity       |
| 🐞 **Debug Mode**              | Displays raw chunks fetched from your PDFs for transparency                 |



## 🛠️ Setup Instructions

1. Clone the Repository

```bash
git clone https://github.com/your-repo/ss-intellibot.git
cd ss-intellibot

2. Install required packages

pip install -r requirements.txt

3. Configure Snowflake credentials
Create a file at .streamlit/secrets.toml with the following content:

[snowflake]
user = "your_user"
password = "your_password"
account = "your_account"
warehouse = "your_warehouse"
database = "your_database"
schema = "your_schema"
role = "your_role"  # Optional, defaults to ACCOUNTADMIN

4. Run the application

streamlit run app.py

5.🧾 Project Structure
.
├── app.py                  # Main Streamlit app
├── session_state.json      # Persistent session storage
├── requirements.txt        # Python dependencies
└── .streamlit/
    └── secrets.toml        # Snowflake secrets config




