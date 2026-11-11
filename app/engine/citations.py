"""Code-verified traceability: every quote must exist in the transcript. Owner: B. Task B-03.

A quote is verified only if its words appear contiguously in one segment (or across two
consecutive segments) after normalization. The model never sets `verified`; this code does.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from decimal import Decimal
from typing import TypeVar

from pydantic import BaseModel

from app.schemas import Evidence, Segment, SuitabilityReport, Transcript

M = TypeVar("M", bound=BaseModel)


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation, collapse whitespace."""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())


def _tokens(seg: Segment) -> list[tuple[str, float, float]]:
    """(token, start, end) for a segment; word timestamps when available, else segment times."""
    if seg.words:
        return [(tok, w.start, w.end) for w in seg.words for tok in normalize(w.text).split()]
    return [(tok, seg.start, seg.end) for tok in normalize(seg.text).split()]


# --- Number canonicalization (B-03 follow-up, C's request) --------------------------------
# Scribe writes some numbers as digits («30 %», «0,2 %») and others as words («cero coma
# veinticinco»); the LLM may quote either form. Before matching, quote and transcript go
# through the same canonicalization: every number (digits or Spanish words) becomes one
# token with its value («treinta mil» = «30.000» = «30 000» = «30000» -> "30000"; «cero
# coma veinticinco» = «0,25» -> "0,25"), and «%» / «por ciento» right after a number is
# folded into it ("30%"). A different number never matches. `normalize()` is unchanged.

Tok = tuple[str, float, float]

_UNITS = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
          "nueve": 9}
_ONE = {"un", "uno", "una"}  # only a number inside a compound («treinta y un», «un millón»)
_TEENS = {"diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
          "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20,
          "veintiun": 21, "veintiuno": 21, "veintiuna": 21, "veintidos": 22, "veintitres": 23,
          "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27,
          "veintiocho": 28, "veintinueve": 29}
_TENS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
         "ochenta": 80, "noventa": 90}
_HUNDREDS = {"cien": 100, "ciento": 100, "quinientos": 500, "quinientas": 500,
             "setecientos": 700, "setecientas": 700, "novecientos": 900, "novecientas": 900,
             **{p + s: v for p, v in (("dos", 200), ("tres", 300), ("cuatro", 400),
                                      ("seis", 600), ("ocho", 800))
                for s in ("cientos", "cientas")}}
_MILLION = {"millon", "millones"}
_MULT = _MILLION | {"mil"}
_LEX = re.compile(r"\d+(?:[.,]\d+)*(?!\w)|%|\w+")
_THOUSANDS = re.compile(r"\d{1,3}(?:\.\d{3})+")


def _lex(text: str) -> list[str]:
    """Like normalize().split(), but keeps numeric literals («0,2», «30.000») and «%» whole."""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return _LEX.findall(t)


def _literal(tok: str) -> Decimal | None:
    """Value of a digit literal: «30.000» thousands, «0,25» / «0.25» decimal; None if unclear."""
    if tok.isdigit():
        return Decimal(tok)
    if _THOUSANDS.fullmatch(tok):
        return Decimal(tok.replace(".", ""))
    m = re.fullmatch(r"(\d{1,3}(?:\.\d{3})+|\d+),(\d+)", tok) or re.fullmatch(r"(\d+)\.(\d+)", tok)
    return Decimal(f"{m[1].replace('.', '')}.{m[2]}") if m else None


def _words_int(toks: list[str], i: int) -> tuple[int, int] | None:
    """Parse Spanish number words from toks[i]; (value, next index) or None."""
    total = group = 0
    lower = "none"  # state of the tens/units part of the current group: none|tens|done
    used_mil = used_millon = seen = False
    j = i
    while j < len(toks):
        t, nxt = toks[j], toks[j + 1] if j + 1 < len(toks) else ""
        if t == "cero" and j == i:
            return 0, j + 1
        if t in _HUNDREDS and group == 0 and lower == "none":
            group, lower = _HUNDREDS[t], ("done" if t == "cien" else "none")
        elif (t in _TEENS or t in _TENS) and lower == "none":
            group += _TEENS.get(t) or _TENS[t]
            lower = "tens" if t in _TENS else "done"
        elif t in _UNITS and lower == "none":
            group, lower = group + _UNITS[t], "done"
        elif t in _ONE and lower == "none" and nxt in _MULT:
            group, lower = group + 1, "done"
        elif t == "y" and lower == "tens" and (nxt in _UNITS or nxt in _ONE):
            group, lower, j = group + (_UNITS.get(nxt) or 1), "done", j + 1
        elif t == "mil" and not used_mil:
            total, group, lower, used_mil = total + (group or 1) * 1000, 0, "none", True
        elif t in _MILLION and not used_millon and not used_mil and group:
            total, group, lower, used_millon = group * 10**6, 0, "none", True
        else:
            break
        seen, j = True, j + 1
    return (total + group, j) if seen else None


def _number(toks: list[str], i: int) -> tuple[Decimal, int] | None:
    """Parse one number (digits or words, optional «coma» decimals and «mil»/«millones»)."""
    t = toks[i]
    if t[0].isdigit():
        val = _literal(t)
        if val is None:
            return None
        j = i + 1
        if len(t) <= 3 and t.isdigit():  # «20 000», «1 200 000» split by spaces
            while j < len(toks) and len(toks[j]) == 3 and toks[j].isdigit():
                val, j = val * 1000 + int(toks[j]), j + 1
        if j < len(toks) and toks[j] in _MULT:  # «30 mil», «1,5 millones»
            val, j = val * (1000 if toks[j] == "mil" else 10**6), j + 1
        return val, j
    parsed = _words_int(toks, i)
    if parsed is None:
        return None
    val, j = Decimal(parsed[0]), parsed[1]
    if j + 1 < len(toks) and toks[j] == "coma":  # «cero coma veinticinco», «cero coma cero dos»
        k, zeros = j + 1, ""
        if toks[k].isdigit():
            return Decimal(f"{val}.{toks[k]}"), k + 1
        while k < len(toks) and toks[k] == "cero":
            zeros, k = zeros + "0", k + 1
        frac = _words_int(toks, k) if k < len(toks) else None
        if frac is not None and frac[0] > 0:
            return Decimal(f"{val}.{zeros}{frac[0]}"), frac[1]
        if zeros:
            return val, k
    return val, j


def _fmt(val: Decimal) -> str:
    s = format(val.normalize(), "f")
    return s.replace(".", ",")


def _canon(toks: list[Tok]) -> list[Tok]:
    """Collapse every number into one value token; keeps first start and last end."""
    words = [t for t, _, _ in toks]
    out: list[Tok] = []
    i = 0
    while i < len(toks):
        w = words[i]
        parsed = _number(words, i) if (w[0].isdigit() or w in _HUNDREDS or w in _TEENS
                                       or w in _TENS or w in _UNITS or w in _ONE
                                       or w in _MULT or w == "cero") else None
        if parsed is None:
            if w == "%":
                i += 1
                continue  # a stray «%»: dropped, as normalize() does
            if w[0].isdigit():  # unclear literal («10.11.2026»): split as normalize() does
                out += [(p, toks[i][1], toks[i][2]) for p in re.split(r"[.,]", w)]
            else:
                out.append(toks[i])
            i += 1
            continue
        val, j = parsed
        text = _fmt(val)
        if j < len(toks) and words[j] == "%":
            text, j = text + "%", j + 1
        elif words[j:j + 2] == ["por", "ciento"]:
            text, j = text + "%", j + 2
        out.append((text, toks[i][1], toks[j - 1][2]))
        i = j
    return out


def _canon_tokens(seg: Segment) -> list[Tok]:
    """Canonical (number-folded) tokens of a segment, with word timestamps when available."""
    if seg.words:
        return _canon([(tok, w.start, w.end) for w in seg.words for tok in _lex(w.text)])
    return _canon([(tok, seg.start, seg.end) for tok in _lex(seg.text)])


def _find(sub: list[str], toks: list[str]) -> int:
    n = len(sub)
    if n == 0 or n > len(toks):
        return -1
    for i in range(len(toks) - n + 1):
        if toks[i:i + n] == sub:
            return i
    return -1


def locate(quote: str, transcript: Transcript) -> Evidence:
    """Find the normalized quote in one segment or across two consecutive ones.

    First with numbers canonicalized («treinta mil» = «30 000»), then, as a fallback, with
    the plain normalized tokens, so nothing that matched before stops matching.
    """
    sub = [t for t, _, _ in _canon([(tok, 0.0, 0.0) for tok in _lex(quote)])]
    ev = _locate(quote, sub, transcript, _canon_tokens)
    if ev.verified:
        return ev
    return _locate(quote, normalize(quote).split(), transcript, _tokens)


def _locate(quote: str, sub: list[str], transcript: Transcript,
            tokens: Callable[[Segment], list[Tok]]) -> Evidence:
    segs = transcript.segments
    for seg in segs:
        toks = tokens(seg)
        pos = _find(sub, [t for t, _, _ in toks])
        if pos >= 0:
            return Evidence(quote=quote, segment_id=seg.id, start=toks[pos][1],
                            end=toks[pos + len(sub) - 1][2], verified=True)
    for a, b in zip(segs, segs[1:], strict=False):  # quote crossing a speaker turn
        toks = tokens(a) + tokens(b)
        pos = _find(sub, [t for t, _, _ in toks])
        if pos >= 0:
            return Evidence(quote=quote, segment_id=a.id, start=toks[pos][1],
                            end=toks[pos + len(sub) - 1][2], verified=True)
    return Evidence(quote=quote, verified=False)


def validate(extraction: M, transcript: Transcript) -> M:
    """Copy of `extraction` (or any model, e.g. ConductCheck) with every Evidence located and `verified` set."""
    out = extraction.model_copy(deep=True)
    _walk(out, transcript)
    return out


def _walk(obj: object, tr: Transcript) -> None:
    if isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            value = getattr(obj, name)
            if name == "evidence" and isinstance(value, list):
                setattr(obj, name, [locate(e.quote, tr) for e in value])
            else:
                _walk(value, tr)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, tr)


def coverage(report: SuitabilityReport) -> float:
    """Percentage (0-100) of kind='claim' sentences with at least one verified evidence."""
    claims = [s for sec in report.sections for s in sec.sentences if s.kind == "claim"]
    if not claims:
        return 100.0
    ok = sum(1 for s in claims if any(e.verified for e in s.evidence))
    return round(100.0 * ok / len(claims), 1)
