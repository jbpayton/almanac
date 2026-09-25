import json

from almanac.generate import Life


def _text(life):
    return "\n".join(m.get("content") or "" for s in life["sessions"] for m in s["messages"]) + "\n" + \
        "\n".join(c["function"]["arguments"] for s in life["sessions"] for m in s["messages"] for c in m.get("tool_calls") or [])


def test_generation_is_reproducible():
    a, b = Life(1, 3).build(), Life(1, 3).build()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert json.dumps(a) != json.dumps(Life(2, 3).build())


def test_every_expected_value_is_in_the_conversation():
    for n in range(1, 6):
        life = Life(1, n).build()
        text = _text(life).lower()
        for q in life["questions"]:
            if q["kind"] in ("unknown", "quiet", "secret"):
                continue
            if q["check"]["any"]:
                assert any(v.lower() in text for v in q["check"]["any"] if len(v) > 3) or \
                    q["category"] in ("change.count", "provenance.web"), (q["question"], q["check"]["any"])


def test_unknowns_are_really_unknown_and_traps_are_present():
    for n in range(1, 6):
        life = Life(1, n).build()
        text = _text(life)
        for q in life["questions"]:
            if q["category"] == "absence" and "mentioned having a" in q["question"]:
                rel = q["question"].split("having a ")[1].rstrip("?")
                assert f" {rel} " not in f" {text.lower()} "
            if q["category"] == "hygiene.secret":
                assert q["check"]["not"][0] in text                      # the key really was pasted
            if q["category"] in ("hygiene.invented", "hygiene.injection"):
                assert q["check"]["not"][0].lower() in text.lower()      # the trap really is in the history


def test_questions_do_not_leak_answers():
    for n in range(1, 6):
        for q in Life(1, n).build()["questions"]:
            for v in q["check"]["any"]:
                if len(v) > 3 and q["category"] not in ("provenance.user",):
                    assert v.lower() not in q["question"].lower(), (q["question"], v)


def test_sessions_are_in_time_order():
    life = Life(1, 1).build()
    stamps = [m["timestamp"] for s in life["sessions"] for m in s["messages"]]
    assert stamps == sorted(stamps) and life["asked_at"] > stamps[-1]
