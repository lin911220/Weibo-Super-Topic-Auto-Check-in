import json
import requests

import config

SESSION = requests.Session()
SESSION.headers.update(config.DEFAULT_HEADERS)


# ──────────────────────────────────────────
# Playwright 登入（本機一次性執行）
# ──────────────────────────────────────────

def login_with_playwright() -> list:
    """
    用 Playwright 開瀏覽器，讓使用者掃碼登入。
    瀏覽器的 JavaScript 會自動完成跨域 Cookie 換取。
    回傳含 domain 資訊的 cookie list。
    僅供本機執行，雲端環境不需安裝 Playwright。
    """
    from playwright.sync_api import sync_playwright

    login_url = (
        "https://passport.weibo.com/sso/signin"
        "?entry=miniblog&source=miniblog&disp=popup"
        "&url=https%3A%2F%2Fweibo.com%2F"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("正在開啟微博登入頁面...")
        page.goto(login_url)
        print("請用微博 APP 掃描 QR Code 並確認登入...")

        # 等待登入成功的標誌：SUB cookie 出現在 weibo.com
        page.wait_for_function(
            """() => document.cookie.includes('SUB=') ||
               window.location.hostname === 'weibo.com'""",
            timeout=120000,
        )

        # 額外等待讓跨域 Cookie 全部設置完成
        page.wait_for_timeout(3000)

        # 訪問 weibo.com 確保所有 Cookie 都已設置
        page.goto("https://weibo.com/")
        page.wait_for_timeout(2000)

        cookies = context.cookies()
        browser.close()

    # 只保留有用的 Cookie（過濾掉空值）
    result = [
        {"name": c["name"], "value": c["value"], "domain": c["domain"]}
        for c in cookies
        if c["value"]
    ]
    print(f"取得 {len(result)} 個 Cookie")
    return result


# ──────────────────────────────────────────
# GCS Cookie 讀寫
# ──────────────────────────────────────────

def _get_gcs_client():
    from google.cloud import storage
    return storage.Client(project="weibo-checkin")


def save_cookie_to_gcs(cookies: list):
    client = _get_gcs_client()
    bucket = client.bucket(config.GCS_BUCKET_NAME)
    blob = bucket.blob(config.GCS_COOKIE_FILE)
    blob.upload_from_string(
        json.dumps(cookies, ensure_ascii=False),
        content_type="application/json",
    )
    print(f"Cookie 已儲存到 gs://{config.GCS_BUCKET_NAME}/{config.GCS_COOKIE_FILE}")


def load_cookie_from_gcs() -> requests.cookies.RequestsCookieJar:
    client = _get_gcs_client()
    bucket = client.bucket(config.GCS_BUCKET_NAME)
    blob = bucket.blob(config.GCS_COOKIE_FILE)
    if not blob.exists():
        raise FileNotFoundError("GCS 上找不到 Cookie 檔案，請先在本機執行登入流程")
    data = json.loads(blob.download_as_text())
    jar = requests.cookies.RequestsCookieJar()
    for c in data:
        jar.set(c["name"], c["value"], domain=c["domain"])
    return jar


# ──────────────────────────────────────────
# Cookie 有效性驗證
# ──────────────────────────────────────────

def verify_cookie(cookies) -> bool:
    """呼叫超話列表 API 確認 Cookie 是否仍有效"""
    try:
        resp = SESSION.get(
            config.ENDPOINTS["followed_supertopics"],
            cookies=cookies,
            params={"tabid": config.SUPERTOPIC_TAB_ID},
            timeout=config.REQUEST_TIMEOUT,
        )
        data = resp.json()
        return "data" in data and data.get("ok") != -100
    except Exception:
        return False


# ──────────────────────────────────────────
# 本機執行入口：登入並存到 GCS
# ──────────────────────────────────────────

if __name__ == "__main__":
    cookies = login_with_playwright()
    save_cookie_to_gcs(cookies)
    print("完成，Cookie 已上傳到 GCS。")
