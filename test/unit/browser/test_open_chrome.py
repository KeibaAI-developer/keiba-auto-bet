"""open_chrome関数のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.browser import open_chrome
from keiba_auto_bet.exceptions import BrowserError
from keiba_auto_bet.models import AutoBetConfig


# 正常系
@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.webdriver.Chrome")
@patch("keiba_auto_bet.browser.Service")
@patch("keiba_auto_bet.browser.Options")
def test_open_chrome_headless(
    mock_options_cls: MagicMock,
    mock_service_cls: MagicMock,
    mock_chrome_cls: MagicMock,
    mock_sleep: MagicMock,
    sample_config: AutoBetConfig,
) -> None:
    """ヘッドレスモードでChromeを起動し、即パットURLを開く."""
    mock_options = MagicMock()
    mock_options_cls.return_value = mock_options
    mock_driver = MagicMock()
    mock_chrome_cls.return_value = mock_driver

    result = open_chrome(sample_config)

    assert result is mock_driver
    mock_options.add_argument.assert_any_call("--headless")
    mock_options.add_argument.assert_any_call("--no-sandbox")
    mock_driver.get.assert_called_once_with(sample_config.ipat_url)


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.webdriver.Chrome")
@patch("keiba_auto_bet.browser.Service")
@patch("keiba_auto_bet.browser.Options")
def test_open_chrome_not_headless(
    mock_options_cls: MagicMock,
    mock_service_cls: MagicMock,
    mock_chrome_cls: MagicMock,
    mock_sleep: MagicMock,
) -> None:
    """ヘッドレスでない場合headless引数が追加されない."""
    config = AutoBetConfig(max_bet=10000, headless=False)
    mock_options = MagicMock()
    mock_options_cls.return_value = mock_options
    mock_chrome_cls.return_value = MagicMock()

    open_chrome(config)

    headless_calls = [
        call for call in mock_options.add_argument.call_args_list if call.args == ("--headless",)
    ]
    assert len(headless_calls) == 0


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.webdriver.Chrome")
@patch("keiba_auto_bet.browser.Service")
@patch("keiba_auto_bet.browser.Options")
def test_open_chrome_with_driver_path(
    mock_options_cls: MagicMock,
    mock_service_cls: MagicMock,
    mock_chrome_cls: MagicMock,
    mock_sleep: MagicMock,
    sample_config_with_driver_path: AutoBetConfig,
) -> None:
    """ChromeDriverパスが指定された場合、Serviceに渡される."""
    mock_chrome_cls.return_value = MagicMock()

    open_chrome(sample_config_with_driver_path)

    mock_service_cls.assert_called_once_with("/usr/local/bin/chromedriver")


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.webdriver.Chrome")
@patch("keiba_auto_bet.browser.Service")
@patch("keiba_auto_bet.browser.Options")
def test_open_chrome_without_driver_path(
    mock_options_cls: MagicMock,
    mock_service_cls: MagicMock,
    mock_chrome_cls: MagicMock,
    mock_sleep: MagicMock,
    sample_config: AutoBetConfig,
) -> None:
    """ChromeDriverパスが未指定の場合、引数なしでServiceが生成される."""
    mock_chrome_cls.return_value = MagicMock()

    open_chrome(sample_config)

    mock_service_cls.assert_called_once_with()


# 準正常系
@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.webdriver.Chrome")
@patch("keiba_auto_bet.browser.Service")
@patch("keiba_auto_bet.browser.Options")
def test_open_chrome_raises_browser_error_on_chrome_init_failure(
    mock_options_cls: MagicMock,
    mock_service_cls: MagicMock,
    mock_chrome_cls: MagicMock,
    mock_sleep: MagicMock,
    sample_config: AutoBetConfig,
) -> None:
    """Chrome起動に失敗した場合BrowserErrorが送出される."""
    mock_chrome_cls.side_effect = Exception("Chrome起動失敗")

    with pytest.raises(BrowserError, match="Chromeの起動に失敗しました"):
        open_chrome(sample_config)


@patch("keiba_auto_bet.browser.time.sleep")
@patch("keiba_auto_bet.browser.webdriver.Chrome")
@patch("keiba_auto_bet.browser.Service")
@patch("keiba_auto_bet.browser.Options")
def test_open_chrome_raises_browser_error_on_get_failure(
    mock_options_cls: MagicMock,
    mock_service_cls: MagicMock,
    mock_chrome_cls: MagicMock,
    mock_sleep: MagicMock,
    sample_config: AutoBetConfig,
) -> None:
    """URLアクセスに失敗した場合BrowserErrorが送出されdriverがquitされる."""
    mock_driver = MagicMock()
    mock_chrome_cls.return_value = mock_driver
    mock_driver.get.side_effect = Exception("ページアクセス失敗")

    with pytest.raises(BrowserError, match="Chromeの起動に失敗しました"):
        open_chrome(sample_config)

    mock_driver.quit.assert_called_once()
