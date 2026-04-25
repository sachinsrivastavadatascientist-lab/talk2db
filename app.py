import streamlit as st
from auth import login

# =========================
# ⚙️ PAGE CONFIG (ONLY ONCE)
# =========================
st.set_page_config(page_title="Talk2DB", page_icon="image.png", layout="wide")

# =========================
# 🔐 LOGIN CHECK
# =========================
if not login():
    st.stop()

# =========================
# ✅ MAIN APP START
# =========================

import base64
from pathlib import Path
import sqlite3

from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from langchain_groq import ChatGroq

# ---------- HEADER ----------
def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_image_base64("image.png")

st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:center; gap:12px;">
        <img src="data:image/png;base64,{img_base64}" width="50">
        <h1 style="margin:0;">Talk2DB</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# 🔓 LOGOUT
# =========================
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.query_params.clear()   # 🔥 important fix
    st.rerun()

# =========================
# ⚙️ SIDEBAR CONFIG
# =========================
LOCALDB = "sqlite"
MySQL = "mysql"

db_choice = st.sidebar.radio(
    "Choose Database",
    ["SQLite (Student.db)", "MySQL"]
)

if db_choice == "MySQL":
    db_uri = MySQL
    mysql_host = st.sidebar.text_input("Host")
    mysql_user = st.sidebar.text_input("User")
    mysql_password = st.sidebar.text_input("Password", type="password")
    mysql_db = st.sidebar.text_input("Database")
else:
    db_uri = LOCALDB

api_key = st.sidebar.text_input("Groq API Key", type="password")

# =========================
# 🚀 DB CONFIG
# =========================
@st.cache_resource
def configure_db(db_uri, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None):

    if db_uri == LOCALDB:
        dbfilepath = (Path(__file__).parent / "student.db").absolute()
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))

    else:
        return SQLDatabase(create_engine(
            f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
        ))

# =========================
# 🚀 LLM + AGENT (ONLY ONCE)
# =========================
if api_key:

    # ✅ MYSQL VALIDATION (fix)
    if db_uri == MySQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.info("🔌 Please fill all MySQL details to connect")
            st.stop()

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        streaming=True
    )

    # DB connect
    if db_uri == LOCALDB:
        db = configure_db(db_uri)
    else:
        db = configure_db(db_uri, mysql_host, mysql_user, mysql_password, mysql_db)

    agent = create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type="zero-shot-react-description"
    )

    # =========================
    # 💬 CHAT UI
    # =========================
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "How can I help you?"}
        ]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # ✅ FIX: unique key
    user_query = st.chat_input(
        "Ask anything from your database...",
        key="chat_input_main"
    )

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            response = agent.invoke({"input": user_query})
            st.write(response["output"])

            st.session_state.messages.append({
                "role": "assistant",
                "content": response["output"]
            })