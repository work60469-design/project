import datetime

import streamlit as st
import extra_streamlit_components as stx
from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired
)

# مهم جدًا: غيّر القيمة دي لسلسلة عشوائية طويلة وسرية بتاعتك
SECRET_KEY = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_STRING"

COOKIE_NAME = "biology_mgmt_auth"
COOKIE_MAX_AGE_DAYS = 365

serializer = URLSafeTimedSerializer(SECRET_KEY)


def get_cookie_manager():
    """
    بترجع نفس الـ CookieManager طول الوقت (instance واحدة)
    بدل ما تتعمل من جديد كل مرة، وده بيمنع مشاكل غريبة.
    """
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(
            key="cookie_manager_init"
        )
    return st.session_state.cookie_manager


def set_auth_cookie(username, role, display_name):
    """
    بتتنادى بعد نجاح تسجيل الدخول، بتخزن بيانات المستخدم
    فى كوكي موقّع (signed) عشان محدش يقدر يعدلها يدويًا.
    """
    cookie_manager = get_cookie_manager()

    token = serializer.dumps({
        "username": username,
        "role": role,
        "display_name": display_name
    })

    expires_at = (
        datetime.datetime.now()
        + datetime.timedelta(days=COOKIE_MAX_AGE_DAYS)
    )

    cookie_manager.set(
        COOKIE_NAME,
        token,
        expires_at=expires_at,
        key="set_auth_cookie"
    )


def get_auth_data_from_cookie():
    """
    بتقرا الكوكي (لو موجودة وصالحة) وبترجع بيانات المستخدم.
    بترجع None لو مفيش كوكي أو انتهت صلاحيتها أو اتلعب فيها.
    """
    cookie_manager = get_cookie_manager()

    # الخطوة دي إجبارية: لازم نقرا كل الكوكيز الأول (hydration)
    # قبل ما نحاول نقرا كوكي بعينها، وإلا هترجع None غلط
    all_cookies = cookie_manager.get_all(key="get_all_cookies")

    if not all_cookies:
        return None

    token = all_cookies.get(COOKIE_NAME)

    if not token:
        return None

    try:
        data = serializer.loads(
            token,
            max_age=COOKIE_MAX_AGE_DAYS * 24 * 60 * 60
        )
        return data

    except (BadSignature, SignatureExpired):
        return None


def clear_auth_cookie():
    """بتتنادى عند تسجيل الخروج."""
    cookie_manager = get_cookie_manager()

    try:
        cookie_manager.delete(
            COOKIE_NAME,
            key="delete_auth_cookie"
        )
    except KeyError:
        pass
