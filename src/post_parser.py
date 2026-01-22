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


def insert_image_links_in_content(content_text, img_urls, illustration, blog_html, blog_parse, template_id=0):
    """
    将图片链接插入到内容中的正确位置
    :param content_text: 提取的文本内容
    :param img_urls: 图片URL列表
    :param illustration: 文章中的图片列表
    :param blog_html: HTML源码
    :param blog_parse: 解析后的HTML树
    :param template_id: 模板ID
    :return: 插入图片链接后的内容
    """
    all_images = list(dict.fromkeys(img_urls + illustration))
    if not all_images:
        return content_text
    
    # 方法1: 对于cont结构（pic在text之前）或content结构（img在text之前）
    print(f"方法1: 尝试匹配cont/content结构")
    try:
        # 先尝试cont结构（模板2）
        cont_selectors = [
            '//body//div[@class="cont"]',
            '//body//div[contains(@class,"cont")]',
        ]
        
        # 再尝试content结构（模板1）
        content_selectors = [
            '//body//div[@class="content"]',
            '//body//div[contains(@class,"content")]',
        ]
        
        all_selectors = []
        for selector in cont_selectors:
            all_selectors.append(('cont', selector))
        for selector in content_selectors:
            all_selectors.append(('content', selector))
        
        for struct_type, parent_selector in all_selectors:
            parent_elements = blog_parse.xpath(parent_selector)
            print(f"方法1: 使用选择器 {parent_selector} ({struct_type}结构), 找到 {len(parent_elements)} 个元素")
            if parent_elements:
                result_parts = []
                img_index = 0
                
                # 先提取图片区域的图片（按顺序）
                # 对于cont结构，查找pic；对于content结构，查找img
                if struct_type == 'cont':
                    pic_elements = blog_parse.xpath(f'{parent_selector}//div[@class="pic"]')
                    print(f"方法1: 找到 {len(pic_elements)} 个pic元素")
                else:
                    # content结构，查找img元素
                    pic_elements = blog_parse.xpath(f'{parent_selector}//div[@class="img"]')
                    print(f"方法1: 找到 {len(pic_elements)} 个img元素")
                for pic in pic_elements:
                    # 从pic中提取图片URL（优先使用bigimgsrc，否则使用img src）
                    img_src = None
                    # 尝试从a标签的bigimgsrc获取
                    bigimgsrc_list = pic.xpath('.//a/@bigimgsrc')
                    if bigimgsrc_list:
                        img_src = bigimgsrc_list[0]
                    else:
                        # 否则从img标签的src获取
                        img_src_list = pic.xpath('.//img/@src')
                        if img_src_list:
                            img_src = img_src_list[0]
                    
                    if img_src and img_index < len(all_images):
                        img_src = img_src.replace('&amp;', '&')
                        match = re.search(r'(https?://imglf\d*\.lf\d+\.net/img/[^?]*)', img_src)
                        if match:
                            clean_url = match.group(1)
                            if '?imageView' in clean_url:
                                clean_url = clean_url.split('?imageView')[0]
                            elif '?' in clean_url:
                                clean_url = clean_url.split('?')[0]
                            # 在图片列表中找到匹配的URL（按顺序）
                            if img_index < len(all_images):
                                img_url = all_images[img_index]
                                url_clean = img_url.split('?imageView')[0].split('?')[0]
                                if clean_url == url_clean or clean_url in img_url or img_url in clean_url:
                                    result_parts.append(f"[图片链接: {img_url}]")
                                    img_index += 1
                
                # 再提取text区域的文字
                text_elements = blog_parse.xpath(f'{parent_selector}//div[@class="text"]')
                if text_elements:
                    # 按顺序提取text区域内的所有段落
                    p_elements = text_elements[0].xpath('.//p')
                    if p_elements:
                        for p in p_elements:
                            p_text = ''.join(p.xpath('.//text()')).strip()
                            if p_text:
                                result_parts.append(p_text)
                    else:
                        # 如果没有p标签，直接提取所有文本
                        text_content = ''.join(text_elements[0].xpath('.//text()')).strip()
                        if text_content:
                            result_parts.append(text_content)
                
                if result_parts:
                    result = '\n\n'.join(result_parts)
                    print(f"方法1: 成功从{struct_type}结构提取内容并插入图片链接，共 {len(result_parts)} 个部分，图片链接数量: {img_index}")
                    if "[图片链接:" in result:
                        print(f"方法1: 确认返回的内容中包含图片链接标记")
                        return result
                    else:
                        print(f"方法1: 警告: 返回的内容中不包含图片链接标记，继续尝试方法2")
                        # 如果方法1没有插入图片链接，继续尝试方法2
    except Exception as e:
        print(f"处理cont结构时出错: {e}")
        import traceback
        traceback.print_exc()
        pass
    
    # 方法2: 尝试从main-content-text区域按顺序提取内容和图片
    print(f"方法2: 尝试匹配main-content-text结构，template_id={template_id}")
    try:
        # 对于模板1（content结构），需要先查找同级的img区域，再查找text区域
        if template_id == 1:
            # 查找content父元素
            content_elements = blog_parse.xpath('//div[@class="content"]')
            if content_elements:
                result_parts = []
                img_index = 0
                
                # 先查找同级的img区域（在content下，text之前）
                img_elements = content_elements[0].xpath('.//div[@class="img"]')
                print(f"方法2: 在content结构中找到 {len(img_elements)} 个img元素")
                
                for img_div in img_elements:
                    # 从img中提取图片URL（优先使用bigimgsrc，否则使用img src）
                    img_src = None
                    # 尝试从a标签的bigimgsrc获取
                    bigimgsrc_list = img_div.xpath('.//a/@bigimgsrc')
                    if bigimgsrc_list:
                        img_src = bigimgsrc_list[0]
                    else:
                        # 否则从img标签的src获取
                        img_src_list = img_div.xpath('.//img/@src')
                        if img_src_list:
                            img_src = img_src_list[0]
                    
                    if img_src and img_index < len(all_images):
                        img_src = img_src.replace('&amp;', '&')
                        # 直接按顺序使用图片列表中的URL
                        img_url = all_images[img_index]
                        print(f"方法2: 插入图片链接 {img_index + 1}/{len(all_images)}: {img_url[:50]}...")
                        result_parts.append(f"[图片链接: {img_url}]")
                        img_index += 1
                
                # 再查找text区域
                text_elements = content_elements[0].xpath('.//div[@class="text"]')
                if text_elements:
                    # 获取text区域内的所有p标签，按顺序
                    p_elements = text_elements[0].xpath('.//p')
                    print(f"方法2: 在content结构中找到 {len(p_elements)} 个p标签")
                    
                    for p in p_elements:
                        p_text = ''.join(p.xpath('.//text()')).strip()
                        if p_text:
                            result_parts.append(p_text)
                    
                    if result_parts:
                        result = '\n\n'.join(result_parts)
                        print(f"方法2: 成功从content结构提取内容并插入图片链接，共 {len(result_parts)} 个部分，图片链接数量: {img_index}")
                        if "[图片链接:" in result:
                            print(f"方法2: 确认返回的内容中包含图片链接标记")
                            return result
        
        # 根据模板ID，优先使用对应的选择器
        template_selectors = [
            None,  # 模板0
            '//div[@class="content"]/div[@class="text"]',  # 模板1（已在上面的if中处理）
            '//div[@class="cont"]/div[@class="text"]',  # 模板2
            '//div[@class="cont"]/div[@class]',  # 模板3
            '//div[@class="txtcont"]',  # 模板4
            '//div[@class="text"]',  # 模板5
            '//div[@class="text"]',  # 模板6
            '//div[contains(@class,"post-ctc box")]',  # 模板7
        ]
        
        # 构建选择器列表：先尝试模板对应的选择器，再尝试其他选择器
        text_selectors = []
        if template_id < len(template_selectors) and template_selectors[template_id] and template_id != 1:
            text_selectors.append(template_selectors[template_id])
        
        # 添加其他可能的选择器
        text_selectors.extend([
            '//body//div[contains(@class,"main")]//div[@class="content"]//div[@class="text"]',
            '//body//div[contains(@class,"main-content")]//div[@class="text"]',
            '//body//div[contains(@class,"main")]//div[contains(@class,"content")]//div[contains(@class,"text")]',
        ])
        
        for text_selector in text_selectors:
            text_elements = blog_parse.xpath(text_selector)
            print(f"方法2: 尝试使用选择器: {text_selector}, 找到 {len(text_elements)} 个text元素")
            if text_elements:
                result_parts = []
                img_index = 0
                
                # 获取text区域内的所有p标签，按顺序
                p_elements = blog_parse.xpath(f'{text_selector}//p')
                
                print(f"尝试使用选择器: {text_selector}, 找到 {len(p_elements)} 个p标签")
                
                if p_elements:
                    for p_idx, p in enumerate(p_elements):
                        # 检查p标签内是否有img
                        img_in_p = p.xpath('.//img')
                        if img_in_p:
                            print(f"找到包含图片的p标签 (第{p_idx+1}个)，图片数量: {len(img_in_p)}, 当前img_index: {img_index}")
                            # 先提取图片前的文本
                            before_text = ''.join(p.xpath('.//text()[preceding::img]')).strip()
                            if before_text:
                                result_parts.append(before_text)
                            
                            # 插入图片链接（按顺序）
                            # 即使p标签内只有img，没有其他文本，也要插入图片链接
                            for img in img_in_p:
                                if img_index >= len(all_images):
                                    print(f"警告: img_index ({img_index}) >= all_images长度 ({len(all_images)})")
                                    break
                                # 直接按顺序使用图片列表中的URL，不需要匹配
                                img_url = all_images[img_index]
                                print(f"插入图片链接 {img_index + 1}/{len(all_images)}: {img_url[:50]}...")
                                result_parts.append(f"[图片链接: {img_url}]")
                                img_index += 1
                            
                            # 提取图片后的文本
                            after_text = ''.join(p.xpath('.//text()[following::img]')).strip()
                            if after_text:
                                result_parts.append(after_text)
                        else:
                            # 没有图片，直接提取文本
                            p_text = ''.join(p.xpath('.//text()')).strip()
                            if p_text:
                                result_parts.append(p_text)
                    
                    # 如果成功提取了内容，检查是否需要返回
                    if result_parts:
                        result = '\n\n'.join(result_parts)
                        print(f"成功从text区域提取内容并插入图片链接，共 {len(result_parts)} 个部分，图片链接数量: {img_index}")
                        
                        # 如果还有未插入的图片链接，在末尾添加
                        if img_index < len(all_images):
                            remaining_images = all_images[img_index:]
                            print(f"还有 {len(remaining_images)} 张图片未插入，将在末尾添加")
                            image_links_text = "\n\n图片链接：\n"
                            for i, img_url in enumerate(remaining_images, 1):
                                image_links_text += f"图{i}: {img_url}\n"
                            result = result + image_links_text
                        
                        # 检查结果中是否包含图片链接
                        has_image_links = "[图片链接:" in result or "图片链接：" in result
                        if has_image_links:
                            print(f"确认: 返回的内容中包含图片链接标记")
                            # 打印结果的前200个字符，用于调试
                            print(f"返回内容预览: {result[:200]}...")
                            return result
                        else:
                            # 如果没有插入图片链接，继续尝试方法3
                            # 如果提取的内容太短（小于原始内容的30%），也继续尝试方法3
                            if len(result) < len(content_text) * 0.3:
                                print(f"警告: 提取的内容太短（{len(result)} < {len(content_text) * 0.3:.0f}），继续尝试方法3")
                            else:
                                print(f"警告: 返回的内容中不包含图片链接标记，继续尝试方法3")
                    else:
                        print(f"警告: 从text区域提取到p标签，但没有提取到任何内容")
                else:
                    print(f"警告: 使用选择器 {text_selector} 没有找到p标签")
    except Exception as e:
        print(f"处理main-content-text结构时出错: {e}")
        import traceback
        traceback.print_exc()
        pass
    
    # 方法3: 如果无法识别位置，在内容末尾添加图片链接（保持原有行为）
    # 这是最后的后备方案，确保图片链接总是被添加
    if all_images:
        print(f"方法3: 在内容末尾添加图片链接（后备方案）")
        image_links_text = "\n\n图片链接：\n"
        for i, img_url in enumerate(all_images, 1):
            image_links_text += f"图{i}: {img_url}\n"
        result = content_text + image_links_text
        print(f"方法3: 已添加 {len(all_images)} 个图片链接到内容末尾")
        return result
    
    return content_text


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
    
    # 优先从归档页面获取时间（参考l10_blogs_txt.py第91-93行）
    # 这是最准确的方法，应该总是尝试
    public_time = ""
    archive_title = ""
    if author_id:
        try:
            print("准备从归档页面获取时间", end="\t")
            time_and_title = get_time_and_title_from_archive(url, author_id, login_key, login_auth)
            public_time = time_and_title[0]
            archive_title = time_and_title[1]  # 保存归档页面的标题作为备用
            if public_time:
                print(f"已获取到时间: {public_time}")
        except Exception as e:
            print(f"从归档页面获取时间失败: {e}")
    
    # 如果<title>标签没有获取到标题，使用归档页面的标题
    if not title and archive_title:
        title = archive_title
        print(f"使用归档页面的标题: {title}")
    
    # 如果归档页面没有获取到时间，尝试从文章页面获取（参考l10_blogs_txt.py第104-111行）
    if not public_time:
        print("尝试从博客页中匹配发表时间", end="\t")
        try:
            re_date = re.search(r"\d{4}[.\\\/-]\d{2}[.\\\/-]\d{2}", blog_html)
            if re_date:
                public_time = re_date.group(0).replace("\\", "-").replace(".", "-").replace("/", "-")
                print(f"匹配成功: {public_time}")
            else:
                public_time = "1970-01-01"
                print("匹配失败，发表时间将设为 1970-01-01")
        except:
            public_time = "1970-01-01"
            print("匹配失败，发表时间将设为 1970-01-01")
    
    # 如果归档页面和title标签都没有获取到标题，尝试从文章页面获取（参考l10_blogs_txt.py第96-102行）
    if not title:
        print("尝试从博客页中匹配标题", end="\t")
        try:
            title_path = blog_parse.xpath("//h2//text()")
            if title_path:
                title = title_path[0].strip()
                print(f"匹配成功: {title}")
            else:
                print("匹配失败，将作为文本保存")
        except:
            pass
    
    # 如果还是没有标题，使用默认标题
    if not title:
        title = f"图片配文 {public_time}" if public_time and public_time != "1970-01-01" else "无标题"
    
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
    
    # 将图片链接按顺序插入到内容中的正确位置
    # 需要根据HTML结构，在图片位置插入图片链接
    if img_urls or illustration:
        print(f"开始插入图片链接，原始内容长度: {len(content_text)}, 图片数量: {len(img_urls) + len(illustration)}")
        content_with_images = insert_image_links_in_content(content_text, img_urls, illustration, blog_html, blog_parse, template_id)
        # 如果插入图片链接后内容发生变化，说明成功插入了
        if content_with_images != content_text:
            print(f"已成功插入图片链接到内容中，新内容长度: {len(content_with_images)}")
            # 检查新内容中是否包含图片链接
            if "[图片链接:" in content_with_images:
                print(f"确认: 新内容中包含图片链接标记")
            else:
                print(f"警告: 新内容中不包含图片链接标记，可能插入失败")
        else:
            print(f"警告: 图片链接未插入，可能未匹配到正确的text区域")
    else:
        content_with_images = content_text
    
    # 保存原始HTML内容区域（用于markdown转换）
    html_content = ""
    try:
        # 根据模板ID获取对应的HTML内容区域
        content_selectors = [
            None,  # 模板0
            '//div[@class="content"]',  # 模板1：提取整个content区域（包含img和text）
            '//div[@class="cont"]',  # 模板2：提取整个cont区域（包含pic和text）
            '//div[@class="cont"]/div[@class]',  # 模板3
            '//div[@class="txtcont"]',  # 模板4
            '//div[@class="text"]',  # 模板5
            '//div[@class="text"]',  # 模板6
            '//div[contains(@class,"post-ctc box")]',  # 模板7
        ]
        
        if template_id > 0 and template_id < len(content_selectors) and content_selectors[template_id]:
            # 对于模板1和模板2，需要提取整个父区域（包含图片和文字）
            if template_id == 1:
                # 模板1：提取整个content区域（包含img和text）
                content_elements = blog_parse.xpath('//div[@class="content"]')
                if content_elements:
                    from lxml.html import tostring
                    html_content = tostring(content_elements[0], encoding='unicode', pretty_print=False)
                    print(f"从模板{template_id}提取到HTML内容（content区域），长度: {len(html_content)}")
                else:
                    print(f"警告: 模板{template_id}的content区域没有匹配到元素")
            elif template_id == 2:
                # 模板2：提取整个cont区域（包含pic和text）
                cont_elements = blog_parse.xpath('//div[@class="cont"]')
                if cont_elements:
                    from lxml.html import tostring
                    html_content = tostring(cont_elements[0], encoding='unicode', pretty_print=False)
                    print(f"从模板{template_id}提取到HTML内容（cont区域），长度: {len(html_content)}")
                else:
                    print(f"警告: 模板{template_id}的cont区域没有匹配到元素")
            else:
                content_elements = blog_parse.xpath(content_selectors[template_id])
                if content_elements:
                    # 获取第一个匹配元素的HTML
                    from lxml.html import tostring
                    html_content = tostring(content_elements[0], encoding='unicode', pretty_print=False)
                    print(f"从模板{template_id}提取到HTML内容，长度: {len(html_content)}")
                else:
                    print(f"警告: 模板{template_id}的选择器 {content_selectors[template_id]} 没有匹配到元素")
        elif template_id == 0:
            # 对于模板0，尝试从main-content或main-cont提取
            selectors = [
                '//body//div[contains(@class,"main")]//div[@class="content"]',
                '//body//div[contains(@class,"main")]//div[contains(@class,"content")]',
                '//body//div[contains(@class,"main-cont")]',
            ]
            for selector in selectors:
                content_elements = blog_parse.xpath(selector)
                if content_elements:
                    from lxml.html import tostring
                    html_content = tostring(content_elements[0], encoding='unicode', pretty_print=False)
                    break
    except Exception as e:
        print(f"提取HTML内容时出错: {e}")
    
    return {
        "url": url,
        "title": title,
        "author_name": author_name,
        "author_ip": author_ip,
        "publish_time": publish_time,
        "tags": tags,
        "content": content_with_images,
        "html_content": html_content,  # 保存原始HTML内容用于markdown转换
        "img_urls": img_urls,
        "illustration": illustration
    }
