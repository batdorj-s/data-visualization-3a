import pandas as pd

from src.names import match_names, normalize, same_person, split_mba_name


def test_normalize():
    assert normalize("  BAATAR-ERDENE   Barsbold. ") == "baatar-erdene barsbold"
    assert normalize("Ölzii") == normalize("ÖLZII")


def test_split_mba_name():
    assert split_mba_name("HUGLEY IV John Ike") == ("hugley iv", "john ike")
    assert split_mba_name("DAVIS MCMURRIN Gage Andrew") == ("davis mcmurrin", "gage andrew")
    assert split_mba_name("BYRON Wesley") == ("byron", "wesley")


def test_same_person_prefix():
    assert same_person(split_mba_name("SCRUBB Jay"), split_mba_name("SCRUBB Jayden Amari")) is True


def test_same_person_fuzzy_given_name():
    assert same_person(("sandagdorj", "binderyaa"), ("sandagdorj", "binderiya")) is True


def test_different_people_same_surname():
    assert same_person(split_mba_name("SMITH Kendall"), split_mba_name("SMITH Donovan")) is False


def test_match_names_returns_pairs():
    left = pd.DataFrame({"id": ["a", "b"], "surname": ["scrubb", "smith"], "given": ["jay", "kendall"]})
    right = pd.DataFrame({"id": ["x", "y"], "surname": ["scrubb", "smith"], "given": ["jayden amari", "donovan"]})
    out = match_names(left, right)
    assert list(out.columns) == ["left_id", "right_id", "score"]
    assert out[["left_id", "right_id"]].values.tolist() == [["a", "x"]]
    assert 0 < out.score.iloc[0] <= 1
