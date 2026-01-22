# -*- coding: utf-8 -*-
"""
作者爬取模块
"""
import re
import time
import random
import requests
from urllib.parse import unquote
from lxml.html import etree
from .utils import get_headers, decode_unicode_escape
from .login import get_login_session
from .config import LOGIN_KEY, DEFAULT_LOGIN_AUTH
from .post_parser import parse_post


def get_author_info(author_url, login_auth=None, login_key=None):
    """
    获取作者信息
    :param author_url: 作者主页URL
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :return: 作者信息字典
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    session = get_login_session(login_auth, login_key)
    
    # 确保URL以/结尾
    if not author_url.endswith('/'):
        author_url += '/'
    
    view_url = author_url + "view"
    response = session.get(view_url, headers=get_headers())
    content = response.content.decode("utf-8")
    parse = etree.HTML(content)
    
    # 获取作者ID
    try:
        iframe_src = parse.xpath("//body//iframe[@id='control_frame']/@src")[0]
        author_id = iframe_src.split("blogId=")[1]
    except:
        author_id = ""
    
    # 获取作者名
    try:
        author_name = parse.xpath("//title//text()")[0].replace("归档 - ", "")
    except:
        try:
            author_name = parse.xpath("//h1/a/text()")[0]
        except:
            author_name = ""
    
    # 获取作者IP
    author_ip_match = re.search(r"http[s]{0,1}://(.*?)\.lofter\.com", author_url)
    author_ip = author_ip_match.group(1) if author_ip_match else ""
    
    return {
        "author_id": author_id,
        "author_name": author_name,
        "author_ip": author_ip,
        "author_url": author_url
    }


def make_archive_data(author_id, query_num=50, timestamp=None):
    """
    生成归档页请求的data
    :param author_id: 作者ID
    :param query_num: 查询数量
    :param timestamp: 时间戳
    :return: data字典
    """
    if timestamp is None:
        timestamp = int(time.time() * 1000)
    
    data = {
        "callCount": "1",
        "scriptSessionId": "${scriptSessionId}187",
        "httpSessionId": "",
        "c0-scriptName": "ArchiveBean",
        "c0-methodName": "getArchivePostByTime",
        "c0-id": "0",
        "c0-param0": "boolean:false",
        "c0-param1": "number:" + str(author_id),
        "c0-param2": "number:" + str(timestamp),
        "c0-param3": "number:" + str(query_num),
        "c0-param4": "boolean:false",
        "batchId": "918906"
    }
    return data


def make_archive_header(author_url):
    """生成归档页请求头"""
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
        "Host": author_url.split("//")[1].replace("/", ""),
        "Origin": author_url,
        "Referer": author_url + "view"
    }
    return header


def crawl_author_posts(author_url, target_tags=None, tags_filter_mode="in", 
                       login_auth=None, login_key=None, start_time=None, end_time=None):
    """
    爬取作者的所有文章
    :param author_url: 作者主页URL
    :param target_tags: 目标tags列表，如果指定则只爬取包含这些tag的文章
    :param tags_filter_mode: tag过滤模式 "in"表示包含指定tag，"out"表示不包含
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :param start_time: 开始时间 "YYYY-MM-DD"
    :param end_time: 结束时间 "YYYY-MM-DD"
    :return: 文章信息列表
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    # 获取作者信息
    author_info = get_author_info(author_url, login_auth, login_key)
    author_id = author_info["author_id"]
    author_name = author_info["author_name"]
    author_ip = author_info["author_ip"]
    
    if not author_id:
        print("无法获取作者ID，请检查URL是否正确")
        return []
    
    session = get_login_session(login_auth, login_key)
    
    # 确保URL以/结尾
    if not author_url.endswith('/'):
        author_url += '/'
    
    archive_url = author_url + "dwr/call/plaincall/ArchiveBean.getArchivePostByTime.dwr"
    header = make_archive_header(author_url)
    
    all_posts = []
    query_num = 50
    timestamp = None
    
    # 时间戳转换
    start_timestamp = None
    end_timestamp = None
    if start_time:
        start_timestamp = int(time.mktime(time.strptime(start_time, "%Y-%m-%d")) * 1000)
    if end_time:
        end_timestamp = int(time.mktime(time.strptime(end_time, "%Y-%m-%d")) * 1000)
    
    while True:
        data = make_archive_data(author_id, query_num, timestamp)
        
        print(f"正在获取归档页面信息，时间戳参数: {data['c0-param2']}")
        
        try:
            # 设置cookies
            cookies = session.cookies
            cookies.set(login_key, login_auth)
            session.cookies = cookies
            
            response = session.post(archive_url, data=data, headers=header)
            page_data = response.content.decode("utf-8")
            
            # 正则匹配出每条博客的信息
            new_blogs_info = re.findall(r"s[\d]*\.blogId.*\n.*noticeLinkTitle", page_data)
            
            if len(new_blogs_info) == 0:
                print("已获取到最后一页")
                break
            
            # 解析每条博客信息
            for blog_info in new_blogs_info:
                try:
                    # 提取时间戳
                    timestamp_match = re.search(r's[\d]*\.time=(\d*);', blog_info)
                    if not timestamp_match:
                        continue
                    blog_timestamp = int(timestamp_match.group(1))
                    
                    # 时间过滤
                    if start_timestamp and blog_timestamp < start_timestamp:
                        print("已到达指定开始时间，停止爬取")
                        return all_posts
                    if end_timestamp and blog_timestamp > end_timestamp:
                        continue
                    
                    # 提取博客编号
                    permalink_match = re.search(r's[\d]*\.permalink="(.*?)";', blog_info)
                    if not permalink_match:
                        continue
                    blog_index = permalink_match.group(1)
                    blog_url = author_url + "post/" + blog_index
                    
                    # 提取标题
                    title_match = re.findall(r'[\d]*\.title="(.*?)";', blog_info)
                    title = ""
                    if title_match and title_match[0]:
                        title = decode_unicode_escape(title_match[0])
                    
                    # 提取内容（用于判断是否有内容）
                    content_match = re.findall(r'[\d]*\.content="(.*?)";', blog_info)
                    has_content = bool(content_match and content_match[0])
                    
                    # 判断博客类型
                    if title:
                        blog_type = "article"
                    elif has_content:
                        blog_type = "text"
                    else:
                        # 可能是纯图片博客，跳过
                        continue
                    
                    # 格式化时间
                    publish_time = time.strftime("%Y-%m-%d", time.localtime(blog_timestamp / 1000))
                    
                    # 解析完整文章信息（需要访问文章页面获取tags等）
                    try:
                        # 先使用基本信息，避免重复请求
                        post_info = {
                            "url": blog_url,
                            "title": title if title else f"{author_name} {publish_time}",
                            "author_name": author_name,
                            "author_ip": author_ip,
                            "publish_time": publish_time,
                            "tags": [],
                            "content": "",
                            "img_urls": [],
                            "illustration": []
                        }
                        
                        # 尝试从页面内容中提取tags
                        try:
                            response = session.get(blog_url, headers=get_headers())
                            page_content = response.content.decode("utf-8")
                            tag_matches = re.findall(r'"http[s]{0,1}://.*?\.lofter\.com/tag/(.*?)"', page_content)
                            if tag_matches:
                                post_info["tags"] = [unquote(tag, "utf-8").replace("\xa0", " ") for tag in tag_matches]
                        except:
                            pass
                    except Exception as e:
                        print(f"解析文章信息时出错: {e}")
                        post_info = {
                            "url": blog_url,
                            "title": title if title else f"{author_name} {publish_time}",
                            "author_name": author_name,
                            "author_ip": author_ip,
                            "publish_time": publish_time,
                            "tags": [],
                            "content": "",
                            "img_urls": [],
                            "illustration": []
                        }
                    
                    # Tag过滤
                    if target_tags:
                        blog_tags = post_info.get("tags", [])
                        if tags_filter_mode == "in":
                            # 包含指定tag或没有tag
                            if blog_tags:
                                if not any(tag in blog_tags for tag in target_tags):
                                    continue
                            # 如果没有tag，根据模式决定是否保留
                            elif tags_filter_mode == "out":
                                continue
                        else:  # out模式
                            if any(tag in blog_tags for tag in target_tags):
                                continue
                    
                    all_posts.append(post_info)
                    
                except Exception as e:
                    print(f"解析博客信息时出错: {e}")
                    continue
            
            # 更新timestamp用于获取下一页
            if len(new_blogs_info) > 0:
                last_blog = new_blogs_info[-1]
                last_timestamp_match = re.search(r's[\d]*\.time=(\d*);', last_blog)
                if last_timestamp_match:
                    timestamp = int(last_timestamp_match.group(1))
                else:
                    break
            else:
                break
            
            # 随机延迟
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"请求出错: {e}")
            break
    
    print(f"总共获取到 {len(all_posts)} 篇文章")
    return all_posts
