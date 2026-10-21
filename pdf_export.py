from fpdf import FPDF
from schemas import SOP

# fpdf2's built-in fonts only support basic Latin characters,
# so we swap common "fancy" characters for plain ones.
_REPLACE = {"→": "->", "’": "'", "‘": "'", "“": '"', "”": '"',
            "–": "-", "—": "-", "•": "-", "₹": "Rs.", "…": "..."}


def _clean(text: str) -> str:
    for k, v in _REPLACE.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


def to_pdf_bytes(sop: SOP) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    W = pdf.epw  # usable page width

    def h1(t):
        pdf.set_font("Helvetica", "B", 18)
        pdf.multi_cell(W, 9, _clean(t), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def h2(t):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(W, 7, _clean(t), new_x="LMARGIN", new_y="NEXT")

    def p(t):
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(W, 6, _clean(t), new_x="LMARGIN", new_y="NEXT")

    h1(f"SOP: {sop.display_title()}")
    h2("1. Purpose"); p(sop.purpose)
    h2("2. Scope"); p(sop.scope)

    h2("3. Roles and Responsibilities")
    roles = sop.roles()
    if roles:
        for role, text in roles:
            p(f"- {role}: {text}")
    else:
        p("No owners identified yet")

    h2("4. Prerequisites")
    if sop.prerequisites:
        for x in sop.prerequisites:
            p(f"- {x}")
    else:
        p("None specified")

    h2("5. Definitions and Criteria")
    if sop.definitions:
        for d in sop.definitions:
            p(f"- {d}")
    else:
        p("None specified")

    h2("6. Procedure")
    for s in sop.steps:
        line = f"{s.number}. {s.action}"
        if s.condition:
            line += f" (If {s.condition})"
        if s.owner:
            line += f" (Owner: {s.owner})"
        if s.timeline:
            line += f" [{s.timeline}]"
        p(line)
        if s.notes:
            p(f"    Note: {s.notes}")

    h2("7. Exceptions and Troubleshooting")
    if sop.exceptions:
        for e in sop.exceptions:
            line = f"- If {e.situation}: {e.action or 'Not defined'}"
            if e.owner:
                line += f" (Owner: {e.owner})"
            if e.timeline:
                line += f" [{e.timeline}]"
            p(line)
    else:
        p("None specified")

    h2("8. Review Information")
    p(sop.review_info or "Not specified")
    return bytes(pdf.output())