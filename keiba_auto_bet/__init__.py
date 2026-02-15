"""keiba-auto-bet: JRA即パットを使用した馬券自動購入ライブラリ.

このライブラリは、JRA即パットを使用した馬券の自動購入機能を提供します。
現在は単勝・複勝に対応しています。
"""

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("keiba-auto-bet")
except (PackageNotFoundError, ImportError):
    __version__ = "unknown"

from keiba_auto_bet.auto_bet import AutoBetter
from keiba_auto_bet.exceptions import (
    BetError,
    BrowserError,
    KeibaAutoBetError,
    LoginError,
    PurchaseError,
    ValidationError,
)
from keiba_auto_bet.models import AutoBetConfig, BetOrder, IpatCredentials, TicketType

__all__ = [
    "AutoBetter",
    "AutoBetConfig",
    "BetOrder",
    "IpatCredentials",
    "TicketType",
    "KeibaAutoBetError",
    "BetError",
    "BrowserError",
    "LoginError",
    "PurchaseError",
    "ValidationError",
]
