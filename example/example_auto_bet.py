"""keiba-auto-bet使用例.

馬券の自動購入を実行するサンプルスクリプト。
"""

from keiba_auto_bet import AutoBetConfig, BetOrder, KeibaAutoBetError, TicketType
from keiba_auto_bet import auto_bet as execute_auto_bet


def main() -> None:
    """メイン関数."""
    # 認証情報は.envファイルから自動的に読み込まれる（credentials引数を省略）

    # 購入注文の作成
    orders = [
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

    # 設定
    config = AutoBetConfig(
        headless=True,
        max_bet=10000,
    )

    # 自動購入を実行（credentialsは省略すると.envから自動読み込み）
    try:
        result = execute_auto_bet(orders, config=config)
        if result:
            print("馬券の自動購入が正常に完了しました")
    except KeibaAutoBetError as exc:
        print(f"自動購入中にエラーが発生しました: {exc}")


if __name__ == "__main__":
    main()
