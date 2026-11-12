import difflib
import re
import unicodedata

import pandas as pd

GIVEN_RATIO = 0.85


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"[.,'’`\"()]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def split_mba_name(name: str) -> tuple[str, str]:
    tokens = str(name).split()
    n_upper = 0
    for tok in tokens:
        letters = [c for c in tok if c.isalpha()]
        if letters and all(c.isupper() for c in letters):
            n_upper += 1
        else:
            break
    if n_upper == len(tokens):
        n_upper = 1
    if n_upper == 0:
        n_upper = 1
    return normalize(" ".join(tokens[:n_upper])), normalize(" ".join(tokens[n_upper:]))


def given_score(g1: str, g2: str) -> float:
    g1, g2 = normalize(g1), normalize(g2)
    if g1 == g2:
        return 1.0
    if g1 and g2 and (g1.startswith(g2) or g2.startswith(g1)):
        return 0.95
    return difflib.SequenceMatcher(None, g1, g2).ratio()


def same_person(a: tuple[str, str], b: tuple[str, str]) -> bool:
    if normalize(a[0]) != normalize(b[0]):
        return False
    return given_score(a[1], b[1]) >= GIVEN_RATIO


def match_names(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    """left/right: id, surname, given багануудтай. Овог ижил, нэр ойролцоо хосуудыг буцаана."""
    rows = []
    by_surname = right.assign(_s=right["surname"].map(normalize)).groupby("_s")
    groups = {k: g for k, g in by_surname}
    for l in left.itertuples(index=False):
        cand = groups.get(normalize(l.surname))
        if cand is None:
            continue
        for r in cand.itertuples(index=False):
            score = given_score(l.given, r.given)
            if score >= GIVEN_RATIO:
                rows.append({"left_id": l.id, "right_id": r.id, "score": round(score, 3)})
    return pd.DataFrame(rows, columns=["left_id", "right_id", "score"])
