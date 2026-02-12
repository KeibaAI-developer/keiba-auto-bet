"""place_orders関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import place_orders
from keiba_auto_bet.exceptions import BetError
from keiba_auto_bet.models import BetOrder, TicketType


# 正常系
@patch("keiba_auto_bet.browser.bet_win_or_place")
@patch("keiba_auto_bet.browser.select_race")
@patch("keiba_auto_bet.browser.navigate_to_bet_page")
def test_place_orders_success(
    mock_navigate: MagicMock,
    mock_select_race: MagicMock,
    mock_bet: MagicMock,
    mock_driver: MagicMock,
    sample_orders: list[BetOrder],
) -> None:
    """全注文が正常に処理される."""
    place_orders(mock_driver, sample_orders)

    mock_navigate.assert_called_once_with(mock_driver)
    assert mock_select_race.call_count == 2
    assert mock_bet.call_count == 2


@patch("keiba_auto_bet.browser.bet_win_or_place")
@patch("keiba_auto_bet.browser.select_race")
@patch("keiba_auto_bet.browser.navigate_to_bet_page")
def test_place_orders_calls_select_race_with_correct_args(
    mock_navigate: MagicMock,
    mock_select_race: MagicMock,
    mock_bet: MagicMock,
    mock_driver: MagicMock,
    sample_orders: list[BetOrder],
) -> None:
    """各注文の競馬場・レース番号がselect_raceに正しく渡される."""
    place_orders(mock_driver, sample_orders)

    mock_select_race.assert_any_call(mock_driver, "東京", 11)
    mock_select_race.assert_any_call(mock_driver, "阪神", 12)


@patch("keiba_auto_bet.browser.bet_win_or_place")
@patch("keiba_auto_bet.browser.select_race")
@patch("keiba_auto_bet.browser.navigate_to_bet_page")
def test_place_orders_calls_bet_with_correct_args(
    mock_navigate: MagicMock,
    mock_select_race: MagicMock,
    mock_bet: MagicMock,
    mock_driver: MagicMock,
    sample_orders: list[BetOrder],
) -> None:
    """各注文の馬券種類・馬番・金額がbet_win_or_placeに正しく渡される."""
    place_orders(mock_driver, sample_orders)

    mock_bet.assert_any_call(mock_driver, TicketType.WIN, 3, 500)
    mock_bet.assert_any_call(mock_driver, TicketType.SHOW, 7, 300)


@patch("keiba_auto_bet.browser.bet_win_or_place")
@patch("keiba_auto_bet.browser.select_race")
@patch("keiba_auto_bet.browser.navigate_to_bet_page")
def test_place_orders_empty_orders(
    mock_navigate: MagicMock,
    mock_select_race: MagicMock,
    mock_bet: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """空の注文リストでもエラーにならない."""
    place_orders(mock_driver, [])

    mock_navigate.assert_called_once_with(mock_driver)
    mock_select_race.assert_not_called()
    mock_bet.assert_not_called()


# 準正常系
@patch("keiba_auto_bet.browser.select_race")
@patch("keiba_auto_bet.browser.navigate_to_bet_page")
def test_place_orders_raises_bet_error_on_unsupported_ticket_type(
    mock_navigate: MagicMock,
    mock_select_race: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """未対応の馬券種類が指定された場合BetErrorが送出される."""
    # 未対応のTicketTypeをシミュレートするためにモック化
    mock_order = MagicMock(spec=BetOrder)
    mock_order.venue = "東京"
    mock_order.race_number = 11
    mock_order.ticket_type = MagicMock()
    mock_order.ticket_type.value = "三連単"
    mock_order.horse_number = 3
    mock_order.amount = 500

    with pytest.raises(BetError, match="未対応の馬券種類です"):
        place_orders(mock_driver, [mock_order])
