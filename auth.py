import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
import base64
import os
from dotenv import load_dotenv
load_dotenv()

# =========================
# 🔐 CONFIG (ADD YOUR KEYS)
# =========================
CLIENT_ID = st.secrets.get("CLIENT_ID", os.getenv("CLIENT_ID"))
CLIENT_SECRET = st.secrets.get("CLIENT_SECRET", os.getenv("CLIENT_SECRET"))

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v1/userinfo"

REDIRECT_URI = "https://talk2db-dhv2fdogneqrp2r5xy2fpg.streamlit.app"


# =========================
# 📸 IMAGE HELPER
# =========================
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()


# =========================
# 🔐 LOGIN FUNCTION
# =========================
def login():

    # session init
    if "user" not in st.session_state:
        st.session_state.user = None

    # already logged in
    if st.session_state.user:
        return True

    # OAuth setup
    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI
    )

    # =========================
    # 🔁 HANDLE CALLBACK (STEP 2)
    # =========================
    if "code" in st.query_params:

        try:
            code = st.query_params["code"]

            oauth.fetch_token(TOKEN_ENDPOINT, code=code)
            user_info = oauth.get(USERINFO_ENDPOINT).json()

            st.session_state.user = user_info["email"]

            # ✅ VERY IMPORTANT (fix invalid_grant)
            st.query_params.clear()

            st.success(f"Welcome {user_info['name']} 🎉")
            st.rerun()

        except Exception:
            # ❌ invalid code / reused code
            st.query_params.clear()
            st.warning("Session expired. Please login again.")
            st.rerun()

    # =========================
    # 🎨 UI (STEP 1)
    # =========================

    img = get_base64("image.png")

    st.markdown(f"""
    <style>
    .left-box {{
        padding: 40px;
    }}

    .title {{
        font-size: 30px;
        font-weight: 700;
    }}

    .subtitle {{
        color: gray;
        margin-bottom: 20px;
    }}

    .google-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #ddd;
        text-decoration: none;
        color: black;
        margin-top: 20px;
        font-weight: 500;
        background: white;
    }}

    .google-btn:hover {{
        background: #f7f7f7;
    }}

    .img-box {{
        background-image: url("data:image/png;base64,{img}");
        background-size: cover;
        background-position: center;
        height: 500px;
        border-radius: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    # LEFT SIDE
    with col1:
        st.markdown('<div class="left-box">', unsafe_allow_html=True)

        st.markdown('<div class="title">Welcome to Talk2DB</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Sign in with Google to continue</div>', unsafe_allow_html=True)

        authorization_url, _ = oauth.create_authorization_url(AUTHORIZATION_ENDPOINT)

        st.markdown(
            f'''
            <a href="{authorization_url}" class="google-btn">
                <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/google/google-original.svg" width="20">
                Sign in with Google
            </a>
            ''',
            unsafe_allow_html=True
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT SIDE IMAGE
    with col2:
        st.markdown('<div class="img-box"></div>', unsafe_allow_html=True)

    return False