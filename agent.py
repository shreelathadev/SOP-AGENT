from llm import ask
from schemas import SOP, GapReport

RULES = (
    "Never invent details. If something is not stated, use null or leave the list "
    "empty instead of guessing. Write clear, grammatical business English that a "
    "non-technical person can follow: every step starts with an imperative verb "
    "(e.g. 'Mark the lead as cold', not 'Go to cold'), and conditions are grammatical "
    "phrases (e.g. 'the person does not pick up'). Keep names and roles exactly as "
    "mentioned. Capture every status/stage name, follow-up timeline and success "
    "criterion mentioned (status meanings and conversion criteria go in 'definitions', "
    "timings go in each step's 'timeline'). "
    "OWNER RULE: set an owner ONLY if the text clearly says who does it. If the text "
    "says 'we', uses passive voice, or says nothing, set owner to null. Do not attach "
    "a rule to a person, status or condition unless the text links them. "
    "EVERY action in the text, including status changes (mark as cold, mark closed-won), "
    "must appear as a step. Put 'if ...' conditions in 'condition', not in notes, and do "
    "not repeat the scope in notes. The title is a short process name without the word "
    "'SOP'. "
    "EXCEPTIONS are deviations from the normal path. 'situation' is a short condition, "
    "'action' says what to do WITHOUT naming who (the name goes in 'owner'). If the text "
    "only says what goes wrong (e.g. 'we forget to reschedule'), set 'action' to null; "
    "never restate the problem as the action. "
    "EVIDENCE RULE: for every step and exception, set 'source_quote' to the EXACT words, "
    "copied character for character, from the process text or from the human's answers "
    "that support it. Never paraphrase a quote. If no words support it, set null."
)


def extract(raw_text: str) -> SOP:
    """Call 1: messy text -> structured SOP draft."""
    system = (
        "You are an operations analyst who writes Standard Operating Procedures "
        "(SOPs) from messy descriptions of how work is done. " + RULES
    )
    return ask(system, f"Process description:\n\n{raw_text}", SOP)


def find_gaps(sop: SOP) -> list[str]:
    """Call 2: review the draft, return questions about what is missing."""
    system = (
        "You are a strict SOP reviewer. Find missing or ambiguous information and "
        "ask at most 5 specific, answerable questions. Prioritise by impact, in "
        "this order: (1) steps with a null owner, (2) missing end states or "
        "statuses (e.g. what happens when a deal is lost), (3) exceptions with no "
        "owner, action or timing, (4) vague decision rules ('interested', 'likes the "
        "property'), (5) missing timelines, then missing prerequisites and review "
        "owner/frequency. Ask at most 2 timeline questions in total, and never "
        "more than 2 questions of the same kind, so the questions cover different "
        "problems. Refer to steps by number. Do not ask about things the SOP "
        "already states. If the SOP is already complete, return an empty list."
    )
    return ask(system, sop.model_dump_json(indent=2), GapReport).questions


def refine(sop: SOP, qa: list[tuple[str, str]]) -> SOP:
    """Call 3: merge the human's answers into the SOP."""
    answers = "\n".join(f"Q: {q}\nA: {a}" for q, a in qa)
    system = (
        "You update an SOP using the answers a human gave. Keep everything that is "
        "still correct, add the new information in the right place, and renumber "
        "steps. Apply each answer ONLY to the item its question is about, leave "
        "unrelated parts unchanged, and never create duplicate rows (update the "
        "existing one instead). For anything you add or change from an answer, set "
        "'source_quote' to the exact words of that answer. Keep existing quotes "
        "unchanged. " + RULES
    )
    user = f"Current SOP:\n{sop.model_dump_json(indent=2)}\n\nAnswers:\n{answers}"
    return ask(system, user, SOP)


def to_markdown(sop: SOP) -> str:
    L = [f"# SOP: {sop.display_title()}", "",
         "## 1. Purpose", sop.purpose, "",
         "## 2. Scope", sop.scope, ""]

    L += ["## 3. Roles and Responsibilities"]
    roles = sop.roles()
    if roles:
        L += ["| Role | Responsibilities (from the steps) |", "|---|---|"]
        L += [f"| {r} | {t} |" for r, t in roles]
    else:
        L += ["_No owners identified yet_"]

    L += ["", "## 4. Prerequisites"]
    L += [f"- {p}" for p in sop.prerequisites] or ["_None specified_"]

    L += ["", "## 5. Definitions and Criteria"]
    L += [f"- {d}" for d in sop.definitions] or ["_None specified_"]

    L += ["", "## 6. Procedure"]
    for s in sop.steps:
        cond = f" *(If {s.condition})*" if s.condition else ""
        owner = f" *(Owner: {s.owner})*" if s.owner else ""
        when = f" **[{s.timeline}]**" if s.timeline else ""
        L.append(f"{s.number}. {s.action}{cond}{owner}{when}")
        if s.notes:
            L.append(f"   - Note: {s.notes}")

    L += ["", "## 7. Exceptions and Troubleshooting"]
    if sop.exceptions:
        L += ["| Situation | Action | Owner | Timeline |", "|---|---|---|---|"]
        for e in sop.exceptions:
            L.append(f"| {e.situation} | {e.action or '_Not defined_'} | "
                     f"{e.owner or '_Not defined_'} | {e.timeline or '_Not defined_'} |")
    else:
        L += ["_None specified_"]

    L += ["", "## 8. Review Information", sop.review_info or "_Not specified_"]
    return "\n".join(L)