
# Standard sizes reference:
# - Amazon KDP Paperback most popular: 6" x 9" (15.24 x 22.86 cm)
# - Trade / Brown 5" x 8" (12.7 x 20.32 cm) - compact novel size
# - 5.5" x 8.5" (13.97 x 21.59 cm)
# - 8.5" x 11" (21.59 x 27.94 cm) - workbook
# - A4 (8.27" x 11.69") - PDF guides
import streamlit as st
import os
from groq import Groq
from huggingface_hub import InferenceClient
from fpdf import FPDF
from PIL import Image

st.set_page_config(page_title="Koncept AI - eBook Studio Pro", layout="wide")

groq_client = Groq(api_key=st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY","")))
hf_token = st.secrets.get("HF_TOKEN", os.getenv("HF_TOKEN",""))
hf_client = InferenceClient(token=hf_token) if hf_token else None

# --- TIERS CONFIG ---
TIERS = {
    "Free": {"books":1, "chapters":3, "features":["Basic writer","PDF export"], "price":"Free"},
    "Pro Std": {"books":10, "chapters":100, "features":["Basic Facilities","Title+Outline","Chapter Writer","PDF"], "price":"₹499"},
    "Pro Dlx": {"books":30, "chapters":500, "features":["Medium Facilities","All Std + Cover Studio","Image upload","Font controls"], "price":"₹999"},
    "Pro Max": {"books":100, "chapters":2000, "features":["Highest Facilities","All Dlx + Priority AI","Chatbot support","Commercial license"], "price":"₹1999"},
}
RAZORPAY_LINK = st.secrets.get("RAZORPAY_LINK", "https://razorpay.com/your-link")
PAYPAL_LINK = st.secrets.get("PAYPAL_LINK", "https://paypal.me/yourlink")

if "tier" not in st.session_state: st.session_state["tier"]="Free"
if "usage" not in st.session_state: st.session_state["usage"]={"books":0,"chapters":0}
if "chat_history" not in st.session_state: st.session_state["chat_history"]=[]

def ai(prompt, task="write"):
    sys="You are expert eBook writer, write clearly."
    r=groq_client.chat.completions.create(model="openai/gpt-oss-20b",
        messages=[{"role":"system","content":sys},{"role":"user","content":prompt}])
    return r.choices[0].message.content

def allowed_books():
    return TIERS[st.session_state["tier"]]["books"]
def can_create_book():
    return st.session_state["usage"]["books"] < allowed_books()

# Sidebar - Plan & Recharge
with st.sidebar:
    st.header("💎 Your Plan")
    st.selectbox("Current tier", list(TIERS.keys()), key="tier")
    t=TIERS[st.session_state["tier"]]
    st.write(f"**{st.session_state['tier']}** - {t['price']}")
    st.write(f"Books: {st.session_state['usage']['books']}/{t['books']}")
    st.write("Features: "+", ".join(t["features"]))
    st.divider()
    st.subheader("🔋 Recharge / Upgrade")
    st.markdown(f"[Pay with Razorpay]({RAZORPAY_LINK})")
    st.markdown(f"[Pay with PayPal]({PAYPAL_LINK})")
    st.caption("After payment, enter key given by admin:")
    key=st.text_input("License key", type="password")
    if st.button("Activate"):
        # Simple mapping: key prefix determines tier, set in secrets in production
        # e.g. STD-XXX, DLX-XXX, MAX-XXX
        if key.startswith("STD-"): st.session_state["tier"]="Pro Std"; st.success("Pro Std activated")
        elif key.startswith("DLX-"): st.session_state["tier"]="Pro Dlx"; st.success("Pro Dlx activated")
        elif key.startswith("MAX-"): st.session_state["tier"]="Pro Max"; st.success("Pro Max activated")
        else: st.error("Invalid key - contact support")
        st.rerun()


# --- Publishing Add-ons ---
import random, datetime, re
try:
    from docx import Document
except ImportError:
    Document = None

def generate_ksbn():
    yr=datetime.datetime.now().year
    rnd=''.join([str(random.randint(0,9)) for _ in range(5)])
    return f"KSBN-{yr}-{rnd}"

def validate_isbn(isbn):
    clean=re.sub(r'[^0-9X]','',isbn.upper())
    return len(clean) in [10,13]

def kdp_checks(plan_text, chapters, has_cover, has_isbn):
    checks=[]
    wc=len((plan_text+" ".join(chapters)).split())
    checks.append(("Word count >= 2500 for KDP" , wc>=2500, f"{wc} words"))
    checks.append(("Table of Contents present", "##" in plan_text or "Chapter" in plan_text, "TOC check"))
    checks.append(("At least 3 chapters", len(chapters)>=3, f"{len(chapters)} chapters"))
    checks.append(("Cover image ready", has_cover, "Cover"))
    checks.append(("ISBN added", has_isbn, "ISBN"))
    # Amazon prohibited: no placeholder lorem
    checks.append(("No lorem ipsum", "lorem" not in (plan_text.lower()), "Clean"))
    return checks

tab1, tab2, tab3, tab4 = st.tabs(["✍️ Writer","📘 eBook Studio","🤖 AI Assistant","📦 Publish"])

with tab1:
    st.subheader("Book Planner")
    topic=st.text_input("Topic")
    audience=st.text_input("Audience")
    goal=st.selectbox("Goal",["Teach","Lead magnet","Sell"])
    if st.button("Generate Title + Outline", key="gen_outline"):
        if not can_create_book():
            st.error(f"Limit reached for {st.session_state['tier']}. Please recharge/upgrade.")
        else:
            with st.spinner("Planning..."):
                plan=ai(f"Plan ebook on {topic} for {audience}, goal {goal}. Give 3 titles + outline Parts->Chapters.")
                st.session_state["usage"]["books"]+=1
                st.session_state["plan"]=plan
                st.markdown(plan)
    if "plan" in st.session_state: st.markdown(st.session_state["plan"])
    st.divider()
    ch_title=st.text_input("Chapter title")
    tone=st.selectbox("Tone",["Simple","Friendly","Professional"])
    if st.button("Write Chapter", key="write_chap"):
        txt=ai(f"Write chapter {ch_title} on {topic}, tone {tone}, with hook, examples, takeaways")
        st.session_state["usage"]["chapters"]+=1
        st.markdown(txt)
        if "chapters" not in st.session_state: st.session_state["chapters"]=[]
        st.session_state["chapters"].append(txt)

with tab2:
    st.header("Design & Export")
    # Feature gating
    tier=st.session_state["tier"]
    font=st.selectbox("Font",["Helvetica","Times"])
    body_size=st.slider("Body size",10,18,12)
    if tier in ["Pro Dlx","Pro Max"]:
        cover_prompt=st.text_input("Cover prompt")
        up_cover=st.file_uploader("Upload cover", type=["png","jpg"])
        if st.button("Generate Cover") and tier=="Pro Max":
            st.info("Priority AI cover generation (Pro Max)")
    else:
        st.info("Cover Studio available in Pro Dlx and above. Upgrade to unlock.")
    st.subheader("📐 Page Size")
    size_opt = st.selectbox("Select trim size", [
        "Amazon KDP - 6x9 inch (15.24 x 22.86 cm) - Most Popular",
        "Brown / Trade - 5x8 inch (12.7 x 20.32 cm)",
        "KDP - 5.5x8.5 inch (13.97 x 21.59 cm)",
        "KDP Large - 8.5x11 inch (21.59 x 27.94 cm)",
        "A4 - 8.27x11.69 inch (21 x 29.7 cm)"
    ])
    # map to FPDF: use custom size in mm
    size_map = {
        "Amazon KDP - 6x9 inch (15.24 x 22.86 cm) - Most Popular": (152.4, 228.6),
        "Brown / Trade - 5x8 inch (12.7 x 20.32 cm)": (127, 203.2),
        "KDP - 5.5x8.5 inch (13.97 x 21.59 cm)": (139.7, 215.9),
        "KDP Large - 8.5x11 inch (21.59 x 27.94 cm)": (215.9, 279.4),
        "A4 - 8.27x11.69 inch (21 x 29.7 cm)": (210, 297),
    }
    pw, ph = size_map[size_opt]
    st.caption(f"Selected: {size_opt} | {pw} x {ph} mm")
    if st.button("Export PDF", key="export_pdf_studio"):

        pdf=FPDF(unit='mm', format=(pw, ph)); pdf.add_page(); pdf.set_font(font,'',body_size)
        txt=st.session_state.get("plan","")[:5000]
        for line in txt.split("\n"):
            pdf.multi_cell(0,8,line.encode('latin-1','replace').decode('latin-1'))
        pdf.output("book.pdf")
        with open("book.pdf","rb") as f: st.download_button("Download",f,"book.pdf")

with tab3:
    st.header("🤖 Koncept AI Assistant")
    st.write("Ask about pricing, features, or how to use the app.")
    q=st.text_input("Ask me...")
    if q:
        # Simple rule-based + AI fallback
        if "price" in q.lower() or "pro" in q.lower():
            ans="Tiers: Free (1 book free). Pro Std ₹499 (up to 10 books, basic). Pro Dlx ₹999 (up to 30 books, medium). Pro Max ₹1999 (up to 100 books, highest). Recharge via Razorpay/PayPal links in sidebar."
        else:
            ans=ai(f"You are Koncept AI support chatbot. Answer briefly: {q}")
        st.session_state["chat_history"].append((q,ans))
    for qq,aa in reversed(st.session_state["chat_history"]):
        st.markdown(f"**You:** {qq}")
        st.markdown(f"**AI:** {aa}")

with tab4:
    st.header("📦 Publishing, ISBN & Amazon KDP")
    col1,col2=st.columns(2)
    with col1:
        isbn=st.text_input("ISBN-13 (if you have one)", placeholder="978-...")
        if isbn:
            if validate_isbn(isbn): st.success("Valid ISBN format")
            else: st.error("Invalid ISBN - should be 10 or 13 digits")
        if "ksbn" not in st.session_state: st.session_state["ksbn"]=generate_ksbn()
        st.text_input("KSBN - Koncept Standard Book Number", value=st.session_state["ksbn"], disabled=True)
        if st.button("Regenerate KSBN", key="regen_ksbn"):
            st.session_state["ksbn"]=generate_ksbn(); st.rerun()
    with col2:
        st.subheader("SEO-friendly metadata")
        if st.button("Generate SEO Pack", key="gen_seo"):
            topic_seo=st.session_state.get("plan","")[:200]
            seo=ai(f"Generate SEO pack for ebook. Give: 1) SEO title <60 chars, 2) Amazon description 150 words with keywords, 3) 7 backend keywords, 4) categories. Context: {topic_seo}")
            st.session_state["seo"]=seo
        if "seo" in st.session_state: st.markdown(st.session_state["seo"])

    st.divider()
    st.subheader("✅ Amazon KDP Protocol Check")
    has_cover = True  # simplified, set true if cover generated
    has_isbn = bool(isbn and validate_isbn(isbn))
    plan_text=st.session_state.get("plan","")
    chapters=st.session_state.get("chapters",[])
    for name, passed, detail in kdp_checks(plan_text, chapters, has_cover, has_isbn):
        st.markdown(f"{'✅' if passed else '❌'} **{name}** - {detail}")
    st.caption("KDP requires original content, no trademarked terms in title, proper TOC, and print-ready PDF 6x9\". Ensure you own rights to cover images.")

    st.divider()
    st.subheader("💾 Export in other formats")
    fmt=st.selectbox("Format", ["PDF","DOCX","EPUB (basic)","HTML","TXT"])
    if st.button("Export "+fmt, key="export_publish_btn"):
        full_text=st.session_state.get("plan","")+"\\n\\n"+"\\n\\n".join(chapters)
        meta=f"Title: eBook\\nISBN: {isbn}\\nKSBN: {st.session_state['ksbn']}\\n\\n"
        if fmt=="TXT":
            open("book.txt","w",encoding="utf-8").write(meta+full_text)
            with open("book.txt","rb") as f: st.download_button("Download TXT",f,"book.txt")
        elif fmt=="HTML":
            html=f"<html><head><meta charset='utf-8'><title>eBook</title></head><body><p>ISBN:{isbn}<br>KSBN:{st.session_state['ksbn']}</p><pre>{full_text}</pre></body></html>"
            open("book.html","w",encoding="utf-8").write(html)
            with open("book.html","rb") as f: st.download_button("Download HTML",f,"book.html")
        elif fmt=="DOCX":
            if Document is None:
                st.error("python-docx not installed. Add python-docx to requirements.txt and reboot.")
            else:
                doc=Document(); doc.add_heading('eBook',0)(); doc.add_heading('eBook',0)
            doc.add_paragraph(f"ISBN: {isbn} | KSBN: {st.session_state['ksbn']}")
            for para in full_text.split("\\n"): doc.add_paragraph(para)
            doc.save("book.docx")
            with open("book.docx","rb") as f: st.download_button("Download DOCX",f,"book.docx")
        elif fmt.startswith("EPUB"):
            # minimal EPUB
            import zipfile
            with zipfile.ZipFile("book.epub","w") as z:
                z.writestr("mimetype","application/epub+zip")
                z.writestr("OEBPS/content.opf",f"<package><metadata><dc:title xmlns:dc='http://purl.org/dc/elements/1.1/'>eBook</dc:title><dc:identifier>ISBN:{isbn}</dc:identifier></metadata></package>")
                z.writestr("OEBPS/ch1.xhtml",f"<html><body><p>ISBN:{isbn} KSBN:{st.session_state['ksbn']}</p><pre>{full_text[:10000]}</pre></body></html>")
            with open("book.epub","rb") as f: st.download_button("Download EPUB",f,"book.epub")
        else:
            st.info("Use eBook Studio tab for PDF")

