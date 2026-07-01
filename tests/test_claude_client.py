from datetime import date, timedelta


def test_pick_verse_same_date_returns_same_verse():
    from claude_client import _pick_verse, _VERSES
    d = date(2026, 7, 1)
    assert _pick_verse(_VERSES, d) == _pick_verse(_VERSES, d)


def test_pick_verse_consecutive_days_differ():
    from claude_client import _pick_verse, _VERSES
    d = date(2026, 7, 1)
    assert _pick_verse(_VERSES, d) != _pick_verse(_VERSES, d + timedelta(days=1))


def test_pick_verse_cycles_after_full_pool_length():
    from claude_client import _pick_verse, _VERSES
    d = date(2026, 7, 1)
    later = d + timedelta(days=len(_VERSES))
    assert _pick_verse(_VERSES, d) == _pick_verse(_VERSES, later)


def test_pick_verse_returns_pool_element():
    from claude_client import _pick_verse, _VERSES
    ref, text = _pick_verse(_VERSES, date(2026, 7, 1))
    assert (ref, text) in _VERSES


def test_pick_verse_works_with_different_pool_sizes():
    from claude_client import _pick_verse, _CLOSING_VERSES
    ref, text = _pick_verse(_CLOSING_VERSES, date(2026, 7, 1))
    assert (ref, text) in _CLOSING_VERSES


def test_morning_message_fallback_includes_verse_of_the_day():
    from claude_client import ClaudeClient, _VERSES, _pick_verse
    ref, text = _pick_verse(_VERSES)
    client = ClaudeClient()  # sin api_key -> modo fallback
    message = client.get_morning_message([])
    assert ref in message
    assert text in message
