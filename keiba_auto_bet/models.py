"""データモデル定義.

馬券自動購入に必要なデータ構造を定義する。
"""

from dataclasses import dataclass
from enum import Enum


class TicketType(Enum):
    """馬券の種類.

    現在は単勝・複勝のみ対応。

    Attributes:
        WIN: 単勝
        SHOW: 複勝
    """

    WIN = "単勝"
    SHOW = "複勝"


@dataclass(frozen=True)
class BetOrder:
    """1件の馬券購入注文.

    Attributes:
        venue: 競馬場名（例: "東京", "阪神"）
        race_number: レース番号（1〜12）
        ticket_type: 馬券の種類
        horse_number: 馬番
        amount: 購入金額（円、100円単位）
    """

    venue: str
    race_number: int
    ticket_type: TicketType
    horse_number: int
    amount: int

    def __post_init__(self) -> None:
        """バリデーション.

        Raises:
            ValueError: パラメータが不正な場合
        """
        if not 1 <= self.race_number <= 12:
            raise ValueError(f"レース番号は1〜12の範囲で指定してください: {self.race_number}")
        if self.horse_number < 1:
            raise ValueError(f"馬番は1以上で指定してください: {self.horse_number}")
        if self.amount < 100:
            raise ValueError(f"購入金額は100円以上で指定してください: {self.amount}")
        if self.amount % 100 != 0:
            raise ValueError(f"購入金額は100円単位で指定してください: {self.amount}")


@dataclass(frozen=True)
class IpatCredentials:
    """即パットの認証情報.

    Attributes:
        inet_id: INET ID
        user_number: 加入者番号
        password: パスワード
        p_ars: P-ARS番号
    """

    inet_id: str
    user_number: str
    password: str
    p_ars: str

    def __post_init__(self) -> None:
        """バリデーション.

        Raises:
            ValueError: パラメータが不正な場合
        """
        if not self.inet_id:
            raise ValueError("INET IDは必須です")
        if not self.user_number:
            raise ValueError("加入者番号は必須です")
        if not self.password:
            raise ValueError("パスワードは必須です")
        if not self.p_ars:
            raise ValueError("P-ARS番号は必須です")


@dataclass(frozen=True)
class AutoBetConfig:
    """自動購入の設定.

    Attributes:
        ipat_url: 即パットのURL
        chrome_driver_path: ChromeDriverのパス（Noneの場合は自動検出）
        headless: ヘッドレスモードで実行するかどうか
        max_bet: 最大合計購入金額（円）
    """

    ipat_url: str = "https://www.ipat.jra.go.jp/"
    chrome_driver_path: str | None = None
    headless: bool = True
    max_bet: int = 10000

    def __post_init__(self) -> None:
        """バリデーション.

        Raises:
            ValueError: パラメータが不正な場合
        """
        if self.max_bet < 100:
            raise ValueError(f"最大合計購入金額は100円以上で指定してください: {self.max_bet}")
