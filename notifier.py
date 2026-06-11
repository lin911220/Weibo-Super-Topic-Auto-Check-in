import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import config


def _send(subject: str, body: str):
    if not all([config.SMTP_USERNAME, config.SMTP_PASSWORD, config.EMAIL_RECEIVER]):
        print(f"[notifier] Email 設定不完整，略過通知。主旨：{subject}")
        return

    msg = MIMEMultipart()
    msg["From"] = config.EMAIL_SENDER
    msg["To"] = config.EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        smtp.send_message(msg)


def notify_cookie_expired():
    _send(
        subject="[微博簽到] Cookie 已過期，需要重新登入",
        body=(
            "微博簽到程式偵測到 Cookie 已過期或失效。\n\n"
            "請在本機執行以下指令重新登入：\n\n"
            "    python auth.py\n\n"
            "掃描 QR Code 後，新的 Cookie 會自動上傳到 GCS。"
        ),
    )


def notify_checkin_failures(failures: list[dict]):
    lines = "\n".join(
        f"  - {f['name']} (ID: {f['id']}): {f['message']}"
        for f in failures
    )
    _send(
        subject=f"[微博簽到] {len(failures)} 個超話簽到失敗",
        body=f"今日簽到有以下超話失敗：\n\n{lines}\n\n請確認帳號狀態或 API 是否異常。",
    )


def notify_daily_summary(date_str: str, total: int, success: int, fail: int):
    _send(
        subject=f"[微博簽到] {date_str} 完成：{success}/{total} 成功",
        body=(
            f"日期：{date_str}\n"
            f"總計：{total} 個超話\n"
            f"成功：{success}\n"
            f"失敗：{fail}\n"
        ),
    )
