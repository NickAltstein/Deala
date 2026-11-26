"""Two-pass WTS/WTB parser for dealer group posts.

Pass 1 picks the watch reference and masks it. Pass 2 reads a price only from
what is left, so the reference, a year, a box/papers date, or a quantity is
not stored as the price.
"""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import BaseModel

# Owner's reference pattern. IGNORECASE so "ln" and "1a" still match.
REF_PATTERN = r"\b([0-9]{4,6}[A-Z]{0,3}(?:/[0-9A-Z-]+)?)\b"
WTS_PATTERN = r"\b(wts|fs|for sale|selling)\b"
WTB_PATTERN = r"\b(wtb|wanted|looking for)\b"

_REF = re.compile(REF_PATTERN, re.IGNORECASE)
_WTS = re.compile(WTS_PATTERN, re.IGNORECASE)
_WTB = re.compile(WTB_PATTERN, re.IGNORECASE)
_YEAR = re.compile(r"(?:19|20)\d{2}\Z")
_FULL_SET = re.compile(r"\bfull\s*set\b", re.IGNORECASE)
_WATCH_ONLY = re.compile(r"\bwatch\s*only\b", re.IGNORECASE)

# A price is a number with a currency symbol or a k/K suffix.
# Comma thousands (28,500) are accepted only when nothing is marked.
_MARKED_PRICE = re.compile(
    r"""
    [$€£]\s*
    (?P<cur>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)
    (?P<cur_k>\s*[kK])?
    (?![\w.])
    |
    (?<![\d.,])
    (?P<knum>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)
    \s*[kK]
    (?![\w.])
    """,
    re.VERBOSE,
)
_COMMA_PRICE = re.compile(r"\b(\d{1,3}(?:,\d{3})+)\b")


class WatchListing(BaseModel):
    intent: str
    reference: str
    price_usd: Optional[int] = None
    set_completeness: Optional[str] = None
    source_group: str
    raw_text: str


def extract_watch_details(text: str, source_group: str = "unknown") -> Optional[WatchListing]:
    """Parse one group post. Returns None when no watch reference is present."""
    ref_match = _choose_reference(text)
    if ref_match is None:
        return None
    reference = _normalize_ref(ref_match.group(1))
    masked = text[: ref_match.start()] + (" " * (ref_match.end() - ref_match.start())) + text[ref_match.end() :]
    return WatchListing(
        intent=_intent(text),
        reference=reference,
        price_usd=_price_usd(masked),
        set_completeness=_completeness(text),
        source_group=source_group,
        raw_text=text,
    )


def render_draft(listing: WatchListing) -> str:
    """Deterministic draft. No model is involved."""
    completeness = listing.set_completeness or "set n/a"
    price = f"${listing.price_usd:,}" if listing.price_usd is not None else "price n/a"
    return f"{listing.intent} {listing.reference} | {completeness} | {price}"


def _intent(text: str) -> str:
    """Word-boundary intent. Anything that is not WTS or WTB is UNKNOWN.

    'fs' inside 'offset' or 'refs' does not match.
    """
    wts = _WTS.search(text)
    wtb = _WTB.search(text)
    if wts and wtb:
        return "WTS" if wts.start() <= wtb.start() else "WTB"
    if wts:
        return "WTS"
    if wtb:
        return "WTB"
    return "UNKNOWN"


def _choose_reference(text: str) -> Optional[re.Match[str]]:
    matches = list(_REF.finditer(text))
    if not matches:
        return None

    def rank(match: re.Match[str]) -> tuple[int, int, int]:
        token = match.group(1)
        has_marker = 1 if re.search(r"[A-Za-z/]", token) else 0
        is_year = 1 if _YEAR.fullmatch(token) else 0
        # Letter/slash refs beat bare numbers. Years lose. Earlier match wins ties.
        return (has_marker, 1 - is_year, -match.start())

    best = max(matches, key=rank)
    token = best.group(1)
    if _YEAR.fullmatch(token) and not re.search(r"[A-Za-z/]", token):
        return None
    return best


def _normalize_ref(raw: str) -> str:
    return "".join(ch.upper() if ch.isalpha() else ch for ch in raw)


def _price_usd(masked_text: str) -> Optional[int]:
    """Currency- or k-marked numbers win. A comma amount is the fallback.

    Years (2024), box/papers dates, and bare quantities never match either shape.
    """
    marked = _MARKED_PRICE.search(masked_text)
    if marked:
        if marked.group("cur") is not None:
            return _to_usd(marked.group("cur"), bool(marked.group("cur_k")))
        return _to_usd(marked.group("knum"), True)
    comma = _COMMA_PRICE.search(masked_text)
    if comma:
        return _to_usd(comma.group(1), False)
    return None


def _to_usd(raw: str, kilo: bool) -> int:
    amount = Decimal(raw.replace(",", ""))
    if kilo:
        amount *= 1000
    return int(amount.to_integral_value(rounding=ROUND_HALF_UP))


def _completeness(text: str) -> Optional[str]:
    found: list[tuple[int, str]] = []
    full = _FULL_SET.search(text)
    watch = _WATCH_ONLY.search(text)
    if full:
        found.append((full.start(), "full set"))
    if watch:
        found.append((watch.start(), "watch only"))
    if not found:
        return None
    found.sort()
    return found[0][1]
