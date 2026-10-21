import streamlit as st
from agent import extract, find_gaps, refine, to_markdown
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

raw = st.text_area(
    "Process description (transcript, chat, existing instructions, or rough notes)",
    SAMPLE, height=220,
)

if st.button("Generate SOP", type="primary"):
    with st.spinner("Extracting SOP and checking for gaps..."):
        s.sop = extract(raw)
        s.source = raw          # everything the SOP is allowed to be based on
        s.questions = find_gaps(s.sop)
        s.round += 1

if "sop" in s:
    left, right = st.columns([3, 2])

    with left:
        st.subheader("Current SOP")
        md = to_markdown(s.sop)
        warnings = check_grounding(s.sop, s.source)
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
        if not s.questions:
            st.success("No gaps found. This SOP looks complete.")
        answers = {}
        for i, q in enumerate(s.questions):
            answers[q] = st.text_input(q, key=f"a_{s.round}_{i}")

        if s.questions and st.button("Refine SOP with my answers"):
            qa = [(q, a) for q, a in answers.items() if a.strip()]
            if qa:
                with st.spinner("Updating SOP..."):
                    s.sop = refine(s.sop, qa)
                    s.source += "\n" + "\n".join(f"{q} {a}" for q, a in qa)
                    s.questions = find_gaps(s.sop)
                    s.round += 1
                st.rerun()
            else:
                st.warning("Answer at least one question first.")