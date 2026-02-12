"""navigate_to_bet_page関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import navigate_to_bet_page
from keiba_auto_bet.exceptions import BetError


# 正常系
@patch("keiba_auto_bet.browser.time.sleep")
def test_navigate_to_bet_page_success(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """正常に購入画面に移動できる場合、例外が送出されない."""
    navigate_to_bet_page(mock_driver)

    assert mock_driver.find_element.call_count >= 2


# 準正常系
@patch("keiba_auto_bet.browser.time.sleep")
def test_navigate_to_bet_page_raises_bet_error_on_button_not_found(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """通常投票ボタンもOKボタンも見つからない場合BetErrorが送出される."""
    mock_driver.find_element.side_effect = Exception("ボタンが見つかりません")

    with pytest.raises(BetError):
        navigate_to_bet_page(mock_driver)


@patch("keiba_auto_bet.browser.time.sleep")
def test_navigate_to_bet_page_fallback_ok_button(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """お知らせページが挟まった場合、OKボタンクリック後に通常投票ボタンを再試行する."""
    mock_ok_button = MagicMock()
    mock_bet_button = MagicMock()
    mock_race_button = MagicMock()

    call_count = 0

    def find_element_side_effect(by: str, value: str) -> MagicMock:
        nonlocal call_count
        call_count += 1
        # 1回目: 通常投票ボタンが見つからない
        if call_count == 1:
            raise Exception("通常投票ボタンが見つかりません")
        # 2回目: OKボタン（CLASS_NAME）
        if call_count == 2:
            return mock_ok_button
        # 3回目: 通常投票ボタン（リトライ）
        if call_count == 3:
            return mock_bet_button
        # 4回目: レース選択ボタン
        return mock_race_button

    mock_driver.find_element.side_effect = find_element_side_effect

    navigate_to_bet_page(mock_driver)

    mock_ok_button.click.assert_called_once()
    mock_bet_button.click.assert_called_once()
    mock_race_button.click.assert_called_once()


@patch("keiba_auto_bet.browser.time.sleep")
def test_navigate_to_bet_page_fallback_ok_button_also_fails(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """お知らせページのOKボタンも見つからない場合BetErrorが送出される."""
    mock_driver.find_element.side_effect = Exception("要素が見つかりません")

    with pytest.raises(BetError):
        navigate_to_bet_page(mock_driver)


@patch("keiba_auto_bet.browser.time.sleep")
def test_navigate_to_bet_page_raises_bet_error_on_race_select_failure(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """レース選択ボタンのクリックに失敗した場合BetErrorが送出される."""
    call_count = 0

    def find_element_side_effect(by: str, value: str) -> MagicMock:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock()
        raise Exception("レースボタンが見つかりません")

    mock_driver.find_element.side_effect = find_element_side_effect

    with pytest.raises(BetError, match="購入画面への移動に失敗しました"):
        navigate_to_bet_page(mock_driver)
