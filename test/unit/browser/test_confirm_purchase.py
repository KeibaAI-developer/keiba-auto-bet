"""confirm_purchase関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import confirm_purchase
from keiba_auto_bet.exceptions import PurchaseError


# 正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_confirm_purchase_success(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """正常に購入が確定される."""
    mock_purchase_button = MagicMock()
    mock_driver.find_element.return_value = mock_purchase_button
    mock_sum_input = MagicMock()
    mock_ok_button = MagicMock()
    mock_wait.return_value.until.side_effect = [
        mock_purchase_button,  # purchase_list_button
        mock_sum_input,  # sum_buy
        mock_purchase_button,  # purchase_button
        mock_ok_button,  # ok_button
        None,  # staleness
    ]

    confirm_purchase(mock_driver, 800)

    mock_sum_input.send_keys.assert_called_once_with("800")


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_confirm_purchase_amount_sent_as_string(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """合計金額が文字列として入力フィールドに送信される."""
    mock_sum_input = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),  # purchase_list_button
        mock_sum_input,  # sum_buy
        MagicMock(),  # purchase_button
        MagicMock(),  # ok_button
        None,  # staleness
    ]

    confirm_purchase(mock_driver, 15000)

    mock_sum_input.send_keys.assert_called_once_with("15000")


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_confirm_purchase_clicks_purchase_button(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """購入ボタンがクリックされる."""
    mock_purchase_button = MagicMock()
    mock_wait.return_value.until.side_effect = [
        MagicMock(),  # purchase_list_button
        MagicMock(),  # sum_buy
        mock_purchase_button,  # purchase_button
        MagicMock(),  # ok_button
        None,  # staleness
    ]

    confirm_purchase(mock_driver, 800)

    mock_purchase_button.click.assert_called()


# 準正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_confirm_purchase_raises_purchase_error_on_list_button_failure(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """購入予定リストボタンが見つからない場合PurchaseErrorが送出される."""
    mock_wait.return_value.until.side_effect = Exception("ボタンが見つかりません")

    with pytest.raises(PurchaseError, match="購入確定に失敗しました"):
        confirm_purchase(mock_driver, 800)


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_confirm_purchase_raises_purchase_error_on_amount_input_failure(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """合計金額の入力に失敗した場合PurchaseErrorが送出される."""
    mock_wait.return_value.until.side_effect = [
        MagicMock(),  # purchase_list_buttonは成功
        Exception("入力フィールドが見つかりません"),
    ]

    with pytest.raises(PurchaseError, match="購入確定に失敗しました"):
        confirm_purchase(mock_driver, 800)


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_confirm_purchase_raises_purchase_error_on_ok_button_failure(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """確認ダイアログのOKボタンが見つからない場合PurchaseErrorが送出される."""
    mock_sum_input = MagicMock()
    # 1回目のuntil（購入予定リストボタン）は成功
    # 2回目のuntil（金額入力）は成功
    # 3回目のuntil（購入ボタン）は成功
    # 4回目（OKボタン）で失敗
    mock_wait.return_value.until.side_effect = [
        MagicMock(),  # purchase_list_button
        mock_sum_input,  # sum_buy
        MagicMock(),  # purchase_button
        Exception("OKボタンが見つかりません"),
    ]

    with pytest.raises(PurchaseError, match="購入確定に失敗しました"):
        confirm_purchase(mock_driver, 800)
