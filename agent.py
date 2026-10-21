from llm import ask
from schemas import SOP, GapReport

RULES = (
    "Never invent details. If something is not stated, use null or leave the list "
    "empty instead of guessing. Write steps as short, actionable sentences starting "
    "with a verb, understandable by someone with no technical knowledge. Keep roles "
    "and names exactly as mentioned. Capture every status/stage name, follow-up "
    "timeline and success criterion mentioned (put status meanings and conversion "
    "criteria in 'definitions', timings in each step's 'timeline'). "
    "OWNER RULE: set a step's owner ONLY if the text clearly says who does it. "
    "If the text says 'we', uses passive voice, or says nothing, set owner to null. "
    "Do not attach a rule to a person, status or condition unless the text links them. "
    "The title must be a short process name and must not contain the word 'SOP'. "
    "For exceptions, 'situation' is a short condition (e.g. 'Client does not show "
    "up for the site visit'), 'action' is what to do. Do not invent actions. "
    "If the text only says what goes wrong (e.g. 'we forget to reschedule'), "
    "set 'action' to null; never restate the problem as the action. "
    "Put 'if ...' conditions of a step in 'condition', not in notes, and do not "
    "repeat the scope in notes. Every action in the text, including status changes "
    "(mark as cold, mark closed-won), must appear as a step, with owner null if "
    "unclear. In 'roles', list only responsibilities the text explicitly assigns "
    "to that role; if the text says 'we', do not assign it to any role."
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
        "problems. Do not ask about things the SOP already states. "
        "If the SOP is already complete, return an empty list."
    )
    return ask(system, sop.model_dump_json(indent=2), GapReport).questions


def refine(sop: SOP, qa: list[tuple[str, str]]) -> SOP:
    """Call 3: merge the human's answers into the SOP."""
    answers = "\n".join(f"Q: {q}\nA: {a}" for q, a in qa)
    system = (
        "You update an SOP using the answers a human gave. Keep everything "
        "that is still correct, add the new information in the right place "
        "(roles, steps, timelines, definitions, exceptions, review info), and "
        "renumber steps. Apply each answer ONLY to the item its question is about, "
        "leave unrelated parts unchanged, and never create duplicate rows (update "
        "the existing one instead). " + RULES
    )
    user = f"Current SOP:\n{sop.model_dump_json(indent=2)}\n\nAnswers:\n{answers}"
    return ask(system, user, SOP)


def to_markdown(sop: SOP) -> str:
    L = [f"# SOP: {sop.display_title()}", "",
         "## 1. Purpose", sop.purpose, "",
         "## 2. Scope", sop.scope, ""]

    L += ["## 3. Roles and Responsibilities"]
    if sop.roles:
        L += ["| Role | Responsibility |", "|---|---|"]
        L += [f"| {r.role} | {r.responsibility} |" for r in sop.roles]
    else:
        L += ["_Not specified_"]

    L += ["", "## 4. Prerequisites"]
    L += [f"- {p}" for p in sop.prerequisites] or ["_None specified_"]

    L += ["", "## 5. Definitions and Criteria"]
    L += [f"- {d}" for d in sop.definitions] or ["_None specified_"]

    L += ["", "## 6. Procedure"]
    for s in sop.steps:
        owner = f" *(Owner: {s.owner})*" if s.owner else ""
        when = f" **[{s.timeline}]**" if s.timeline else ""
        cond = f" *(If {s.condition})*" if s.condition else ""
        L.append(f"{s.number}. {s.action}{cond}{owner}{when}")
        if s.notes:
            L.append(f"   - Note: {s.notes}")

    L += ["", "## 7. Exceptions and Troubleshooting"]
    if sop.exceptions:
        L += ["| Situation | What to do |", "|---|---|"]
        L += [f"| {e.situation} | {e.action or '_Not defined_'} |" for e in sop.exceptions]
    else:
        L += ["_None specified_"]

    L += ["", "## 8. Review Information", sop.review_info or "_Not specified_"]
    return "\n".join(L)