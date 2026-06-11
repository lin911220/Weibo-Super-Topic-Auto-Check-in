import requests
import config

SESSION = requests.Session()
SESSION.headers.update(config.DEFAULT_HEADERS)


def get_followed_super_topics(cookies) -> list[dict]:
    """
    取得目前帳號關注的超話列表（自動處理分頁）。
    回傳 [{"name": "...", "id": "..."}]
    """
    topics = []
    page = 1
    max_page = 1

    while page <= max_page:
        resp = SESSION.get(
            config.ENDPOINTS["followed_supertopics"],
            cookies=cookies,
            params={"tabid": config.SUPERTOPIC_TAB_ID, "page": page},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        max_page = data.get("max_page", 1)

        for topic in data.get("list", []):
            title = topic.get("title", "")
            link = topic.get("link", "")
            last_slash = link.rfind("/")
            topic_id = link[last_slash + 1:] if last_slash != -1 else link
            if title and topic_id:
                topics.append({"name": title, "id": topic_id})

        page += 1

    return topics


def checkin_super_topic(cookies, topic_id: str) -> dict:
    """
    對單一超話發送簽到請求。
    回傳原始 API 回應 dict。
    """
    import time
    params = {
        "ajwvr": "6",
        "api": config.CHECKIN_API,
        "texta": "簽到",
        "textb": "已簽到",
        "status": "0",
        "id": topic_id,
        "location": "page_100808_super_index",
        "timezone": "GMT+0800",
        "lang": "zh-cn",
        "plat": "Win32",
        "ua": config.DEFAULT_HEADERS["User-Agent"],
        "screen": "1920*1080",
        "__rnd": str(int(time.time() * 1000)),
    }
    resp = SESSION.get(
        config.ENDPOINTS["checkin"],
        cookies=cookies,
        params=params,
        timeout=config.REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
