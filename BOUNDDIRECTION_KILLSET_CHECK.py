"""
Kill-set + rubric gate for BoundDirection (project WhichWay).

GATE 1  no token or bigram may separate the two classes.
GATE 2  the rubric may share no content word with any case.
        (No stemming: 'pay' and 'paid' look different to it, so a green gate
         still needs a human read of the rubric.)

Run:  python3 BOUNDDIRECTION_KILLSET_CHECK.py
      python3 BOUNDDIRECTION_KILLSET_CHECK.py rubrics/BoundDirection.txt
      python3 BOUNDDIRECTION_KILLSET_CHECK.py contracts/BoundDirection.py
"""

import re
import sys

DECLARED = "the recorded amount"

CASES = {
    "IS_MINIMUM": {
        "F1": "Staffing on site must not drop below the agreed level.",
        "F2": "We guarantee the agreed number of hours each week.",
        "F3": "Anything under the agreed figure counts as a shortfall.",
        "F4": "The agreed figure is the least we will provide.",
        "F5": "Falling short of the agreed quantity is a breach on our part.",
    },
    "IS_MAXIMUM": {
        "C1": "Charges will never exceed the agreed figure.",
        "C2": "The agreed figure is a cap, not a goal.",
        "C3": "Anything over the agreed quantity is at our own expense.",
        "C4": "We keep consumption inside the agreed allowance.",
        "C5": "The agreed figure is the most we will provide.",
    },
}

PAIRS = [
    ["F4", "C5", "nine words, identical except least/most"],
    ["F3", "C3", "both open with the same words and both set a consequence"],
    ["F1", "C1", "both are negative"],
    ["F2", "C4", "neither uses a comparison word"],
    ["F5", "C2", "both name the thing itself rather than a direction"],
]

MUST_REVERT = {
    "N1": "The agreed figure applies to this work.",
    "N2": "The agreed figure governs this engagement.",
}


def features(text):
    tok = re.findall(r"[a-z]+", text.lower())
    result = set(tok)
    result.update(" ".join(pair) for pair in zip(tok, tok[1:]))
    return result


def leaks(case_set):
    sides = {
        key: {name: features(text) for name, text in values.items()}
        for key, values in case_set.items()
    }
    names = list(sides)
    result = []
    for index, name in enumerate(names):
        other = names[1 - index]
        common = set.intersection(*sides[name].values())
        absent = set().union(*sides[other].values())
        result += [(name, feature) for feature in sorted(common - absent)]
    return result


STOP = set(
    """a an and are as at be been by do does for from has have in into is it its
of on or our that the their them there these this to us we will with your you not no
if any each one two both same other than then when where which while who whom what""".split()
)


def content_words(text):
    return {
        word
        for word in re.findall(r"[a-z]+", text.lower())
        if word not in STOP and len(word) > 2
    }


flat = {}
for group in CASES.values():
    flat.update(group)

all_texts = dict(flat)
all_texts.update(MUST_REVERT)

print("=" * 74)
print("DECLARED CONTEXT:", DECLARED)
print("=" * 74)

found = leaks(CASES)
if found:
    print(f"LEAK: {len(found)} separating feature(s) — set is NOT usable:")
    for side, feature in found:
        print(f"   {feature!r:32s} -> in ALL {side}, in NO case of the other class")
else:
    print("NO LEAK: no token or bigram separates the two classes.")

print()
print("Adversarial pairs (same surface, opposite label):")
for first, second, why in PAIRS:
    print(f"   {first} / {second}  - {why}")

print()
if MUST_REVERT:
    print()
    print("Must-REVERT texts (not in gate 1; the open method must raise on each):")
    for name, text in sorted(MUST_REVERT.items()):
        print(f"   {name}  {text}")

print()
print("Byte length per case (255-byte calldata cliff; method name + 64-hex id add more):")
for name, text in sorted(all_texts.items()):
    size = len(text.encode("utf-8"))
    print(f"   {name}  {size:3d} bytes{'   <-- CHECK' if size > 150 else ''}")


def rubric_text(path):
    source = open(path, encoding="utf-8").read()
    if path.endswith(".txt"):
        return source
    match = re.search(r'RUBRIC\s*=\s*f?"""(.*?)"""', source, re.S)
    return match.group(1) if match else None


def rubric_overlap(path):
    body = rubric_text(path)
    if body is None:
        print("\ncould not find a RUBRIC block in", path)
        return 1
    case_words = set()
    for text in all_texts.values():
        case_words |= content_words(text)
    overlap = sorted(content_words(body) & case_words)
    print()
    print("=" * 74)
    print("RUBRIC OVERLAP GATE —", path)
    print("=" * 74)
    if overlap:
        print(f"FAIL: {len(overlap)} content word(s) shared with the case set:")
        for word in overlap:
            print("   ", word)
        print("The rubric defines the TASK. It never quotes an answer.")
        return 1
    print("PASS: rubric shares no content word with any case.")
    print("      (No stemming — read the rubric yourself for near-matches.)")
    return 0


print("=" * 74)
if len(sys.argv) > 1:
    sys.exit((1 if found else 0) or rubric_overlap(sys.argv[1]))
sys.exit(1 if found else 0)
