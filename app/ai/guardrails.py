import re

BANNED = ["limited-time", "limited time", "link in bio", "swipe up", "buy now", "shop now",
          "order now", "promo code", "coupon code", "use code", "guaranteed", "never forget again"]
PCT = re.compile(r"\d+\s?%")
CODE = re.compile(r"\b[A-Z]{4,}\d{1,3}\b")


def _strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _strings(v)


def find_violations(content, allowed=""):
    """Rules the prompts ask for, checked in code. `allowed` = text the user supplied."""
    text = " ".join(_strings(content))
    low, allow = text.lower(), allowed.lower()
    out = [f'banned phrase: "{p}"' for p in BANNED if p in low and p not in allow]
    out += [f"unsupported percentage: {m}" for m in sorted(set(PCT.findall(text)))
            if m.replace(" ", "") not in allow.replace(" ", "")]
    out += [f"invented code: {m}" for m in sorted(set(CODE.findall(text))) if m.lower() not in allow]
    for name, p in (content or {}).items():
        for h in (p.get("hashtags", []) if isinstance(p, dict) else []):
            if not h.startswith("#"):
                out.append(f"{name} hashtag without #: {h}")
    return out
