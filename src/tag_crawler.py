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
    爬取tag下的所有文章
    :param tag_name: tag名称
    :param sort_type: 排序类型 new(最新), total(全部最热), month(月榜), week(周榜), date(日榜)
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :param min_hot: 最低热度限制
    :return: 文章信息列表
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    session = get_login_session(login_auth, login_key)
    
    # URL编码tag名称
    tag_encoded = parse.quote(tag_name)
    tag_url = f"https://www.lofter.com/tag/{tag_encoded}/{sort_type}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
        "Host": "www.lofter.com",
        "Referer": tag_url
    }
    session.headers.update(headers)
    
    rtag_url = "http://www.lofter.com/dwr/call/plaincall/TagBean.search.dwr"
    
    all_posts = []
    got_num = 0
    get_num = 100
    
    data = make_tag_data(tag_name, sort_type, get_num, got_num)
    
    while True:
        print(f"正在获取{got_num}-{got_num + get_num}", end="\t")
        
        try:
            response = session.post(rtag_url, data=data)
            content = response.content.decode("utf-8")
            
            # 从返回内容中提取博客信息
            # activityTags应该是第一或者第二个属性
            new_info = content.split("activityTags")[1:]
            
            if len(new_info) == 0:
                print("\n已获取到最后一页，tag信息获取完成")
                break
            
            # 解析每条博客信息
            for info in new_info:
                try:
                    # 提取博客链接
                    url_match = re.search(r's\d{1,5}\.blogPageUrl="(.*?)"', info)
                    if not url_match:
                        continue
                    url = url_match.group(1)
                    
                    # 提取热度
                    hot_match = re.search(r's\d{1,5}\.hot=(.*?);', info)
                    hot = int(hot_match.group(1)) if hot_match else 0
                    
                    if hot < min_hot:
                        continue
                    
                    # 提取作者名
                    author_match = re.search(r's\d{1,5}\.blogNickName="(.*?)"', info)
                    if author_match:
                        author_name = author_match.group(1).encode('latin-1').decode('unicode_escape', errors="replace")
                    else:
                        # 如果当前信息中没有，尝试从前面查找
                        author_name = "未知作者"
                    
                    # 提取作者IP
                    author_ip_match = re.search(r"http[s]{0,1}://(.*?)\.lofter\.com", url)
                    author_ip = author_ip_match.group(1) if author_ip_match else ""
                    
                    # 提取发表时间
                    publish_time_match = re.search(r's\d{1,5}\.publishTime=(.*?);', info)
                    publish_timestamp = int(publish_time_match.group(1)) if publish_time_match else 0
                    publish_time = time.strftime("%Y-%m-%d", time.localtime(publish_timestamp / 1000))
                    
                    # 提取标题
                    title_match = re.search(r's\d{1,5}\.title="(.*?)"', info)
                    title = ""
                    if title_match:
                        title = title_match.group(1).encode('latin-1').decode('unicode_escape', errors="ignore")
                    
                    # 提取tags
                    tags_match = re.search(r's\d{1,5}\.tag[s]{0,1}="(.*?)";', info)
                    tags = []
                    if tags_match:
                        tags_str = tags_match.group(1).strip().encode('utf-8').decode('unicode_escape')
                        if tags_str:
                            tags = [tag.strip() for tag in tags_str.split(",")]
                    
                    # 提取图片链接
                    img_urls = []
                    img_urls_match = re.search(r'originPhotoLinks="(\[.*?\])"', info)
                    if img_urls_match:
                        urls_str = img_urls_match.group(1).replace("\\", "").replace("false", "False").replace("true", "True")
                        try:
                            urls_infos = eval(urls_str)
                            for url_info in urls_infos:
                                img_url = url_info.get("raw", "")
                                if not img_url or "netease" in img_url:
                                    img_url = url_info.get("orign", "").split("?imageView")[0]
                                if img_url:
                                    img_urls.append(img_url)
                        except:
                            pass
                    
                    # 提取正文内容
                    content_match = re.search(r's\d{1,5}\.content="(.*?)";', info)
                    content = ""
                    if content_match:
                        content_html = content_match.group(1).encode('latin-1').decode('unicode_escape', errors="ignore")
                        # 使用html2text转换
                        try:
                            import html2text
                            h = html2text.HTML2Text()
                            h.ignore_links = False
                            h.ignore_images = False
                            h.body_width = 0
                            content = h.handle(content_html)
                        except:
                            content = content_html
                    
                    post_info = {
                        "url": url,
                        "title": title,
                        "author_name": author_name,
                        "author_ip": author_ip,
                        "publish_time": publish_time,
                        "tags": tags,
                        "hot": hot,
                        "img_urls": img_urls,
                        "content": content
                    }
                    
                    all_posts.append(post_info)
                    
                except Exception as e:
                    print(f"解析博客信息时出错: {e}")
                    continue
            
            got_num += get_num
            print(f"实际返回条数 {len(new_info)}", end="\t")
            
            # 更新data用于获取下一页
            if len(new_info) > 0:
                last_info = new_info[-1]
                last_timestamp_match = re.search(r's\d{1,5}\.publishTime=(.*?);', last_info)
                if last_timestamp_match:
                    last_timestamp = last_timestamp_match.group(1)
                    data = update_tag_data(data, get_num, got_num, last_timestamp)
                else:
                    break
            else:
                break
            
            print()
            
        except Exception as e:
            print(f"请求出错: {e}")
            break
    
    print(f"总共获取到 {len(all_posts)} 篇文章")
    return all_posts
