# SOP Creation Agent

Turns a messy process description into a structured SOP, asks about missing info, and refines.
Output: Markdown + PDF. Template: Purpose, Scope, Roles, Prerequisites, Definitions, Procedure, Exceptions, Review.

## Run
    pip install -r requirements.txt
    export LLM_PROVIDER=gemini        # or anthropic / openai
    export GEMINI_API_KEY=...         # or ANTHROPIC_API_KEY / OPENAI_API_KEY
    streamlit run app.py

## Flow
Extract (LLM call 1) -> Gap finder (call 2) -> human answers -> Refine (call 3) -> Markdown / PDF export

## Test case
Real estate CRM: new property inquiry -> site visit -> closed deal (pre-filled in the app).
