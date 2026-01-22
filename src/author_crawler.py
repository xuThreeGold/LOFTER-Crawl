# -*- coding: utf-8 -*-
"""
作者爬取模块（参考lofterSpider-master_v2/src/author_spider.py）
"""
import re
import time
import random
import requests
from urllib.parse import unquote
from lxml.html import etree
from .utils import get_headers
from .login import get_login_session
from .config import LOGIN_KEY, DEFAULT_LOGIN_AUTH


def get_author_info(author_url, login_auth=None, login_key=None):
    """
    获取作者信息（参考lofterSpider-master_v2/src/author_spider.py第19-82行）
    :param author_url: 作者主页URL
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :return: 作者信息字典
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    # 确保URL以/结尾
    if not author_url.endswith('/'):
        author_url += '/'
    
    # 获取作者IP
    author_ip_match = re.search(r"http[s]*://(.*?)\.lofter\.com/", author_url)
    if not author_ip_match:
        raise ValueError(f"无效的作者URL: {author_url}")
    author_ip = author_ip_match.group(1)
    
    # 获取作者view页面（参考lofterSpider-master_v2/src/author_spider.py第46-54行）
    author_view_url = author_url + "view"
    headers = get_headers()
    
    author_id = ""
    author_name = ""
    
    # 首先尝试从/view页面获取
    try:
        # 直接使用requests.get，与lofterSpider-master_v2保持一致
        author_view_html = requests.get(
            author_view_url,
            headers=headers,
            cookies={login_key: login_auth}
        ).content.decode("utf-8")
        
        author_view_parse = etree.HTML(author_view_html)
        
        # 获取作者ID
        iframe_src = author_view_parse.xpath("//body//iframe[@id='control_frame']/@src")
        if iframe_src:
            author_id = iframe_src[0].split("blogId=")[1]
        
        # 获取作者名
        author_name_elem = author_view_parse.xpath("//h1/a/text()")
        if author_name_elem:
            author_name = author_name_elem[0]
        else:
            # 尝试从title获取
            title_elem = author_view_parse.xpath("//title/text()")
            if title_elem:
                author_name = title_elem[0].replace("归档 - ", "").strip()
    except Exception as e:
        print(f"访问/view页面失败: {e}")
    
    # 如果/view页面无法获取author_id，尝试从主页获取
    if not author_id:
        try:
            print("访问/view页面失败，尝试访问主页...")
            main_html = requests.get(
                author_url,
                headers=headers,
                cookies={login_key: login_auth}
            ).content.decode("utf-8")
            
            main_parse = etree.HTML(main_html)
            
            # 尝试从主页的iframe获取
            iframe_src = main_parse.xpath("//body//iframe[@id='control_frame']/@src")
            if iframe_src:
                author_id = iframe_src[0].split("blogId=")[1]
                print(f"从主页找到blogId: {author_id}")
            else:
                # 尝试从页面源码中正则匹配
                blog_id_matches = re.findall(r'blogId[=:](\d+)', main_html)
                if blog_id_matches:
                    author_id = blog_id_matches[0]
                    print(f"从主页源码中找到blogId: {author_id}")
            
            # 如果还没有获取到作者名，尝试从主页获取
            if not author_name:
                author_name_elem = main_parse.xpath("//h1/a/text()")
                if author_name_elem:
                    author_name = author_name_elem[0]
                else:
                    title_elem = main_parse.xpath("//title/text()")
                    if title_elem:
                        title_text = title_elem[0]
                        author_name = title_text.replace("归档 - ", "").replace(" - LOFTER", "").strip()
                        # 如果标题包含"404"等错误信息，使用author_ip
                        if "404" in author_name or "Not Found" in author_name:
                            author_name = author_ip
        except Exception as e:
            print(f"访问主页也失败: {e}")
    
    if not author_id:
        raise ValueError("无法获取作者ID，请检查URL是否正确")
    
    if not author_name:
        author_name = author_ip
    
    return {
        'author_id': author_id,
        'author_name': author_name,
        'author_ip': author_ip,
        'author_url': author_url
    }


def make_archive_data(author_id, query_num=50, timestamp=None):
    """
    构建归档页面请求的data（参考lofterSpider-master_v2/src/author_spider.py第85-111行）
    :param author_id: 作者ID
    :param query_num: 每次查询数量
    :param timestamp: 时间戳，用于分页
    """
    if timestamp is None:
        timestamp = round(time.time() * 1000)  # 使用round而不是int
    
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
    """
    构建归档页面请求的header（参考lofterSpider-master_v2/src/author_spider.py第114-125行）
    """
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/79.0.3945.88 Safari/537.36",
        "Host": author_url.split("//")[1].replace("/", ""),
        "Origin": author_url.rstrip('/'),
        "Referer": author_url.rstrip('/') + "/view"
    }
    return header


def get_author_blog_urls(author_url, login_auth=None, login_key=None):
    """
    获取作者的所有博客链接（参考lofterSpider-master_v2/src/author_spider.py第128-226行）
    :param author_url: 作者主页URL
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :return: (博客链接列表, 作者信息字典) - 博客链接列表（所有博客，不进行tag过滤），作者信息字典
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    # 获取作者信息
    author_info = get_author_info(author_url, login_auth, login_key)
    author_id = author_info['author_id']
    author_name = author_info['author_name']
    
    print(f"作者: {author_name} (ID: {author_id})")
    
    # 确保URL以/结尾
    if not author_url.endswith('/'):
        author_url += '/'
    
    # 归档页URL
    archive_url = author_url + "dwr/call/plaincall/ArchiveBean.getArchivePostByTime.dwr"
    
    # 请求头和data
    header = make_archive_header(author_url)
    query_num = 50
    data = make_archive_data(author_id, query_num)
    
    blog_urls = []
    # 创建新的session（参考lofterSpider-master_v2/src/author_spider.py第162-164行）
    session = requests.session()
    session.headers = header
    session.cookies.set(login_key, login_auth)
    
    print("开始获取博客列表...")
    
    while True:
        print(f"正在获取第 {len(blog_urls) + 1} 批博客...", end="\t")
        
        try:
            response = session.post(archive_url, data=data)
            page_data = response.content.decode("utf-8")
        except Exception as e:
            print(f"\n请求失败: {e}")
            break
        
        # 正则匹配出每条博客的信息（参考lofterSpider-master_v2/src/author_spider.py第179行）
        # 注意：点号不转义，匹配任意字符
        new_blogs_info = re.findall(r"s[\d]*.blogId.*\n.*\n", page_data)
        
        if len(new_blogs_info) == 0:
            print("\n已获取到最后一页")
            break
        
        # 从每条信息中提取博客链接
        for blog_info in new_blogs_info:
            try:
                # 获取博客permalink（参考lofterSpider-master_v2/src/author_spider.py第189行）
                permalink_match = re.search(r's[\d]*.permalink="(.*?)";', blog_info)
                if not permalink_match:
                    continue
                
                permalink = permalink_match.group(1)
                blog_url = author_url + "post/" + permalink
                
                # 不在这里进行tag过滤，因为归档页面的tag信息可能不完整
                # 所有tag过滤将在main.py中通过check_blog_has_tag进行准确验证
                blog_urls.append(blog_url)
            except:
                continue
        
        print(f"本批获取 {len(new_blogs_info)} 条，当前总数: {len(blog_urls)}")
        
        # 检查是否还有更多
        if len(new_blogs_info) < query_num:
            break
        
        # 获取最后一条的时间戳用于下次请求（参考lofterSpider-master_v2/src/author_spider.py第210-214行）
        try:
            # 使用原始字符串避免转义警告
            pattern = r's%d\.time=(.*);s.*type' % (query_num - 1)
            last_timestamp = re.search(pattern, page_data)
            if last_timestamp:
                next_timestamp = last_timestamp.group(1)
                data['c0-param2'] = 'number:' + str(next_timestamp)
            else:
                break
        except:
            break
        
        time.sleep(random.randint(1, 2))  # 避免请求过快
    
    # 注意：这里返回的是所有博客，不进行tag过滤
    # tag过滤将在main.py中通过check_blog_has_tag进行准确验证
    print(f"\n共获取到 {len(blog_urls)} 篇博客（将进行tag验证）")
    
    return blog_urls, author_info


def check_blog_has_tag(blog_url, target_tags, login_auth=None, login_key=None):
    """
    检查博客是否包含指定tag（参考lofterSpider-master_v2/src/author_spider.py第229-262行）
    通过访问博客页面获取tag信息
    :param blog_url: 博客链接
    :param target_tags: 目标tag列表（支持多个tag，只要包含任一tag即返回True）
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :return: 如果包含任一目标tag返回True，否则返回False
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    try:
        headers = get_headers()
        # 直接使用requests.get，与lofterSpider-master_v2保持一致（参考第244行）
        blog_html = requests.get(blog_url, headers=headers,
                                cookies={login_key: login_auth}).content.decode("utf-8")
        
        # 从HTML中提取tag（参考lofterSpider-master_v2/src/author_spider.py第249行）
        blog_tags = re.findall(r'"http[s]{0,1}://.*?\.lofter\.com/tag/(.*?)"', blog_html)
        blog_tags = [unquote(tag, "utf-8").replace("\xa0", " ").strip().lower() for tag in blog_tags]
        
        # 检查是否包含任一目标tag
        for target_tag in target_tags:
            target_tag_lower = target_tag.lower().strip()
            for tag in blog_tags:
                if target_tag_lower == tag:
                    return True
        
        return False
    except:
        # 如果检查失败，返回True（不跳过该博客）
        return True
