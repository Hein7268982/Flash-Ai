import streamlit as st
import google.generativeai as genai
from supabase import create_client
import streamlit_authenticator as stauth
import tempfile
import os
import time
import yt_dlp
import hashlib

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Flash AI",
    page_icon="⚡",
    layout="wide"
)

# ---------------- LOAD SECRETS ----------------

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    COOKIE_PASSWORD = st.secrets["COOKIE_PASSWORD"]
except:
    st.error("❌ Missing Streamlit Secrets")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- UI STYLE (TEAM ALPHA PREMIUM) ----------------

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #0E1117 0%, #111827 100%);
}

h1, h2, h3 {
    color: #E6EDF3;
}

.stButton button {
    background: linear-gradient(90deg, #FF4B4B 0%, #FF914D 100%);
    color: white;
    border-radius: 12px;
    border: none;
    font-weight: bold;
    transition: 0.3s;
}

.stButton button:hover {
    transform: scale(1.03);
    box-shadow: 0 4px 15px rgba(255,75,75,0.4);
}

.stTextInput input, .stSelectbox div {
    background-color: #262730 !important;
    color: white !important;
    border-radius: 8px;
}

section[data-testid="stSidebar"] {
    background-color: #161B22;
}

.result-box {
    background: #161B22;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #30363D;
}

</style>
""", unsafe_allow_html=True)

# ---------------- FETCH USERS FROM SUPABASE ----------------

def fetch_users():
    try:
        res = supabase.table("profile").select("*").execute()
        users = {}
        for u in res.data:
            users[u["email"]] = {
                "name": u["email"],
                "password": u["password"]  # must be hashed
            }
        return users
    except:
        return {}

credentials = {"usernames": fetch_users()}

authenticator = stauth.Authenticate(
    credentials,
    "flash_ai_cookie",
    COOKIE_PASSWORD,
    cookie_expiry_days=7
)

name, authentication_status, username = authenticator.login("Login", "main")

# ---------------- LOGIN STATES ----------------

if authentication_status is False:
    st.error("Invalid Credentials")
elif authentication_status is None:
    st.warning("Enter Email & Password")

# ---------------- MAIN DASHBOARD ----------------

if authentication_status:

    user_data = supabase.table("profile").select("*").eq("email", username).execute()
    credits = user_data.data[0]["credits"]

    with st.sidebar:
        st.title("⚡ Flash AI")
        st.metric("Available Credits", credits)
        authenticator.logout("Logout")

    st.title("🎬 Flash AI Tactical Video Intelligence")

    # ---------- OPTIONS ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        mode = st.selectbox(
            "Analysis Mode",
            ["Detailed Report", "Short Summary", "Threat Detection"]
        )

    with col2:
        language = st.selectbox(
            "Language",
            ["Burmese", "English"]
        )

    with col3:
        creativity = st.slider("Creativity", 0.0, 1.0, 0.5)

    custom_prompt = st.text_area("Custom Instruction (Optional)")

    st.divider()

    tab1, tab2 = st.tabs(["📤 Upload Video", "🔗 YouTube"])

    video_path = None

    # -------- UPLOAD --------
    with tab1:
        file = st.file_uploader("Upload Video", type=["mp4","mov","avi"])
        if file:
            st.video(file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(file.read())
                video_path = tmp.name

    # -------- YOUTUBE --------
    with tab2:
        url = st.text_input("YouTube URL")
        if url and ("youtube.com" in url or "youtu.be" in url):
            st.video(url)
            if st.button("Download Video"):
                with st.spinner("Downloading..."):
                    try:
                        ydl_opts = {
                            "format": "best[ext=mp4]/best",
                            "outtmpl": "%(id)s.%(ext)s",
                            "quiet": True
                        }
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            video_path = ydl.prepare_filename(info)
                        st.success("Download Complete")
                    except Exception as e:
                        st.error(e)

    # -------- ANALYZE --------
    if video_path:
        st.divider()
        if st.button("🚀 Start Analysis (-10 Credits)"):

            if credits < 10:
                st.error("Not enough credits")
            else:
                with st.spinner("AI Processing..."):
                    try:
                        file = genai.upload_file(path=video_path)

                        while file.state.name == "PROCESSING":
                            time.sleep(2)
                            file = genai.get_file(file.name)

                        model = genai.GenerativeModel("gemini-1.5-flash")

                        prompt = f"""
                        Mode: {mode}
                        Language: {language}
                        {custom_prompt}
                        """

                        response = model.generate_content(
                            [file, prompt],
                            generation_config={"temperature": creativity}
                        )

                        genai.delete_file(file.name)

                        new_credit = credits - 10
                        supabase.table("profile").update(
                            {"credits": new_credit}
                        ).eq("email", username).execute()

                        st.success("Analysis Complete")
                        st.markdown(
                            f'<div class="result-box">{response.text}</div>',
                            unsafe_allow_html=True
                        )

                    except Exception as e:
                        st.error(e)

                    finally:
                        if os.path.exists(video_path):
                            os.remove(video_path)
