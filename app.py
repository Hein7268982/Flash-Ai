import streamlit as st
import google.generativeai as genai
from supabase import create_client
import tempfile
import os

# 1. Configuration (Streamlit Secrets မှ Keys များယူခြင်း)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Gemini & Supabase Setup
genai.configure(api_key=GEMINI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Page UI Styling
st.set_page_config(page_title="Flash AI Video Recap", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #FF4B4B; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 3. Login Session Management (ခနခန Login မဝင်ရအောင်)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_user(email):
    # Supabase မှာ user ရှိမရှိစစ်ပြီး Login သွင်းခြင်း
    res = supabase.table("profile").select("*").eq("email", email).execute()
    if res.data:
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.session_state.user_credits = res.data[0]['credits']
        st.rerun()
    else:
        st.error("User အကောင့် ရှာမတွေ့ပါ။")

# --- UI Logic ---
if not st.session_state.logged_in:
    st.title("⚡ Flash Recap Login")
    email_input = st.text_input("Email ရိုက်ထည့်ပါ")
    if st.button("Login"):
        login_user(email_input)
else:
    # Sidebar UI
    with st.sidebar:
        st.title("⚡ FLASH RECAP")
        st.write(f"📧 {st.session_state.user_email}")
        st.write(f"💰 Credits: {st.session_state.user_credits}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("🎬 Video Intelligence Recap")
    
    # Video Input Options
    tab1, tab2 = st.tabs(["📤 Upload Video", "🔗 YouTube Link"])
    
    video_file = None
    
    with tab1:
        uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင် ရွေးပါ", type=['mp4', 'mov', 'avi'])
        if uploaded_file:
            video_file = uploaded_file

    with tab2:
        youtube_url = st.text_input("YouTube URL ထည့်ပါ (Coming Soon - Currently use Upload)")

    if video_file:
        st.video(video_file)
        
        if st.button("Generate AI Intelligence (-10 Credits)"):
            if st.session_state.user_credits >= 10:
                try:
                    with st.spinner('AI က ဗီဒီယိုကို လေ့လာနေပါတယ်... ခဏစောင့်ပေးပါ...'):
                        # ဗီဒီယိုကို ယာယီသိမ်းခြင်း
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
                            tfile.write(video_file.read())
                            file_path = tfile.name

                        # Gemini သို့ Upload တင်ခြင်း
                        model = genai.GenerativeModel('gemini-1.5-flash') # Stable Name
                        video_part = genai.upload_file(path=file_path)

                        # Processing Wait
                        import time
                        while video_part.state.name == "PROCESSING":
                            time.sleep(2)
                            video_part = genai.get_file(video_part.name)

                        # AI Analysis
                        response = model.generate_content([video_part, "ဒီဗီဒီယိုကို အသေးစိတ် ရှင်းပြပေးပါ"])
                        
                        # Credits နှုတ်ခြင်း
                        new_credits = st.session_state.user_credits - 10
                        supabase.table("profile").update({"credits": new_credits}).eq("email", st.session_state.user_email).execute()
                        st.session_state.user_credits = new_credits
                        
                        st.success("Analysis ပြီးပါပြီ!")
                        st.write(response.text)
                        
                        os.remove(file_path) # File ပြန်ဖျက်ခြင်း

                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Credit မလုံလောက်ပါ။")
