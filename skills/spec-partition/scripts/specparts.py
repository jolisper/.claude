"""Shared parsing and reference handling for the spec-partition scripts.

Not a CLI. Imported by plan-partition.py, write-partition.py and verify-partition.py so
all three read a functional-spec.md the same way.
"""
import json
import re
import sys

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BOLD_HEADING = re.compile(r"^\*\*([^*]+?)\*\*\s*:?\s*$")
ITEM = re.compile(r"^(\d+)[.)]\s+(.*)$")
LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")

# "<part-dir> invariant N": part dirs are <name>-<NN>-<slug>, optionally backticked.
PART_DIR = r"`?[\w.\-/]*?([\w.\-]+-\d{2}-[\w\-]+)/?`?"
CITATION = re.compile(PART_DIR + r"\s+[Ii]nvariants?\s+(\d+(?:\s*(?:,|and|or|&)\s*\d+)*)")
PREFIX = re.compile(PART_DIR + r"\s+(?=[Ii]nvariants?\b)")
NUMS = re.compile(r"\b([Ii]nvariants?)\s+\d+(?:\s*(?:,|and|or|&|to|–|-)\s*\d+)*")
REF = re.compile(r"\b([Ii]nvariants?)(\s+)(\d+(?:\s*(?:,|and|or|&|to|–|-)\s*\d+)*)")
SEP = re.compile(r"\s*(?:,|and|or|&)\s*")
RANGE = re.compile(r"\s*(?:to|–|-)\s*")


def die(msg, hint):
    print("status=error")
    print(f"message={msg}")
    print(f"hint={hint}")
    sys.exit(2)


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}", "check the path; parts are <root>/initiatives/<name>-<NN>-<slug>/")


def load_json(path, what):
    try:
        return json.loads(read(path))
    except json.JSONDecodeError as e:
        die(f"{what} {path} is not valid JSON: {e}", f"fix the JSON syntax in {path} and rerun")


def heading(line):
    """(level, title) for a markdown heading or a bold-only line (level 0), else None."""
    m = HEADING.match(line)
    if m:
        return len(m.group(1)), m.group(2).strip()
    b = BOLD_HEADING.match(line)
    if b:
        return 0, b.group(1).strip()
    return None


def norm(text):
    return " ".join(text.split())


def mask(text):
    """Text with cross-reference tokens neutralized, for verbatim comparison."""
    text = PREFIX.sub("", text)
    return NUMS.sub(lambda m: m.group(1) + " N", text)


def is_weak(edge):
    """Fixture-only, or a single shared error code: kept apart despite the link."""
    r = set(edge["rules"])
    return r <= {"fixture"} or (r == {"code"} and edge.get("codes", 1) == 1)


class Item:
    def __init__(self, label, first, sub):
        self.label = label
        self.lines = [first]
        self.sub = sub  # sub-section heading line inside Behavior, or None

    def raw(self):
        lines = list(self.lines)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines)

    @property
    def text(self):
        return norm(" ".join(l.strip() for l in self.lines))


class Spec:
    """A functional-spec.md split into title, top-level sections and Behavior items."""

    def __init__(self, path):
        self.path = path
        self.lines = read(path).splitlines()
        start = None
        for i, line in enumerate(self.lines):
            h = heading(line)
            if h and h[1].lower().startswith("behavior"):
                start, self.level = i, h[0]
                break
        if start is None:
            die(f"no Behavior heading in {path}",
                "expected a '## Behavior' line (any heading level) or a '**Behavior**' line")
        self.title = None
        self.sections = []  # [title, heading line, body lines]
        cur = None
        for line in self.lines:
            h = heading(line)
            if h and self._top(h):
                cur = [h[1], line, []]
                self.sections.append(cur)
            elif h and h[0] == 1 and self.title is None and cur is None:
                self.title = h[1]
            elif cur is not None:
                cur[2].append(line)
        self.items = self._items()

    def _top(self, h):
        return h[0] == self.level

    def section(self, title):
        for s in self.sections:
            if s[0].lower() == title.lower():
                return s
        return None

    @property
    def behavior(self):
        for s in self.sections:
            if s[0].lower().startswith("behavior"):
                return s
        return None

    def _items(self):
        items, cur, sub = [], None, None
        for line in self.behavior[2]:
            if heading(line):
                sub, cur = line, None
                continue
            m = ITEM.match(line)
            if m:
                cur = Item(int(m.group(1)), m.group(2), sub)
                items.append(cur)
            elif cur is not None:
                cur.lines.append(line)
        return items

    def numbering_problems(self):
        return [(pos, it.label) for pos, it in enumerate(self.items, 1) if it.label != pos]


class RefError(Exception):
    def __init__(self, kind, token):
        super().__init__(kind)
        self.kind, self.token = kind, token


def ref_numbers(nums):
    """Old invariant numbers named by a REF match's number group (ranges expanded)."""
    out = []
    for chunk in SEP.split(nums):
        bounds = [int(x) for x in RANGE.split(chunk)]
        out.extend(range(bounds[0], bounds[-1] + 1) if len(bounds) == 2 else bounds)
    return out


def rewrite_refs(text, loc, k, dirs):
    """Rewrite every 'invariant N' token in text for part k.

    loc maps old number -> (part index, new number); dirs maps part index -> dir name.
    Same-part references get the new number; earlier-part references become
    '<dir> invariant M'. Raises RefError for later_ref, mixed_ref, range_ref, bad_ref.
    """
    def sub(m):
        word, space, nums = m.groups()
        if any(RANGE.search(s) for s in SEP.split(nums)):
            raise RefError("range_ref", m.group(0))
        olds = [int(x) for x in SEP.split(nums)]
        seps = SEP.findall(nums)
        if any(o not in loc for o in olds):
            raise RefError("bad_ref", m.group(0))
        targets = [loc[o] for o in olds]
        parts = {p for p, _ in targets}
        if len(parts) > 1:
            raise RefError("mixed_ref", m.group(0))
        p = parts.pop()
        if p > k:
            raise RefError("later_ref", m.group(0))
        new = "".join(str(n) + (seps[i] if i < len(seps) else "") for i, (_, n) in enumerate(targets))
        return ("" if p == k else dirs[p] + " ") + word + space + new
    return REF.sub(sub, text)
