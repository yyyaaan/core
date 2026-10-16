import pytest

from play.digest.hok import parse_campaigns


@pytest.mark.parametrize(
    "fixture, expected",
    [
        (
            "hok_campaign_li",
            [
                "Prisma Itäkeskus ja Prisma Itäkeskus ruoan verkkokaupan nouto 11.-17.5.2026. HUOM! Kampanja ei koske Prisma.fi ostoja!"
            ],
        ),
        ("hok_dash_none", []),  # "- Ei kampanjoita tällä hetkellä."
        ("hok_other_promo", []),  # unrelated -15% promo in the same article
        ("hok_empty", []),  # empty <li>, as of 2026-10
    ],
)
def test_parse_campaigns(fixture_text, fixture, expected):
    assert parse_campaigns(fixture_text(f"{fixture}.html")) == expected


def test_dash_lines_in_spans():
    html = "<article><h2>Bonus tuplana</h2><span>- Prisma Kaari 1.-3.6.\n- Sokos 2.6.</span></article>"
    assert parse_campaigns(html) == ["Prisma Kaari 1.-3.6.", "Sokos 2.6."]


def test_missing_section_raises():
    with pytest.raises(ValueError):
        parse_campaigns("<article><h2>Muut edut</h2></article>")
