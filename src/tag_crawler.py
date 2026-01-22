# -*- coding: utf-8 -*-
"""
Tag爬取模块
"""
import re
import time
import requests
from urllib import parse
from .login import get_login_session
from .config import LOGIN_KEY, DEFAULT_LOGIN_AUTH


def make_tag_data(tag_name, sort_type="new", get_num=100, got_num=0):
    """
    生成tag请求的data
    :param tag_name: tag名称
    :param sort_type: 排序类型 new(最新), total(全部最热), month(月榜), week(周榜), date(日榜)
    :param get_num: 要获取的条数
    :param got_num: 已获取的条数
    :return: data字典
    """
    base_data = {
        'callCount': '1',
        'httpSessionId': '',
        'scriptSessionId': '${scriptSessionId}187',
        'c0-id': '0',
        "batchId": "472351"
    }
    
    data_parme = {
        'c0-scriptName': 'TagBean',
        'c0-methodName': 'search',
        'c0-param0': 'string:' + tag_name,
        'c0-param1': 'number:0',
        'c0-param2': 'string:',
        'c0-param3': 'string:' + sort_type,
        'c0-param4': 'boolean:false',
        'c0-param5': 'number:0',
        'c0-param6': 'number:' + str(get_num),
        'c0-param7': 'number:' + str(got_num),
        'c0-param8': 'number:' + str(int(time.time() * 1000)),
        'batchId': '870178'
    }
    
    return {**base_data, **data_parme}


def update_tag_data(data, get_num, got_num, last_timestamp):
    """更新tag请求的data"""
    data["c0-param6"] = 'number:' + str(get_num)
    data["c0-param7"] = 'number:' + str(got_num)
    data["c0-param8"] = 'number:' + str(last_timestamp)
    return data


def crawl_tag_posts(tag_name, sort_type="new", login_auth=None, login_key=None, min_hot=0):
    """
    爬取tag下的所有文章链接（参考l13_like_share_tag.py）
    只返回文章URL列表，不解析完整内容
    :param tag_name: tag名称
    :param sort_type: 排序类型 new(最新), total(全部最热), month(月榜), week(周榜), date(日榜)
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :param min_hot: 最低热度限制
    :return: 文章URL列表
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    # 参考l13_like_share_tag.py第1128行，构建tag URL
    # URL编码tag名称
    tag_encoded = parse.quote(tag_name, safe='')
    tag_url = f"https://www.lofter.com/tag/{tag_encoded}/{sort_type}"
    
    # 参考l13_like_share_tag.py第131行，从URL中提取编码后的tag名称用于data参数
    url_search = re.search("http[s]{0,1}://www.lofter.com/tag/(.*?)/(.*)", tag_url)
    if not url_search:
        print(f"错误: 无法解析tag URL: {tag_url}")
        return []
    
    tag_name_encoded = url_search.group(1)  # 从URL中提取的编码后的tag名称
    type_from_url = url_search.group(2) if url_search.group(2) else "new"
    
    # 参考l13_like_share_tag.py第154-174行，生成headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
        "Host": "www.lofter.com",
        "Referer": tag_url
    }
    
    # 参考l13_like_share_tag.py第216行，使用http而不是https
    rtag_url = "http://www.lofter.com/dwr/call/plaincall/TagBean.search.dwr"
    
    all_urls = []  # 只保存URL列表
    got_num = 0
    get_num = 100
    
    # 参考l13_like_share_tag.py第82-151行，生成data
    base_data = {
        'callCount': '1',
        'httpSessionId': '',
        'scriptSessionId': '${scriptSessionId}187',
        'c0-id': '0',
        "batchId": "472351"
    }
    
    data_parme = {
        'c0-scriptName': 'TagBean',
        'c0-methodName': 'search',
        'c0-param0': 'string:' + tag_name_encoded,  # 使用从URL提取的编码后的tag名称
        'c0-param1': 'number:0',
        'c0-param2': 'string:',
        'c0-param3': 'string:' + sort_type,
        'c0-param4': 'boolean:false',
        'c0-param5': 'number:0',
        'c0-param6': 'number:' + str(get_num),
        'c0-param7': 'number:' + str(got_num),
        'c0-param8': 'number:' + str(int(time.time() * 1000)),
        'batchId': '870178'
    }
    
    data = {**base_data, **data_parme}
    
    # 参考l13_like_share_tag.py第236-237行，使用session并设置cookies
    from requests.cookies import RequestsCookieJar
    session = requests.session()
    session.headers = headers
    
    # 设置cookies
    cookies_jar = RequestsCookieJar()
    cookies_jar.set(login_key, login_auth)
    session.cookies = cookies_jar
    
    # 参考l13_like_share_tag.py第245-305行，循环获取所有文章
    while True:
        print(f"正在获取{got_num}-{got_num + get_num}", end="\t")
        
        try:
            # 参考l13_like_share_tag.py第248行
            response = session.post(rtag_url, data=data)
            content = response.content.decode("utf-8")
            
            # 参考l13_like_share_tag.py第251行，从activityTags切分
            new_info = content.split("activityTags")[1:]
            
            if len(new_info) == 0:
                print("\n已获取到最后一页，tag信息获取完成")
                break
            
            # 只提取URL和热度，用于过滤
            for info in new_info:
                try:
                    # 提取博客链接
                    url_match = re.search(r's\d{1,5}\.blogPageUrl="(.*?)"', info)
                    if not url_match:
                        continue
                    url = url_match.group(1)
                    
                    # 提取热度（参考l13_like_share_tag.py第346-349行）
                    hot_match = re.search(r's\d{1,5}\.hot=(.*?);', info)
                    hot = int(hot_match.group(1)) if hot_match else 0
                    
                    if hot < min_hot:
                        continue
                    
                    # 只保存URL，完整内容通过save_single_post获取
                    all_urls.append(url)
                    
                except Exception as e:
                    print(f"解析博客信息时出错: {e}")
                    continue
            
            got_num += get_num
            print(f"实际返回条数 {len(new_info)}", end="\t")
            
            # 更新data用于获取下一页（参考l13_like_share_tag.py第298-302行）
            if len(new_info) > 0:
                last_info = new_info[-1]
                # 参考l13_like_share_tag.py第301行，tag模式使用publishTime作为时间戳
                last_timestamp_match = re.search(r's\d{1,5}\.publishTime=(.*?);', last_info)
                if last_timestamp_match:
                    last_timestamp = int(last_timestamp_match.group(1))
                    # 更新data
                    data["c0-param6"] = 'number:' + str(get_num)
                    data["c0-param7"] = 'number:' + str(got_num)
                    data["c0-param8"] = 'number:' + str(last_timestamp)
                else:
                    print("无法提取时间戳，停止获取")
                    break
            else:
                break
            
            print()
            
        except Exception as e:
            print(f"请求出错: {e}")
            break
    
    print(f"总共获取到 {len(all_urls)} 篇文章链接")
    return all_urls
