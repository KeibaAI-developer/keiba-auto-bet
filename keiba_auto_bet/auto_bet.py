"""自動購入メインモジュール.

馬券自動購入の公開APIを提供する。
"""

import logging
import os

from dotenv import load_dotenv

from keiba_auto_bet.browser import (
    confirm_purchase,
    login,
    navigate_to_top,
    open_chrome,
    place_orders,
)
from keiba_auto_bet.exceptions import KeibaAutoBetError, ValidationError
from keiba_auto_bet.models import AutoBetConfig, BetOrder, IpatCredentials

logger = logging.getLogger(__name__)


def auto_bet(
    orders: list[BetOrder],
    credentials: IpatCredentials | None = None,
    config: AutoBetConfig | None = None,
) -> bool:
    """馬券を自動購入する.

    指定された購入注文リストに基づいて、即パットを使用して馬券を自動購入する。
    あらかじめ即パットに入金しておくこと。

    Args:
        orders: 購入注文リスト
        credentials: 即パットの認証情報（Noneの場合は環境変数から読み込む）
        config: 自動購入の設定（Noneの場合はデフォルト設定を使用）

    Returns:
        bool: 購入が正常に完了した場合はTrue

    Raises:
        ValidationError: 入力内容のバリデーションエラー
        KeibaAutoBetError: 購入処理中にエラーが発生した場合
    """
    if credentials is None:
        credentials = _load_credentials_from_env()

    if config is None:
        config = AutoBetConfig()

    _validate_orders(orders, config.max_bet)

    total_amount = sum(order.amount for order in orders)
    logger.info("購入合計金額: %d円（%d件）", total_amount, len(orders))

    driver = open_chrome(config)

    try:
        login(driver, credentials)
        place_orders(driver, orders)
        confirm_purchase(driver, total_amount)
        navigate_to_top(driver)
        logger.info("馬券の自動購入が完了しました")
        return True
    except KeibaAutoBetError:
        raise
    except Exception as exc:
        raise KeibaAutoBetError(f"予期しないエラーが発生しました: {exc}") from exc
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def _load_credentials_from_env() -> IpatCredentials:
    """環境変数から認証情報を読み込む.

    .envファイルが存在する場合は自動的に読み込む。

    Returns:
        IpatCredentials: 環境変数から読み込んだ認証情報

    Raises:
        ValidationError: 必要な環境変数が設定されていない場合
    """
    load_dotenv()

    inet_id = os.getenv("IPAT_INET_ID", "")
    user_number = os.getenv("IPAT_USER_NUMBER", "")
    password = os.getenv("IPAT_PASSWORD", "")
    p_ars = os.getenv("IPAT_P_ARS", "")

    try:
        return IpatCredentials(
            inet_id=inet_id,
            user_number=user_number,
            password=password,
            p_ars=p_ars,
        )
    except ValueError as exc:
        raise ValidationError(
            f"環境変数から認証情報を読み込めませんでした。.envファイルを確認してください: {exc}"
        ) from exc


def _validate_orders(orders: list[BetOrder], max_bet: int) -> None:
    """購入注文リストのバリデーションを行う.

    Args:
        orders: 購入注文リスト
        max_bet: 最大合計購入金額（円）

    Raises:
        ValidationError: バリデーションエラー
    """
    if not orders:
        raise ValidationError("購入注文リストが空です")

    total_amount = sum(order.amount for order in orders)
    if total_amount > max_bet:
        raise ValidationError(f"合計金額{total_amount}円が最大購入金額{max_bet}円を超えています")
