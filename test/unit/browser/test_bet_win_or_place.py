"""bet_win_or_place関数のテスト."""

import logging
from unittest.mock import MagicMock, call, patch

import pytest
from selenium.common.exceptions import StaleElementReferenceException

from keiba_auto_bet.browser import bet_win_or_place
from keiba_auto_bet.exceptions import BetError
from keiba_auto_bet.models import TicketType


# 正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_win(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """単勝の馬券を正常に選択できる."""
    mock_select_instance = MagicMock()
    mock_select_cls.return_value = mock_select_instance
    mock_label = MagicMock()
    mock_checkbox = MagicMock()
    mock_label.find_element.return_value = mock_checkbox
    mock_amount_input = MagicMock()
    mock_set_button = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),  # bet_type_select用のelement_to_be_clickable
        mock_label,  # label_element用
        mock_amount_input,  # amount_input用
        mock_set_button,  # set_button用
        MagicMock(),  # セット後の待機
    ]

    bet_win_or_place(mock_driver, TicketType.WIN, 3, 500, mock_logger)

    mock_select_instance.select_by_visible_text.assert_called_once_with("単勝")
    mock_amount_input.send_keys.assert_called_once_with("5")
    mock_set_button.click.assert_called_once()


@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_show(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """複勝の馬券を正常に選択できる."""
    mock_select_instance = MagicMock()
    mock_select_cls.return_value = mock_select_instance
    mock_label = MagicMock()
    mock_checkbox = MagicMock()
    mock_label.find_element.return_value = mock_checkbox
    mock_amount_input = MagicMock()
    mock_set_button = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),
        mock_label,
        mock_amount_input,
        mock_set_button,
        MagicMock(),
    ]

    bet_win_or_place(mock_driver, TicketType.SHOW, 7, 300, mock_logger)

    mock_select_instance.select_by_visible_text.assert_called_once_with("複勝")
    mock_amount_input.send_keys.assert_called_once_with("3")


@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_amount_converted_to_units(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """金額が100円単位に変換されて入力される（1000円→10）."""
    mock_select_cls.return_value = MagicMock()
    mock_label = MagicMock()
    mock_label.find_element.return_value = MagicMock()
    mock_amount_input = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),
        mock_label,
        mock_amount_input,
        MagicMock(),
        MagicMock(),
    ]

    bet_win_or_place(mock_driver, TicketType.WIN, 1, 1000, mock_logger)

    mock_amount_input.send_keys.assert_called_once_with("10")


# 準正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_raises_bet_error_on_select_failure(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """馬券タイプの選択に失敗した場合BetErrorが送出される."""
    mock_wait.return_value.until.side_effect = Exception("要素が見つかりません")
    mock_select_cls.side_effect = Exception("要素が見つかりません")

    with pytest.raises(BetError, match="馬券選択に失敗しました"):
        bet_win_or_place(mock_driver, TicketType.WIN, 3, 500, mock_logger)


@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_raises_bet_error_on_checkbox_failure(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """馬番チェックボックスのクリックに失敗した場合BetErrorが送出される."""
    mock_select_cls.return_value = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),
        Exception("ラベルが見つかりません"),
    ]

    with pytest.raises(BetError, match="馬券選択に失敗しました"):
        bet_win_or_place(mock_driver, TicketType.WIN, 3, 500, mock_logger)


@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_error_message_contains_details(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """エラーメッセージに馬券種類・馬番・金額が含まれる."""
    mock_wait.return_value.until.side_effect = Exception("失敗")
    mock_select_cls.side_effect = Exception("失敗")

    with pytest.raises(BetError, match="単勝 3番 500円"):
        bet_win_or_place(mock_driver, TicketType.WIN, 3, 500, mock_logger)


# StaleElementReferenceExceptionリトライ
@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_retries_on_stale_select_constructor(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """Selectコンストラクタでstaleが発生してもリトライで成功する."""
    mock_select_instance = MagicMock()
    mock_select_cls.side_effect = [
        StaleElementReferenceException(),
        mock_select_instance,
    ]
    mock_label = MagicMock()
    mock_label.find_element.return_value = MagicMock()
    mock_amount_input = MagicMock()
    mock_set_button = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),  # 1回目のbet_type_select（staleになる）
        MagicMock(),  # 2回目のbet_type_select（成功）
        mock_label,
        mock_amount_input,
        mock_set_button,
        MagicMock(),
    ]

    bet_win_or_place(mock_driver, TicketType.WIN, 3, 500, mock_logger)

    assert mock_select_cls.call_count == 2
    mock_select_instance.select_by_visible_text.assert_called_once_with("単勝")
    mock_sleep.assert_called_once_with(1.0)


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_retries_on_stale_select_by_visible_text(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """select_by_visible_textでstaleが発生してもリトライで成功する."""
    mock_select_stale = MagicMock()
    mock_select_stale.select_by_visible_text.side_effect = StaleElementReferenceException()
    mock_select_ok = MagicMock()
    mock_select_cls.side_effect = [mock_select_stale, mock_select_ok]
    mock_label = MagicMock()
    mock_label.find_element.return_value = MagicMock()
    mock_amount_input = MagicMock()
    mock_set_button = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),  # 1回目のbet_type_select（staleになる）
        MagicMock(),  # 2回目のbet_type_select（成功）
        mock_label,
        mock_amount_input,
        mock_set_button,
        MagicMock(),
    ]

    bet_win_or_place(mock_driver, TicketType.SHOW, 7, 300, mock_logger)

    assert mock_select_cls.call_count == 2
    mock_select_ok.select_by_visible_text.assert_called_once_with("複勝")
    mock_sleep.assert_called_once_with(1.0)


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_bet_win_or_place_raises_error_after_max_stale_retries(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """リトライ上限を超えた場合BetErrorが送出される."""
    mock_select_cls.side_effect = [
        StaleElementReferenceException(),
        StaleElementReferenceException(),
        StaleElementReferenceException(),
    ]
    mock_wait.return_value.until.side_effect = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]

    with pytest.raises(BetError, match="馬券選択に失敗しました"):
        bet_win_or_place(mock_driver, TicketType.WIN, 3, 500, mock_logger)

    assert mock_select_cls.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_has_calls([call(1.0), call(1.0)])
