from almanac.score import checks


def test_dates_match_in_any_format_but_not_neighbours():
    c = {"any": [], "dates": ["2024-05-18"], "not": [], "judge": False}
    for ok in ["May 18th", "on 2024-05-18", "18 May", "the 18th of May", "5/18/2024", "May 18, 2024"]:
        assert checks(ok, c)["dates"], ok
    for bad in ["May 1", "May 12, 2024", "15/18", "March 18"]:
        assert not checks(bad, c)["dates"], bad


def test_values_are_word_bounded_and_forbidden_strings_fail():
    c = {"any": ["Austin", "2"], "dates": [], "not": ["Oslo"], "judge": False}
    assert checks("You live in Austin.", c)["any"]
    assert not checks("You live in Austinville since 2024.", c)["any"]
    assert not checks("Your brother lives in Oslo.", c)["not"]
