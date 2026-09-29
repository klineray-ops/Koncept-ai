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
.brand-title {font-size:18rem !important;font-weight:900 !important;letter-spacing:-1px;margin:0;color:#ffffff !important;line-height:0.9 !important;}
@media (max-width: 768px) {
  .brand-title {font-size:11.2rem !important;}
  button[data-baseweb="tab"] {font-size:12px !important;white-space:nowrap;padding:8px 4px !important;}
  .stButton>button {padding:.6rem 1rem !important;font-size:15px !important;}
}
</style>""", unsafe_allow_html=True)

import base64, glob
def _find_image(name):
    """Find an image file robustly: exact name, then case-insensitive search in repo."""
    import os
    if os.path.exists(name): return name
    base = os.path.splitext(name)[0].lower()
    for root, dirs, files in os.walk("."):
        if ".git" in root: continue
        for f in files:
            if os.path.splitext(f)[0].lower() == base and f.lower().endswith((".png",".jpg",".jpeg",".webp")):
                return os.path.join(root, f)
    return None

def _logo_html():
    found = _find_image("koncept_book_logo.png")
    if found:
        try:
            with open(found,"rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"<img src='data:image/png;base64,{b64}' style='width:min(340px,80vw);height:auto;object-fit:contain;filter:drop-shadow(0 10px 30px rgba(139,92,246,0.45));'/>"
        except Exception as e:
            return f"<div style='color:#fbbf24'>⚠️ Logo found but could not load: {e}</div>"
    return "<div style='color:#fbbf24;font-size:14px'>⚠️ koncept_book_logo.png not found in repo — upload it next to app.py, then Reboot.</div>"
st.markdown(f"<div style='text-align:center;padding:1.5rem 1rem 0.5rem'>{_logo_html()}<p style='color:#cbd5e1;font-size:1.3rem;font-weight:600;margin-top:1rem;'>Concept, Write, Design, Publish, Earn<br/>Through BrOwn, KDP, Google, eBookSelf</p></div>", unsafe_allow_html=True)

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

# ============ KOBOT CHATBOT ============
SUPPORT_EMAIL = "klineray@gmail.com"
if "kobot_open" not in st.session_state: st.session_state["kobot_open"]=False
if "kobot_step" not in st.session_state: st.session_state["kobot_step"]="greet"
if "kobot_profile" not in st.session_state: st.session_state["kobot_profile"]={}
if "kobot_hist" not in st.session_state: st.session_state["kobot_hist"]=[]

def _kobot_log_to_sheet(entry):
    """Append chat/support entry to Google Sheet if configured, always mailto fallback."""
    try:
        import json, urllib.request
        url = _safe_env("KOBOT_SHEET_WEBHOOK")
        if url:
            req = urllib.request.Request(url, data=json.dumps(entry).encode(), headers={"Content-Type":"application/json"})
            urllib.request.urlopen(req, timeout=5)
    except: pass

# Floating Kobot button
_kobot_icon_b64 = ""
_kobot_found = _find_image("kobot_icon_cat.png")
if _kobot_found:
    try:
        with open(_kobot_found,"rb") as _f: _kobot_icon_b64 = base64.b64encode(_f.read()).decode()
    except: pass
if _kobot_icon_b64:
    st.markdown(f"""<style>
    #kobot-fab {{position:fixed;bottom:24px;right:24px;z-index:9999;cursor:pointer;}}
    #kobot-fab img {{width:64px;height:64px;border-radius:50%;box-shadow:0 4px 16px rgba(139,92,246,.6);border:3px solid #8b5cf6;}}
    </style>""", unsafe_allow_html=True)

kcol1, kcol2 = st.columns([9,1])
with kcol2:
    if _kobot_icon_b64:
        import base64 as _b64m
        st.markdown(f"<img src='data:image/png;base64,{_kobot_icon_b64}' style='width:56px;height:56px;border-radius:50%;'/>", unsafe_allow_html=True)
    if st.button("💬 Kobot", key="kobot_toggle", use_container_width=True):
        st.session_state["kobot_open"] = not st.session_state["kobot_open"]
        if st.session_state["kobot_open"] and st.session_state["kobot_step"]=="greet":
            st.session_state["kobot_hist"].append({"r":"bot","t":"Hi, I am Kobot, how can I help you? 😊 Please tell me your details so I can assist you better."})
            st.session_state["kobot_step"]="collect_name"

if st.session_state.get("kobot_open"):
    with st.expander("🤖 Kobot — your Koncept AI assistant", expanded=True):
        if _kobot_icon_b64:
            st.markdown(f"<img src='data:image/png;base64,{_kobot_icon_b64}' style='width:48px;height:48px;border-radius:50%;'/>", unsafe_allow_html=True)
        for m in st.session_state["kobot_hist"]:
            who = "🧑 You" if m["r"]=="user" else "🤖 Kobot"
            st.write(f"**{who}:** {m['t']}")
        step = st.session_state["kobot_step"]
        prof = st.session_state["kobot_profile"]
        if step == "collect_name":
            nm = st.text_input("Your name", key="kb_name")
            if st.button("Next →", key="kb_n1"):
                if nm.strip():
                    prof["name"]=nm.strip(); st.session_state["kobot_step"]="collect_email"
                    st.session_state["kobot_hist"].append({"r":"user","t":nm.strip()})
                    st.session_state["kobot_hist"].append({"r":"bot","t":f"Nice to meet you, {nm.strip()}! What is your email id?"})
                    st.rerun()
        elif step == "collect_email":
            ema = st.text_input("Your email id", key="kb_email")
            if st.button("Next →", key="kb_n2"):
                if ema.strip():
                    prof["email"]=ema.strip(); st.session_state["kobot_step"]="collect_purpose"
                    st.session_state["kobot_hist"].append({"r":"user","t":ema.strip()})
                    st.session_state["kobot_hist"].append({"r":"bot","t":"What is the purpose of your visit? (e.g. create ebook, support, pricing)"})
                    st.rerun()
        elif step == "collect_purpose":
            pur = st.text_input("Purpose", key="kb_purpose")
            if st.button("Next →", key="kb_n3"):
                if pur.strip():
                    prof["purpose"]=pur.strip(); st.session_state["kobot_step"]="collect_place"
                    st.session_state["kobot_hist"].append({"r":"user","t":pur.strip()})
                    st.session_state["kobot_hist"].append({"r":"bot","t":"Which place / city are you from?"})
                    st.rerun()
        elif step == "collect_place":
            plc = st.text_input("Your place / city", key="kb_place")
            if st.button("Start Chatting 💬", key="kb_n4"):
                if plc.strip():
                    prof["place"]=plc.strip()
                    st.session_state["kobot_step"]="chat"
                    st.session_state["kobot_hist"].append({"r":"user","t":plc.strip()})
                    st.session_state["kobot_hist"].append({"r":"bot","t":f"Thanks {prof.get('name','friend')}! You can now chat freely. All our conversations will be sent to our support team ({SUPPORT_EMAIL}). How can I help?"})
                    _kobot_log_to_sheet({"type":"new_lead","profile":prof,"time":str(datetime.datetime.now())})
                    st.rerun()
        elif step == "chat":
            q = st.text_input("Type your message...", key="kb_q")
            if st.button("Send 📩", key="kb_send"):
                if q.strip():
                    st.session_state["kobot_hist"].append({"r":"user","t":q})
                    client=get_groq()
                    if client:
                        try:
                            r=client.chat.completions.create(model="llama-3.1-8b-instant",messages=[{"role":"system","content":"You are Kobot, friendly assistant for Koncept AI eBook Studio."},{"role":"user","content":q}],max_tokens=500)
                            ans=r.choices[0].message.content
                        except Exception as e: ans=f"Sorry, AI is busy: {e}"
                    else:
                        ql=q.lower()
                        if "price" in ql or "plan" in ql: ans="Plans: Free (3 books $0), Pro Std (10 books $3.99/mo), Pro Dlx (30 books $5.99/mo), Pro Max (99 books $9.99/mo)."
                        elif "pdf" in ql: ans="Go to Export tab → Build PDF, then Get tab → Download PDF."
                        elif "support" in ql or "ticket" in ql: ans=f"Please raise a support ticket in the sidebar, or email us at {SUPPORT_EMAIL}."
                        else: ans="Thanks for your message! Our team will follow up. Meanwhile ask me about plans, writer, exports."
                    st.session_state["kobot_hist"].append({"r":"bot","t":ans})
                    _kobot_log_to_sheet({"type":"chat","profile":prof,"q":q,"a":ans,"time":str(datetime.datetime.now())})
                    st.rerun()
            st.markdown("---")
            _mailto_body = f"Hi Support, I am {prof.get('name','')} ({prof.get('email','')}) from {prof.get('place','')}. Purpose: {prof.get('purpose','')}"
            import urllib.parse as _up
            _mailto = f"mailto:{SUPPORT_EMAIL}?subject="+_up.quote("Kobot chat transcript request")+ "&body="+_up.quote(_mailto_body)
            st.markdown(f"📧 Need human help? [Email us at {SUPPORT_EMAIL}]({_mailto})")
            st.caption("All chats & support requests are logged and directed to klineray@gmail.com + Google Sheet (set KOBOT_SHEET_WEBHOOK secret for auto-logging).")

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

