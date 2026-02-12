"""auto_bet関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.auto_bet import auto_bet
from keiba_auto_bet.exceptions import ValidationError
from keiba_auto_bet.models import AutoBetConfig, BetOrder, IpatCredentials, TicketType


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


@pytest.fixture()
def sample_config() -> AutoBetConfig:
    """テスト用の設定."""
    return AutoBetConfig(max_bet=10000)


# 正常系
@patch("keiba_auto_bet.auto_bet.navigate_to_top")
@patch("keiba_auto_bet.auto_bet.confirm_purchase")
@patch("keiba_auto_bet.auto_bet.place_orders")
@patch("keiba_auto_bet.auto_bet.login")
@patch("keiba_auto_bet.auto_bet.open_chrome")
def test_auto_bet_success(
    mock_open_chrome: MagicMock,
    mock_login: MagicMock,
    mock_place_orders: MagicMock,
    mock_confirm_purchase: MagicMock,
    mock_navigate_to_top: MagicMock,
    sample_orders: list[BetOrder],
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
) -> None:
    """正常に購入が完了する場合Trueを返す."""
    mock_driver = MagicMock()
    mock_open_chrome.return_value = mock_driver

    result = auto_bet(sample_orders, sample_credentials, sample_config)

    assert result is True
    mock_open_chrome.assert_called_once_with(sample_config)
    mock_login.assert_called_once_with(mock_driver, sample_credentials)
    mock_place_orders.assert_called_once_with(mock_driver, sample_orders)
    mock_confirm_purchase.assert_called_once_with(mock_driver, 800)
    mock_navigate_to_top.assert_called_once_with(mock_driver)
    mock_driver.quit.assert_called_once()


@patch("keiba_auto_bet.auto_bet.navigate_to_top")
@patch("keiba_auto_bet.auto_bet.confirm_purchase")
@patch("keiba_auto_bet.auto_bet.place_orders")
@patch("keiba_auto_bet.auto_bet.login")
@patch("keiba_auto_bet.auto_bet.open_chrome")
def test_auto_bet_default_config(
    mock_open_chrome: MagicMock,
    mock_login: MagicMock,
    mock_place_orders: MagicMock,
    mock_confirm_purchase: MagicMock,
    mock_navigate_to_top: MagicMock,
    sample_orders: list[BetOrder],
    sample_credentials: IpatCredentials,
) -> None:
    """configがNoneの場合デフォルト設定が使用される."""
    mock_driver = MagicMock()
    mock_open_chrome.return_value = mock_driver

    result = auto_bet(sample_orders, sample_credentials, None)

    assert result is True
    mock_open_chrome.assert_called_once()


# 準正常系
def test_auto_bet_empty_orders(
    sample_credentials: IpatCredentials, sample_config: AutoBetConfig
) -> None:
    """空の注文リストでValidationErrorが発生する."""
    with pytest.raises(ValidationError, match="購入注文リストが空です"):
        auto_bet([], sample_credentials, sample_config)


def test_auto_bet_exceeds_max_bet(sample_credentials: IpatCredentials) -> None:
    """合計金額が最大購入金額を超える場合ValidationErrorが発生する."""
    orders = [
        BetOrder(
            venue="東京",
            race_number=1,
            ticket_type=TicketType.WIN,
            horse_number=1,
            amount=600,
        ),
    ]
    config = AutoBetConfig(max_bet=500)

    with pytest.raises(ValidationError, match="合計金額600円が最大購入金額500円を超えています"):
        auto_bet(orders, sample_credentials, config)


# 異常系
@patch("keiba_auto_bet.auto_bet.login")
@patch("keiba_auto_bet.auto_bet.open_chrome")
def test_auto_bet_driver_quit_on_error(
    mock_open_chrome: MagicMock,
    mock_login: MagicMock,
    sample_orders: list[BetOrder],
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
) -> None:
    """エラー発生時でもdriver.quit()が呼ばれる."""
    mock_driver = MagicMock()
    mock_open_chrome.return_value = mock_driver
    mock_login.side_effect = Exception("ログインエラー")

    with pytest.raises(Exception):
        auto_bet(sample_orders, sample_credentials, sample_config)

    mock_driver.quit.assert_called_once()
