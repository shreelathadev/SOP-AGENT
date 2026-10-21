import re

from pydantic import BaseModel, Field


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


class ExceptionCase(BaseModel):
    situation: str = Field(description="Short condition, e.g. 'Client does not show up for the site visit'")
    action: str | None = Field(default=None, description="Corrective action WITHOUT naming who does it; null if the text gives none")
    owner: str | None = Field(default=None, description="Who handles it; null if not stated")
    timeline: str | None = Field(default=None, description="Deadline for the action; null if not stated")
    source_quote: str | None = Field(default=None, description="EXACT words copied from the input that support this; null if none")


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


class GapReport(BaseModel):
    questions: list[str] = Field(description="Specific questions about missing info")