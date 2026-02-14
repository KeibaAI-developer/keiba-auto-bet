"""navigate_to_bet_page関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import navigate_to_bet_page
from keiba_auto_bet.exceptions import BetError


# 正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_navigate_to_bet_page_success(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """正常に購入画面に移動できる場合、例外が送出されない."""
    mock_element = MagicMock()
    mock_wait.return_value.until.return_value = mock_element

    navigate_to_bet_page(mock_driver)

    assert mock_wait.call_count >= 2


# 準正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_navigate_to_bet_page_raises_bet_error_on_button_not_found(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """通常投票ボタンもOKボタンも見つからない場合BetErrorが送出される."""
    mock_wait.return_value.until.side_effect = Exception("ボタンが見つかりません")

    with pytest.raises(BetError):
        navigate_to_bet_page(mock_driver)


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_navigate_to_bet_page_raises_bet_error_on_race_select_failure(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """レース選択ボタンのクリックに失敗した場合BetErrorが送出される."""
    call_count = 0

    def until_side_effect(condition: object) -> MagicMock:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock()
        raise Exception("レースボタンが見つかりません")

    mock_wait.return_value.until.side_effect = until_side_effect

    with pytest.raises(BetError, match="購入画面への移動に失敗しました"):
        navigate_to_bet_page(mock_driver)
