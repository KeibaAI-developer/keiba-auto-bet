"""navigate_to_top関数のテスト."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import navigate_to_top
from keiba_auto_bet.exceptions import BrowserError


# 正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_navigate_to_top_success(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """正常にトップ画面に戻れる."""
    mock_link = MagicMock()
    mock_wait.return_value.until.side_effect = [
        mock_link,  # top_return_link
        None,  # staleness
    ]

    navigate_to_top(mock_driver, mock_logger)

    mock_link.click.assert_called_once()


# 準正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_navigate_to_top_raises_browser_error_on_element_not_found(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """トップリンクが見つからない場合BrowserErrorが送出される."""
    mock_wait.return_value.until.side_effect = Exception("リンクが見つかりません")

    with pytest.raises(BrowserError, match="トップ画面への遷移に失敗しました"):
        navigate_to_top(mock_driver, mock_logger)


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_navigate_to_top_raises_browser_error_on_click_failure(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """リンクのクリックに失敗した場合BrowserErrorが送出される."""
    mock_link = MagicMock()
    mock_link.click.side_effect = Exception("クリック失敗")
    mock_wait.return_value.until.return_value = mock_link

    with pytest.raises(BrowserError, match="トップ画面への遷移に失敗しました"):
        navigate_to_top(mock_driver, mock_logger)
