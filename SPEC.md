# 微博超話自動簽到系統 規格書

## 目標
每天自動對所有關注的超話進行簽到，不需要人工介入。

## 系統環境
- 平台：GCP Cloud Functions（第二代，HTTP trigger，region: asia-east1）
- 排程：Cloud Scheduler 每天固定時間觸發（目前：台灣時間 09:00，cron `0 9 * * *`）
- 語言：Python 3.11

## 功能流程
1. 使用者在本機執行 auth.py，透過 Playwright 開啟瀏覽器掃 QR Code 登入微博，程式取得並儲存 Cookie（含 domain 資訊）到 GCS
2. Cloud Functions 啟動時從 GCS 讀取 Cookie，並驗證是否仍有效
3. 程式用 Cookie 向微博 API 請求「我關注的超話列表」（自動處理分頁，取得全部超話）
4. 從列表中提取每個超話的名稱和 ID
5. 對每個超話發送簽到請求（每次之間加隨機延遲）
6. 記錄每次簽到結果到 Cloud Logging
7. 若 Cookie 過期或簽到有失敗項目，發 Email 通知使用者
8. 無論成功或失敗，每次執行完畢都發送「每日完成摘要」Email（含日期、成功/失敗數量），方便確認系統正常運作並觀察 Cookie 有效期

## 輸入
- 微博登入 Cookie（透過 Playwright 開瀏覽器掃 QR Code 取得，含各 domain 的 Cookie）
- 超話列表（從微博 API 動態獲取並自動翻頁，不寫死）

## 輸出
- Cloud Logging 記錄：時間、超話名稱、簽到結果（成功/失敗/原因）
- Email 通知（Gmail SMTP）：
  - Cookie 過期時提示重新掃碼
  - 有簽到失敗時附上失敗詳情
  - 每日完成摘要（日期、成功/失敗數量），不論結果皆發送

## 限制
- 不使用帳號密碼登入（微博限制）
- Cookie 持久化儲存於 GCS（費用考量，安全性足夠）；不可 commit 到 git
- 簽到需模擬真人行為（隨機間隔延遲、模擬 HTTP header 等），避免被偵測為 bot
- Cookie 過期需人工重新掃碼，程式負責偵測並以 Email 通知
- 微博 API endpoint 集中在 config.py 管理，方便 API 結構變動時維護
- 登入須使用 Playwright（本機執行，需安裝 Chromium），純 API 呼叫無法取得 weibo.com 網域所需的完整 Cookie
- Cloud Functions 部署不包含 Playwright（僅本機登入流程需要），`auth.py` 中 Playwright 為延遲載入（lazy import），避免雲端環境因缺少套件而啟動失敗
- Cloud Function 設定 `--no-allow-unauthenticated`，僅允許具備 invoker 權限的服務帳號呼叫（Cloud Scheduler 透過 OIDC token 驗證）

## 模組架構
```
weibo-checkin/
├── main.py                 # Cloud Functions 入口點（HTTP trigger）
├── auth.py                 # Cookie 管理（Playwright 登入、GCS 讀寫、有效性驗證）
├── weibo_api.py            # 微博 API 封裝（超話列表含分頁、簽到請求、HTTP headers）
├── checkin.py              # 主流程協調器（串接 auth + weibo_api，控制隨機延遲）
├── notifier.py             # Gmail SMTP Email 通知
├── config.py               # 集中管理設定常數（endpoint、bucket、延遲範圍、收件人）
├── requirements.txt        # Cloud Functions 部署依賴（不含 playwright）
├── requirements-local.txt  # 本機開發依賴（含 playwright，用於 auth.py 登入）
├── .gcloudignore           # 部署時排除 myenv/、.env、測試檔案等
├── relogin.bat             # 本機一鍵重新登入捷徑（含桌面捷徑）
├── .env                    # 實際環境變數（不入 git）
└── .env.example            # 環境變數範本（不含真實值）
```

## 架構圖
```
┌─────────────┐
│ 你的電腦     │
│ auth.py     │── Playwright 開瀏覽器掃 QR Code
└──────┬──────┘
       │ 把 Cookie 寫成 JSON
       ▼
┌─────────────┐
│ GCS Bucket  │── 雲端硬碟，存 Cookie
└──────┬──────┘
       │ 每天 09:00 被讀取
       ▼
┌──────────────────┐     ┌──────────────────┐
│ Cloud Scheduler   │────▶│ Cloud Functions   │
│ (鬧鐘，定時發請求)  │ HTTP│ (跑 main.py)      │
└──────────────────┘     └─────────┬─────────┘
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
                   Cloud Logging        Gmail SMTP
                  （記錄簽到結果）        （Email 通知）
```

## 已驗證可運作
- Playwright 登入並取得完整 Cookie（含 weibo.com、m.weibo.cn 等 domain）
- Cookie 存取 GCS（bucket: weibo-checkin-project）
- 取得超話列表（含分頁，目前共 24 個）
- 逐一簽到（測試全部成功，24/24 成功）
- Email 通知（Gmail SMTP，已設定應用程式密碼並測試成功，含每日摘要）
- 部署到 Cloud Functions（asia-east1，URL: https://asia-east1-weibo-checkin.cloudfunctions.net/weibo-checkin）
- Cloud Scheduler 每日定時觸發（job: weibo-checkin-daily，每天台灣時間 09:00，已手動測試成功）
- 本機重新登入捷徑（桌面捷徑「微博重新登入」，雙擊執行 auth.py 並更新 GCS 上的 Cookie）

## 尚待完成
- 持續觀察每日摘要 Email（自 2026-06-11 起），記錄 Cookie 大約可使用幾天，作為後續優化依據
- 視需要調整觸發時間或加入隨機偏移機制
- （未來可選）若觀察後認為手動重新登入頻率過高，可考慮 Telegram Bot 推送 QR Code 的方案（需將登入流程搬到雲端容器執行）
