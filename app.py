import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import tempfile
import time

# --- CONFIGURATION (Streamlit Secrets မှ ယူမည်) ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Setup Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Flash Recap | AI Intelligence", page_icon="⚡", layout="wide")

# --- DARK THEME STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; background-color: #007bff; color: white; border-radius: 8px; font-weight: bold; height: 3em; }
    .credit-box { padding: 15px; background: #161b22; border-radius: 12px; border: 1px solid #30363d; text-align: center; }
    .result-area { background-color: #1c2128; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'user' not in st.session_state: st.session_state['user'] = None
if 'user_credits' not in st.session_state: st.session_state['user_credits'] = 0

# --- DATABASE FUNCTIONS ---
def get_user_data(email):
    res = supabase.table("profile").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None

def update_credits(email, new_amount):
    supabase.table("profiles").update({"credits": new_amount}).eq("email", email).execute()

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", width=180)
    except:
        st.title("⚡ FLASH RECAP")
    
    st.markdown("---")
    if not st.session_state['user']:
        st.subheader("🔑 Login / Register")
        email = st.text_input("Email Address")
        if st.button("Enter App"):
            user_data = get_user_data(email)
            if user_data:
                st.session_state['user'] = email
                st.session_state['user_credits'] = user_data['credits']
                st.rerun()
            else:
                supabase.table("profiles").insert({"email": email, "credits": 0}).execute()
                st.success("အကောင့်ဖွင့်ပြီးပါပြီ။ ပြန်ဝင်ပေးပါ။")
    else:
        st.write(f"Logged in: **{st.session_state['user']}**")
        st.markdown(f"<div class='credit-box'>Available Credits<br><h3>{st.session_state['user_credits']}</h3></div>", unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state['user'] = None
            st.rerun()
    st.markdown("---")
    st.caption("Contact Admin for Credits: @TelegramID")

# --- MAIN CONTENT ---
st.title("🚀 Flash Recap: AI Video Analyzer")

if st.session_state['user']:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("📥 Upload Source")
        video_file = st.file_uploader("ဗီဒီယိုတင်ပါ (MP4, MOV)", type=['mp4', 'mov'])
        if video_file:
            st.video(video_file)
        
        if st.button("Generate AI Intelligence (-10 Credits)"):
            if st.session_state['user_credits'] >= 10:
                if video_file:
                    try:
                        with st.spinner("AI က ဗီဒီယိုကို လေ့လာနေပါတယ်..."):
                            tfile = tempfile.NamedTemporaryFile(delete=False)
                            tfile.write(video_file.read())
                            
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            video_part = genai.upload_file(path=tfile.name)
                            
                            while video_part.state.name == "PROCESSING":
                                time.sleep(2)
                                video_part = genai.get_file(video_part.name)
                            
                            prompt = "ဒီဗီဒီယိုကို မြန်မာလို အသေးစိတ်အကျဉ်းချုပ်ပေးပါ။ အဓိကအချက်တွေကို Timestamp (အချိန်) နဲ့တကွ ဖော်ပြပေးပါ။"
                            response = model.generate_content([prompt, video_part])
                            
                            # Credit နှုတ်ခြင်း
                            new_credit = st.session_state['user_credits'] - 10
                            update_credits(st.session_state['user'], new_credit)
                            st.session_state['user_credits'] = new_credit
                            st.session_state['result'] = response.text
                            st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                else: st.warning("ဗီဒီယို အရင်တင်ပေးပါ။")
            else: st.error("Credit မလုံလောက်ပါ။")

    with col2:
        st.subheader("💡 Analysis Result")
        if 'result' in st.session_state:
            st.markdown(f"<div class='result-area'>{st.session_state['result']}</div>", unsafe_allow_html=True)
        else:
            st.info("Analysis လုပ်ပြီးပါက ရလဒ်များကို ဤနေရာတွင် ပြသပါမည်။")
else:

    st.warning("အသုံးမပြုခင် Sidebar မှတစ်ဆင့် Login ဝင်ပေးပါ။")
