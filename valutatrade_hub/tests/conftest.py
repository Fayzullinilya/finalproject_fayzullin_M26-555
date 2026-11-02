# tests/conftest.py
import pytest
from unittest.mock import patch, MagicMock
import valutatrade_hub.cli.interface as cli_mod

@pytest.fixture
def cli():
    return cli_mod.CLI()

@pytest.fixture(autouse=True)
def mock_prompt():
    with patch.object(cli_mod, "prompt") as mock_module:
        yield mock_module

@pytest.fixture
def mock_usecases():
    mocks = {
        "register_user": MagicMock(),
        "login_user": MagicMock(),
        "show_portfolio": MagicMock(),
        "buy_currency": MagicMock(),
        "sell_currency": MagicMock(),
        "get_rate": MagicMock(),
    }
    with patch.dict(cli_mod.__dict__, mocks):
        yield mocks
