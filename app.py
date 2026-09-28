import streamlit as st
import os, requests
from io import BytesIO

st.set_page_config(page_title="Koncept AI", page_icon="✨", layout="wide")

# --- Secure secrets handling ---
def get_secret(name):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, "")

GROQ_KEY = get_secret("GROQ_API_KEY")
HF_TOKEN = get_secret("HF_TOKEN")

if not GROQ_KEY:
    st.error("Missing GROQ_API_KEY. Add it in Streamlit Secrets. See README.")
    st.stop()

from groq import Groq
from huggingface_hub import InferenceClient
from fpdf import FPDF
import matplotlib.pyplot as plt

groq_client = Groq(api_key=GROQ_KEY)
hf_client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None

for k in ['text','book','blueprint','has_chart']:
    if k not in st.session_state: st.session_state[k]=""

# --- Theme ---
st.markdown("<style>.stButton>button{background:linear-gradient(90deg,#8E2DE2,#4A00E0);color:white;border-radius:20px;padding:10px 25px;border:none;font-weight:bold;}</style>", unsafe_allow_html=True)
logo_path = "assets/logo.png"
header_img = f"<img src='{logo_path}' width='60'>" if os.path.exists(logo_path) else "✨"
st.markdown(f"""<div style="text-align:center;padding:20px;background:linear-gradient(135deg,#8E2DE2,#4A00E0);border-radius:15px;margin-bottom:15px;"><h1 style="color:white;margin:0;">{header_img} Koncept AI</h1><p style="color:white;">Write, Visualize, Publish - All Free</p></div>""", unsafe_allow_html=True)

# --- Reader comfort ---
st.sidebar.title("📖 Reader")
font_size = st.sidebar.slider("Font Size", 12, 22, 16)
dark_mode = st.sidebar.checkbox("Dark Mode")
bg = "#1e1e1e" if dark_mode else "#ffffff"; tc = "#fff" if dark_mode else "#000"
st.markdown(f"<style>.reader{{background:{bg};color:{tc};font-size:{font_size}px;line-height:1.8;padding:20px;border-radius:10px;}}</style>", unsafe_allow_html=True)

def ai(prompt, task="write"):
    sys={"write":"You are expert eBook writer.","grammar":"Fix spelling/grammar only.","improve":"Improve clarity, flow, engagement."}
    r=groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":sys.get(task,"")},{"role":"user","content":prompt}], temperature=0.7)
    return r.choices[0].message.content

def ai_image(prompt, save_as="cover.png"):
    # Try HF first, fallback to Pollinations
    try:
        if hf_client:
            img = hf_client.text_to_image(prompt, model="stabilityai/stable-diffusion-xl-base-1.0")
            img.save(save_as); return save_as
    except Exception: pass
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=800&height=1000&nologo=true"
        res = requests.get(url, timeout=60); res.raise_for_status()
        open(save_as,'wb').write(res.content); return save_as
    except Exception as e:
        st.warning(f"Image gen failed: {e}"); return None

class PDF(FPDF):
    def footer(self):
        self.set_y(-15); self.set_font("Arial","I",8); self.cell(0,10,f"Page {self.page_no()}", align='C')

tab1,tab2 = st.tabs(["📝 Writer","📚 eBook Studio"])
with tab1:
    t=st.text_input("Topic")
    if st.button("Generate"):
        if t:
            with st.spinner("Writing..."): st.session_state['text']=ai(t)
    if st.session_state['text']:
        ed=st.text_area("Edit", st.session_state['text'], height=250)
        c1,c2,c3,c4=st.columns(4)
        if c1.button("Fix Grammar"): st.session_state['text']=ai(ed,"grammar"); st.rerun()
        if c2.button("Improve"): st.session_state['text']=ai(ed,"improve"); st.rerun()
        if c3.button("Originality Check"):
            with st.spinner("Checking..."): st.info(ai(f"Flag plagiarism risk and rewrite risky parts originally: {ed}"))
        if c4.button("Paraphrase"): st.session_state['text']=ai(f"Paraphrase originally: {ed}","improve"); st.rerun()
        st.markdown(f"<div class='reader'>{st.session_state['text']}</div>", unsafe_allow_html=True)

with tab2:
    title=st.text_input("Book Title", key="btitle")
    n=st.number_input("Chapters",1,10,3); lang=st.selectbox("Language",["English","Hindi","Bengali"])
    if st.button("Create eBook"):
        full=""; prog=st.progress(0)
        for i in range(int(n)):
            with st.spinner(f"Chapter {i+1}..."):
                ch=ai(f"Write chapter {i+1} for '{title}': hook, explanation, examples, takeaways")
                if lang!="English": ch=ai(f"Translate to {lang}: {ch}")
                full+=f"\n\nCHAPTER {i+1}\n{ch}"
            prog.progress((i+1)/int(n))
        st.session_state['book']=full
        p=ai_image(f"professional book cover for '{title}'", "cover.png")
        if p: st.image(p, width=300)

    st.subheader("📊 Chart")
    ct=st.selectbox("Type",["Bar","Pie","Line"]); la=st.text_input("Labels","A,B,C"); va=st.text_input("Values","10,20,30")
    if st.button("Make Chart"):
        try:
            L=[x.strip() for x in la.split(",")]; V=[float(x.strip()) for x in va.split(",")]
            plt.figure(figsize=(6,4))
            if ct=="Bar": plt.bar(L,V,color='#8E2DE2')
            elif ct=="Pie": plt.pie(V,labels=L,autopct='%1.1f%%')
            else: plt.plot(L,V,marker='o')
            plt.tight_layout(); plt.savefig("chart.png"); plt.close(); st.image("chart.png"); st.session_state['has_chart']=True
        except Exception as e: st.error(e)

    if st.session_state['book']:
        st.markdown(f"<div class='reader'>{st.session_state['book'][:3000]}</div>", unsafe_allow_html=True)
        if st.button("Export PDF"):
            pdf=PDF(); pdf.set_auto_page_break(True,15)
            pdf.add_page(); pdf.set_font("Arial","B",20); pdf.cell(0,10,title.encode('latin-1','replace').decode('latin-1'),ln=True,align='C')
            if os.path.exists("cover.png"): pdf.image("cover.png",w=150)
            # TOC
            pdf.add_page(); pdf.set_font("Arial","B",16); pdf.cell(0,10,"Table of Contents",ln=True)
            pdf.set_font("Arial","",12)
            for i in range(int(n)): pdf.cell(0,10,f"Chapter {i+1}",ln=True)
            # Content - note: non-latin scripts will show as ? in PDF, preview preserves unicode
            pdf.add_page(); pdf.set_font("Arial","",max(10,font_size-4))
            clean=st.session_state['book'].encode('latin-1','replace').decode('latin-1')
            pdf.multi_cell(0,10,clean)
            if st.session_state.get('has_chart') and os.path.exists("chart.png"):
                pdf.add_page(); pdf.set_font("Arial","B",14); pdf.cell(0,10,"Chart",ln=True); pdf.image("chart.png",w=170)
            pdf.add_page(); pdf.set_font("Arial","I",10)
            pdf.multi_cell(0,10,"Copyright (c) 2026 Koncept AI. AI-generated text and images. Review for originality before commercial use.")
            if lang!="English": pdf.multi_cell(0,10,"Note: PDF uses Latin encoding. For Hindi/Bengali full script, use DOCX export or web preview.")
            pdf.output("koncept_ebook.pdf")
            with open("koncept_ebook.pdf","rb") as f: st.download_button("📥 Download PDF",f,"koncept_ebook.pdf")
