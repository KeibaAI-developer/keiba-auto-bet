"""IpatCredentialsのテスト."""

import pytest

from keiba_auto_bet.models import IpatCredentials


# 正常系
def test_ipat_credentials_valid() -> None:
    """有効なパラメータでIpatCredentialsが生成できる."""
    credentials = IpatCredentials(
        inet_id="test_id",
        user_number="12345678",
        password="test_pass",
        p_ars="1234",
    )
    assert credentials.inet_id == "test_id"
    assert credentials.user_number == "12345678"
    assert credentials.password == "test_pass"
    assert credentials.p_ars == "1234"


def test_ipat_credentials_is_frozen() -> None:
    """IpatCredentialsが不変（frozen）であることを確認する."""
    credentials = IpatCredentials(
        inet_id="test_id",
        user_number="12345678",
        password="test_pass",
        p_ars="1234",
    )
    with pytest.raises(AttributeError):
        credentials.inet_id = "new_id"  # type: ignore[misc]


# 準正常系
@pytest.mark.parametrize(
    "inet_id, user_number, password, p_ars, expected_msg",
    [
        ("", "12345678", "pass", "1234", "INET IDは必須です"),
        ("id", "", "pass", "1234", "加入者番号は必須です"),
        ("id", "12345678", "", "1234", "パスワードは必須です"),
        ("id", "12345678", "pass", "", "P-ARS番号は必須です"),
    ],
)
def test_ipat_credentials_empty_fields(
    inet_id: str,
    user_number: str,
    password: str,
    p_ars: str,
    expected_msg: str,
) -> None:
    """空の認証情報でValueErrorが発生する."""
    with pytest.raises(ValueError, match=expected_msg):
        IpatCredentials(
            inet_id=inet_id,
            user_number=user_number,
            password=password,
            p_ars=p_ars,
        )
