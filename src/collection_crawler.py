# -*- coding: utf-8 -*-
"""
合集爬取模块

原理参考 `lofter-helper-main/scripts/lofter-collection.js`：
1. 通过 `https://api.lofter.com/v1.1/postCollection.api?method=getCollectionDetail` 接口
2. 携带 header: `lofter-phone-login-auth: <授权码>`（即浏览器 Cookie 中的 `LOFTER-PHONE-LOGIN-AUTH`）
3. 分页获取某个合集下的所有文章，字段为 `response.items[*].post.blogPageUrl`
"""

import requests
from typing import List, Dict, Any, Optional

from .config import LOGIN_KEY, DEFAULT_LOGIN_AUTH
from .utils import get_headers


API_COLLECTION_URL = "https://api.lofter.com/v1.1/postCollection.api"


def _build_collection_headers(login_auth: Optional[str]) -> Dict[str, str]:
    """
    构建合集相关请求的 headers
    """
    headers = get_headers()
    # API 要求在 header 中携带手机端登录授权
    if login_auth:
        headers[LOGIN_KEY.lower()] = login_auth  # "lofter-phone-login-auth"
    return headers


def get_collection_detail(
    collection_id: str,
    offset: int,
    limit: int = 15,
    order: int = 1,
    login_auth: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取某一合集的一页详情（对应 Tampermonkey 中 getCollectionDetail）

    :param collection_id: 合集 ID（在网页脚本中点击“复制ID”拿到的字符串）
    :param offset: 偏移量，分页用，第一页为 0
    :param limit: 每页条数，默认为 15，与脚本中保持一致
    :param order: 排序方式，1 为默认顺序
    :param login_auth: 登录授权码（LOFTER-PHONE-LOGIN-AUTH），如果为 None 则使用 DEFAULT_LOGIN_AUTH
    :return: 后端返回的 `response` 字段（字典）
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH

    headers = _build_collection_headers(login_auth)

    params = {
        "method": "getCollectionDetail",
        "product": "lofter-android-7.6.12",
        "offset": offset,
        "limit": limit,
        "collectionid": collection_id,
        "order": order,
    }

    resp = requests.get(API_COLLECTION_URL, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    # 与 Tampermonkey 脚本保持一致，真正有用的数据在 data.response 下
    return data.get("response", {})


def get_collection_all_post_urls(
    collection_id: str,
    login_auth: Optional[str] = None,
    limit: int = 15,
    order: int = 1,
) -> List[str]:
    """
    获取某个合集下所有文章的 URL 列表

    会自动分页，直到没有更多 items（len(items) < limit）。
    :param collection_id: 合集 ID
    :param login_auth: 授权码
    :param limit: 每页条数
    :param order: 排序方式
    :return: 文章 URL 列表
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH

    all_urls: List[str] = []
    offset = 0

    while True:
        detail = get_collection_detail(
            collection_id=collection_id,
            offset=offset,
            limit=limit,
            order=order,
            login_auth=login_auth,
        )

        items = detail.get("items", []) or []
        if not items:
            break

        for item in items:
            try:
                post = item.get("post", {})
                url = post.get("blogPageUrl")
                if url and url not in all_urls:
                    all_urls.append(url)
            except Exception:
                continue

        # 分页：如果本页数量小于 limit，说明已经到末尾
        if len(items) < limit:
            break

        offset += limit

    return all_urls

