"""login関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import login
from keiba_auto_bet.exceptions import LoginError
from keiba_auto_bet.models import IpatCredentials


# 正常系
@patch("keiba_auto_bet.browser.time.sleep")
def test_login_success(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
) -> None:
    """正常にログインできる場合、例外が送出されない."""
    login(mock_driver, sample_credentials)

    assert mock_driver.find_element.call_count >= 5


@patch("keiba_auto_bet.browser.time.sleep")
def test_login_sends_inet_id(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
) -> None:
    """INET IDが入力フィールドに送信される."""
    mock_input = MagicMock()
    mock_driver.find_element.return_value = mock_input

    login(mock_driver, sample_credentials)

    mock_input.send_keys.assert_any_call(sample_credentials.inet_id)


# 準正常系
@patch("keiba_auto_bet.browser.time.sleep")
def test_login_raises_login_error_on_element_not_found(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
) -> None:
    """要素が見つからない場合LoginErrorが送出される."""
    mock_driver.find_element.side_effect = Exception("要素が見つかりません")

    with pytest.raises(LoginError, match="ログインに失敗しました"):
        login(mock_driver, sample_credentials)


@patch("keiba_auto_bet.browser.time.sleep")
def test_login_raises_login_error_on_click_failure(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
) -> None:
    """ログインボタンのクリックに失敗した場合LoginErrorが送出される."""
    mock_element = MagicMock()
    mock_driver.find_element.return_value = mock_element
    mock_element.click.side_effect = Exception("クリック失敗")

    with pytest.raises(LoginError, match="ログインに失敗しました"):
        login(mock_driver, sample_credentials)


@patch("keiba_auto_bet.browser.time.sleep")
def test_login_raises_login_error_on_send_keys_failure(
    mock_sleep: MagicMock,
    mock_driver: MagicMock,
    sample_credentials: IpatCredentials,
) -> None:
    """send_keysに失敗した場合LoginErrorが送出される."""
    mock_element = MagicMock()
    mock_driver.find_element.return_value = mock_element
    mock_element.send_keys.side_effect = Exception("入力失敗")

    with pytest.raises(LoginError, match="ログインに失敗しました"):
        login(mock_driver, sample_credentials)
