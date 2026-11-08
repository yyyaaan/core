import pytest

from play.digest.migri import ProcessingTime, parse_processing_time


@pytest.mark.parametrize(
    "fixture, expected",
    [
        ("migri_2026_11", ProcessingTime(most="35 months", minority="17 months")),
        (
            "migri_2025_01_ranges",
            ProcessingTime(most="9–31 months", minority="2–9 months"),
        ),
    ],
)
def test_adult_electronic(fixture_text, fixture, expected):
    assert parse_processing_time(fixture_text(f"{fixture}.html")) == expected


def test_missing_section_raises():
    with pytest.raises(ValueError):
        parse_processing_time(
            '<div class="tabPanel"><div class="heading">Release from Finnish citizenship</div></div>'
        )


def test_missing_column_raises():
    html = """<div class="tabPanel"><div class="heading">Citizenship application for an adult</div>
    <table><tr><td></td><td>Paper application</td></tr><tr><td>in most cases</td><td>35 months</td></tr></table></div>"""
    with pytest.raises(ValueError):
        parse_processing_time(html)
