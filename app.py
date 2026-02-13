import streamlit as st
import google.generativeai as genai
from supabase import create_client
import tempfile
import os
import time
import yt_dlp

# -------------------- CONFIG --------------------

st.set_page_config(
    page_title="Flash AI Intelligence",
    page_icon="⚡",
    layout="wide"
)

# Load Secrets Safely
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("❌ Secrets not found. Configure Streamlit secrets.")
    st.stop()

# Setup Clients
genai.configure(api_key=GEMINI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------- UI STYLE --------------------

st.markdown("""
<style>
.stApp { background-color: #0E1117; }

.stTextInput input {
    background-color: #262730 !important;
    color: white !important;
    border-radius: 10px;
    border: 1px solid #4A4A4A;
}

.stButton button {
    width: 100%;
    background: linear-gradient(90deg, #FF4B4B 0%, #FF914D 100%);
    color: white;
    border: none;
    padding: 0.6rem 1rem;
    border-radius: 12px;
    font-weight: bold;
    transition: 0.2s;
}
.stButton button:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 15px rgba(255,75,75,0.4);
}

section[data-testid="stSidebar"] {
    background-color: #161B22;
    border-right: 1px solid #30363D;
}

.result-box {
    background-color: #161B22;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #30363D;
}
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION --------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_credits" not in st.session_state:
    st.session_state.user_credits = 0

# -------------------- FUNCTIONS --------------------

def login_user(email):
    try:
        res = supabase.table("profile").select("*").eq("email", email).execute()
        if res.data:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_credits = res.data[0]["credits"]
            st.success("✅ Login Successful")
            time.sleep(1)
            st.rerun()
        else:
            st.error("⛔ Account not found")
    except Exception as e:
        st.error(f"Login Error: {e}")

def download_youtube(url):
    try:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": "%(id)s.%(ext)s",
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        raise Exception(f"YouTube Download Failed: {e}")

def analyze_video(video_path):
    try:
        file = genai.upload_file(path=video_path)

        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = genai.get_file(file.name)

        if file.state.name == "FAILED":
            raise Exception("AI Processing Failed")

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            [file, "ဒီဗီဒီယိုကို အသေးစိတ် ခွဲခြမ်းစိတ်ဖြာပြီး ရှင်းပြပါ"]
        )

        genai.delete_file(file.name)
        return response.text

    except Exception as e:
        raise Exception(f"Analysis Error: {e}")

# -------------------- LOGIN SCREEN --------------------

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("⚡ TEAM ALPHA ACCESS")
        email = st.text_input("Enter Email")
        if st.button("AUTHENTICATE"):
            if email:
                login_user(email)
            else:
                st.warning("Enter email first")

# -------------------- DASHBOARD --------------------

else:

    with st.sidebar:
        st.header("👤 AGENT PROFILE")
        st.info(st.session_state.user_email)
        st.metric("AVAILABLE CREDITS", st.session_state.user_credits)
        if st.button("LOGOUT"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    st.title("🎬 TACTICAL VIDEO INTEL")
    st.write("Upload video file or paste YouTube link.")

    tab1, tab2 = st.tabs(["📤 Upload", "🔗 YouTube"])

    video_path = None

    # -------- Upload --------
    with tab1:
        file = st.file_uploader("Upload Video", type=["mp4","mov","avi"])
        if file:
            st.video(file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(file.read())
                video_path = tmp.name

    # -------- YouTube --------
    with tab2:
        url = st.text_input("YouTube URL")
        if url and ("youtube.com" in url or "youtu.be" in url):
            st.video(url)
            if st.button("Download Video"):
                with st.spinner("📥 Downloading..."):
                    try:
                        video_path = download_youtube(url)
                        st.success("Downloaded Successfully")
                    except Exception as e:
                        st.error(e)

    # -------- Analyze --------
    if video_path:
        st.divider()
        if st.button("🚀 INITIATE ANALYSIS (-10 Credits)"):
            if st.session_state.user_credits < 10:
                st.error("⛔ Not enough credits")
            else:
                with st.spinner("🤖 AI is analyzing..."):
                    try:
                        result = analyze_video(video_path)

                        # Deduct Credits
                        new_credit = st.session_state.user_credits - 10
                        supabase.table("profile").update(
                            {"credits": new_credit}
                        ).eq(
                            "email", st.session_state.user_email
                        ).execute()

                        st.session_state.user_credits = new_credit

                        st.success("✅ Mission Complete")
                        st.markdown(
                            f'<div class="result-box">{result}</div>',
                            unsafe_allow_html=True
                        )

                    except Exception as e:
                        st.error(e)

                    finally:
                        if os.path.exists(video_path):
                            os.remove(video_path)
