"""browser.open_chrome関数の共通fixture."""

from unittest.mock import MagicMock

import pytest

from keiba_auto_bet.models import AutoBetConfig, BetOrder, IpatCredentials, TicketType


@pytest.fixture()
def sample_config() -> AutoBetConfig:
    """テスト用の設定."""
    return AutoBetConfig(max_bet=10000)


@pytest.fixture()
def sample_config_with_driver_path() -> AutoBetConfig:
    """ChromeDriverパス指定付きのテスト用設定."""
    return AutoBetConfig(
        max_bet=10000,
        chrome_driver_path="/usr/local/bin/chromedriver",
    )


@pytest.fixture()
def sample_credentials() -> IpatCredentials:
    """テスト用の認証情報."""
    return IpatCredentials(
        inet_id="test_id",
        user_number="12345678",
        password="test_pass",
        p_ars="1234",
    )


@pytest.fixture()
def mock_driver() -> MagicMock:
    """モック化したWebDriverオブジェクト."""
    driver = MagicMock()
    driver.find_element.return_value = MagicMock()
    return driver


@pytest.fixture()
def sample_orders() -> list[BetOrder]:
    """テスト用の購入注文リスト."""
    return [
        BetOrder(
            venue="東京",
            race_number=11,
            ticket_type=TicketType.WIN,
            horse_number=3,
            amount=500,
        ),
        BetOrder(
            venue="阪神",
            race_number=12,
            ticket_type=TicketType.SHOW,
            horse_number=7,
            amount=300,
        ),
    ]
