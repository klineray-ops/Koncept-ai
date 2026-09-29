
import streamlit as st
st.set_page_config(page_title="Koncept AI - Premium eBook Studio", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
import os, hashlib, traceback

# --- Fast helpers ---
def _safe_env(k):
    try: return st.secrets.get(k, "")
    except: return os.getenv(k, "")

@st.cache_resource(show_spinner=False)
def get_groq():
    try:
        from groq import Groq
        key = _safe_env("GROQ_API_KEY")
        return Groq(api_key=key) if key else None
    except: return None

@st.cache_resource(show_spinner=False)
def get_sb():
    url=_safe_env("SUPABASE_URL"); key=_safe_env("SUPABASE_KEY")
    if not url or not key: return None
    try:
        from supabase import create_client
        return create_client(url,key)
    except: return None

def _hash(pw): return hashlib.sha256(str(pw).encode()).hexdigest()

# --- UI ---
st.markdown('''<style>
.stApp{background:#0f172a !important;}
.stApp p, .stApp div, .stApp label, .stApp span, .stMarkdown {color:#ffffff !important;font-size:16px !important;line-height:1.6 !important;}
h1,h2,h3,h4 {color:#ffffff !important;font-weight:800 !important;}
.stTextInput>div>div>input, .stTextArea>div>div>textarea {background:#ffffff !important;color:#111111 !important;font-size:16px !important;}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {color:#64748b !important;}
.stButton>button{background:linear-gradient(90deg,#8b5cf6,#ec4899)!important;color:#ffffff!important;border:none!important;border-radius:12px!important;padding:.7rem 1.8rem!important;font-weight:700!important;font-size:16px!important;}
.stButton>button:hover{filter:brightness(1.1);}
/* Alerts - ensure readable dark text on light backgrounds */
div[data-testid="stAlert"] {font-size:15px !important;}
div[data-testid="stAlert"] * {color:#111111 !important;}
/* Tabs */
button[data-baseweb="tab"] {color:#ffffff !important;font-size:16px !important;font-weight:600 !important;}
button[data-baseweb="tab"][aria-selected="true"] {color:#fbbf24 !important;border-bottom-color:#fbbf24 !important;}
/* Sidebar */
section[data-testid="stSidebar"] {background:#1e293b !important;}
section[data-testid="stSidebar"] * {color:#ffffff !important;}
section[data-testid="stSidebar"] .stTextInput>div>div>input {color:#111111 !important;}
/* Captions and small text */
.stCaption, small {color:#e2e8f0 !important;font-size:14px !important;}
/* Radio and checkbox labels */
div[data-testid="stRadio"] label, div[data-testid="stCheckbox"] label {color:#ffffff !important;}
</style>''', unsafe_allow_html=True)
import base64
def _logo_html():
    try:
        with open("logo.png","rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' style='width:110px;height:110px;object-fit:contain;filter:drop-shadow(0 8px 24px rgba(139,92,246,0.5));'/>"
    except:
        return "<div style='font-size:64px'>📚</div>"
st.markdown(f"<div style='text-align:center;padding:1.5rem 1rem 0.5rem'>{_logo_html()}<h1 style='margin:0.5rem 0;color:#ffffff !important;font-size:3rem;font-weight:800;'>Koncept AI</h1><p style='color:#ffffff !important;font-size:1.2rem;font-weight:500;'>Concept to Publish, KDP, BrOwn, eBookSelf...</p></div>", unsafe_allow_html=True)

TIERS = {
    "Free": {"books":1,"chapters":3,"price":0,"price_label":"$0"},
    "Pro Std": {"books":10,"chapters":100,"price":9,"price_label":"$9/mo"},
    "Pro Dlx": {"books":30,"chapters":500,"price":19,"price_label":"$19/mo"},
    "Pro Max": {"books":100,"chapters":2000,"price":39,"price_label":"$39/mo"},
}

if "users" not in st.session_state: st.session_state["users"]={}
if "auth" not in st.session_state: st.session_state["auth"]={"logged_in":False,"email":None,"is_admin":False}
ADMIN_EMAIL=(_safe_env("ADMIN_EMAIL") or "admin@koncept.ai").lower()
ADMIN_HASH=_hash(_safe_env("ADMIN_PASSWORD") or "admin123")

def is_admin(): return st.session_state["auth"].get("is_admin",False)
def cur_user():
    a=st.session_state["auth"]
    if not a["logged_in"]: return None
    if a["is_admin"]: return {"name":"Admin","tier":"Pro Max","email":ADMIN_EMAIL}
    return st.session_state["users"].get(a["email"])

# Auth sidebar
with st.sidebar:
    st.markdown("### 🔐 Account")
    if st.session_state["auth"]["logged_in"]:
        u=cur_user(); st.success(f"Hi {u['name']} {'👑' if is_admin() else ''}")
        if st.button("Logout"):
            st.session_state["auth"]={"logged_in":False,"email":None,"is_admin":False}; st.rerun()
    else:
        mode=st.radio("Access",["Login","Register"],horizontal=True)
        em=st.text_input("Email").strip().lower(); pw=st.text_input("Password",type="password")
        if mode=="Register":
            nm=st.text_input("Name")
            if st.button("Create account"):
                if not em or not pw or not nm: st.warning("Fill all fields"); st.stop()
                if em in st.session_state["users"]: st.error("Already registered"); st.stop()
                # try supabase persist (lazy, non-blocking)
                sb=get_sb()
                if sb:
                    try: sb.table("users").upsert({"email":em,"name":nm,"pw_hash":_hash(pw),"tier":"Free","books_used":0}).execute()
                    except Exception as e: st.caption(f"DB note: {e}")
                st.session_state["users"][em]={"name":nm,"pw":_hash(pw),"tier":"Free","usage":{"books":0}}
                st.success("Registered! Login now.")
        else:
            if st.button("Login"):
                if em==ADMIN_EMAIL and _hash(pw)==ADMIN_HASH:
                    st.session_state["auth"]={"logged_in":True,"email":em,"is_admin":True}; st.rerun()
                elif em in st.session_state["users"] and st.session_state["users"][em]["pw"]==_hash(pw):
                    st.session_state["auth"]={"logged_in":True,"email":em,"is_admin":False}; st.rerun()
                else: st.error("Invalid credentials")

    st.markdown("---"); st.markdown("### 💳 Plan")
    cur_tier = cur_user()["tier"] if cur_user() else "Free"
    # admin can edit tiers
    if is_admin():
        st.markdown("👑 **Admin Panel**")
        st.write(f"Users: {len(st.session_state['users'])}")
        for email,u in list(st.session_state["users"].items()):
            c1,c2=st.columns([3,2])
            c1.write(f"{u['name']} ({email}) {u['usage']['books']}b")
            nt=c2.selectbox("Tier",list(TIERS.keys()),index=list(TIERS.keys()).index(u["tier"]),key=f"t_{email}")
            if nt!=u["tier"]:
                st.session_state["users"][email]["tier"]=nt; st.rerun()
    else:
        cfg=TIERS.get(cur_tier,TIERS["Free"])
        st.write(f"**{cur_tier}** {cfg['price_label']} — {cfg['books']} books")
        st.progress(min(1.0,(cur_user()["usage"]["books"] if cur_user() and "usage" in cur_user() else 0)/cfg["books"]) if cur_user() else 0)
        sl=_safe_env("STRIPE_LINK") or "https://buy.stripe.com/your-link"
        st.link_button(f"Upgrade {cfg['price_label']}",sl)

# Main tabs - heavy libs loaded ONLY inside actions
tab1,tab2=st.tabs(["✍️ Writer","📦 Export"])
with tab1:
    title=st.text_input("Book title")
    prompt=st.text_area("Prompt / outline")
    if st.button("Generate eBook",type="primary"):
        if not title.strip() or not prompt.strip(): st.warning("Enter title and prompt"); st.stop()
        # check limit (admin bypass)
        if not is_admin():
            u=cur_user()
            if not u: st.warning("Please Register/Login first"); st.stop()
            lim=TIERS[u["tier"]]["books"]
            if u["usage"]["books"]>=lim: st.error(f"Limit reached ({lim} books on {u['tier']}). Please upgrade."); st.stop()
        client=get_groq()
        if not client: st.error("Add GROQ_API_KEY in Secrets"); st.stop()
        with st.spinner("Writing... (AI loading on demand)"):
            try:
                r=client.chat.completions.create(model="llama-3.1-8b-instant",messages=[{"role":"user","content":f"Write chapter outline for '{title}': {prompt}"}],max_tokens=800)
                out=r.choices[0].message.content
                st.session_state["last_book"]=out
                st.success("Done!"); st.write(out)
                if not is_admin():
                    em=st.session_state["auth"]["email"]; st.session_state["users"][em]["usage"]["books"]+=1
            except Exception as e:
                st.error(f"AI unavailable: {e}")

with tab2:
    content=st.session_state.get("last_book","")
    st.text_area("Preview",content,height=200)
    c1,c2=st.columns(2)
    if c1.button("Export PDF"):
        if not content: st.warning("Generate first"); st.stop()
        with st.spinner("Building PDF..."):
            try:
                from fpdf import FPDF
                pdf=FPDF(); pdf.add_page(); pdf.set_font("Arial",size=12)
                for line in content.split("\n"): pdf.multi_cell(0,10,line)
                pdf.output("/tmp/book.pdf")
                with open("/tmp/book.pdf","rb") as f: st.download_button("Download PDF",f,"book.pdf")
            except Exception as e: st.error(f"PDF failed: {e}")
    if c2.button("Export DOCX"):
        if not content: st.warning("Generate first"); st.stop()
        with st.spinner("Building DOCX..."):
            try:
                from docx import Document
                doc=Document(); doc.add_paragraph(content); doc.save("/tmp/book.docx")
                with open("/tmp/book.docx","rb") as f: st.download_button("Download DOCX",f,"book.docx")
            except ImportError: st.error("Add python-docx to requirements.txt")
            except Exception as e: st.error(f"DOCX failed: {e}")

st.caption("⚡ Fast boot: heavy libraries load only when needed. If spinner hangs >2 min, reboot via Manage app → Reboot.")

