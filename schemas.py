import re

from pydantic import BaseModel, Field, field_validator


def _clean_owner(v):
    """'The manager' -> 'manager' so one role never appears under two names."""
    if not v:
        return None
    v = re.sub(r"^(the|a|an)\s+", "", v.strip(), flags=re.I).strip()
    return v or None


def _lower_first(v):
    """'Within 24 hours' -> 'within 24 hours' so timelines read consistently."""
    if v and not v[:2].isupper():
        return v.strip()[:1].lower() + v.strip()[1:]
    return v or None


def _cap_first(v):
    return v[:1].upper() + v[1:] if v else v


def _clean_condition(v):
    """Drop a leading 'if/when/once' (the display adds 'If') and lowercase the first letter."""
    if not v:
        return None
    v = re.sub(r"^(if|when|once)\s+", "", v.strip(), flags=re.I).strip()
    if v and not v[:2].isupper():
        v = v[:1].lower() + v[1:]
    return v or None


class Step(BaseModel):
    number: int
    action: str = Field(description="One clear action, starts with an imperative verb")
    owner: str | None = Field(default=None, description="Who does it; null if the text does not clearly say")
    condition: str | None = Field(default=None, description="Only do this if..., e.g. 'the client likes the property'; null if always")
    timeline: str | None = Field(default=None, description="Deadline or follow-up timing; null if not stated")
    notes: str | None = None
    source_quote: str | None = Field(
        default=None,
        description="EXACT words copied from the input text (or the human's answers) that support this step; null if none",
    )

    _owner = field_validator("owner")(_clean_owner)
    _cond = field_validator("condition")(_clean_condition)
    _timeline = field_validator("timeline")(_lower_first)


class ExceptionCase(BaseModel):
    situation: str = Field(description="Short condition, e.g. 'Client does not show up for the site visit'")
    action: str | None = Field(default=None, description="Corrective action WITHOUT naming who does it; null if the text gives none")
    owner: str | None = Field(default=None, description="Who handles it; null if not stated")
    timeline: str | None = Field(default=None, description="Deadline for the action; null if not stated")
    source_quote: str | None = Field(default=None, description="EXACT words copied from the input that support this; null if none")

    _owner = field_validator("owner")(_clean_owner)
    _timeline = field_validator("timeline")(_lower_first)
    _action = field_validator("action")(_cap_first)


class SOP(BaseModel):
    title: str
    purpose: str
    scope: str = Field(description="When this SOP applies and when it does not")
    prerequisites: list[str] = Field(default=[], description="What must be ready before starting")
    definitions: list[str] = Field(
        default=[],
        description="Key terms and criteria, e.g. status names and what each means, conversion criteria",
    )
    steps: list[Step]
    exceptions: list[ExceptionCase] = []
    review_info: str | None = Field(default=None, description="Who reviews this SOP and how often; null if not stated")

    def display_title(self) -> str:
        """Title without a duplicated 'SOP' word, e.g. 'X SOP' -> 'X'."""
        return re.sub(r"^\s*SOP:?\s*|\s+SOP\s*$", "", self.title, flags=re.I).strip()

    def roles(self) -> list[tuple[str, str]]:
        """Roles table built in plain code from the step/exception owners.
        Because no LLM writes it, it can never disagree with the Procedure."""
        names: dict[str, str] = {}
        grouped: dict[str, list[str]] = {}

        def add(owner: str | None, text: str):
            if not owner or not owner.strip():
                return
            key = owner.strip().lower()
            names.setdefault(key, owner.strip())
            grouped.setdefault(key, []).append(text)

        for s in self.steps:
            add(s.owner, s.action)
        for e in self.exceptions:
            if e.action:
                add(e.owner, f"{e.action} (if {e.situation[:1].lower() + e.situation[1:]})")
        return [(names[k], "; ".join(v)) for k, v in grouped.items()]


class RejectedAnswer(BaseModel):
    question: str
    answer: str
    reason: str = Field(description="One sentence: why this answer was not applied")


class RefineResult(BaseModel):
    sop: SOP
    rejected: list[RejectedAnswer] = Field(
        default=[], description="Answers that did not answer their question and were NOT applied"
    )


class GapReport(BaseModel):
    questions: list[str] = Field(description="Specific questions about missing info")