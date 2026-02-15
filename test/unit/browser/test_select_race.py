"""select_race関数のテスト."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import select_race
from keiba_auto_bet.exceptions import BetError


@pytest.fixture()
def mock_select(mock_driver: MagicMock) -> tuple[MagicMock, MagicMock]:
    """Select要素をモック化するfixture."""
    mock_venue_option = MagicMock()
    mock_venue_option.text = "東京"
    mock_race_option = MagicMock()
    mock_race_option.text = "11R"

    mock_venue_select = MagicMock()
    mock_venue_select.options = [mock_venue_option]
    mock_race_select = MagicMock()
    mock_race_select.options = [mock_race_option]

    return mock_venue_select, mock_race_select


# 正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_select_race_success(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_select: tuple[MagicMock, MagicMock],
    mock_logger: logging.Logger,
) -> None:
    """正常に競馬場とレースを選択できる."""
    mock_venue_select, mock_race_select = mock_select
    mock_select_cls.side_effect = [mock_venue_select, mock_race_select]
    mock_wait.return_value.until.return_value = MagicMock()

    select_race(mock_driver, "東京", 11, mock_logger)

    mock_venue_select.select_by_visible_text.assert_called_once_with("東京")
    mock_race_select.select_by_visible_text.assert_called_once_with("11R")


# 準正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_select_race_venue_not_found(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """指定した競馬場が見つからない場合BetErrorが送出される."""
    mock_venue_select = MagicMock()
    mock_option = MagicMock()
    mock_option.text = "東京"
    mock_venue_select.options = [mock_option]
    mock_select_cls.return_value = mock_venue_select
    mock_wait.return_value.until.return_value = MagicMock()

    with pytest.raises(BetError, match="競馬場が見つかりませんでした: 阪神"):
        select_race(mock_driver, "阪神", 11, mock_logger)


@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_select_race_race_not_found(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """指定したレースが見つからない場合BetErrorが送出される."""
    mock_venue_select = MagicMock()
    mock_venue_option = MagicMock()
    mock_venue_option.text = "東京"
    mock_venue_select.options = [mock_venue_option]

    mock_race_select = MagicMock()
    mock_race_option = MagicMock()
    mock_race_option.text = "1R"
    mock_race_select.options = [mock_race_option]

    mock_select_cls.side_effect = [mock_venue_select, mock_race_select]
    mock_wait.return_value.until.return_value = MagicMock()

    with pytest.raises(BetError, match="レースが見つかりませんでした: 11R"):
        select_race(mock_driver, "東京", 11, mock_logger)


@patch("keiba_auto_bet.browser.WebDriverWait")
@patch("keiba_auto_bet.browser.Select")
def test_select_race_raises_bet_error_on_unexpected_exception(
    mock_select_cls: MagicMock,
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    mock_logger: logging.Logger,
) -> None:
    """WebDriverWaitのタイムアウト等で予期しない例外が発生した場合BetErrorが送出される."""
    mock_wait.return_value.until.side_effect = Exception("タイムアウト")
    mock_select_cls.side_effect = Exception("タイムアウト")

    with pytest.raises(BetError, match="レース選択に失敗しました"):
        select_race(mock_driver, "東京", 11, mock_logger)
