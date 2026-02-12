"""bet_win_or_place関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import bet_win_or_place
from keiba_auto_bet.exceptions import BetError
from keiba_auto_bet.models import TicketType


# 正常系
@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_win(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """単勝の馬券を正常に選択できる."""
    mock_select_instance = MagicMock()
    mock_select_cls.return_value = mock_select_instance
    mock_label = MagicMock()
    mock_checkbox = MagicMock()
    mock_label.find_element.return_value = mock_checkbox
    mock_driver.find_element.return_value = mock_label
    mock_amount_input = MagicMock()
    mock_set_button = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),  # bet_type_select用のelement_to_be_clickable
        mock_amount_input,  # amount_input用
        mock_set_button,  # set_button用
    ]

    bet_win_or_place(mock_driver, TicketType.WIN, 3, 500)

    mock_select_instance.select_by_visible_text.assert_called_once_with("単勝")
    mock_amount_input.send_keys.assert_called_once_with("5")
    mock_set_button.click.assert_called_once()


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_show(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """複勝の馬券を正常に選択できる."""
    mock_select_instance = MagicMock()
    mock_select_cls.return_value = mock_select_instance
    mock_label = MagicMock()
    mock_checkbox = MagicMock()
    mock_label.find_element.return_value = mock_checkbox
    mock_driver.find_element.return_value = mock_label
    mock_amount_input = MagicMock()
    mock_set_button = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),
        mock_amount_input,
        mock_set_button,
    ]

    bet_win_or_place(mock_driver, TicketType.SHOW, 7, 300)

    mock_select_instance.select_by_visible_text.assert_called_once_with("複勝")
    mock_amount_input.send_keys.assert_called_once_with("3")


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_amount_converted_to_units(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """金額が100円単位に変換されて入力される（1000円→10）."""
    mock_select_cls.return_value = MagicMock()
    mock_label = MagicMock()
    mock_label.find_element.return_value = MagicMock()
    mock_driver.find_element.return_value = mock_label
    mock_amount_input = MagicMock()
    mock_wait.return_value.until.side_effect = [MagicMock(), mock_amount_input, MagicMock()]

    bet_win_or_place(mock_driver, TicketType.WIN, 1, 1000)

    mock_amount_input.send_keys.assert_called_once_with("10")


# 準正常系
@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_raises_bet_error_on_select_failure(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """馬券タイプの選択に失敗した場合BetErrorが送出される."""
    mock_wait.return_value.until.side_effect = Exception("要素が見つかりません")
    mock_select_cls.side_effect = Exception("要素が見つかりません")

    with pytest.raises(BetError, match="馬券選択に失敗しました"):
        bet_win_or_place(mock_driver, TicketType.WIN, 3, 500)


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_raises_bet_error_on_checkbox_failure(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """馬番チェックボックスのクリックに失敗した場合BetErrorが送出される."""
    mock_select_cls.return_value = MagicMock()
    mock_wait.return_value.until.return_value = MagicMock()
    mock_driver.find_element.side_effect = Exception("ラベルが見つかりません")

    with pytest.raises(BetError, match="馬券選択に失敗しました"):
        bet_win_or_place(mock_driver, TicketType.WIN, 3, 500)


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_error_message_contains_details(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """エラーメッセージに馬券種類・馬番・金額が含まれる."""
    mock_wait.return_value.until.side_effect = Exception("失敗")
    mock_select_cls.side_effect = Exception("失敗")

    with pytest.raises(BetError, match="単勝 3番 500円"):
        bet_win_or_place(mock_driver, TicketType.WIN, 3, 500)
