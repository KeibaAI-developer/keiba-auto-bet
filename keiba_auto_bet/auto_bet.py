"""自動購入メインモジュール.

馬券自動購入の公開APIを提供する。
"""

import logging
import os
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

from keiba_auto_bet.exceptions import (
    BetError,
    BrowserError,
    KeibaAutoBetError,
    LoginError,
    PurchaseError,
    ValidationError,
)
from keiba_auto_bet.models import AutoBetConfig, BetOrder, IpatCredentials, TicketType

_DEFAULT_TIMEOUT = 10  # タイムアウト秒数
_MAX_STALE_RETRIES = 3  # StaleElementReferenceException発生時のリトライ回数
_STALE_RETRY_INTERVAL = 1.0  # StaleElementReferenceException発生時のリトライ間隔（秒）


class AutoBetter:
    """馬券自動購入クライアント.

    即パットを使用して馬券を自動購入するクライアント。
    Seleniumを使用してブラウザ操作を行う。

    Attributes:
        _credentials: 即パットの認証情報
        _config: 自動購入の設定
        _logger: ロガーインスタンス
        _driver: WebDriverオブジェクト
    """

    def __init__(
        self,
        credentials: IpatCredentials | None = None,
        config: AutoBetConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """コンストラクタ.

        Args:
            credentials: 即パットの認証情報（Noneの場合は環境変数から読み込む）
            config: 自動購入の設定（Noneの場合はデフォルト設定を使用）
            logger: ロガーインスタンス。Noneの場合はモジュールロガーを使用

        Raises:
            ValidationError: 環境変数から認証情報を読み込めない場合
        """
        if credentials is None:
            credentials = _load_credentials_from_env()
        if config is None:
            config = AutoBetConfig()
        if logger is None:
            logger = logging.getLogger(__name__)

        self._credentials = credentials
        self._config = config
        self._logger = logger
        self._driver: webdriver.Chrome | None = None

    def bet(self, orders: list[BetOrder]) -> bool:
        """馬券を自動購入する.

        指定された購入注文リストに基づいて、即パットを使用して馬券を自動購入する。
        あらかじめ即パットに入金しておくこと。

        Args:
            orders: 購入注文リスト

        Returns:
            bool: 購入が正常に完了した場合はTrue

        Raises:
            ValidationError: 入力内容のバリデーションエラー
            KeibaAutoBetError: 購入処理中にエラーが発生した場合
        """
        _validate_orders(orders, self._config.max_bet)

        total_amount = sum(order.amount for order in orders)
        self._logger.info("購入合計金額: %d円（%d件）", total_amount, len(orders))

        self._open_chrome()

        try:
            self._login()
            self._dismiss_announce_page()
            self._place_orders(orders)
            self._confirm_purchase(total_amount)
            self._navigate_to_top()
            self._logger.info("馬券の自動購入が完了しました")
            return True
        except KeibaAutoBetError:
            raise
        except Exception as exc:
            raise KeibaAutoBetError(f"予期しないエラーが発生しました: {exc}") from exc
        finally:
            try:
                if self._driver is not None:
                    self._driver.quit()
            except Exception:
                pass

    def _open_chrome(self) -> None:
        """Chromeブラウザを起動して即パットページを開く.

        Raises:
            BrowserError: Chromeの起動に失敗した場合
        """
        try:
            chrome_options = Options()
            if self._config.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            if self._config.chrome_driver_path:
                service = Service(self._config.chrome_driver_path)
            else:
                service = Service()

            self._driver = webdriver.Chrome(service=service, options=chrome_options)
            self._driver.get(self._config.ipat_url)
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception as exc:
            if self._driver is not None:
                self._driver.quit()
                self._driver = None
            raise BrowserError(f"Chromeの起動に失敗しました: {exc}") from exc

    def _login(self) -> None:
        """即パットにログインする.

        Raises:
            LoginError: ログインに失敗した場合
        """
        assert self._driver is not None
        try:
            # INET IDの入力
            inetid_input = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.presence_of_element_located((By.NAME, "inetid"))
            )
            inetid_input.send_keys(self._credentials.inet_id)

            # ログインボタンをクリック
            login_link = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, "//a[@title='ログイン' and @tabindex='4']"))
            )
            login_link.click()

            # 加入者番号・パスワード・P-ARSの入力
            user_number_input = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.presence_of_element_located((By.NAME, "i"))
            )
            user_number_input.send_keys(self._credentials.user_number)
            password_input = self._driver.find_element(By.NAME, "p")
            password_input.send_keys(self._credentials.password)
            p_ars_input = self._driver.find_element(By.NAME, "r")
            p_ars_input.send_keys(self._credentials.p_ars)

            # ネット投票メニューへボタンをクリック
            element = "//a[@title='ネット投票メニューへ' and @tabindex='5']"
            menu_link = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, element))
            )
            menu_link.click()
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(ec.staleness_of(menu_link))
        except Exception as exc:
            raise LoginError(f"ログインに失敗しました: {exc}") from exc

    def _dismiss_announce_page(self) -> None:
        """お知らせページが表示されていた場合にOKボタンをクリックして閉じる.

        ログイン直後にお知らせページが挟まることがある。
        お知らせページでない場合は何もしない。

        Raises:
            BrowserError: お知らせページの処理に失敗した場合
        """
        assert self._driver is not None
        announce_elements = self._driver.find_elements(
            By.XPATH, "//h1[contains(text(), 'お知らせ')]"
        )
        if not announce_elements:
            self._logger.debug("お知らせページではありません。スキップします")
            return

        self._logger.info("お知らせページが検出されました。OKボタンをクリックして閉じます")
        try:
            ok_button = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-ok"))
            )
            ok_button.click()
            self._logger.info("お知らせページのOKボタンをクリックしました")

            # お知らせページからの遷移を待機
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(ec.staleness_of(ok_button))
            self._logger.info("お知らせページからの遷移が完了しました")
        except Exception as exc:
            raise BrowserError(f"お知らせページの処理に失敗しました: {exc}") from exc

    def _navigate_to_bet_page(self) -> None:
        """購入画面に移動する.

        Raises:
            BetError: 購入画面への移動に失敗した場合
        """
        assert self._driver is not None
        try:
            # 通常投票ボタンをクリック
            element = "//button[@title='出馬表から馬を選択する方式です。']"
            bet_button = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, element))
            )
            bet_button.click()
            self._logger.info("通常投票ボタンをクリックしました")

            # 通常投票ボタンクリック後のページ遷移を待機
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(ec.staleness_of(bet_button))
            self._logger.info("通常投票画面に遷移しました")

            # レース選択ボタン（12Rを選択して購入画面に遷移）
            race_select_button = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, "//button[contains(., '12R')]"))
            )
            race_select_button.click()

            # 購入画面への遷移を待機（馬券タイプ選択が表示されるまで待つ）
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.ID, "bet-basic-type"))
            )
            self._logger.info("購入画面に遷移しました")
        except BetError:
            raise
        except Exception as exc:
            raise BetError(f"購入画面への移動に失敗しました: {exc}") from exc

    def _select_race(self, venue: str, race_number: int) -> None:
        """競馬場とレースを選択する.

        Args:
            venue: 競馬場名
            race_number: レース番号

        Raises:
            BetError: レース選択に失敗した場合
        """
        assert self._driver is not None
        try:
            # 競馬場を選択
            element_id = "select-course-race-course"
            keibajo_select = Select(
                WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                    ec.element_to_be_clickable((By.ID, element_id))
                )
            )
            venue_found = False
            for option in keibajo_select.options:
                if venue in option.text:
                    keibajo_select.select_by_visible_text(option.text)
                    venue_found = True
                    break
            if not venue_found:
                raise BetError(f"競馬場が見つかりませんでした: {venue}")

            # レースを選択（競馬場選択後のプルダウン更新を待機）
            element_id = "select-course-race-race"
            race_option_xpath = (
                f"//select[@id='{element_id}']//option[contains(., '{race_number}R')]"
            )
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.presence_of_element_located((By.XPATH, race_option_xpath))
            )
            race_select = Select(self._driver.find_element(By.ID, element_id))
            race_found = False
            for option in race_select.options:
                if f"{race_number}R" in option.text:
                    race_select.select_by_visible_text(option.text)
                    race_found = True
                    break
            if not race_found:
                raise BetError(f"レースが見つかりませんでした: {race_number}R")

            # レース選択後、AngularJSのDOM再レンダリング完了を待機
            self._wait_for_element_stable(By.ID, "bet-basic-type")
        except BetError:
            raise
        except Exception as exc:
            raise BetError(f"レース選択に失敗しました: {exc}") from exc

    def _bet_win_or_place(
        self,
        ticket_type: TicketType,
        horse_number: int,
        amount: int,
    ) -> None:
        """単勝または複勝の馬券を選択して金額を入力する.

        Args:
            ticket_type: 馬券の種類（単勝または複勝）
            horse_number: 馬番
            amount: 購入金額（円）

        Raises:
            BetError: 馬券選択または金額入力に失敗した場合
        """
        assert self._driver is not None
        try:
            # 馬券タイプのプルダウンから選択（DOM再レンダリングによるstale対策でリトライ）
            self._select_bet_type_with_retry(ticket_type)

            # 馬番のチェックボックスにチェックを入れる
            label_element = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.presence_of_element_located((By.XPATH, f"//label[@for='no{horse_number}']"))
            )
            checkbox = label_element.find_element(By.CLASS_NAME, "check")
            self._driver.execute_script("arguments[0].click();", checkbox)

            # 金額入力
            amount_input = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//input[@maxlength='4' and @ng-model='vm.nUnit']")
                )
            )
            amount_input.clear()
            amount_input.send_keys(str(amount // 100))

            # セットボタンをクリック
            element = "button.btn.btn-lg.btn-set.btn-primary[ng-click='vm.onSet()']"
            set_button = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.CSS_SELECTOR, element))
            )
            set_button.click()
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.ID, "bet-basic-type"))
            )
        except Exception as exc:
            raise BetError(
                f"馬券選択に失敗しました"
                f"（{ticket_type.value} {horse_number}番 {amount}円）: {exc}"
            ) from exc

    def _place_orders(self, orders: list[BetOrder]) -> None:
        """全ての購入注文を処理する.

        Args:
            orders: 購入注文リスト

        Raises:
            BetError: 馬券の選択・入力に失敗した場合
        """
        self._navigate_to_bet_page()

        for order in orders:
            self._select_race(order.venue, order.race_number)

            if order.ticket_type in (TicketType.WIN, TicketType.SHOW):
                self._bet_win_or_place(order.ticket_type, order.horse_number, order.amount)
            else:
                raise BetError(f"未対応の馬券種類です: {order.ticket_type}")

    def _confirm_purchase(self, total_amount: int) -> None:
        """購入を確定する.

        Args:
            total_amount: 合計購入金額（円）

        Raises:
            PurchaseError: 購入確定に失敗した場合
        """
        assert self._driver is not None
        try:
            # 購入予定リストボタンを押す
            element = "//button[contains(@class, 'btn btn-vote-list')]"
            purchase_list_button = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, element))
            )
            purchase_list_button.click()

            # 合計金額を入力する
            element = "//input[@ng-model='vm.cAmountTotal']"
            sum_buy = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, element))
            )
            sum_buy.clear()
            sum_buy.send_keys(str(total_amount))

            # 購入ボタンを押す
            purchase_button = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, "//button[contains(text(), '購入')]"))
            )
            purchase_button.click()

            # 確認ダイアログのOKボタンを押す（ダイアログ本文が重なる場合があるためJS経由でクリック）
            element = "//button[contains(@class, 'btn-ok') and contains(text(), 'OK')]"
            ok_button = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, element))
            )
            self._driver.execute_script("arguments[0].click();", ok_button)

            # ダイアログが閉じるのを待機（SPAのためstaleness_ofではなく非表示を待つ）
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.invisibility_of_element_located((By.XPATH, element))
            )
        except Exception as exc:
            raise PurchaseError(f"購入確定に失敗しました: {exc}") from exc

    def _navigate_to_top(self) -> None:
        """トップ画面に戻る.

        Raises:
            BrowserError: トップ画面への遷移に失敗した場合
        """
        assert self._driver is not None
        try:
            element = "//a[@ui-sref='home' and @ng-click='vm.clickLogo()']"
            top_return_link = WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, element))
            )
            top_return_link.click()

            # ホーム画面の通常投票ボタンが表示されるまで待機（SPAのためstaleness_ofは使わない）
            home_element = "//button[@title='出馬表から馬を選択する方式です。']"
            WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                ec.element_to_be_clickable((By.XPATH, home_element))
            )
        except Exception as exc:
            raise BrowserError(f"トップ画面への遷移に失敗しました: {exc}") from exc

    def _wait_for_element_stable(
        self,
        by: str,
        value: str,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        """要素のDOMが安定するまで待機する.

        AngularJSのダイジェストサイクルによるDOM再レンダリング後、
        要素が安定的にアクセス可能になるまで待機する。

        Args:
            by: ロケータ戦略（By.ID等）
            value: ロケータの値
            timeout: タイムアウト秒数

        Raises:
            TimeoutException: タイムアウトしても要素が安定しなかった場合
        """
        assert self._driver is not None
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                element = self._driver.find_element(by, value)
                element.is_displayed()
                time.sleep(0.5)
                element.is_displayed()
                return
            except StaleElementReferenceException:
                time.sleep(0.5)
        raise TimeoutException(f"要素 {value} の安定化待機がタイムアウトしました")

    def _select_bet_type_with_retry(self, ticket_type: TicketType) -> None:
        """馬券タイプを選択する（StaleElementReferenceException対策でリトライ）.

        Args:
            ticket_type: 馬券の種類

        Raises:
            StaleElementReferenceException: リトライ上限を超えてもstaleの場合
        """
        assert self._driver is not None
        for attempt in range(_MAX_STALE_RETRIES):
            try:
                bet_type_select = Select(
                    WebDriverWait(self._driver, _DEFAULT_TIMEOUT).until(
                        ec.element_to_be_clickable((By.ID, "bet-basic-type"))
                    )
                )
                bet_type_select.select_by_visible_text(ticket_type.value)
                return
            except StaleElementReferenceException:
                if attempt == _MAX_STALE_RETRIES - 1:
                    raise
                self._logger.debug(
                    "馬券タイプ選択でStaleElementReferenceExceptionが発生、リトライ(%d/%d)",
                    attempt + 1,
                    _MAX_STALE_RETRIES,
                )
                time.sleep(_STALE_RETRY_INTERVAL)


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
    except ValueError as e:
        raise ValidationError(
            f"環境変数から認証情報を読み込めませんでした。環境設定ファイル（.env）を確認してください: {e}"
        ) from e


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
