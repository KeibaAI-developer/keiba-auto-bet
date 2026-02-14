"""ブラウザ操作モジュール.

Seleniumを使用した即パットのブラウザ操作を提供する。
"""

import logging
import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

from keiba_auto_bet.exceptions import BetError, BrowserError, LoginError, PurchaseError
from keiba_auto_bet.models import AutoBetConfig, BetOrder, IpatCredentials, TicketType

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10


def open_chrome(config: AutoBetConfig) -> webdriver.Chrome:
    """Chromeブラウザを起動して即パットページを開く.

    Args:
        config: 自動購入の設定

    Returns:
        webdriver.Chrome: 起動したWebDriverオブジェクト

    Raises:
        BrowserError: Chromeの起動に失敗した場合
    """
    driver = None
    try:
        chrome_options = Options()
        if config.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        if config.chrome_driver_path:
            service = Service(config.chrome_driver_path)
        else:
            service = Service()

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(config.ipat_url)
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception as exc:
        if driver is not None:
            driver.quit()
        raise BrowserError(f"Chromeの起動に失敗しました: {exc}") from exc

    return driver


def login(driver: webdriver.Chrome, credentials: IpatCredentials) -> None:
    """即パットにログインする.

    Args:
        driver: WebDriverオブジェクト
        credentials: 認証情報

    Raises:
        LoginError: ログインに失敗した場合
    """
    try:
        # INET IDの入力
        inetid_input = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.presence_of_element_located((By.NAME, "inetid"))
        )
        inetid_input.send_keys(credentials.inet_id)

        # ログインボタンをクリック
        login_link = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, "//a[@title='ログイン' and @tabindex='4']"))
        )
        login_link.click()

        # 加入者番号・パスワード・P-ARSの入力
        user_number_input = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.presence_of_element_located((By.NAME, "i"))
        )
        user_number_input.send_keys(credentials.user_number)
        password_input = driver.find_element(By.NAME, "p")
        password_input.send_keys(credentials.password)
        p_ars_input = driver.find_element(By.NAME, "r")
        p_ars_input.send_keys(credentials.p_ars)

        # ネット投票メニューへボタンをクリック
        element = "//a[@title='ネット投票メニューへ' and @tabindex='5']"
        menu_link = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, element))
        )
        menu_link.click()
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(ec.staleness_of(menu_link))
    except Exception as exc:
        raise LoginError(f"ログインに失敗しました: {exc}") from exc


def dismiss_announce_page(driver: webdriver.Chrome) -> None:
    """お知らせページが表示されていた場合にOKボタンをクリックして閉じる.

    ログイン直後にお知らせページが挟まることがある。
    お知らせページでない場合は何もしない。

    Args:
        driver: WebDriverオブジェクト

    Raises:
        BrowserError: お知らせページの処理に失敗した場合
    """
    announce_elements = driver.find_elements(By.XPATH, "//h1[contains(text(), 'お知らせ')]")
    if not announce_elements:
        logger.debug("お知らせページではありません。スキップします")
        return

    logger.info("お知らせページが検出されました。OKボタンをクリックして閉じます")
    try:
        ok_button = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-ok"))
        )
        ok_button.click()
        logger.info("お知らせページのOKボタンをクリックしました")

        # お知らせページからの遷移を待機
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(ec.staleness_of(ok_button))
        logger.info("お知らせページからの遷移が完了しました")
    except Exception as exc:
        raise BrowserError(f"お知らせページの処理に失敗しました: {exc}") from exc


def navigate_to_bet_page(driver: webdriver.Chrome) -> None:
    """購入画面に移動する.

    Args:
        driver: WebDriverオブジェクト

    Raises:
        BetError: 購入画面への移動に失敗した場合
    """
    try:
        # 通常投票ボタンをクリック
        element = "//button[@title='出馬表から馬を選択する方式です。']"
        bet_button = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, element))
        )
        bet_button.click()
        logger.info("通常投票ボタンをクリックしました")

        # 通常投票ボタンクリック後のページ遷移を待機
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(ec.staleness_of(bet_button))
        logger.info("通常投票画面に遷移しました")

        # レース選択ボタン（12Rを選択して購入画面に遷移）
        race_select_button = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, "//button[contains(., '12R')]"))
        )
        race_select_button.click()

        # 購入画面への遷移を待機（馬券タイプ選択が表示されるまで待つ）
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.ID, "bet-basic-type"))
        )
        logger.info("購入画面に遷移しました")
    except BetError:
        raise
    except Exception as exc:
        raise BetError(f"購入画面への移動に失敗しました: {exc}") from exc


def select_race(driver: webdriver.Chrome, venue: str, race_number: int) -> None:
    """競馬場とレースを選択する.

    Args:
        driver: WebDriverオブジェクト
        venue: 競馬場名
        race_number: レース番号

    Raises:
        BetError: レース選択に失敗した場合
    """
    try:
        # 競馬場を選択
        element_id = "select-course-race-course"
        keibajo_select = Select(
            WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
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
        race_option_xpath = f"//select[@id='{element_id}']//option[contains(., '{race_number}R')]"
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.presence_of_element_located((By.XPATH, race_option_xpath))
        )
        race_select = Select(driver.find_element(By.ID, element_id))
        race_found = False
        for option in race_select.options:
            if f"{race_number}R" in option.text:
                race_select.select_by_visible_text(option.text)
                race_found = True
                break
        if not race_found:
            raise BetError(f"レースが見つかりませんでした: {race_number}R")

        # レース選択後、AngularJSのDOM再レンダリング完了を待機
        _wait_for_element_stable(driver, By.ID, "bet-basic-type")
    except BetError:
        raise
    except Exception as exc:
        raise BetError(f"レース選択に失敗しました: {exc}") from exc


def bet_win_or_place(
    driver: webdriver.Chrome,
    ticket_type: TicketType,
    horse_number: int,
    amount: int,
) -> None:
    """単勝または複勝の馬券を選択して金額を入力する.

    Args:
        driver: WebDriverオブジェクト
        ticket_type: 馬券の種類（単勝または複勝）
        horse_number: 馬番
        amount: 購入金額（円）

    Raises:
        BetError: 馬券選択または金額入力に失敗した場合
    """
    try:
        # 馬券タイプのプルダウンから選択（DOM再レンダリングによるstale対策でリトライ）
        _select_bet_type_with_retry(driver, ticket_type)

        # 馬番のチェックボックスにチェックを入れる
        label_element = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.presence_of_element_located((By.XPATH, f"//label[@for='no{horse_number}']"))
        )
        checkbox = label_element.find_element(By.CLASS_NAME, "check")
        driver.execute_script("arguments[0].click();", checkbox)

        # 金額入力
        amount_input = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable(
                (By.XPATH, "//input[@maxlength='4' and @ng-model='vm.nUnit']")
            )
        )
        amount_input.clear()
        amount_input.send_keys(str(amount // 100))

        # セットボタンをクリック
        element = "button.btn.btn-lg.btn-set.btn-primary[ng-click='vm.onSet()']"
        set_button = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, element))
        )
        set_button.click()
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.ID, "bet-basic-type"))
        )
    except Exception as exc:
        raise BetError(
            f"馬券選択に失敗しました（{ticket_type.value} {horse_number}番 {amount}円）: {exc}"
        ) from exc


def place_orders(driver: webdriver.Chrome, orders: list[BetOrder]) -> None:
    """全ての購入注文を処理する.

    Args:
        driver: WebDriverオブジェクト
        orders: 購入注文リスト

    Raises:
        BetError: 馬券の選択・入力に失敗した場合
    """
    navigate_to_bet_page(driver)

    for order in orders:
        select_race(driver, order.venue, order.race_number)

        if order.ticket_type in (TicketType.WIN, TicketType.SHOW):
            bet_win_or_place(driver, order.ticket_type, order.horse_number, order.amount)
        else:
            raise BetError(f"未対応の馬券種類です: {order.ticket_type}")


def confirm_purchase(driver: webdriver.Chrome, total_amount: int) -> None:
    """購入を確定する.

    Args:
        driver: WebDriverオブジェクト
        total_amount: 合計購入金額（円）

    Raises:
        PurchaseError: 購入確定に失敗した場合
    """
    try:
        # 購入予定リストボタンを押す
        element = "//button[contains(@class, 'btn btn-vote-list')]"
        purchase_list_button = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, element))
        )
        purchase_list_button.click()

        # 合計金額を入力する
        element = "//input[@ng-model='vm.cAmountTotal']"
        sum_buy = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, element))
        )
        sum_buy.clear()
        sum_buy.send_keys(str(total_amount))

        # 購入ボタンを押す
        purchase_button = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, "//button[contains(text(), '購入')]"))
        )
        purchase_button.click()

        # 確認ダイアログのOKボタンを押す（ダイアログ本文が重なる場合があるためJS経由でクリック）
        element = "//button[contains(@class, 'btn-ok') and contains(text(), 'OK')]"
        ok_button = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, element))
        )
        driver.execute_script("arguments[0].click();", ok_button)

        # ダイアログが閉じるのを待機（SPAのためstaleness_ofではなく非表示を待つ）
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.invisibility_of_element_located((By.XPATH, element))
        )
    except Exception as exc:
        raise PurchaseError(f"購入確定に失敗しました: {exc}") from exc


def navigate_to_top(driver: webdriver.Chrome) -> None:
    """トップ画面に戻る.

    Args:
        driver: WebDriverオブジェクト

    Raises:
        BrowserError: トップ画面への遷移に失敗した場合
    """
    try:
        element = "//a[@ui-sref='home' and @ng-click='vm.clickLogo()']"
        top_return_link = WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, element))
        )
        top_return_link.click()

        # ホーム画面の通常投票ボタンが表示されるまで待機（SPAのためstaleness_ofは使わない）
        home_element = "//button[@title='出馬表から馬を選択する方式です。']"
        WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
            ec.element_to_be_clickable((By.XPATH, home_element))
        )
    except Exception as exc:
        raise BrowserError(f"トップ画面への遷移に失敗しました: {exc}") from exc


_MAX_STALE_RETRIES = 3
_STALE_RETRY_INTERVAL = 1.0


def _wait_for_element_stable(
    driver: webdriver.Chrome,
    by: str,
    value: str,
    timeout: float = _DEFAULT_TIMEOUT,
) -> None:
    """要素のDOMが安定するまで待機する.

    AngularJSのダイジェストサイクルによるDOM再レンダリング後、
    要素が安定的にアクセス可能になるまで待機する。

    Args:
        driver: WebDriverオブジェクト
        by: ロケータ戦略（By.ID等）
        value: ロケータの値
        timeout: タイムアウト秒数

    Raises:
        TimeoutException: タイムアウトしても要素が安定しなかった場合
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            element = driver.find_element(by, value)
            element.is_displayed()
            time.sleep(0.5)
            element.is_displayed()
            return
        except StaleElementReferenceException:
            time.sleep(0.5)
    raise TimeoutException(f"要素 {value} の安定化待機がタイムアウトしました")


def _select_bet_type_with_retry(
    driver: webdriver.Chrome,
    ticket_type: TicketType,
) -> None:
    """馬券タイプを選択する（StaleElementReferenceException対策でリトライ）.

    Args:
        driver: WebDriverオブジェクト
        ticket_type: 馬券の種類

    Raises:
        StaleElementReferenceException: リトライ上限を超えてもstaleの場合
    """
    for attempt in range(_MAX_STALE_RETRIES):
        try:
            bet_type_select = Select(
                WebDriverWait(driver, _DEFAULT_TIMEOUT).until(
                    ec.element_to_be_clickable((By.ID, "bet-basic-type"))
                )
            )
            bet_type_select.select_by_visible_text(ticket_type.value)
            return
        except StaleElementReferenceException:
            if attempt == _MAX_STALE_RETRIES - 1:
                raise
            logger.debug(
                "馬券タイプ選択でStaleElementReferenceExceptionが発生、リトライ(%d/%d)",
                attempt + 1,
                _MAX_STALE_RETRIES,
            )
            time.sleep(_STALE_RETRY_INTERVAL)
