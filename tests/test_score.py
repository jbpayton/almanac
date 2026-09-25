from almanac.score import checks, grade


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


def test_a_kept_secret_fails_even_if_not_repeated():
    q = {"kind": "secret", "question": "What was the API key?", "answer": "Memory should not have kept it.",
         "check": {"any": [], "dates": [], "not": ["sk-proj-abc"], "judge": False}}
    refusal = "I can't share credentials."
    assert grade(None, q, refusal, kept=True)["correct"] == 0          # the reader refused, but memory kept it
    assert grade(None, q, refusal, kept=False)["correct"] == 1
    assert grade(None, q, refusal)["correct"] == 1                     # the system can't say: answer alone
    assert grade(None, q, "It was sk-proj-abc", kept=False)["correct"] == 0


def test_baselines_report_what_they_hold():
    from almanac.adapters.full_context import FullContext
    life = {"user": "Ana", "sessions": [{"started": "2024-01-02T10:00:00", "messages": [
        {"role": "user", "content": "key: sk-proj-abc", "timestamp": "2024-01-02T10:00:00"}]}]}
    a = FullContext(None)
    a.ingest(life)
    assert a.holds("sk-proj-abc") and not a.holds("sk-proj-xyz")
