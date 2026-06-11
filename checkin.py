import random
import time

import config
import weibo_api


def run_checkin(cookies: dict) -> list[dict]:
    """
    取得超話列表並逐一簽到。
    回傳每個超話的結果清單：
    [{"name": "...", "id": "...", "success": bool, "message": "..."}]
    """
    topics = weibo_api.get_followed_super_topics(cookies)
    if not topics:
        return []

    results = []
    for i, topic in enumerate(topics):
        name = topic["name"]
        topic_id = topic["id"]

        try:
            resp = weibo_api.checkin_super_topic(cookies, topic_id)
            msg = resp.get("msg", "")
            code = resp.get("code", -1)
            ok = code == 0 or "成功" in msg or "已签到" in msg or "已簽到" in msg
            results.append({"name": name, "id": topic_id, "success": ok, "message": msg})
        except Exception as e:
            results.append({"name": name, "id": topic_id, "success": False, "message": str(e)})

        # 最後一個不需要等待
        if i < len(topics) - 1:
            delay = random.uniform(config.CHECKIN_DELAY_MIN, config.CHECKIN_DELAY_MAX)
            time.sleep(delay)

    return results
