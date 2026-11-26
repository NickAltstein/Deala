from app.agent.parser import extract_watch_details, render_draft


def test_wts_full_set_k_price_ignores_year_and_reference():
    listing = extract_watch_details("WTS 126610LN full set 2024 $14.2k", source_group="g1")
    assert listing is not None
    assert listing.intent == "WTS"
    assert listing.reference == "126610LN"
    assert listing.price_usd == 14200
    assert listing.set_completeness == "full set"
    assert listing.source_group == "g1"
    assert listing.price_usd != 2024
    assert listing.price_usd != 126610


def test_fs_watch_only_comma_price():
    listing = extract_watch_details("FS 116500LN watch only 28,500")
    assert listing is not None
    assert listing.intent == "WTS"
    assert listing.reference == "116500LN"
    assert listing.price_usd == 28500
    assert listing.set_completeness == "watch only"


def test_wtb_reference_with_slash_and_no_price():
    listing = extract_watch_details("WTB 5711/1A")
    assert listing is not None
    assert listing.intent == "WTB"
    assert listing.reference == "5711/1A"
    assert listing.price_usd is None
    assert listing.set_completeness is None


def test_offset_is_not_a_for_sale_keyword():
    # 'fs' is a substring of 'offset'. Word boundaries must not treat that as WTS.
    listing = extract_watch_details("offset 126610LN full set $14.2k")
    assert listing is not None
    assert listing.intent == "UNKNOWN"
    assert listing.reference == "126610LN"
    assert listing.price_usd == 14200


def test_k_suffix_without_currency_symbol():
    listing = extract_watch_details("WTS 126610LN full set 14.2k")
    assert listing is not None
    assert listing.price_usd == 14200


def test_year_box_date_and_quantity_are_not_prices():
    listing = extract_watch_details("WTS 126610LN box 2019 papers 2020 qty 2 full set")
    assert listing is not None
    assert listing.intent == "WTS"
    assert listing.reference == "126610LN"
    assert listing.price_usd is None
    assert listing.set_completeness == "full set"


def test_marked_price_wins_over_comma_amount_and_year():
    listing = extract_watch_details("WTS 126610LN full set 2024 28,500 asking $14.2k")
    assert listing is not None
    assert listing.price_usd == 14200


def test_looking_for_and_wanted_are_wtb():
    looking = extract_watch_details("looking for 5711/1A")
    wanted = extract_watch_details("wanted 116500LN")
    assert looking is not None and looking.intent == "WTB"
    assert wanted is not None and wanted.intent == "WTB"
    assert looking.reference == "5711/1A"


def test_refs_does_not_flip_wtb_to_wts():
    listing = extract_watch_details("WTB 126610LN refs only")
    assert listing is not None
    assert listing.intent == "WTB"


def test_no_reference_returns_none():
    assert extract_watch_details("WTS full set $14.2k") is None


def test_draft_template():
    listing = extract_watch_details("WTS 126610LN full set 2024 $14.2k")
    assert listing is not None
    assert render_draft(listing) == "WTS 126610LN | full set | $14,200"
