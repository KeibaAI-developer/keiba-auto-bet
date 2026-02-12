"""例外クラス定義.

このモジュールは、keiba-auto-betライブラリで使用される例外クラスを定義する。
"""


class KeibaAutoBetError(Exception):
    """keiba-auto-bet基底例外.

    keiba-auto-betライブラリの全ての例外の基底クラス。
    """

    pass


class BrowserError(KeibaAutoBetError):
    """ブラウザ操作に関するエラー.

    Chromeの起動・終了に失敗した場合に送出される。
    """

    pass


class LoginError(KeibaAutoBetError):
    """ログインに関するエラー.

    即パットへのログインに失敗した場合に送出される。
    """

    pass


class BetError(KeibaAutoBetError):
    """馬券選択に関するエラー.

    馬券の種類選択・馬番選択・金額入力に失敗した場合に送出される。
    """

    pass


class PurchaseError(KeibaAutoBetError):
    """購入確定に関するエラー.

    購入確定処理に失敗した場合に送出される。
    """

    pass


class ValidationError(KeibaAutoBetError):
    """入力バリデーションに関するエラー.

    購入注文の内容が不正な場合に送出される。
    """

    pass
