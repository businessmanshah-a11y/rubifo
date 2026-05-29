import re


RTL_PREFIX = "\u200f"
LTR_START = "\u2066"
BIDI_END = "\u2069"

_LTR_FRAGMENT_RE = re.compile(
    r"(https?://[^\s]+|rubika\.ir/[^\s]+|@[A-Za-z0-9_]+|/[A-Za-z0-9_]+|\b[0-9]+(?:[.:/,-][0-9]+)*\b)"
)


def format_rtl_message(text: str) -> str:
    """Make mixed Persian/ASCII bot text render predictably in RTL clients."""
    if not text:
        return RTL_PREFIX

    def isolate(match: re.Match) -> str:
        value = match.group(0)
        if value.startswith(LTR_START) and value.endswith(BIDI_END):
            return value
        return f"{LTR_START}{value}{BIDI_END}"

    formatted = _LTR_FRAGMENT_RE.sub(isolate, text)
    if not formatted.startswith(RTL_PREFIX):
        formatted = f"{RTL_PREFIX}{formatted}"
    return formatted
