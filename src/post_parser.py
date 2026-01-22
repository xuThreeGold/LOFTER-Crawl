# -*- coding: utf-8 -*-
"""
文章解析模块
参考lofterSpider-master的实现
"""
import re
import time
import random
import requests
from urllib.parse import unquote
from lxml.html import etree
import html2text
from .utils import get_headers, decode_unicode_escape
from .config import LOGIN_KEY, DEFAULT_LOGIN_AUTH
from .parse_template import matcher, get_content


def get_time_and_title_from_archive(blog_url, author_id, login_key, login_auth):
    """
    从归档页面获取文章时间和标题（参考l10_blogs_txt.py）
    :param blog_url: 文章URL
    :param author_id: 作者ID
    :param login_key: 登录key
    :param login_auth: 登录授权码
    :return: [public_time, title]
    """
    from .author_crawler import make_archive_data, make_archive_header
    
    author_url = blog_url.split("/post")[0] + "/"
    archive_url = author_url + "dwr/call/plaincall/ArchiveBean.getArchivePostByTime.dwr"
    data = make_archive_data(author_id, 50)
    header = make_archive_header(author_url)
    blog_id = blog_url.split("/")[-1]
    
    flag = False
    the_blog_info = ""
    
    while True:
        try:
            # 使用post_content方法
            session = requests.session()
            session.headers = header
            cookies = session.cookies
            cookies.set(login_key, login_auth)
            session.cookies = cookies
            
            response = session.post(archive_url, data=data)
            page_data = response.content.decode("utf-8")
            
            # 正则匹配出每条博客的信息
            blogs_info = re.findall(r"s[\d]*\.blogId.*\n.*\n", page_data)
            
            # 循环每条信息，找到匹配的
            for blog_info in blogs_info:
                if blog_id in blog_info:
                    the_blog_info = blog_info
                    flag = True
                    break
            
            if flag:
                break
            
            # 更新data用于获取下一页
            try:
                next_param2 = 'number:' + str(re.search(r's%d\.time=(.*);s.*type' % (50 - 1), page_data).group(1))
                data['c0-param2'] = next_param2
            except AttributeError:
                # 最后一页，没有更多数据
                break
            
            time.sleep(random.randint(1, 2))
        except Exception as e:
            print(f"从归档页面获取信息时出错: {e}")
            break
    
    if not the_blog_info:
        return ["", ""]
    
    # 提取时间戳和标题
    try:
        timestamp = re.search(r's[\d]*\.time=(\d*);', the_blog_info).group(1)
        public_time = time.strftime("%Y-%m-%d", time.localtime(int(int(timestamp) / 1000)))
        
        re_title = re.findall(r'[\d]*\.title="(.*?)"', the_blog_info)
        if re_title and re_title[0]:
            title = re_title[0].encode('latin-1').decode('unicode_escape')
        else:
            title = ""
        
        return [public_time, title]
    except:
        return ["", ""]


def parse_post(url, login_auth=None, login_key=None):
    """
    解析单篇文章（参考lofterSpider-master的l10_blogs_txt.py和l9_author_txt.py）
    :param url: 文章URL
    :param login_auth: 登录授权码
    :param login_key: 登录key
    :return: 文章信息字典
    """
    if login_auth is None:
        login_auth = DEFAULT_LOGIN_AUTH
    if login_key is None:
        login_key = LOGIN_KEY
    
    # 确保URL是https
    url = url.replace('http://', 'https://')
    
    # 提取作者IP
    author_ip_match = re.search(r"http[s]{0,1}://(.*?)\.lofter\.com", url)
    author_ip = author_ip_match.group(1) if author_ip_match else ""
    
    # 从作者主页获取作者信息（参考l8_blogs_img.py和l10_blogs_txt.py）
    author_name = author_ip  # 默认值
    author_id = ""
    
    try:
        author_view_url = url.split("/post")[0] + "/view"
        author_view_response = requests.get(author_view_url, 
                                          headers=get_headers(),
                                          cookies={login_key: login_auth})
        author_view_content = author_view_response.content.decode("utf-8")
        author_view_parse = etree.HTML(author_view_content)
        
        # 获取作者名（参考l10_blogs_txt.py第89行）
        try:
            author_name = author_view_parse.xpath("//h1/a/text()")[0]
            author_name = decode_unicode_escape(author_name)
        except:
            try:
                author_name = author_view_parse.xpath("//title/text()")[0]
                author_name = author_name.replace("归档 - ", "").split(" - ")[0].strip()
            except:
                author_name = author_ip
        
        # 获取作者ID（参考l10_blogs_txt.py第88行）
        try:
            iframe_src = author_view_parse.xpath("//body//iframe[@id='control_frame']/@src")[0]
            author_id = iframe_src.split("blogId=")[1]
        except:
            pass
    except Exception as e:
        print(f"获取作者信息时出错: {e}，使用IP作为作者名")
    
    # 获取文章页面内容（参考l9_author_txt.py第141行）
    try:
        blog_html = requests.get(url, 
                                headers=get_headers(),
                                cookies={login_key: login_auth}).content.decode("utf-8")
    except Exception as e:
        print(f"获取文章页面失败: {e}")
        blog_html = ""
    
    blog_parse = etree.HTML(blog_html)
    
    # 优先从HTML的<title>标签中提取标题（用户要求使用title标签的完整内容）
    title = ""
    try:
        title_elements = blog_parse.xpath("//head/title/text()")
        if title_elements:
            title = title_elements[0].strip()
            # 只移除" - LOFTER"这种特定的后缀，保留其他内容（如"-吃瓜惹"）
            if title.endswith(" - LOFTER"):
                title = title[:-10].strip()
            elif title.endswith(" -LOFTER"):
                title = title[:-8].strip()
            print(f"从<title>标签提取到标题: {title}")
    except Exception as e:
        print(f"从<title>标签提取标题失败: {e}")
    
    # 从归档页面获取时间和标题（参考l10_blogs_txt.py）
    # 如果title标签没有获取到，才从归档页面获取
    public_time = ""
    if not title and author_id:
        try:
            time_and_title = get_time_and_title_from_archive(url, author_id, login_key, login_auth)
            public_time = time_and_title[0]
            title = time_and_title[1]
        except Exception as e:
            print(f"从归档页面获取时间标题失败: {e}")
    
    # 如果归档页面没有获取到，尝试从文章页面获取（参考l10_blogs_txt.py第94-111行）
    if not public_time and not title:
        print("尝试从博客页中匹配标题和时间", end="\t")
        try:
            title_path = blog_parse.xpath("//h2//text()")
            if title_path:
                title = title_path[0].strip()
                print(f"匹配成功: {title}")
        except:
            pass
        
        try:
            re_date = re.search(r"\d{4}[.\\\/-]\d{2}[.\\\/-]\d{2}", blog_html)
            if re_date:
                public_time = re_date.group(0).replace("\\", "-").replace(".", "-").replace("/", "-")
                print(f"匹配成功: {public_time}")
            else:
                public_time = time.strftime("%Y-%m-%d", time.localtime())
                print("匹配失败，使用当前日期")
        except:
            public_time = time.strftime("%Y-%m-%d", time.localtime())
    
    if not title:
        title = f"图片配文 {public_time}" if public_time else "无标题"
    
    if not public_time:
        public_time = time.strftime("%Y-%m-%d", time.localtime())
    
    # 使用从归档页面或文章页面获取的时间和标题
    publish_time = public_time
    
    # 获取tags（参考l9_author_txt.py第144-145行）
    tags = []
    try:
        tag_matches = re.findall(r'"http[s]{0,1}://.*?\.lofter\.com/tag/(.*?)"', blog_html)
        tags = [unquote(tag, "utf-8").replace("\xa0", " ") for tag in tag_matches]
    except:
        pass
    
    # 获取正文内容（参考l9_author_txt.py第151-153行）
    content_text = ""
    # 判断博文类型：检查HTML中是否有photo相关的class
    blog_type = "text"
    try:
        # 检查是否是photo类型（图片博文）
        photo_elements = blog_parse.xpath('//div[contains(@class,"photo")] | //div[contains(@class,"main-content-img")]')
        if photo_elements:
            blog_type = "img"
        elif title and title != f"图片配文 {public_time}":
            blog_type = "article"
    except:
        blog_type = "article" if title and title != f"图片配文 {public_time}" else "text"
    
    try:
        # 使用模板匹配（参考l9_author_txt.py第109行和l10_blogs_txt.py第125行）
        template_id = matcher(blog_parse)
        print(f"文字匹配模板为模板{template_id}")
        
        if template_id == 0:
            print("警告: 使用模板0（通用模板），可能包含额外内容或缺失部分内容")
        
        # 获取文章内容（参考l9_author_txt.py第153行）
        article_content = get_content(blog_parse, template_id, title, blog_type, "\n")
        content_text = article_content
        
        # 如果模板匹配失败（特别是模板0），不再使用html2text作为后备
        # 因为html2text会提取整个页面，包括CSS、导航等无关内容
        # 模板0已经尝试从main-content或main-cont提取，如果失败则返回空内容
        if not content_text or len(content_text.strip()) < 10:
            # 只在使用非模板0时才使用html2text作为后备
            if template_id != 0:
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.body_width = 0
                content_text = h.handle(blog_html)
                # 移除标题
                if title and content_text.startswith(title):
                    content_text = content_text[len(title):].strip()
                # 移除评论部分
                content_text = re.split(r'\s评论\s', content_text)[0].strip()
    except Exception as e:
        print(f"解析内容时出错: {e}")
        content_text = ""
    
    # 获取图片链接（参考LoftTagDownloader-master和lofterSpider-master）
    illustration = []
    img_urls = []
    
    try:
        # 优先从文章正文区域提取图片，避免提取到头像、推荐图片等
        # 根据匹配的模板，从对应的正文区域提取图片
        # template_id 已在前面获取，这里直接使用
        
        # 定义文章正文区域的xpath选择器（对应各个模板）
        content_selectors = [
            None,  # 模板0：通用模板，使用整个页面
            '//div[@class="content"]/div[@class="text"]',  # 模板1
            '//div[@class="cont"]/div[@class="text"]',  # 模板2
            '//div[@class="cont"]/div[@class]',  # 模板3
            '//div[@class="txtcont"]',  # 模板4
            '//div[@class="text"]',  # 模板5
            '//div[@class="text"]',  # 模板6
            '//div[contains(@class,"post-ctc box")]',  # 模板7
        ]
        
        content_selector = content_selectors[template_id] if template_id < len(content_selectors) else None
        
        # 方法1: 优先从文章正文区域的img标签提取图片
        if content_selector:
            try:
                # 从正文区域提取img标签
                img_elements = blog_parse.xpath(f'{content_selector}//img/@src')
                
                # 如果正文区域（text）没有图片，尝试从cont或content下的pic类提取
                # 图片可能在 cont/pic 或 content/pic 中
                if not img_elements:
                    # 尝试从cont下的pic类提取
                    pic_elements = blog_parse.xpath('//div[@class="cont"]//div[@class="pic"]//img/@src')
                    if not pic_elements:
                        # 尝试从content下的pic类提取
                        pic_elements = blog_parse.xpath('//div[@class="content"]//div[@class="pic"]//img/@src')
                    if pic_elements:
                        img_elements = pic_elements
                
                # 处理提取到的图片
                for src in img_elements:
                    # 移除HTML实体编码
                    src = src.replace('&amp;', '&')
                    # 匹配lofter图片链接（新格式：imglf[数字].lf[数字].net）
                    match = re.search(r'(https?://imglf\d*\.lf\d+\.net/img/[^?]*)', src)
                    if match:
                        clean_url = match.group(1)
                        # 移除imageView参数，但保留基础URL
                        if '?imageView' in clean_url:
                            clean_url = clean_url.split('?imageView')[0]
                        elif '?' in clean_url:
                            clean_url = clean_url.split('?')[0]
                        # 确保URL以图片扩展名结尾
                        if clean_url and any(clean_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                            if clean_url not in img_urls:
                                img_urls.append(clean_url)
                    else:
                        # 尝试旧格式
                        match = re.search(r'(https?://imglf\d\.nosdn\d*\.[0-9]{0,3}\d\.net[^?]*)', src)
                        if match:
                            clean_url = match.group(1)
                            clean_url = clean_url.split('?imageView')[0].split('imageView')[0]
                            if clean_url not in img_urls:
                                img_urls.append(clean_url)
                
                if img_urls:
                    print(f"从文章正文区域提取到 {len(img_urls)} 个图片链接")
            except Exception as e:
                print(f"从正文区域提取图片失败: {e}")
        
        # 如果模板0（通用模板）或没有content_selector，尝试从photo-main-content-img提取
        if (not img_urls) and (template_id == 0 or not content_selector):
            try:
                # 尝试从main-content-img类提取（photo类型博文）
                img_elements = blog_parse.xpath('//div[contains(@class,"main-content-img")]//img/@src')
                if not img_elements:
                    # 尝试从photo类提取
                    img_elements = blog_parse.xpath('//div[contains(@class,"photo")]//div[contains(@class,"img")]//img/@src')
                
                if img_elements:
                    for src in img_elements:
                        # 移除HTML实体编码
                        src = src.replace('&amp;', '&')
                        # 匹配lofter图片链接（新格式：imglf[数字].lf[数字].net）
                        match = re.search(r'(https?://imglf\d*\.lf\d+\.net/img/[^?]*)', src)
                        if match:
                            clean_url = match.group(1)
                            # 移除imageView参数，但保留基础URL
                            if '?imageView' in clean_url:
                                clean_url = clean_url.split('?imageView')[0]
                            elif '?' in clean_url:
                                clean_url = clean_url.split('?')[0]
                            # 确保URL以图片扩展名结尾
                            if clean_url and any(clean_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                if clean_url not in img_urls:
                                    img_urls.append(clean_url)
                        else:
                            # 尝试旧格式
                            match = re.search(r'(https?://imglf\d\.nosdn\d*\.[0-9]{0,3}\d\.net[^?]*)', src)
                            if match:
                                clean_url = match.group(1)
                                clean_url = clean_url.split('?imageView')[0].split('imageView')[0]
                                if clean_url not in img_urls:
                                    img_urls.append(clean_url)
                    
                    if img_urls:
                        print(f"从photo/main-content-img区域提取到 {len(img_urls)} 个图片链接")
            except Exception as e:
                print(f"从photo/main-content-img区域提取图片失败: {e}")
        
        # 方法2: 如果正文区域没有提取到，且是纯图片博文，才尝试从content或cont下的img标签提取
        # 注意：纯文字文章不应该从content/cont提取，因为可能包含非文章内容的图片
        if not img_urls and blog_type == "img":
            try:
                # 尝试从content下的img标签提取（排除text区域，因为text区域已经在方法1中检查过了）
                content_imgs = blog_parse.xpath('//div[@class="content"]//img/@src')
                if not content_imgs:
                    # 尝试从cont下的img标签提取
                    content_imgs = blog_parse.xpath('//div[@class="cont"]//img/@src')
                
                for src in content_imgs:
                    # 移除HTML实体编码
                    src = src.replace('&amp;', '&')
                    # 匹配lofter图片链接（新格式：imglf[数字].lf[数字].net）
                    match = re.search(r'(https?://imglf\d*\.lf\d+\.net/img/[^?]*)', src)
                    if match:
                        clean_url = match.group(1)
                        # 移除imageView参数，但保留基础URL
                        if '?imageView' in clean_url:
                            clean_url = clean_url.split('?imageView')[0]
                        elif '?' in clean_url:
                            clean_url = clean_url.split('?')[0]
                        # 确保URL以图片扩展名结尾
                        if clean_url and any(clean_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                            if clean_url not in img_urls:
                                img_urls.append(clean_url)
                    else:
                        # 尝试旧格式
                        match = re.search(r'(https?://imglf\d\.nosdn\d*\.[0-9]{0,3}\d\.net[^?]*)', src)
                        if match:
                            clean_url = match.group(1)
                            clean_url = clean_url.split('?imageView')[0].split('imageView')[0]
                            if clean_url not in img_urls:
                                img_urls.append(clean_url)
                
                if img_urls:
                    print(f"从content/cont区域提取到 {len(img_urls)} 个图片链接")
            except Exception as e:
                print(f"从content/cont区域提取图片失败: {e}")
        
        # 方法3: 如果正文区域和content/cont都没有图片，说明可能是纯文字文章，不应该从整个HTML提取
        # 只有在确认是图片类型博文且前面方法都没提取到图片时，才尝试从originPhotoLinks提取
        if not img_urls and blog_type == "img":
            origin_photo_links_pattern = re.compile(r'originPhotoLinks\s*=\s*"\[(.*?)\]"', re.DOTALL)
            origin_match = origin_photo_links_pattern.search(blog_html)
            
            if origin_match:
                # 提取raw链接（原图，参考LoftTagDownloader-master第346行）
                raw_pattern = re.compile(r'"raw":"(.+?)"')
                raw_links = raw_pattern.findall(origin_match.group(1))
                
                # 如果没有raw，尝试orign（大图）
                if not raw_links:
                    orign_pattern = re.compile(r'"orign":"(.+?)"')
                    orign_links = orign_pattern.findall(origin_match.group(1))
                    raw_links = orign_links
                
                # 清理链接（移除查询参数，参考LoftTagDownloader-master第138行）
                for link in raw_links:
                    clean_link = link.split('?')[0].split('imageView')[0]
                    if clean_link and clean_link not in img_urls:
                        img_urls.append(clean_link)
                
                if img_urls:
                    print(f"从originPhotoLinks提取到 {len(img_urls)} 个图片链接")
        
        # 使用img_fliter过滤（参考l9_author_txt.py第241行）
        from .utils import img_fliter
        img_urls = img_fliter(img_urls, blog_type)
        
        print(f"过滤后剩余 {len(img_urls)} 个图片链接")
        
        # illustration用于文章中的图片，img_urls用于主图
        illustration = img_urls.copy()
        
    except Exception as e:
        print(f"获取图片链接时出错: {e}")
        import traceback
        traceback.print_exc()
        illustration = []
        img_urls = []
    
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
