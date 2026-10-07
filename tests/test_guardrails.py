from app.ai.guardrails import find_violations

OK = {"instagram": {"hook": "Drink up", "caption": "Get 20% off the bottle", "hashtags": ["#water"]},
      "tiktok": {"hook": "Hi", "caption": "Reusable bottle", "hashtags": ["#tok"]}}


def test_clean_content_passes():
    assert find_violations(OK, "20% off") == []


def test_invented_offer_details_are_caught():
    bad = {"instagram": {"caption": "Use code HYDRATE20, limited time, 50% off!", "hashtags": ["water"]}}
    v = " ".join(find_violations(bad, "20% off"))
    assert "limited time" in v and "HYDRATE20" in v and "50%" in v and "hashtag without #" in v


def test_percentage_allowed_when_user_gave_it():
    assert find_violations({"a": {"caption": "20% off"}}, "20% off") == []
