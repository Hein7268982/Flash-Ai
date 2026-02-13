import streamlit as st
import google.generativeai as genai
from supabase import create_client
import tempfile
import os
import time
import yt_dlp

# --- 1. CONFIGURATION ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    st.error("Secrets not found! Please check Streamlit Cloud settings.")
    st.stop()

# Setup Clients
genai.configure(api_key=GEMINI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. TEAM ALPHA UI STYLING ---
st.set_page_config(page_title="Flash AI Intelligence", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Login & Containers */
    .stTextInput > div > div > input {
        background-color: #262730;
        color: white;
        border-radius: 10px;
        border: 1px solid #4A4A4A;
    }
    
    /* Buttons - Team Alpha Red/Orange Gradient */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF914D 100%);
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        border-radius: 12px;
        font-weight: bold;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* Metrics Card */
    div[data-testid="metric-container"] {
        background-color: #21262D;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #FF4B4B;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #E6EDF3 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def login_user(email):
    """Logs the user in via Supabase"""
    try:
        res = supabase.table("profile").select("*").eq("email", email).execute()
        if res.data:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_credits = res.data[0]['credits']
            st.rerun()
        else:
            st.error("⚠️ Access Denied: User account not found.")
    except Exception as e:
        st.error(f"Login Error: {e}")

def download_youtube_video(url):
    """Downloads YouTube video using yt-dlp"""
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': '%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
        return filename

def process_video_with_gemini(video_path, prompt="ဒီဗီဒီယိုမှာ ဘာတွေပါလဲ အသေးစိတ် ရှင်းပြပါ"):
    """Handles upload to Gemini and processing"""
    # Upload
    video_file = genai.upload_file(path=video_path)
    
    # Wait for processing
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed by Google AI.")

    # Generate Content
    model = genai.GenerativeModel('gemini-1.5-flash') # Stable Name
    response = model.generate_content([video_file, prompt])
    
    # Cleanup Gemini File
    genai.delete_file(video_file.name)
    return response.text

# --- 4. MAIN APP LOGIC ---

# Initialize Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- LOGIN SCREEN ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("⚡ TEAM ALPHA ACCESS")
        st.markdown("Please verify your identity.")
        email_input = st.text_input("Enter Email Address", placeholder="name@example.com")
        if st.button("AUTHENTICATE"):
            login_user(email_input)

else:
    # --- DASHBOARD UI ---
    
    # Sidebar Info
    with st.sidebar:
        st.header("👤 AGENT PROFILE")
        st.info(f"ID: {st.session_state.user_email}")
        
        # Credit Display
        st.markdown(f"""
            <div style="background-color: #21262D; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="margin:0; color: #8B949E; font-size: 14px;">AVAILABLE CREDITS</h3>
                <h1 style="margin:0; color: #FF4B4B; font-size: 32px;">{st.session_state.user_credits}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()

    # Main Content
    st.title("🎬 TACTICAL VIDEO INTEL")
    st.markdown("Upload footage or provide a YouTube link for AI analysis.")
    
    tab1, tab2 = st.tabs(["📤 UPLOAD FILE", "🔗 YOUTUBE LINK"])
    
    temp_video_path = None
    
    # TAB 1: FILE UPLOAD
    with tab1:
        uploaded_file = st.file_uploader("", type=['mp4', 'mov', 'avi'])
        if uploaded_file:
            st.video(uploaded_file)
            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
                tfile.write(uploaded_file.read())
                temp_video_path = tfile.name

    # TAB 2: YOUTUBE
    with tab2:
        yt_url = st.text_input("Paste YouTube URL here")
        if yt_url:
            if "youtube.com" in yt_url or "youtu.be" in yt_url:
                st.video(yt_url)
                if st.button("Process YouTube Video"):
                    with st.status("📥 Extracting YouTube Stream...", expanded=True) as status:
                        try:
                            temp_video_path = download_youtube_video(yt_url)
                            status.update(label="YouTube Downloaded!", state="complete", expanded=False)
                        except Exception as e:
                            st.error(f"Download Error: {e}")
            else:
                st.warning("Invalid YouTube URL")

    # EXECUTION BUTTON
    if temp_video_path:
        st.divider()
        if st.button("🚀 INITIATE ANALYSIS (-10 CREDITS)"):
            if st.session_state.user_credits >= 10:
                try:
                    # UI Spinner
                    with st.spinner("🤖 AI AGENT IS ANALYZING FOOTAGE..."):
                        
                        # Call Gemini Processing
                        result_text = process_video_with_gemini(temp_video_path)
                        
                        # Deduct Credits
                        new_credits = st.session_state.user_credits - 10
                        supabase.table("profile").update({"credits": new_credits}).eq("email", st.session_state.user_email).execute()
                        st.session_state.user_credits = new_credits
                        
                        # Display Result
                        st.success("✅ MISSION COMPLETE")
                        st.markdown(f"""
                        <div style="background-color: #161B22; padding: 20px; border-radius: 10px; border: 1px solid #30363D;">
                            {result_text}
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"❌ Mission Failed: {e}")
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_video_path):
                        os.remove(temp_video_path)
            else:
                st.error("⛔ INSUFFICIENT FUNDS: Please recharge your credits.")
