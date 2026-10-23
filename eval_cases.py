"""Test cases for the SOP agent. Each case = a process text + facts the SOP MUST contain.

Fact types:
  {"name": ..., "all": [req, ...]}          one step/exception must contain every req
  {"name": ..., "before": ([A...], [B...])} the first step matching A comes before the first matching B
A req is a lowercase substring; "a|b" means "a or b".
"unowned": keyword lists; a STEP matching one must have NO owner (the text says "we", not a person).
"""

REAL_ESTATE = (
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

ONBOARDING = """Employee Onboarding and IT Access Provisioning Workflow

When HR hires a new candidate, HR sends the signed offer letter to the IT support desk at least 3 days before the join date. The IT admin then creates the employee's company email account and generates a temporary password.

On day 1, HR conducts the orientation session in the morning and hands over the welcome kit. HR also notifies the IT team once orientation is complete.

After notification, IT grants access to internal tools (Slack, Google Workspace, and Jira) based on the role specified in the offer letter. If the employee is in engineering, IT assigns access to GitHub repositories, but the Lead Engineer must approve repository access first.

Equipment Handover:
IT hands over the laptop and setup instructions to the candidate. The candidate must sign an asset tracking sheet. If equipment is unavailable on day 1, IT issues a temporary loaner device within 4 hours.

Background Verification & Document Collection:
HR collects police verification and degree certificates within 7 days of joining. If documents are missing after 7 days, HR sends a reminder and gives a grace period of 3 days. If still not submitted, HR escalates to the HR Manager for account suspension.

Security Training:
The employee must complete the mandatory cybersecurity training module within their first 14 days. Compliance team monitors progress.
"""

def _load_pdf(name: str) -> str:
    """Read a sample PDF through the same extractor the app uses (tests PDF reading too)."""
    import os
    from extract import extract_text
    path = os.path.join(os.path.dirname(__file__), "samples", name)
    with open(path, "rb") as f:
        return extract_text(name, f.read())[0]


GREENFIELD = {
    "name": "greenfield_pdf (held-out)",
    "text": _load_pdf("greenfield_lead_process.pdf"),
    "facts": [
        {"name": "CRM assigns lead round-robin", "all": ["assign", "round"]},
        {"name": "front desk logs walk-ins same day", "all": ["front desk", "walk"]},
        {"name": "call within 30 minutes", "all": ["call", "30 minutes"]},
        {"name": "after-hours lead called by 11 AM", "all": ["11 am"]},
        {"name": "2 more attempts + WhatsApp brochure", "all": ["whatsapp", "brochure"]},
        {"name": "Unreachable after 3 attempts", "all": ["unreachable"]},
        {"name": "Team Lead reviews nurture list Monday", "all": ["nurture", "monday"]},
        {"name": "Qualified = Rs. 60 lakh + 6 months", "all": ["60 lakh", "6 months"]},
        {"name": "site visit booked within 3 days", "all": ["site visit", "3 days"]},
        {"name": "confirmation 24 hours before", "all": ["confirm", "24 hours"]},
        {"name": "reminder 2 hours before", "all": ["reminder", "2 hours"]},
        {"name": "missed visit: reschedule once", "all": ["miss", "reschedul"]},
        {"name": "cost sheet within 24 hours", "all": ["cost sheet", "24 hours"]},
        {"name": "Sales Manager approves 2-5% discount", "all": ["sales manager", "2%"]},
        {"name": "Business Head approves >5% discount", "all": ["business head", "5%"]},
        {"name": "token amount Rs. 1 lakh", "all": ["token", "1 lakh"]},
        {"name": "KYC documents collected", "all": ["kyc"]},
        {"name": "Finance issues receipt", "all": ["finance", "receipt"]},
        {"name": "Legal prepares agreement in 7 days", "all": ["legal", "7 days"]},
        {"name": "follow-up every 3 days", "all": ["follow", "3 days"]},
        {"name": "Lost after 60 days", "all": ["lost", "60 days"]},
        {"name": "incomplete KYC: 5 days", "all": ["kyc", "5 days"]},
        {"name": "payment failure: Finance informs SE", "all": ["payment", "finance"]},
    ],
    # passive sentences with no actor: status changed, lead marked Unreachable/Lost, feedback entered, lead goes back to Nurture
    "unowned": [["status", "booked"], ["lost", "60 days"], ["unreachable"], ["feedback"], ["nurture", "again"]],
}

CASES = [
    {
        "name": "real_estate_crm",
        "text": REAL_ESTATE,
        "facts": [
            {"name": "call within an hour", "all": ["call", "hour"]},
            {"name": "retry when no pickup", "all": ["pick up", "again|back|retry"]},
            {"name": "warm status", "all": ["warm"]},
            {"name": "fix site visit", "all": ["fix", "site visit"]},
            {"name": "confirm visit day before", "all": ["confirm", "day before"]},
            {"name": "send quotation", "all": ["quotation"]},
            {"name": "follow up every 2-3 days", "all": ["follow", "2-3 days"]},
            {"name": "manager approves discount >2%", "all": ["manager", "discount", "2%"]},
            {"name": "cold after a month", "all": ["cold", "month"]},
            {"name": "closed-won on booking + agreement", "all": ["closed-won", "booking"]},
            {"name": "accounts team invoice", "all": ["accounts", "invoice"]},
            {"name": "no-show exception", "all": ["show up"]},
        ],
        "unowned": [["quotation"], ["follow"], ["cold"], ["closed-won"]],
    },
    {
        "name": "employee_onboarding",
        "text": ONBOARDING,
        "facts": [
            {"name": "offer letter >=3 days before join", "all": ["offer letter", "3 days"]},
            {"name": "IT admin creates email", "all": ["email", "admin"]},
            {"name": "HR orientation on day 1", "all": ["orientation", "hr"]},
            {"name": "HR notifies IT", "all": ["notify", "hr"]},
            {"name": "access to Slack/Google/Jira", "all": ["slack", "jira"]},
            {"name": "access depends on role in offer letter", "all": ["slack", "role"]},
            {"name": "Lead Engineer approves repo access", "all": ["lead engineer", "approv"]},
            {"name": "approval comes BEFORE github assignment",
             "before": (["lead engineer", "approv"], ["assign", "github|repositor"])},
            {"name": "laptop handover", "all": ["laptop"]},
            {"name": "asset tracking sheet signed", "all": ["asset tracking"]},
            {"name": "loaner device within 4 hours", "all": ["loaner", "4 hours"]},
            {"name": "documents within 7 days", "all": ["police", "7 days"]},
            {"name": "reminder + 3 day grace", "all": ["reminder", "3 days"]},
            {"name": "escalate to HR Manager", "all": ["hr manager", "escalat"]},
            {"name": "training within 14 days", "all": ["training", "14 days"]},
            {"name": "Compliance team monitors", "all": ["compliance", "monitor"]},
        ],
        "unowned": [],
    },
    GREENFIELD,
]