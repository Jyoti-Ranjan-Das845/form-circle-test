"""Text normalisation so small formatting differences are not counted as errors."""
import re

DASHES = "‐‑‒–—―−"
EDGE_PUNCT = " \t\n.,;:!?\"'()[]{}“”‘’"


def norm(s):
    """Lowercase, unify dashes and quotes, collapse spaces, strip punctuation at both ends.

    Inner punctuation is kept, so "32,000", "4.6%", "$19 billion" and "-3.92" keep their meaning.
    "Pittsburgh," -> "pittsburgh", "(BIAD #93-13104)" -> "biad #93-13104", "−3.92" -> "-3.92".
    """
    if s is None:
        return ""
    s = str(s)
    for d in DASHES:
        s = s.replace(d, "-")
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = re.sub(r"\s+", " ", s.lower())
    return s.strip(EDGE_PUNCT)


def squash(s):
    """norm() with every space removed, so "D. M. Teng" matches "D.M. Teng"."""
    return norm(s).replace(" ", "")


def same_text(a, b):
    return norm(a) == norm(b) or squash(a) == squash(b)


def words(s):
    """Word set of a context line, for checking which occurrence of a repeated word was found."""
    return set(re.findall(r"[a-z0-9/#$%.-]+", norm(s).replace(",", " ")))
