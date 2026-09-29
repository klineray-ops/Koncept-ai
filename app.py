import streamlit as st
st.set_page_config(page_title="Koncept AI - Premium eBook Studio", page_icon="📚", layout="centered", initial_sidebar_state="collapsed")
import os, hashlib, traceback, datetime

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

def _hash(pw): return hashlib.sha256(str(pw).encode()).hexdigest()

# --- UI CSS ---
st.markdown("""<style>
.stApp{background:#0f172a !important;}
.stApp p, .stApp div, .stApp label, .stApp span, .stMarkdown {color:#ffffff !important;font-size:16px !important;line-height:1.6 !important;}
h1,h2,h3,h4 {color:#ffffff !important;font-weight:800 !important;}
.stTextInput>div>div>input, .stTextArea>div>div>textarea {background:#ffffff !important;color:#111111 !important;font-size:16px !important;}
.stButton>button{background:linear-gradient(90deg,#8b5cf6,#ec4899)!important;color:#ffffff!important;border:none!important;border-radius:12px!important;padding:.7rem 1.8rem!important;font-weight:700!important;font-size:16px!important;}
.stButton>button:hover{filter:brightness(1.1);}
div[data-testid="stAlert"] * {color:#111111 !important;}
button[data-baseweb="tab"] {color:#ffffff !important;font-size:15px !important;font-weight:600 !important;}
button[data-baseweb="tab"][aria-selected="true"] {color:#fbbf24 !important;border-bottom-color:#fbbf24 !important;}
section[data-testid="stSidebar"] {background:#1e293b !important;}
section[data-testid="stSidebar"] * {color:#ffffff !important;}
section[data-testid="stSidebar"] .stTextInput>div>div>input {color:#111111 !important;}
.stCaption, small {color:#e2e8f0 !important;font-size:14px !important;}
.brand-title {font-size:4.5rem !important;font-weight:900 !important;letter-spacing:-1px;margin:0;color:#ffffff !important;}
@media (max-width: 768px) {
  .brand-title {font-size:2.8rem !important;}
  button[data-baseweb="tab"] {font-size:12px !important;white-space:nowrap;padding:8px 4px !important;}
  .stButton>button {padding:.6rem 1rem !important;font-size:15px !important;}
}
</style>""", unsafe_allow_html=True)

import base64
def _logo_html():
    try:
        with open("logo.png","rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' style='width:120px;height:120px;object-fit:contain;'/>"
    except:
        return "<div style='font-size:64px'>📚</div>"
st.markdown(f"<div style='text-align:center;padding:1rem'><div style='font-size:4rem;font-weight:900;color:#fff;letter-spacing:2px;'>K</div>{_logo_html()}<div class='brand-title'>KONCEPT</div><div style='font-size:1.6rem;color:#fbbf24;font-weight:700;letter-spacing:6px;'>AI STUDIO</div><p style='color:#cbd5e1;font-size:1.1rem;'>Concept to Publish • KDP • eBookSelf</p></div>", unsafe_allow_html=True)

TIERS = {
    "Free": {"books":3,"chapters":9,"price":0,"price_label":"$0"},
    "Pro Std": {"books":10,"chapters":100,"price":3.99,"price_label":"$3.99/mo"},
    "Pro Dlx": {"books":30,"chapters":500,"price":5.99,"price_label":"$5.99/mo"},
    "Pro Max": {"books":99,"chapters":2000,"price":9.99,"price_label":"$9.99/mo"},
}

if "users" not in st.session_state: st.session_state["users"]={}
if "auth" not in st.session_state: st.session_state["auth"]={"logged_in":False,"email":None,"is_admin":False}
if "tickets" not in st.session_state: st.session_state["tickets"]=[]
if "chat_hist" not in st.session_state: st.session_state["chat_hist"]=[]
ADMIN_EMAIL=(_safe_env("ADMIN_EMAIL") or "admin@koncept.ai").lower()
ADMIN_HASH=_hash(_safe_env("ADMIN_PASSWORD") or "admin123")

def is_admin(): return st.session_state["auth"].get("is_admin",False)
def cur_user():
    a=st.session_state["auth"]
    if not a["logged_in"]: return None
    if a["is_admin"]: return {"name":"Admin","tier":"Pro Max","email":ADMIN_EMAIL}
    return st.session_state["users"].get(a["email"])

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### 🔐 Account")
    if st.session_state["auth"]["logged_in"]:
        u=cur_user(); st.success(f"Hi {u['name']} {'👑' if is_admin() else ''}")
        if st.button("Logout",use_container_width=True):
            st.session_state["auth"]={"logged_in":False,"email":None,"is_admin":False}; st.rerun()
    else:
        mode=st.radio("Access",["Login","Register"],horizontal=True)
        em=st.text_input("Email",key="sb_em").strip().lower(); pw=st.text_input("Password",type="password",key="sb_pw")
        if mode=="Register":
            nm=st.text_input("Name",key="sb_nm")
            if st.button("Create account",use_container_width=True):
                if not em or not pw or not nm: st.warning("Fill all fields"); st.stop()
                if em in st.session_state["users"]: st.error("Already registered"); st.stop()
                st.session_state["users"][em]={"name":nm,"pw":_hash(pw),"tier":"Free","usage":{"books":0}}
                st.success("Registered! Now Login.")
        else:
            if st.button("Login",use_container_width=True):
                if em==ADMIN_EMAIL and _hash(pw)==ADMIN_HASH:
                    st.session_state["auth"]={"logged_in":True,"email":em,"is_admin":True}; st.rerun()
                elif em in st.session_state["users"] and st.session_state["users"][em]["pw"]==_hash(pw):
                    st.session_state["auth"]={"logged_in":True,"email":em,"is_admin":False}; st.rerun()
                else: st.error("Invalid credentials")

    st.markdown("---")
    st.markdown("### 💳 All Plans")
    for tname, cfg in TIERS.items():
        cur = cur_user()["tier"] if cur_user() else "Free"
        marker = " ✅" if tname==cur else ""
        st.write(f"**{tname}**{marker} — {cfg['price_label']} • {cfg['books']} books")
    st.markdown("---")
    st.markdown("### ⬆️ Upgrade")
    sl=_safe_env("STRIPE_LINK") or "https://buy.stripe.com/your-link"
    for tname, cfg in TIERS.items():
        if tname=="Free": continue
        st.link_button(f"Get {tname} — {cfg['price_label']}", sl, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📘 Help & Manual")
    if st.button("📖 Open User Manual",use_container_width=True):
        st.session_state["show_manual"]=True
    if st.session_state.get("show_manual"):
        try:
            st.image("manual_poster.png", use_container_width=True)
        except: st.info("📘 Koncept AI User Manual")
        st.markdown("**6 Steps:** 1.Writer → 2.Checker → 3.Designer → 4.Finishing → 5.Exports → 6.Downloads")
        st.markdown("**Tips:** Generate in Writer, check grammar in Checker, build PDF/DOCX in Exports, download in Downloads tab.")
        if st.button("Close Manual"): st.session_state["show_manual"]=False; st.rerun()

    st.markdown("---")
    st.markdown("### 🎫 Support Ticket")
    if st.button("📝 New Support Ticket",use_container_width=True):
        st.session_state["show_ticket"]=True
    if st.session_state.get("show_ticket"):
        t_sub=st.text_input("Subject",key="tk_sub")
        t_msg=st.text_area("Describe your issue",key="tk_msg")
        if st.button("Submit Ticket"):
            if t_sub and t_msg:
                st.session_state["tickets"].append({"sub":t_sub,"msg":t_msg,"email":st.session_state["auth"].get("email","guest"),"time":str(datetime.datetime.now())[:16],"status":"Open"})
                st.success("Ticket submitted! Admin will review."); st.session_state["show_ticket"]=False
            else: st.warning("Fill subject and message")
    if is_admin() and st.session_state["tickets"]:
        st.markdown("**🎫 Tickets (Admin):**")
        for i,tk in enumerate(st.session_state["tickets"]):
            st.write(f"{i+1}. [{tk['status']}] {tk['sub']} — {tk['email']}")
            st.caption(tk["msg"][:100])
            if st.button(f"Resolve #{i+1}",key=f"res_{i}"):
                st.session_state["tickets"][i]["status"]="Resolved"; st.rerun()

    if is_admin():
        st.markdown("---"); st.markdown("👑 **Admin Panel**")
        st.write(f"Users: {len(st.session_state['users'])}")
        for email,u in list(st.session_state["users"].items()):
            c1,c2=st.columns([3,2])
            c1.write(f"{u['name']} ({email})")
            nt=c2.selectbox("Tier",list(TIERS.keys()),index=list(TIERS.keys()).index(u["tier"]),key=f"t_{email}")
            if nt!=u["tier"]: st.session_state["users"][email]["tier"]=nt; st.rerun()

# ============ AI HELP CHATBOT ============
with st.expander("🤖 AI Help Assistant — ask anything about Koncept AI"):
    for m in st.session_state["chat_hist"]:
        st.write(f"**{'You' if m['r']=='user' else '🤖 AI'}:** {m['t']}")
    q=st.text_input("Ask a question...",key="ai_q")
    if st.button("Send"):
        if q.strip():
            st.session_state["chat_hist"].append({"r":"user","t":q})
            client=get_groq()
            if client:
                try:
                    r=client.chat.completions.create(model="llama-3.1-8b-instant",messages=[{"role":"system","content":"You are a helpful assistant for Koncept AI eBook Studio. Help users with plans, workflow, exports."},{"role":"user","content":q}],max_tokens=500)
                    ans=r.choices[0].message.content
                except Exception as e: ans=f"AI error: {e}"
            else:
                # offline FAQ fallback
                ql=q.lower()
                if "price" in ql or "plan" in ql: ans="Plans: Free (3 books $0), Pro Std (10 books $3.99/mo), Pro Dlx (30 books $5.99/mo), Pro Max (99 books $9.99/mo)."
                elif "pdf" in ql: ans="Go to 5.Exports → Build PDF, then 6.Downloads → Download PDF."
                elif "manual" in ql: ans="Click 📖 Open User Manual in the sidebar for the full guide."
                else: ans="I can help with plans, writer, exports, downloads. Ask me anything!"
            st.session_state["chat_hist"].append({"r":"ai","t":ans})
            st.rerun()

# ============ MAIN 6 TABS ============
tab1,tab2,tab3,tab4,tab5,tab6=st.tabs(["✍️ Writer","🔍 Checker","🎨 Design","✨ Finish","📦 Export","⬇️ Get"])

with tab1:
    st.markdown("### ✍️ Writer — Generate your eBook")
    title=st.text_input("Book title",key="w_title")
    prompt=st.text_area("Prompt / outline",key="w_prompt",height=120)
    c1,c2=st.columns(2)
    if c1.button("Generate eBook",type="primary",use_container_width=True):
        if not title.strip() or not prompt.strip(): st.warning("Enter title and prompt"); st.stop()
        if not is_admin():
            u=cur_user()
            if not u: st.warning("Please Register/Login first"); st.stop()
            lim=TIERS[u["tier"]]["books"]
            if u["usage"]["books"]>=lim: st.error(f"Limit reached ({lim} books on {u['tier']}). Please upgrade."); st.stop()
        client=get_groq()
        if not client: st.error("Add GROQ_API_KEY in Secrets"); st.stop()
        with st.spinner("Writing..."):
            try:
                r=client.chat.completions.create(model="llama-3.1-8b-instant",messages=[{"role":"user","content":f"Write engaging book content for '{title}': {prompt}"}],max_tokens=2000)
                st.session_state["last_book"]=r.choices[0].message.content
                st.session_state["book_title"]=title
                st.success("Done! Check the Checker tab →"); st.write(st.session_state["last_book"])
                if not is_admin():
                    em2=st.session_state["auth"]["email"]; st.session_state["users"][em2]["usage"]["books"]+=1
            except Exception as e: st.error(f"AI unavailable: {e}")
    if c2.button("Clear",use_container_width=True):
        st.session_state["last_book"]=""; st.rerun()

with tab2:
    st.markdown("### 🔍 Checker — Review & improve")
    content=st.session_state.get("last_book","")
    txt=st.text_area("Content to check",value=content,height=200,key="ck")
    if st.button("Check Grammar & Clarity",use_container_width=True):
        if not txt.strip(): st.warning("Generate in Writer first"); st.stop()
        client=get_groq()
        if not client: st.error("Add GROQ_API_KEY"); st.stop()
        with st.spinner("Checking..."):
            try:
                r=client.chat.completions.create(model="llama-3.1-8b-instant",messages=[{"role":"user","content":f"Check grammar and clarity, list top 5 issues:\n{txt[:4000]}"}],max_tokens=1200)
                st.session_state["checked"]=r.choices[0].message.content; st.success("Done!")
            except Exception as e: st.error(str(e))
    if st.session_state.get("checked"): st.info("Report:"); st.write(st.session_state["checked"])

with tab3:
    st.markdown("### 🎨 Designer — Cover ideas")
    bt=st.text_input("Cover title",value=st.session_state.get("book_title",""))
    sty=st.selectbox("Style",["Modern Minimal","Classic Premium","Bold Colorful","Elegant Serif"])
    if st.button("Generate Cover Concept",use_container_width=True):
        client=get_groq()
        if not client: st.warning("Add GROQ_API_KEY"); st.stop()
        with st.spinner("Designing..."):
            try:
                r=client.chat.completions.create(model="llama-3.1-8b-instant",messages=[{"role":"user","content":f"Suggest 3 cover concepts for '{bt}' style {sty}"}],max_tokens=800)
                st.session_state["cover"]=r.choices[0].message.content
            except Exception as e: st.error(str(e))
    if st.session_state.get("cover"): st.write(st.session_state["cover"])

with tab4:
    st.markdown("### ✨ Finishing — Format")
    fs=st.slider("Font size",10,16,12); ls=st.slider("Line spacing",8,20,12)
    tc=st.checkbox("Table of Contents",True); cp=st.checkbox("Copyright page",True)
    if st.button("Apply Finishing",use_container_width=True):
        st.session_state["fmt"]={"fs":fs,"ls":ls,"tc":tc,"cp":cp}; st.success("Saved!")

with tab5:
    st.markdown("### 📦 Exports — Build files")
    content=st.session_state.get("last_book","")
    fmt=st.session_state.get("fmt",{"fs":12,"ls":12,"tc":True,"cp":True})
    st.text_area("Preview",content,height=150,key="ex_pv")
    e1,e2=st.columns(2)
    if e1.button("📄 Build PDF",use_container_width=True):
        if not content: st.warning("Generate first"); st.stop()
        with st.spinner("Building..."):
            try:
                from fpdf import FPDF
                pdf=FPDF(); pdf.add_page()
                pdf.set_font("Arial",size=fmt["fs"])
                for ln in content.split("\n"): pdf.multi_cell(0,fmt["ls"],ln)
                pdf.output("/tmp/book.pdf"); st.success("PDF ready! Go to Get tab →")
            except Exception as e: st.error(str(e))
    if e2.button("📝 Build DOCX",use_container_width=True):
        if not content: st.warning("Generate first"); st.stop()
        with st.spinner("Building..."):
            try:
                from docx import Document
                d=Document(); d.add_paragraph(content); d.save("/tmp/book.docx"); st.success("DOCX ready! Go to Get tab →")
            except Exception as e: st.error(str(e))

with tab6:
    st.markdown("### ⬇️ Downloads")
    content=st.session_state.get("last_book","")
    if not content: st.info("No book yet — start in Writer")
    else:
        d1,d2=st.columns(2)
        with d1:
            try:
                with open("/tmp/book.pdf","rb") as f: st.download_button("⬇️ Download PDF",f,"book.pdf",mime="application/pdf",use_container_width=True)
            except: st.caption("Build PDF in Export tab first")
        with d2:
            try:
                with open("/tmp/book.docx","rb") as f: st.download_button("⬇️ Download DOCX",f,"book.docx",use_container_width=True)
            except: st.caption("Build DOCX in Export tab first")
        st.download_button("📋 Download TXT",content,"book.txt",use_container_width=True)

st.caption("Koncept AI Studio • Fast & mobile-friendly")

