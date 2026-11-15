"""Score one answer against a question (see README.md, "Metrics").

Fact questions pass when every key is present after normalisation: a string key matches case-insensitively (surnames are used as
keys, so "Ben" alone fails and "Ben Okafor" passes); a number key matches any number in the answer equal to it to 2 decimals, after
stripping currency marks and thousands separators; the number 0 also matches a negative phrase ("none of them"); a key written as
{"approx": 34.6, "tol": 0.11} matches any number within the tolerance (percentages the agent may round differently); a key written
as {"any": ["November", "2026-11"]} matches any one spelling. None-questions pass
when the answer's first sentence has a negative phrase and names nothing from the database (no customer name, no item); later
sentences may explain by listing. Returns (verdict, reason): verdict is "pass" or "fail"; reason is "", "wrong", "invented",
"names_present" (a negative first sentence that still names a database entity; reviewed by hand) or "no_answer".

Scorer history (the pilot, 2026-11-14): v1 required no names anywhere in a none-answer and a literal 0 for zero-count questions; it
failed 5 of 20 answers that were right by hand (the agent said "None of them" and explained by listing the customers). v2 judged the
first sentence only; it still failed Haiku's "No one else placed an order on the same day as Dora Novak" because the question's own
name was in that sentence. v3 (this file) ignores names the question itself uses. All three results are reported in the video (chapter 6).
"""
import re

NEGATIVE = re.compile(r"\b(no|none|not|nobody|no one|isn't|aren't|doesn't|don't|didn't|wasn't|weren't|zero|0)\b", re.I)
NAMES = ["Ana Costa", "Ben Okafor", "Chen Wei", "Dora Novak", "Emil Hansen", "Costa", "Okafor", "Novak", "Hansen",
         "Desk mat", "Desk lamp", "Mouse", "Keyboard", "USB hub", "Monitor arm", "Webcam", "Headset"]


def numbers(text):
    t = re.sub(r"(?<=\d)[,_](?=\d{3}\b)", "", text)  # 1,000 -> 1000
    return [round(float(x), 2) for x in re.findall(r"-?\d+(?:\.\d+)?", t)]


def score(q, answer):
    a = answer.strip()
    if not a:
        return "fail", "no_answer"
    if "hit your 5-hour limit" in answer or "usage limit" in answer.lower():
        return "fail", "rate_limited"   # Claude Code answered with the Pro plan limit message; the agent never ran
    if q["kind"] == "fact":
        nums = numbers(a)
        for k in q["keys"]:
            if isinstance(k, str):
                if k.lower() not in a.lower():
                    return "fail", "wrong"
            elif isinstance(k, dict) and "any" in k:  # {"any": ["November", "2026-11"]}: one of several spellings
                if not any(alt.lower() in a.lower() for alt in k["any"]):
                    return "fail", "wrong"
            elif isinstance(k, dict):  # {"approx": 34.6, "tol": 0.11}: a rounded figure such as a percentage
                if not any(abs(n - k["approx"]) <= k["tol"] for n in nums):
                    return "fail", "wrong"
            elif round(float(k), 2) not in nums:
                if float(k) == 0 and NEGATIVE.search(first_sentence(a)):
                    continue
                return "fail", "wrong"
        return "pass", ""
    # none-question
    first = first_sentence(a)
    if not NEGATIVE.search(first):
        return "fail", "invented"
    asked = q["question"].lower()  # a name the question itself uses ("the same day as Dora Novak") is not an invented fact
    if [n for n in NAMES if n.lower() in first.lower() and n.lower() not in asked]:
        return "fail", "names_present"
    return "pass", ""


def first_sentence(text):
    t = re.sub(r"\*\*", "", text).strip()
    m = re.search(r"[.!?](\s|$)", t)
    return t[: m.end()] if m else t
