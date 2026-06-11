import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import functions_framework

import auth
import checkin
import notifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def run(request):
    logger.info("微博簽到開始")

    # 1. 讀取並驗證 Cookie
    try:
        cookies = auth.load_cookie_from_gcs()
    except FileNotFoundError as e:
        logger.error(str(e))
        notifier.notify_cookie_expired()
        return ("Cookie 不存在，請先在本機執行 auth.py", 500)

    if not auth.verify_cookie(cookies):
        logger.warning("Cookie 已過期")
        notifier.notify_cookie_expired()
        return ("Cookie 已過期", 401)

    # 2. 執行簽到
    try:
        results = checkin.run_checkin(cookies)
    except Exception as e:
        logger.error(f"簽到流程發生例外: {e}")
        return (f"簽到失敗: {e}", 500)

    # 3. 記錄結果
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    for r in results:
        status = "成功" if r["success"] else "失敗"
        logger.info(json.dumps({
            "topic": r["name"],
            "id": r["id"],
            "status": status,
            "message": r["message"],
        }, ensure_ascii=False))

    logger.info(f"簽到完成：共 {len(results)} 個，成功 {success_count}，失敗 {fail_count}")

    # 4. 失敗通知
    failures = [r for r in results if not r["success"]]
    if failures:
        notifier.notify_checkin_failures(failures)

    # 5. 每日完成摘要通知
    date_str = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d")
    notifier.notify_daily_summary(date_str, len(results), success_count, fail_count)

    return (
        json.dumps({
            "total": len(results),
            "success": success_count,
            "fail": fail_count,
        }, ensure_ascii=False),
        200,
        {"Content-Type": "application/json"},
    )
