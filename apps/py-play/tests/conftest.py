from pathlib import Path

import pytest

from play.digest import build

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_text():
    return lambda name: (FIXTURES / name).read_text()


@pytest.fixture(autouse=True)
def _reset_digest_cache():
    build._latest = None
