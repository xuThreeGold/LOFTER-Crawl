# -*- coding: utf-8 -*-
"""
合集爬取模块

原理参考 `lofter-helper-main/scripts/lofter-collection.js`：
1. 通过 `https://api.lofter.com/v1.1/postCollection.api?method=getCollectionDetail` 接口
2. 携带 header: `lofter-phone-login-auth: <授权码>`（即浏览器 Cookie 中的 `LOFTER-PHONE-LOGIN-AUTH`）
3. 分页获取某个合集下的所有文章，字段为 `response.items[*].post.blogPageUrl`
"""

import re
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


def get_collections_by_blogdomain(
    blogdomain: str,
    login_auth: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    获取某个作者在 LOFTER 上的所有合集列表（对应 JS 中 getCollection）

    :param blogdomain: 形如 "xxx.lofter.com" 的域名
    :param login_auth: 登录授权码
    :return: 合集列表，每个元素是后端返回的 collection 字典
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH

    headers = _build_collection_headers(login_auth)

    params = {
        "method": "getCollectionList",
        "needViewCount": 1,
        "blogdomain": blogdomain,
        "product": "lofter-android-7.6.12",
    }

    resp = requests.get(API_COLLECTION_URL, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    response = data.get("response", {}) or {}
    collections = response.get("collections", []) or []
    return collections


def get_collections_by_author_url(
    author_url: str,
    login_auth: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    通过作者主页 URL 获取该作者的所有合集

    :param author_url: 作者主页，例如 "https://xxx.lofter.com" 或 "https://xxx.lofter.com/"
    """
    # 提取作者 ip / 子域名部分
    m = re.search(r"http[s]?://([^/]+)\.lofter\.com", author_url)
    if not m:
        raise ValueError(f"无效的作者 URL：{author_url}")

    author_ip = m.group(1)
    blogdomain = f"{author_ip}.lofter.com"
    return get_collections_by_blogdomain(blogdomain, login_auth=login_auth)


def get_collection_meta(
    collection_id: str,
    login_auth: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取单个合集的元信息（名称、作者等），用于文件夹命名。

    由于 postCollection.api 并没有“按ID查单个合集”的独立接口，
    这里的做法是：
    1. 先用 getCollectionDetail 拿一页详情，里面包含 collection 的基础信息
    2. 再从 response 中抽取 name、blogs 等字段
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH

    headers = _build_collection_headers(login_auth)
    params = {
        "method": "getCollectionDetail",
        "product": "lofter-android-7.6.12",
        "offset": 0,
        "limit": 1,
        "collectionid": collection_id,
        "order": 1,
    }

    resp = requests.get(API_COLLECTION_URL, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    response = data.get("response", {}) or {}
    # 通常 response 中会包含 collection 信息（兼容字段名未知时，直接全部返回）
    return response

