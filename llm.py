"""One function that talks to any LLM and returns a validated Pydantic object.
Set LLM_PROVIDER to: gemini | anthropic | openai  (default: gemini)
"""
import json
import os
import re

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


def _raw_call(system: str, user: str) -> str:
    if PROVIDER == "gemini":
        from google import genai
        client = genai.Client()  # reads GEMINI_API_KEY
        r = client.models.generate_content(
            model=os.getenv("LLM_MODEL", "gemini-3.5-flash-lite"),
            contents=user,
            config={"system_instruction": system,
                    "response_mime_type": "application/json"},
        )
        return r.text
    if PROVIDER == "anthropic":
        import anthropic
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        r = client.messages.create(
            model=os.getenv("LLM_MODEL", "claude-sonnet-5-5"),
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return r.content[0].text
    if PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI()  # reads OPENAI_API_KEY
        r = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return r.choices[0].message.content
    raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}")


def ask(system: str, user: str, schema):
    """Call the LLM, validate the JSON against `schema`, retry once if invalid."""
    system += "\n\nReturn ONLY valid JSON matching this JSON schema:\n" + json.dumps(
        schema.model_json_schema()
    )
    for attempt in range(2):
        text = _raw_call(system, user)
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        try:
            return schema.model_validate_json(text)
        except Exception as e:
            user += f"\n\nYour last output was invalid ({e}). Return corrected JSON only."
    raise RuntimeError("LLM did not return valid JSON after 2 tries")
