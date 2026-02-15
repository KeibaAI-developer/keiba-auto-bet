"""AutoBetter.betメソッドのテスト."""

import logging
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from keiba_auto_bet.auto_bet import AutoBetter
from keiba_auto_bet.exceptions import BrowserError, KeibaAutoBetError, ValidationError
from keiba_auto_bet.models import AutoBetConfig, BetOrder, IpatCredentials, TicketType


@pytest.fixture()
def sample_credentials() -> IpatCredentials:
    """テスト用の認証情報."""
    return IpatCredentials(
        inet_id="test_id",
        user_number="12345678",
        password="test_pass",
        p_ars="1234",
    )


@pytest.fixture()
def sample_orders() -> list[BetOrder]:
    """テスト用の購入注文リスト."""
    return [
        BetOrder(
            venue="東京",
            race_number=11,
            ticket_type=TicketType.WIN,
            horse_number=3,
            amount=500,
        ),
        BetOrder(
            venue="阪神",
            race_number=12,
            ticket_type=TicketType.SHOW,
            horse_number=7,
            amount=300,
        ),
    ]


@pytest.fixture()
def sample_config() -> AutoBetConfig:
    """テスト用の設定."""
    return AutoBetConfig(max_bet=10000)


@pytest.fixture()
def mock_logger() -> MagicMock:
    """テスト用ロガー."""
    return MagicMock(spec=logging.Logger)


def _select_factory(*args: Any, **kwargs: Any) -> MagicMock:
    """Select要素のモックファクトリ."""
    select = MagicMock()
    options = []
    for text in [
        "東京",
        "阪神",
        "中山",
        "1R",
        "2R",
        "3R",
        "4R",
        "5R",
        "6R",
        "7R",
        "8R",
        "9R",
        "10R",
        "11R",
        "12R",
    ]:
        opt = MagicMock()
        opt.text = text
        options.append(opt)
    select.options = options
    return select


@pytest.fixture()
def mock_selenium() -> Generator[tuple[MagicMock, MagicMock, MagicMock], None, None]:
    """Selenium関連の依存をモック化するfixture.

    Yields:
        tuple[MagicMock, MagicMock, MagicMock]:
            (driver, chrome_cls, wait_cls)のタプル
    """
    with (
        patch("keiba_auto_bet.auto_bet.webdriver.Chrome") as mock_chrome_cls,
        patch("keiba_auto_bet.auto_bet.WebDriverWait") as mock_wait_cls,
        patch("keiba_auto_bet.auto_bet.Select") as mock_select_cls,
        patch("keiba_auto_bet.auto_bet.Options"),
        patch("keiba_auto_bet.auto_bet.Service"),
        patch("keiba_auto_bet.auto_bet.time.sleep"),
    ):
        mock_driver = MagicMock()
        mock_chrome_cls.return_value = mock_driver
        mock_driver.find_elements.return_value = []
        mock_select_cls.side_effect = _select_factory
        yield mock_driver, mock_chrome_cls, mock_wait_cls


# 正常系
def test_auto_bet_success(
    mock_selenium: tuple[MagicMock, MagicMock, MagicMock],
    sample_orders: list[BetOrder],
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
    mock_logger: MagicMock,
) -> None:
    """正常に購入が完了する場合Trueを返しdriver.quit()が呼ばれる."""
    mock_driver, _, _ = mock_selenium

    better = AutoBetter(sample_credentials, sample_config, mock_logger)
    result = better.bet(sample_orders)

    assert result is True
    mock_driver.quit.assert_called_once()
    mock_logger.info.assert_any_call("購入合計金額: %d円（%d件）", 800, 2)
    mock_logger.info.assert_any_call("馬券の自動購入が完了しました")


def test_auto_bet_with_default_config(
    mock_selenium: tuple[MagicMock, MagicMock, MagicMock],
    sample_orders: list[BetOrder],
    sample_credentials: IpatCredentials,
    mock_logger: MagicMock,
) -> None:
    """configがNoneの場合デフォルト設定で正常に動作する."""
    better = AutoBetter(sample_credentials, logger=mock_logger)

    assert better._config == AutoBetConfig()
    result = better.bet(sample_orders)

    assert result is True


# 準正常系
def test_auto_bet_empty_orders(
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
) -> None:
    """空の注文リストでValidationErrorが発生する."""
    better = AutoBetter(sample_credentials, sample_config)

    with pytest.raises(ValidationError, match="購入注文リストが空です"):
        better.bet([])


def test_auto_bet_exceeds_max_bet(
    sample_credentials: IpatCredentials,
) -> None:
    """合計金額が最大購入金額を超える場合ValidationErrorが発生する."""
    orders = [
        BetOrder(
            venue="東京",
            race_number=1,
            ticket_type=TicketType.WIN,
            horse_number=1,
            amount=600,
        ),
    ]
    config = AutoBetConfig(max_bet=500)
    better = AutoBetter(sample_credentials, config)

    with pytest.raises(
        ValidationError,
        match="合計金額600円が最大購入金額500円を超えています",
    ):
        better.bet(orders)


# 異常系
def test_auto_bet_raises_browser_error_on_chrome_failure(
    mock_selenium: tuple[MagicMock, MagicMock, MagicMock],
    sample_orders: list[BetOrder],
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
) -> None:
    """Chrome起動に失敗した場合BrowserErrorが送出される."""
    _, mock_chrome_cls, _ = mock_selenium
    mock_chrome_cls.side_effect = Exception("Chrome起動失敗")

    better = AutoBetter(sample_credentials, sample_config)

    with pytest.raises(BrowserError, match="Chromeの起動に失敗しました"):
        better.bet(sample_orders)


def test_auto_bet_driver_quit_on_error(
    mock_selenium: tuple[MagicMock, MagicMock, MagicMock],
    sample_orders: list[BetOrder],
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
) -> None:
    """エラー発生時でもdriver.quit()が呼ばれる."""
    mock_driver, _, mock_wait_cls = mock_selenium
    mock_wait_cls.return_value.until.side_effect = [
        MagicMock(),
        Exception("処理エラー"),
    ]

    better = AutoBetter(sample_credentials, sample_config)

    with pytest.raises(KeibaAutoBetError, match="ログインに失敗しました"):
        better.bet(sample_orders)

    mock_driver.quit.assert_called_once()


def test_auto_bet_wraps_unexpected_exception(
    mock_selenium: tuple[MagicMock, MagicMock, MagicMock],
    sample_orders: list[BetOrder],
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
) -> None:
    """予期しない例外がKeibaAutoBetErrorでラップされる."""
    mock_driver, _, _ = mock_selenium
    mock_driver.find_elements.side_effect = RuntimeError("unexpected")

    better = AutoBetter(sample_credentials, sample_config)

    with pytest.raises(KeibaAutoBetError, match="予期しないエラーが発生しました"):
        better.bet(sample_orders)


def test_init_uses_module_logger_when_logger_not_provided(
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
) -> None:
    """logger未指定時はモジュールロガーが使用される."""
    module_logger = MagicMock(spec=logging.Logger)
    with patch("keiba_auto_bet.auto_bet.logging.getLogger", return_value=module_logger) as mock_get:
        better = AutoBetter(sample_credentials, sample_config)

    assert better._logger is module_logger
    mock_get.assert_called_once_with("keiba_auto_bet.auto_bet")


def test_init_prefers_explicit_logger(
    sample_credentials: IpatCredentials,
    sample_config: AutoBetConfig,
    mock_logger: MagicMock,
) -> None:
    """logger指定時はlogging.getLoggerを呼ばず、指定ロガーを利用する."""
    with patch("keiba_auto_bet.auto_bet.logging.getLogger") as mock_get:
        better = AutoBetter(sample_credentials, sample_config, mock_logger)

    assert better._logger is mock_logger
    mock_get.assert_not_called()
