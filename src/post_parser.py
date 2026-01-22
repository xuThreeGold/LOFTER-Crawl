# -*- coding: utf-8 -*-
"""
文章解析模块
"""
import re
import time
import requests
from urllib.parse import unquote
from lxml.html import etree
import html2text
from .utils import get_headers, decode_unicode_escape
from .login import get_login_session
from .config import LOGIN_KEY, DEFAULT_LOGIN_AUTH
from .parse_template import matcher, get_content


def parse_post(url, login_auth=None, login_key=None):
    """
    解析单篇文章
    :param url: 文章URL
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :return: 文章信息字典
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    session = get_login_session(login_auth, login_key)
    
    # 确保URL是https
    url = url.replace('http://', 'https://')
    
    response = session.get(url)
    content = response.content.decode("utf-8")
    parse = etree.HTML(content)
    
    # 提取作者信息
    author_ip = re.search(r"http[s]{0,1}://(.*?)\.lofter\.com", url)
    author_ip = author_ip.group(1) if author_ip else ""
    
    # 获取作者名
    try:
        author_name = parse.xpath("//h1/a/text()")[0]
        author_name = decode_unicode_escape(author_name)
    except:
        try:
            author_name = parse.xpath("//title/text()")[0]
            author_name = author_name.replace("归档 - ", "").split(" - ")[0]
        except:
            author_name = author_ip
    
    # 获取标题
    title = ""
    try:
        title_elem = parse.xpath("//h2[@class='title']/text()")
        if title_elem:
            title = decode_unicode_escape(title_elem[0])
    except:
        pass
    
    # 获取发表时间
    publish_time = ""
    try:
        time_elem = parse.xpath("//span[@class='time']/text()")
        if time_elem:
            publish_time = time_elem[0].strip()
    except:
        pass
    
    # 如果没有获取到时间，尝试从URL或内容中提取
    if not publish_time:
        try:
            # 尝试从归档页面获取时间
            author_url = url.split("/post")[0] + "/"
            archive_url = author_url + "dwr/call/plaincall/ArchiveBean.getArchivePostByTime.dwr"
            blog_id = url.split("/")[-1]
            # 这里简化处理，实际可能需要遍历归档页
            publish_time = time.strftime("%Y-%m-%d", time.localtime())
        except:
            publish_time = time.strftime("%Y-%m-%d", time.localtime())
    
    # 获取tags
    tags = []
    try:
        tag_links = parse.xpath("//a[contains(@href, '/tag/')]/text()")
        tags = [tag.strip() for tag in tag_links if tag.strip()]
    except:
        pass
    
    # 如果没有从页面获取到tags，尝试从内容中提取
    if not tags:
        tag_matches = re.findall(r'"http[s]{0,1}://.*?\.lofter\.com/tag/(.*?)"', content)
        tags = [unquote(tag, "utf-8").replace("\xa0", " ") for tag in tag_matches]
    
    # 获取正文内容
    content_text = ""
    try:
        # 判断博客类型
        blog_type = "article" if title else "text"
        
        # 使用模板匹配
        template_id = matcher(parse)
        content_text = get_content(parse, template_id, title, blog_type, "\n")
        
        # 如果模板匹配失败，使用html2text作为后备
        if not content_text or len(content_text.strip()) < 10:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0
            content_text = h.handle(content)
            # 移除标题
            if title and content_text.startswith(title):
                content_text = content_text[len(title):].strip()
            # 移除评论部分
            content_text = re.split(r'\s评论\s', content_text)[0].strip()
        
    except Exception as e:
        print(f"解析内容时出错: {e}")
        # 如果解析失败，尝试使用html2text
        try:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0
            content_text = h.handle(content)
        except:
            content_text = ""
    
    # 获取图片链接
    img_urls = []
    try:
        # 匹配新格式
        img_matches = re.findall(r'"(http[s]{0,1}://imglf\d{0,1}\.lf\d*\.[0-9]{0,3}\.net[^"]*?)"', content)
        if not img_matches:
            # 匹配旧格式
            img_matches = re.findall(r'"(http[s]{0,1}://imglf\d{0,1}\.nosdn\d*\.[0-9]{0,3}\.net[^"]*?)"', content)
        
        for img_url in img_matches:
            # 移除图片大小参数
            img_url = img_url.split("?imageView")[0].split("imageView")[0]
            if img_url and img_url not in img_urls:
                # 过滤掉头像等小图
                if not re.search(r"[1649]{2}[xy][1649]{2}", img_url):
                    img_urls.append(img_url)
    except:
        pass
    
    # 获取文章中的图片（illustration）
    illustration = []
    try:
        img_src = parse.xpath("//img/@src")
        for src in img_src:
            match = re.search(r'(http[s]{0,1}://imglf\d{0,1}\.lf\d*\.[0-9]{0,3}\.net[^?]*)', src)
            if match:
                img_url = match.group(1)
                if img_url not in illustration:
                    illustration.append(img_url)
    except:
        pass
    
    return {
        "url": url,
        "title": title,
        "author_name": author_name,
        "author_ip": author_ip,
        "publish_time": publish_time,
        "tags": tags,
        "content": content_text,
        "img_urls": img_urls,
        "illustration": illustration
    }
