import streamlit as st
from agent import extract, find_gaps, refine, to_markdown
from extract import MAX_CHARS, extract_text
from grounding import check_grounding
from pdf_export import to_pdf_bytes

st.set_page_config(page_title="SOP Creation Agent", page_icon="📋", layout="wide")
st.title("📋 SOP Creation Agent")
st.caption("Paste a messy process description. Get a clean SOP. Answer the agent's questions to improve it.")

# Sample test case: real estate CRM process (as suggested by the manager)
SAMPLE = (
    "When a new property inquiry comes in from 99acres, MagicBricks or our website, "
    "the sales exec calls the person within an hour. Sometimes they don't pick up so "
    "we try again later. If the person is interested we mark them as warm and fix a "
    "site visit. The exec confirms the visit the day before. After the visit, if the "
    "client likes the property, we send the quotation and follow up every 2-3 days. "
    "Hot leads are the ones who ask for price negotiation. The manager approves any "
    "discount above 2%. If nothing happens for a month the lead goes to cold. Once the "
    "client pays the booking amount and signs the agreement, we mark it closed-won and "
    "the accounts team creates the invoice. Sometimes the client doesn't show up for "
    "the site visit and we forget to reschedule."
)

s = st.session_state
s.setdefault("round", 0)
s.setdefault("rejected", [])
s.setdefault("answers", [])

s.setdefault("raw_text", SAMPLE)
s.setdefault("upload_note", None)

uploaded = st.file_uploader(
    "Or upload a document (.txt, .md, .pdf, .docx). Its text appears below so you can edit it.",
    type=["txt", "md", "pdf", "docx"],
)
if uploaded is not None:
    file_id = (uploaded.name, uploaded.size)
    if s.get("loaded_file") != file_id:  # only read a file once, not on every rerun
        try:
            text, truncated = extract_text(uploaded.name, uploaded.getvalue())
            s.raw_text = text
            s.loaded_file = file_id
            s.upload_note = (
                f"Only the first {MAX_CHARS:,} characters were used." if truncated else None
            )
        except Exception as e:
            s.loaded_file = file_id
            st.error(f"Could not read this file: {e}")
if s.upload_note:
    st.warning(s.upload_note)

raw = st.text_area(
    "Process description (transcript, chat, existing instructions, or rough notes)",
    height=220, key="raw_text",
)

if st.button("Generate SOP", type="primary"):
    with st.spinner("Extracting SOP and checking for gaps..."):
        s.sop = extract(raw)
        s.source = raw          # everything the SOP is allowed to be based on
        s.rejected = []
        s.answers = []
        s.questions = find_gaps(s.sop)
        s.round += 1

if "sop" in s:
    left, right = st.columns([3, 2])

    with left:
        st.subheader("Current SOP")
        md = to_markdown(s.sop)
        warnings = check_grounding(s.sop, s.source, s.answers)
        if warnings:
            with st.expander(f"⚠️ {len(warnings)} item(s) to verify against your source text"):
                for w in warnings:
                    st.write("- " + w)
        else:
            st.success("Every step is backed by a quote from your source text.")
        st.markdown(md)
        d1, d2 = st.columns(2)
        d1.download_button("Download Markdown", md, file_name="sop.md")
        d2.download_button("Download PDF", to_pdf_bytes(s.sop), file_name="sop.pdf",
                           mime="application/pdf")

    with right:
        st.subheader("Agent's questions")
        for r in s.rejected:
            st.warning(f"Not applied: \"{r.answer}\" (to: {r.question}). {r.reason}")
        if not s.questions:
            st.success("No gaps found. This SOP looks complete.")
        answers = {}
        for i, q in enumerate(s.questions):
            answers[q] = st.text_input(q, key=f"a_{s.round}_{i}")

        if s.questions and st.button("Refine SOP with my answers"):
            qa = [(q, a) for q, a in answers.items() if a.strip()]
            if qa:
                with st.spinner("Updating SOP..."):
                    res = refine(s.sop, qa)
                    s.sop = res.sop
                    s.rejected = res.rejected
                    bad = {r.answer.strip() for r in res.rejected}
                    ok = [(q, ans) for q, ans in qa if ans.strip() not in bad]
                    s.source += "\n" + "\n".join(f"{q} {ans}" for q, ans in ok)
                    s.answers += [ans for _, ans in ok]
                    s.questions = find_gaps(s.sop)
                    s.round += 1
                st.rerun()
            else:
                st.warning("Answer at least one question first.")