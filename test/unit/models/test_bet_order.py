"""BetOrderのテスト."""

import pytest

from keiba_auto_bet.models import BetOrder, TicketType


# 正常系
@pytest.mark.parametrize(
    "venue, race_number, ticket_type, horse_number, amount",
    [
        ("東京", 1, TicketType.WIN, 1, 100),
        ("阪神", 12, TicketType.SHOW, 18, 10000),
        ("中山", 6, TicketType.WIN, 10, 500),
    ],
)
def test_bet_order_valid(
    venue: str,
    race_number: int,
    ticket_type: TicketType,
    horse_number: int,
    amount: int,
) -> None:
    """有効なパラメータでBetOrderが生成できる."""
    order = BetOrder(
        venue=venue,
        race_number=race_number,
        ticket_type=ticket_type,
        horse_number=horse_number,
        amount=amount,
    )
    assert order.venue == venue
    assert order.race_number == race_number
    assert order.ticket_type == ticket_type
    assert order.horse_number == horse_number
    assert order.amount == amount


def test_bet_order_is_frozen() -> None:
    """BetOrderが不変（frozen）であることを確認する."""
    order = BetOrder(
        venue="東京",
        race_number=1,
        ticket_type=TicketType.WIN,
        horse_number=1,
        amount=100,
    )
    with pytest.raises(AttributeError):
        order.amount = 200  # type: ignore[misc]


# 準正常系
@pytest.mark.parametrize(
    "race_number, expected_msg",
    [
        (0, "レース番号は1〜12の範囲で指定してください"),
        (13, "レース番号は1〜12の範囲で指定してください"),
        (-1, "レース番号は1〜12の範囲で指定してください"),
    ],
)
def test_bet_order_invalid_race_number(race_number: int, expected_msg: str) -> None:
    """不正なレース番号でValueErrorが発生する."""
    with pytest.raises(ValueError, match=expected_msg):
        BetOrder(
            venue="東京",
            race_number=race_number,
            ticket_type=TicketType.WIN,
            horse_number=1,
            amount=100,
        )


@pytest.mark.parametrize(
    "horse_number, expected_msg",
    [
        (0, "馬番は1以上で指定してください"),
        (-1, "馬番は1以上で指定してください"),
    ],
)
def test_bet_order_invalid_horse_number(horse_number: int, expected_msg: str) -> None:
    """不正な馬番でValueErrorが発生する."""
    with pytest.raises(ValueError, match=expected_msg):
        BetOrder(
            venue="東京",
            race_number=1,
            ticket_type=TicketType.WIN,
            horse_number=horse_number,
            amount=100,
        )


@pytest.mark.parametrize(
    "amount, expected_msg",
    [
        (0, "購入金額は100円以上で指定してください"),
        (50, "購入金額は100円以上で指定してください"),
        (99, "購入金額は100円以上で指定してください"),
        (150, "購入金額は100円単位で指定してください"),
        (250, "購入金額は100円単位で指定してください"),
    ],
)
def test_bet_order_invalid_amount(amount: int, expected_msg: str) -> None:
    """不正な購入金額でValueErrorが発生する."""
    with pytest.raises(ValueError, match=expected_msg):
        BetOrder(
            venue="東京",
            race_number=1,
            ticket_type=TicketType.WIN,
            horse_number=1,
            amount=amount,
        )
