"""Score the SOP agent against known facts.   Usage:  python run_eval.py [runs_per_case] [--show]
Measures RECALL (did it capture the facts?) and PRECISION problems (invented owners,
owners where the text says 'we', quotes not found in the source). Runs each case several
times because LLM output changes from run to run."""
import re
import sys

from eval_cases import CASES
from grounding import check_grounding

_STOP = {"the", "a", "an", "team", "of", "and", "or", "to"}


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def items(sop):
    out = []
    for s in sop.steps:
        text = " ".join(x for x in [s.action, s.owner, s.condition, s.timeline, s.notes] if x)
        out.append(("step", text.lower(), s.owner))
    for e in sop.exceptions:
        text = " ".join(x for x in [e.situation, e.action, e.owner, e.timeline] if x)
        out.append(("exception", text.lower(), e.owner))
    for d in list(sop.definitions) + list(sop.prerequisites):
        out.append(("definition", d.lower(), None))
    return out


def _match(text: str, reqs: list[str]) -> bool:
    return all(any(alt in text for alt in r.split("|")) for r in reqs)


def score(sop, case) -> dict:
    its = items(sop)
    steps = [i for i in its if i[0] == "step"]
    passed, failed = [], []
    for f in case["facts"]:
        if "all" in f:
            ok = any(_match(t, f["all"]) for _, t, _ in its)
        else:
            a, b = f["before"]
            ia = next((n for n, (_, t, _) in enumerate(steps) if _match(t, a)), None)
            ib = next((n for n, (_, t, _) in enumerate(steps) if _match(t, b)), None)
            ok = ia is not None and ib is not None and ia < ib
        (passed if ok else failed).append(f["name"])

    src_words = set(_norm(case["text"]).split())
    invented = []
    for _, _, owner in its:
        words = [w for w in _norm(owner or "").split() if w not in _STOP]
        if words and not any(w in src_words for w in words):
            invented.append(owner)

    owner_violations = [
        kw[0] for kw in case["unowned"]
        if any(k == "step" and _match(t, kw) and o for k, t, o in its)
    ]
    return {
        "passed": passed, "failed": failed, "invented": invented,
        "owner_violations": owner_violations,
        "quote_warnings": len(check_grounding(sop, case["text"])),
    }


def main(runs: int, show: bool = False):
    from agent import extract  # imported here so scoring can be tested without an LLM
    for case in CASES:
        total = len(case["facts"])
        fail_count: dict[str, int] = {}
        recalls, invented, viol, qw, errors = [], 0, 0, [], 0
        for r in range(runs):
            try:
                sop = extract(case["text"])
                res = score(sop, case)
            except Exception as e:  # API/JSON failure counts as an error, not a crash
                errors += 1
                print(f"  run {r + 1}: ERROR {e}")
                continue
            recalls.append(len(res["passed"]) / total)
            invented += len(res["invented"])
            viol += len(res["owner_violations"])
            qw.append(res["quote_warnings"])
            for name in res["failed"]:
                fail_count[name] = fail_count.get(name, 0) + 1
            print(f"  run {r + 1}: {len(res['passed'])}/{total} facts, "
                  f"invented owners: {res['invented']}, owner violations: {res['owner_violations']}")
            if show and (res["failed"] or res["owner_violations"] or res["quote_warnings"]):
                from agent import to_markdown
                print(f"    missed: {res['failed']}\n")
                print("    --- SOP from this run ---")
                print("\n".join("    " + ln for ln in to_markdown(sop).splitlines()))
                for w in check_grounding(sop, case["text"]):
                    print("    warning:", w)
                print()
        ok_runs = runs - errors
        print(f"\n== {case['name']} ==")
        if ok_runs:
            print(f"recall: {100 * sum(recalls) / ok_runs:.0f}% average over {ok_runs} run(s)")
            print(f"invented owners: {invented} | owner-rule violations: {viol} | "
                  f"avg quote warnings: {sum(qw) / ok_runs:.1f}")
            for name, n in sorted(fail_count.items(), key=lambda x: -x[1]):
                print(f"  MISSED {n}/{ok_runs} runs: {name}")
        print()


if __name__ == "__main__":
    nums = [a for a in sys.argv[1:] if a.isdigit()]
    main(int(nums[0]) if nums else 3, show="--show" in sys.argv)