import os
from dotenv import load_dotenv

load_dotenv()

# ============ GCP 配置 ============
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "weibo-checkin-bucket")
GCS_COOKIE_FILE = "weibo_cookie.json"

# ============ 微博 QR Code 登入 API ============
WEIBO_QR_IMAGE_URL = "https://login.sina.com.cn/sso/qrcode/image"
WEIBO_QR_CHECK_URL = "https://login.sina.com.cn/sso/qrcode/check"
WEIBO_QR_LOGIN_URL = "https://login.sina.com.cn/sso/login.php"

# ============ 微博功能 API ============
WEIBO_H5_BASE = "https://m.weibo.cn"

ENDPOINTS = {
    "followed_supertopics": "https://weibo.com/ajax/profile/topicContent",
    "checkin":              "https://weibo.com/p/aj/general/button",
}

SUPERTOPIC_TAB_ID = "231093_-_chaohua"
CHECKIN_API = "http://i.huati.weibo.com/aj/super/checkin"

# ============ HTTP Headers（模擬真人瀏覽器）============
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://weibo.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
}

# ============ 簽到間隔（秒）============
CHECKIN_DELAY_MIN = 3
CHECKIN_DELAY_MAX = 8
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

# ============ QR Code 輪詢設定 ============
QR_POLL_INTERVAL = 3
QR_POLL_TIMEOUT = 120

# ============ Email 通知（Gmail SMTP）============
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", SMTP_USERNAME)
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")

# ============ 環境 ============
ENV = os.getenv("ENV", "local")
IS_PRODUCTION = ENV == "gcp"
