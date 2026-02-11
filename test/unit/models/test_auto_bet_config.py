"""AutoBetConfigのテスト."""

import pytest

from keiba_auto_bet.models import AutoBetConfig


# 正常系
def test_auto_bet_config_default() -> None:
    """デフォルト値でAutoBetConfigが生成できる."""
    config = AutoBetConfig()
    assert config.ipat_url == "https://www.ipat.jra.go.jp/"
    assert config.chrome_driver_path is None
    assert config.headless is True
    assert config.max_bet == 10000


def test_auto_bet_config_custom() -> None:
    """カスタム値でAutoBetConfigが生成できる."""
    config = AutoBetConfig(
        ipat_url="https://example.com/",
        chrome_driver_path="/usr/local/bin/chromedriver",
        headless=False,
        max_bet=50000,
    )
    assert config.ipat_url == "https://example.com/"
    assert config.chrome_driver_path == "/usr/local/bin/chromedriver"
    assert config.headless is False
    assert config.max_bet == 50000


def test_auto_bet_config_is_frozen() -> None:
    """AutoBetConfigが不変（frozen）であることを確認する."""
    config = AutoBetConfig()
    with pytest.raises(AttributeError):
        config.max_bet = 999  # type: ignore[misc]


# 準正常系
def test_auto_bet_config_invalid_max_bet() -> None:
    """不正な最大合計購入金額でValueErrorが発生する."""
    with pytest.raises(ValueError, match="最大合計購入金額は100円以上で指定してください"):
        AutoBetConfig(max_bet=50)
