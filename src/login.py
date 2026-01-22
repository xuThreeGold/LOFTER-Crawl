# -*- coding: utf-8 -*-
"""
登录功能模块
"""
import requests
from .utils import get_headers
from .config import LOGIN_KEY, DEFAULT_LOGIN_AUTH


def get_login_session(login_auth=None, login_key=None):
    """
    获取一个登录过的session
    :param login_auth: 登录授权码，如果为None则使用默认值
    :param login_key: 登录key，如果为None则使用默认值
    :return: session
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    headers = get_headers()
    headers["Host"] = "www.lofter.com"
    
    session = requests.session()
    session.headers = headers
    
    # 请求登录页
    login_page_url = "http://www.lofter.com/login"
    payload = {"urschecked": "true"}
    login_page_response = session.get(login_page_url, params=payload)
    print(f"登录页状态码 {login_page_response.status_code}")
    
    # 设置Referer
    headers["Referer"] = "http://www.lofter.com/login"
    session.headers = headers
    
    # 设置cookies
    homepage_url = "http://www.lofter.com/"
    cookies = session.cookies
    cookies.set(login_key, login_auth)
    session.cookies = cookies
    
    # 请求主页验证登录
    response = session.get(homepage_url)
    print(f"主页请求状态码 {response.status_code}")
    
    return session
