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


def test_v01_lives_are_unchanged():
    from pathlib import Path
    root = Path(__file__).parent.parent / "data"
    for sub, seed in (("lives", 1), ("dev", 2)):
        for f in sorted((root / sub).glob("life-*.json")):
            life = Life(seed, int(f.stem.split("-")[1]), "0.1").build()
            assert json.dumps(life, indent=1, ensure_ascii=False) == f.read_text(), f


def test_v02_near_misses_are_near_and_the_asked_thing_is_absent():
    import re
    for n in range(1, 6):
        life = Life(1, n).build()
        text = _text(life).lower()
        cats = {q["category"] for q in life["questions"]}
        assert {"nearmiss.person", "nearmiss.domain", "noanswer.topic", "stale.true", "stale.followup"} <= cats
        for q in life["questions"]:
            for word in q.get("absent", []):                    # "my brother" must not match "my brother-in-law"
                assert not re.search(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", text), (q["question"], word)
            if q["category"] == "nearmiss.domain":
                assert "family doctor" in text and "dentist" in text


def test_v02_follow_up_is_about_a_long_past_plan_in_the_same_conversation():
    import datetime as dt
    for n in range(1, 6):
        life = Life(1, n).build()
        (q,) = [q for q in life["questions"] if q["category"] == "stale.followup"]
        said = dt.date.fromisoformat(q["answer"].split(" on ")[1][:10])
        asked = dt.datetime.fromisoformat(life["asked_at"])
        assert (asked.date() - said).days > 90
        assert [m["role"] for m in q["context"]] == ["user", "assistant"]
        assert all(m["timestamp"] < life["asked_at"] for m in q["context"])
        assert q["context"][0]["content"] not in _text(life)      # said only in the conversation the question is in
