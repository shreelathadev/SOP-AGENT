from llm import ask
from schemas import SOP, GapReport, RefineResult

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
    "says 'we', uses passive voice, or says nothing, set owner to null. Passive voice means there is no actor: 'the lead is marked Unreachable', 'feedback is entered in the CRM' and 'the lead goes back to Nurture' all have NO owner, even if one role does most of the other steps. Do not attach "
    "a rule to a person, status or condition unless the text links them. "
    "EVERY action in the text, including status changes (mark as cold, mark closed-won), "
    "must appear as a step. Put 'if ...' conditions in 'condition', not in notes, and do "
    "not repeat the scope in notes. The title is a short process name without the word "
    "'SOP'. "
    "OWNER NAMES: write a role as a short noun phrase with no article (e.g. 'sales exec', "
    "not 'the exec'). If the text refers to one role in different ways (e.g. 'the sales "
    "exec' and 'the exec'), use the fullest name everywhere. "
    "CONDITIONS: a short clause WITHOUT a leading 'if', 'when', 'once' or 'after' (e.g. "
    "'the client likes the property', 'the discount is above 2%'). Put pure timing "
    "relations such as 'after the visit' in 'timeline'. "
    "APPROVALS: if the text says someone must approve, check or sign off before an action, "
    "make that approval its own step (owner = the approver) placed BEFORE the action it "
    "gates. If approval depends on a threshold (e.g. discount tiers), make one step per level, with the approver as owner and the threshold in the condition. ONE ACTION PER STEP: split steps joined by 'and' when the parts have different timings or owners (a confirmation 24 hours before and a reminder 2 hours before are two steps). ACTORS: every person or team the text gives a duty to, including monitoring or "
    "oversight duties, must own a step or an exception. QUALIFIERS such as 'based on the "
    "role in the offer letter' must be kept in the step's notes (not in 'condition'). PREREQUISITES are only things the text says must exist or be done before the process starts; never restate the process trigger and never invent them. Every step names what it acts on (not 'Monitor progress' but 'Monitor the employee's cybersecurity training progress'). "
    "DETAIL: keep named lists and examples (tools, documents, systems, amounts) exactly as "
    "written; never replace them with a general phrase such as 'internal tools'. "
    "EXCEPTIONS are deviations from the normal path. 'situation' is a short condition, "
    "'action' says what to do WITHOUT naming who (the name goes in 'owner'). If the text "
    "only says what goes wrong (e.g. 'we forget to reschedule'), set 'action' to null; "
    "never restate the problem as the action. If an exception involves several actors, make one row per actor and action (same situation). The situation must make sense on its own (e.g. 'documents are still not submitted after the 3-day grace period', never just 'still not submitted'). "
    "EVIDENCE RULE: for every step and exception, set 'source_quote' to the EXACT words, "
    "copied character for character, from the process text or from the human's answers "
    "that support it, as the whole clause INCLUDING who does the action (e.g. 'the SE books a site visit within 3 days', not just 'books a site visit'). Never paraphrase a quote. If no words support it, set null."
)


def extract(raw_text: str) -> SOP:
    """Call 1: messy text -> structured SOP draft."""
    system = (
        "You are an operations analyst who writes Standard Operating Procedures "
        "(SOPs) from messy descriptions of how work is done. " + RULES
    )
    draft = ask(system, f"Process description:\n\n{raw_text}", SOP)
    return complete(raw_text, draft)


def complete(raw_text: str, draft: SOP) -> SOP:
    """Call 1b: completeness pass. Add anything the text says that the draft missed."""
    system = (
        "You audit an SOP draft against the original process text. Find every fact in the "
        "text that is missing from the draft: people or teams with a duty, approvals or "
        "'must approve first' gates, approval levels or thresholds (e.g. discount tiers), monitoring or oversight duties, conditions, "
        "qualifiers, timelines and exceptions. Return the SOP with the missing items ADDED "
        "in the right place and the steps numbered in process order. Do not remove or "
        "reword anything that is already correct, and do not add anything the text does "
        "not say. Every addition needs an exact source_quote. " + RULES
    )
    user = f"Process text:\n\n{raw_text}\n\nDraft SOP:\n{draft.model_dump_json(indent=2)}"
    done = ask(system, user, SOP)
    # Safety net: an audit may only ADD. If it lost steps or exceptions, keep the draft.
    if len(done.steps) < len(draft.steps) or len(done.exceptions) < len(draft.exceptions):
        return draft
    return done


def find_gaps(sop: SOP) -> list[str]:
    """Call 2: review the draft, return questions about what is missing."""
    system = (
        "You are a strict SOP reviewer. Find missing or ambiguous information and "
        "ask at most 5 specific, answerable questions. Prioritise by impact, in "
        "this order: (1) steps with a null owner (ask ONE combined question that lists all such steps by number and name, e.g. 'Who is responsible for steps 5, 8 and 10?'), (2) missing end states or "
        "statuses (e.g. what happens when a deal is lost), (3) exceptions with no "
        "owner, action or timing, (4) vague decision rules ('interested', 'likes the "
        "property'), (5) missing timelines, then missing prerequisites and review "
        "owner/frequency. Also ask ONE question when different role names may mean the "
        "same role (e.g. 'IT', 'IT team' and 'IT admin', or 'candidate' and 'employee'), and "
        "one when an escalation or approval has no owner for its outcome (e.g. who "
        "suspends the account?). Ask at most 2 timeline questions in total, and never "
        "more than 2 questions of the same kind, so the questions cover different "
        "problems. Refer to steps by number, and mention each step in only one question. Never combine steps and exceptions in "
        "one question. Do not ask about things the SOP "
        "already states. If the SOP is already complete, return an empty list."
    )
    return ask(system, sop.model_dump_json(indent=2), GapReport).questions


def refine(sop: SOP, qa: list[tuple[str, str]]) -> RefineResult:
    """Call 3: merge the human's answers into the SOP."""
    answers = "\n".join(f"Q: {q}\nA: {a}" for q, a in qa)
    system = (
        "You update an SOP using the answers a human gave. Keep everything that is "
        "still correct, add the new information in the right place, and renumber "
        "steps. Apply each answer ONLY to the item its question is about, leave "
        "unrelated parts unchanged, and never create duplicate rows (update the "
        "existing one instead). For anything you add or change from an answer, set "
        "'source_quote' to the exact words of that answer. Keep existing quotes "
        "unchanged. "
        "If an answer says two role names mean the same role, use one name for that role "
        "everywhere in the SOP. "
        "VALIDATE EVERY ANSWER FIRST. Answers are SUPPOSED to add information that is not in "
        "the original process text (new statuses, owners, timelines, prerequisites, review "
        "info), so new information is never a reason to reject. Reject an answer ONLY if "
        "(a) it answers a different question than the one asked (e.g. a timeline given for "
        "a 'who is responsible' question), (b) it is too vague to use (e.g. 'as needed', "
        "'ASAP'), or (c) it is impossible or self-contradictory. If you reject, leave that "
        "item of the SOP unchanged and list the answer in 'rejected' with a one-sentence "
        "reason that names the problem. If a valid answer disagrees with something an "
        "earlier answer set (e.g. a different definition of 'interested'), the newest "
        "answer replaces it. Never overwrite a value from the original process text (an "
        "owner, a timeline) unless the answer is clearly about that exact item. "
        "A lost-deal answer such as 'Closed-Lost' or 'mark it closed-lost' is valid: add a "
        "definition for that status and a step that sets it, with the condition 'the deal "
        "is lost or rejected'. If an answer defines a term (e.g. what 'interested' means), "
        "add it to 'definitions' and keep the term itself in the step's condition. Split a "
        "multi-part answer across the fields: 'calls back within 4 hours, max 3 attempts' "
        "becomes action 'Call back, with a maximum of 3 attempts', timeline 'within 4 "
        "hours'. A 'timeline' is a short time expression like 'within 24 hours', never a "
        "sentence. Fix spelling and grammar in anything you write (but never inside a "
        "source_quote, which must stay exact). "
        "Return JSON with the keys 'sop' and 'rejected'. " + RULES
    )
    user = f"Current SOP:\n{sop.model_dump_json(indent=2)}\n\nAnswers:\n{answers}"
    return ask(system, user, RefineResult)


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