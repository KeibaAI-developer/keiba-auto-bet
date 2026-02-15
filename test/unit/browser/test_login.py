"""login関数のテスト."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import login
from keiba_auto_bet.exceptions import LoginError
from keiba_auto_bet.models import IpatCredentials


# 正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_login_success(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
    mock_logger: logging.Logger,
) -> None:
    """正常にログインできる場合、例外が送出されない."""
    mock_element = MagicMock()
    mock_wait.return_value.until.return_value = mock_element

    login(mock_driver, sample_credentials, mock_logger)

    assert mock_wait.call_count >= 4


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_login_sends_inet_id(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
    mock_logger: logging.Logger,
) -> None:
    """INET IDが入力フィールドに送信される."""
    mock_input = MagicMock()
    mock_wait.return_value.until.return_value = mock_input

    login(mock_driver, sample_credentials, mock_logger)

    mock_input.send_keys.assert_any_call(sample_credentials.inet_id)


# 準正常系
@patch("keiba_auto_bet.browser.WebDriverWait")
def test_login_raises_login_error_on_element_not_found(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
    mock_logger: logging.Logger,
) -> None:
    """要素が見つからない場合LoginErrorが送出される."""
    mock_wait.return_value.until.side_effect = Exception("要素が見つかりません")

    with pytest.raises(LoginError, match="ログインに失敗しました"):
        login(mock_driver, sample_credentials, mock_logger)


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_login_raises_login_error_on_click_failure(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
    mock_logger: logging.Logger,
) -> None:
    """ログインボタンのクリックに失敗した場合LoginErrorが送出される."""
    mock_element = MagicMock()
    mock_wait.return_value.until.return_value = mock_element
    mock_element.click.side_effect = Exception("クリック失敗")

    with pytest.raises(LoginError, match="ログインに失敗しました"):
        login(mock_driver, sample_credentials, mock_logger)


@patch("keiba_auto_bet.browser.WebDriverWait")
def test_login_raises_login_error_on_send_keys_failure(
    mock_wait: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
    mock_logger: logging.Logger,
) -> None:
    """send_keysに失敗した場合LoginErrorが送出される."""
    mock_element = MagicMock()
    mock_wait.return_value.until.return_value = mock_element
    mock_element.send_keys.side_effect = Exception("入力失敗")

    with pytest.raises(LoginError, match="ログインに失敗しました"):
        login(mock_driver, sample_credentials, mock_logger)
