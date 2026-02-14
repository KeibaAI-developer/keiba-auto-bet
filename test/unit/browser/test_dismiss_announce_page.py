"""dismiss_announce_page関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import dismiss_announce_page
from keiba_auto_bet.exceptions import BrowserError


# 正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_dismiss_announce_page_with_announce(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """お知らせページが表示されている場合OKボタンをクリックして閉じる."""
    mock_announce_element = MagicMock()
    mock_driver.find_elements.return_value = [mock_announce_element]

    mock_ok_button = MagicMock()
    mock_wait.return_value.until.return_value = mock_ok_button

    dismiss_announce_page(mock_driver)

    mock_ok_button.click.assert_called_once()
    assert mock_wait.return_value.until.call_count == 2


def test_dismiss_announce_page_without_announce(
    mock_driver: MagicMock,
) -> None:
    """お知らせページが表示されていない場合は何もしない."""
    mock_driver.find_elements.return_value = []

    dismiss_announce_page(mock_driver)

    mock_driver.find_elements.assert_called_once()


# 準正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_dismiss_announce_page_ok_button_not_found(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
) -> None:
    """お知らせページのOKボタンが見つからない場合BrowserErrorが送出される."""
    mock_announce_element = MagicMock()
    mock_driver.find_elements.return_value = [mock_announce_element]

    mock_wait.return_value.until.side_effect = Exception("OKボタンが見つかりません")

    with pytest.raises(BrowserError, match="お知らせページの処理に失敗しました"):
        dismiss_announce_page(mock_driver)
