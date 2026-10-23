# SOP Creation Agent

Turns a messy description of a business process (pasted text, transcript, or an uploaded
.txt / .md / .pdf / .docx) into a clear Standard Operating Procedure. Instead of guessing
what is missing, the agent asks the user and updates the SOP from the answers.

Output: Markdown and PDF, using a standard SOP template (Purpose, Scope, Roles and
Responsibilities, Prerequisites, Definitions and Criteria, Procedure, Exceptions and
Troubleshooting, Review Information).

## Run it
    pip install -r requirements.txt
    set LLM_PROVIDER=gemini            (Windows; use export on Mac/Linux)
    set GEMINI_API_KEY=your_key        (or ANTHROPIC_API_KEY / OPENAI_API_KEY)
    set LLM_MODEL=gemini-3.5-flash-lite   (optional)
    streamlit run app.py

Never commit API keys. Keys are read from environment variables only.

## How it works
1. **Extract** - the LLM fills a fixed SOP schema (Pydantic validates the JSON).
2. **Completeness pass** - a second call adds anything the text mentions that the draft
   missed (approvals, people with duties, qualifiers, exceptions). It may only add.
3. **Gap finder** - a reviewer call asks up to 5 targeted questions (missing owners,
   undefined statuses, exceptions with no action, same role under different names).
4. **Refine** - the user's answers are merged into the SOP. Each answer is validated first;
   wrong-topic or too-vague answers are rejected with a reason instead of being applied.

Design choices: plain Python (no LangChain/LangGraph), no RAG (a process description fits in
one prompt), structured output with Pydantic.

## Accuracy features
- **Owner rule:** an owner is set only if the text says who does the step ("we" and passive
  sentences leave it empty and become a question).
- **Evidence quotes:** every step/exception carries the exact words from the source. Code
  (not the LLM) checks the quote exists and names the owner; problems show as warnings.
- **Roles table built in code** from the step owners, so it cannot disagree with the Procedure.
- **Answer validation** with visible "Not applied" messages.

## Evaluation
    python run_eval.py 10 --show > eval_out.txt
`eval_cases.py` holds test processes plus the facts each SOP must contain; `run_eval.py`
runs each case several times and reports recall, invented owners, owner-rule violations
and quote warnings. Add a case by copying an existing one.

### Results
| Case | Runs | Recall | Owner violations | Avg quote warnings |
|---|---|---|---|---|
| real_estate_crm | | | | |
| employee_onboarding | | | | |
| greenfield_pdf | 10 | 98% | 0 | 1.6 |

(Fill the empty rows from `eval_out.txt`.)

## Known limitations
- The eval checks extraction only (not the refine step) and uses keyword matching, so a
  miss can be a wording difference. Only 3 test processes; all were used while tuning
  prompts, so scores are optimistic. Not yet tested on real transcripts or client documents.
- The evidence check covers steps and exceptions, not Prerequisites/Definitions, and it
  checks that a quote exists, not that the step's meaning matches it.
- Scanned PDFs are not supported (needs OCR). Files are cut at 40,000 characters.
- Process text is sent to the LLM provider's API; check data-handling needs before using
  confidential documents.
- No login, saved SOPs, versioning, in-app editing or Word export. State lives in the
  browser session only.
- LLM output varies between runs. Tested with one model (gemini-3.5-flash-lite).

## Files
`app.py` UI | `agent.py` prompts and pipeline | `schemas.py` data model | `grounding.py`
evidence checks | `llm.py` provider wrapper | `extract.py` file reading | `pdf_export.py`
PDF output | `run_eval.py`, `eval_cases.py` evaluation | `samples/` test documents