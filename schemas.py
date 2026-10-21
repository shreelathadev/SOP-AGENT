import re

from pydantic import BaseModel, Field


class Role(BaseModel):
    role: str = Field(description="Job title or team, exactly as mentioned")
    responsibility: str


class Step(BaseModel):
    number: int
    action: str = Field(description="One clear action, starts with a verb")
    owner: str | None = Field(default=None, description="Who does it, null if not stated")
    condition: str | None = Field(default=None, description="Only do this if..., e.g. 'the client likes the property'; null if always")
    timeline: str | None = Field(default=None, description="Deadline or follow-up timing, null if not stated")
    notes: str | None = None


class ExceptionCase(BaseModel):
    situation: str = Field(description="What goes wrong or deviates")
    action: str | None = Field(default=None, description="Corrective action; null if the text gives none")


class SOP(BaseModel):
    title: str
    purpose: str
    scope: str = Field(description="When this SOP applies and when it does not")
    roles: list[Role] = []
    prerequisites: list[str] = Field(default=[], description="What must be ready before starting")
    definitions: list[str] = Field(
        default=[],
        description="Key terms and criteria, e.g. status names and what each means, conversion criteria",
    )
    steps: list[Step]
    exceptions: list[ExceptionCase] = []
    review_info: str | None = Field(default=None, description="Who reviews this SOP and how often, null if not stated")

    def display_title(self) -> str:
        """Title without a duplicated 'SOP' word, e.g. 'X SOP' -> 'X'."""
        return re.sub(r"^\s*SOP:?\s*|\s+SOP\s*$", "", self.title, flags=re.I).strip()


class GapReport(BaseModel):
    questions: list[str] = Field(description="Specific questions about missing info")