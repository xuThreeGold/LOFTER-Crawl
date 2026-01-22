# -*- coding: utf-8 -*-
"""
文件保存模块
"""
import os
import re
import requests
import yaml
import html2text
from urllib.parse import quote
from .utils import sanitize_filename, filename_check, get_headers
from .config import DEFAULT_SAVE_PATH


def save_post_txt(post_info, save_path, save_images=True):
    """
    保存文章为TXT格式
    :param post_info: 文章信息字典
    :param save_path: 保存路径
    :param save_images: 是否保存图片文件
    :return: 保存的文件名
    """
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)
    
    # 构建文件头
    title = post_info.get("title", "无标题")
    author_name = post_info.get("author_name", "未知作者")
    author_ip = post_info.get("author_ip", "")
    publish_time = post_info.get("publish_time", "")
    url = post_info.get("url", "")
    
    file_head = f"{title} by {author_name}[{author_ip}]\n"
    file_head += f"发表时间：{publish_time}\n"
    file_head += f"原文链接：{url}\n"
    
    # 构建文件内容
    # content中已经包含了按位置插入的图片链接，不需要再在末尾添加
    content = post_info.get("content", "")
    
    # 处理图片（用于下载）
    img_urls = post_info.get("img_urls", [])
    illustration = post_info.get("illustration", [])
    # 合并并去重，避免重复下载
    all_images = list(dict.fromkeys(img_urls + illustration))  # 使用dict.fromkeys保持顺序并去重
    
    # 构建完整内容（content中已经包含了图片链接）
    full_content = file_head + "\n\n" + content
    
    # 生成文件名：只使用标题内容
    title_safe = sanitize_filename(title)
    filename = f"{title_safe}.txt"
    
    # 检查文件名是否重复（传入发表时间用于判断是否覆盖）
    original_filename = filename
    filename = filename_check(filename, full_content, save_path, "txt", publish_time)
    
    # 判断是否需要覆盖文件
    is_overwrite = (filename == original_filename)
    
    # 保存文件
    file_path = os.path.join(save_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    
    # 保存图片文件（参考LoftTagDownloader-master的DownloadFile函数和lofterSpider-master的l13_like_share_tag.py）
    if save_images:
        if all_images:
            print(f"找到 {len(all_images)} 张图片，开始下载...")
            # 如果文件被覆盖，图片也使用原名称；如果文件添加了(2)，图片也添加(2)
            base_name = filename.rsplit(".", 1)[0]
            
            for i, img_url in enumerate(all_images, 1):
                try:
                    print(f"正在下载图片 {i}/{len(all_images)}: {img_url[:80]}...", end="")
                    
                    # 设置headers（参考LoftTagDownloader-master第167-168行和lofterSpider-master第842-844行）
                    headers = get_headers()
                    # 设置Referer（参考lofterSpider-master第844行）
                    headers["Referer"] = url.split("/post")[0] + "/"
                    
                    # 使用stream方式下载（参考LoftTagDownloader-master第171行）
                    img_response = requests.get(img_url, headers=headers, timeout=30, stream=True)
                    
                    if img_response.status_code == 200:
                        # 判断图片类型（参考lofterSpider-master第824-831行）
                        img_ext = "jpg"
                        if "gif" in img_url.lower():
                            img_ext = "gif"
                        elif "png" in img_url.lower():
                            img_ext = "png"
                        
                        img_filename = f"{base_name}_picture{i}.{img_ext}"
                        img_path = os.path.join(save_path, img_filename)
                        
                        # 流式写入（参考LoftTagDownloader-master第185-186行）
                        with open(img_path, "wb") as img_f:
                            for chunk in img_response.iter_content(chunk_size=8192):
                                if chunk:
                                    img_f.write(chunk)
                        
                        # 获取文件大小用于显示
                        file_size = os.path.getsize(img_path)
                        if file_size > 1048576:
                            size_str = f"{file_size / 1048576:.2f}MB"
                        else:
                            size_str = f"{file_size / 1024:.2f}KB"
                        
                        print(f" ✓ 已保存: {img_filename} ({size_str})")
                    else:
                        print(f" ✗ 下载失败，状态码: {img_response.status_code}")
                except Exception as e:
                    print(f" ✗ 保存失败: {str(e)}")
        else:
            print("未找到图片链接")
    
    return filename


def convert_post_to_markdown(post_info, save_path, save_images=True):
    """
    将文章信息转换为Markdown格式（参考LOFTER2Hexo和lofter2Jekyll的实现）
    :param post_info: 文章信息字典
    :param save_path: 保存路径（用于图片下载）
    :param save_images: 是否下载图片
    :return: (front_matter, body_md, image_map) - front_matter字典、markdown正文、图片URL到本地文件名的映射
    """
    title = post_info.get("title", "无标题")
    author_name = post_info.get("author_name", "未知作者")
    author_ip = post_info.get("author_ip", "")
    publish_time = post_info.get("publish_time", "")
    url = post_info.get("url", "")
    tags = post_info.get("tags", [])
    
    # 构建YAML Front-Matter
    front_matter = {
        "title": title,
        "date": publish_time,
        "author": f"{author_name}[{author_ip}]",
        "original_url": url,
    }
    if tags:
        front_matter["tags"] = tags
    
    # 获取HTML内容并转换为Markdown
    html_content = post_info.get("html_content", "")
    body_md = ""
    image_map = {}  # 图片URL到本地文件名的映射
    
    # 获取图片信息
    img_urls = post_info.get("img_urls", [])
    illustration = post_info.get("illustration", [])
    all_images = list(dict.fromkeys(img_urls + illustration))
    
    if html_content:
        print(f"使用HTML内容转换Markdown，HTML内容长度: {len(html_content)}")
        from lxml.html import fromstring, tostring
        
        try:
            html_parse = fromstring(html_content)
            
            # 处理内联样式：将style="text-decoration:underline;"转换为<u>标签
            underline_elements = html_parse.xpath('.//span[@style[contains(., "underline")]] | .//*[@style[contains(., "underline")]]')
            for elem in underline_elements:
                style = elem.get('style', '')
                if 'underline' in style.lower():
                    parent = elem.getparent()
                    if parent is not None:
                        u_elem = fromstring('<u></u>')
                        if elem.text:
                            u_elem.text = elem.text
                        for child in elem:
                            u_elem.append(child)
                        if elem.tail:
                            u_elem.tail = elem.tail
                        parent.replace(elem, u_elem)
            
            # 处理删除线样式
            strikethrough_elements = html_parse.xpath('.//span[@style[contains(., "line-through")]] | .//*[@style[contains(., "line-through")]]')
            for elem in strikethrough_elements:
                style = elem.get('style', '')
                if 'line-through' in style.lower():
                    parent = elem.getparent()
                    if parent is not None:
                        s_elem = fromstring('<s></s>')
                        if elem.text:
                            s_elem.text = elem.text
                        for child in elem:
                            s_elem.append(child)
                        if elem.tail:
                            s_elem.tail = elem.tail
                        parent.replace(elem, s_elem)
            
            # 处理图片：下载并替换为本地路径
            img_elements = html_parse.xpath('.//img')
            img_index = 0
            
            for img in img_elements:
                if img_index < len(all_images):
                    img_url = all_images[img_index]
                    img_alt = img.get('alt', '') or img.get('title', '') or f"图{img_index + 1}"
                    
                    # 检查图片是否在链接内
                    parent = img.getparent()
                    link_parent = None
                    if parent is not None and parent.tag == 'a':
                        link_parent = parent
                    elif parent is not None:
                        # 检查父元素的父元素是否是链接
                        grandparent = parent.getparent()
                        if grandparent is not None and grandparent.tag == 'a':
                            link_parent = grandparent
                    
                    if save_images:
                        try:
                            print(f"正在下载图片 {img_index + 1}/{len(all_images)}: {img_url[:80]}...", end="")
                            img_response = requests.get(img_url, headers=get_headers(), timeout=30)
                            if img_response.status_code == 200:
                                img_ext = "jpg"
                                if "gif" in img_url.lower():
                                    img_ext = "gif"
                                elif "png" in img_url.lower():
                                    img_ext = "png"
                                
                                base_name = sanitize_filename(title)
                                img_filename = f"{base_name}_picture{img_index + 1}.{img_ext}"
                                img_path = os.path.join(save_path, img_filename)
                                
                                with open(img_path, "wb") as img_f:
                                    img_f.write(img_response.content)
                                
                                # 获取文件大小用于显示
                                file_size = os.path.getsize(img_path)
                                if file_size > 1048576:
                                    size_str = f"{file_size / 1048576:.2f}MB"
                                else:
                                    size_str = f"{file_size / 1024:.2f}KB"
                                print(f" ✓ 已保存: {img_filename} ({size_str})")
                                
                                # 保存映射关系
                                image_map[img_url] = img_filename
                                
                                # 替换img标签为markdown格式
                                # 对文件名进行URL编码，确保包含emoji和特殊字符的路径能正确显示
                                # 只编码空格和特殊字符，保留字母数字和常见符号
                                encoded_filename = quote(img_filename, safe='._-')
                                img_md = f"![{img_alt}]({encoded_filename})"
                                
                                # 如果图片在链接内，替换整个链接；否则只替换图片
                                if link_parent is not None:
                                    # 替换整个链接为图片
                                    link_parent.addprevious(fromstring(f"<p>{img_md}</p>"))
                                    link_parent.getparent().remove(link_parent)
                                else:
                                    # 只替换图片
                                    if parent is not None:
                                        parent.addprevious(fromstring(f"<p>{img_md}</p>"))
                                        parent.remove(img)
                            else:
                                print(f" ✗ 下载失败，状态码: {img_response.status_code}")
                                # 下载失败，使用链接
                                img_md = f"![{img_alt}]({img_url})"
                                if link_parent is not None:
                                    link_parent.addprevious(fromstring(f"<p>{img_md}</p>"))
                                    link_parent.getparent().remove(link_parent)
                                elif parent is not None:
                                    parent.addprevious(fromstring(f"<p>{img_md}</p>"))
                                    parent.remove(img)
                        except Exception as e:
                            print(f" ✗ 保存失败: {str(e)}")
                            img_md = f"![{img_alt}]({img_url})"
                            if link_parent is not None:
                                link_parent.addprevious(fromstring(f"<p>{img_md}</p>"))
                                link_parent.getparent().remove(link_parent)
                            elif parent is not None:
                                parent.addprevious(fromstring(f"<p>{img_md}</p>"))
                                parent.remove(img)
                    else:
                        # 不下载图片，直接使用链接
                        img_md = f"![{img_alt}]({img_url})"
                        if link_parent is not None:
                            link_parent.addprevious(fromstring(f"<p>{img_md}</p>"))
                            link_parent.getparent().remove(link_parent)
                        elif parent is not None:
                            parent.addprevious(fromstring(f"<p>{img_md}</p>"))
                            parent.remove(img)
                    
                    img_index += 1
        except Exception as e:
            print(f"处理HTML内容时出错: {e}")
            try:
                html_parse = fromstring(html_content)
            except:
                html_parse = None
                body_md = post_info.get("content", "")
                return front_matter, body_md, image_map
        
        # 使用html2text转换HTML为Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        h.unicode_snob = True
        h.escape_snob = True
        h.skip_internal_links = False
        h.inline_links = True
        h.wrap_links = False
        h.ignore_emphasis = False
        h.ignore_tables = False
        h.bypass_tables = False
        h.ignore_anchors = False
        h.mark_code = True
        h.use_automatic_links = True
        h.escape_misc = False
        h.ignore_mailto_links = False
        
        # 转换HTML为Markdown
        body_md = h.handle(tostring(html_parse, encoding='unicode'))
        
        # 修复被html2text转义的Markdown图片语法
        # html2text可能会转义 ![]() 为 \!\[\]\(\)
        import re
        # 修复转义的图片语法：\!\[.*?\]\(.*?\)
        # 匹配模式：\!\[...\]\(...\)，包括转义的下划线
        # 先处理包含转义下划线的图片路径
        body_md = re.sub(r'\\!\\\[([^\]]+)\\\]\\\(([^)]*)\\_([^)]*)\\\)', r'![\1](\2_\3)', body_md)
        # 再处理不包含转义下划线的图片路径
        body_md = re.sub(r'\\!\\\[([^\]]+)\\\]\\\(([^\)]+)\\\)', r'![\1](\2)', body_md)
        # 修复图片路径中剩余的转义下划线（在括号内）
        body_md = re.sub(r'!\[([^\]]+)\]\(([^)]*)\\_([^)]*)\)', r'![\1](\2_\3)', body_md)
        
        # 修复链接包裹图片的格式：[![...](...)](...)
        # 这种情况是图片在链接内，html2text会转换为链接格式，需要提取出图片部分
        body_md = re.sub(r'\[!\[([^\]]+)\]\(([^)]+)\)\]\([^)]*\)', r'![\1](\2)', body_md)
        
        # 处理content中已插入的图片链接标记（格式：[图片链接: url]）
        def replace_image_link(match):
            img_url = match.group(1)
            if img_url in image_map:
                # 对文件名进行URL编码
                encoded_filename = quote(image_map[img_url], safe='._-')
                return f"![图片]({encoded_filename})"
            else:
                return f"![图片]({img_url})"
        
        body_md = re.sub(r'\[图片链接:\s*([^\]]+)\]', replace_image_link, body_md)
    else:
        # 如果没有HTML内容，使用纯文本内容，但需要处理图片
        print(f"警告: 没有HTML内容，使用纯文本内容")
        body_md = post_info.get("content", "")
        
        # 如果没有HTML内容但有图片，需要下载图片并插入到内容中
        if all_images:
            if save_images:
                print(f"找到 {len(all_images)} 张图片，开始下载...")
            # 下载所有图片
            base_name = sanitize_filename(title)
            for i, img_url in enumerate(all_images, 1):
                try:
                    print(f"正在下载图片 {i}/{len(all_images)}: {img_url[:80]}...", end="")
                    img_response = requests.get(img_url, headers=get_headers(), timeout=30)
                    if img_response.status_code == 200:
                        img_ext = "jpg"
                        if "gif" in img_url.lower():
                            img_ext = "gif"
                        elif "png" in img_url.lower():
                            img_ext = "png"
                        
                        img_filename = f"{base_name}_picture{i}.{img_ext}"
                        img_path = os.path.join(save_path, img_filename)
                        
                        with open(img_path, "wb") as img_f:
                            img_f.write(img_response.content)
                        
                        # 获取文件大小用于显示
                        file_size = os.path.getsize(img_path)
                        if file_size > 1048576:
                            size_str = f"{file_size / 1048576:.2f}MB"
                        else:
                            size_str = f"{file_size / 1024:.2f}KB"
                        print(f" ✓ 已保存: {img_filename} ({size_str})")
                        
                        # 保存映射关系
                        image_map[img_url] = img_filename
                    else:
                        print(f" ✗ 下载失败，状态码: {img_response.status_code}")
                except Exception as e:
                    print(f" ✗ 保存失败: {str(e)}")
        
        # 处理content中的图片链接标记
        import re
        def replace_image_link(match):
            img_url = match.group(1)
            try:
                img_idx = all_images.index(img_url)
                if img_url in image_map:
                    # 对文件名进行URL编码
                    encoded_filename = quote(image_map[img_url], safe='._-')
                    return f"![图{img_idx + 1}]({encoded_filename})"
                else:
                    return f"![图{img_idx + 1}]({img_url})"
            except ValueError:
                return f"![图片]({img_url})"
        
        body_md = re.sub(r'\[图片链接:\s*([^\]]+)\]', replace_image_link, body_md)
    
    return front_matter, body_md.strip(), image_map


def save_post_markdown(post_info, save_path, save_images=True):
    """
    保存文章为Markdown格式（使用convert_post_to_markdown函数）
    :param post_info: 文章信息字典
    :param save_path: 保存路径
    :param save_images: 是否下载并嵌入图片
    :return: 保存的文件名
    """
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)
    
    # 使用convert_post_to_markdown函数转换
    front_matter, body_md, image_map = convert_post_to_markdown(post_info, save_path, save_images)
    
    # 构建完整的Markdown内容（YAML Front-Matter + 正文）
    md_content = "---\n"
    # 使用yaml.dump生成Front-Matter，确保格式正确
    yaml_str = yaml.dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    md_content += yaml_str
    md_content += "---\n\n"
    md_content += body_md
    
    # 生成文件名：只使用标题内容
    title = post_info.get("title", "无标题")
    title_safe = sanitize_filename(title)
    filename = f"{title_safe}.md"
    publish_time = post_info.get("publish_time", "")
    
    # 检查文件名是否重复（传入发表时间用于判断是否覆盖）
    filename = filename_check(filename, md_content, save_path, "md", publish_time)
    
    # 保存文件
    file_path = os.path.join(save_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return filename


def save_posts(posts, save_path, file_format="txt", group_by_author=True, save_images=True):
    """
    批量保存文章
    :param posts: 文章信息列表
    :param save_path: 保存路径
    :param file_format: 文件格式 "txt" 或 "md"
    :param group_by_author: 是否按作者分组
    :param save_images: 是否保存图片
    :return: 保存的文件列表
    """
    saved_files = []
    
    if group_by_author:
        # 按作者分组
        authors = {}
        for post in posts:
            author_name = post.get("author_name", "未知作者")
            if author_name not in authors:
                authors[author_name] = []
            authors[author_name].append(post)
        
        # 为每个作者创建文件夹
        for author_name, author_posts in authors.items():
            author_name_safe = sanitize_filename(author_name)
            author_path = os.path.join(save_path, f"作者_{author_name_safe}")
            
            print(f"正在保存作者 {author_name} 的 {len(author_posts)} 篇文章...")
            
            for post in author_posts:
                try:
                    if file_format == "md":
                        filename = save_post_markdown(post, author_path, save_images)
                    else:
                        filename = save_post_txt(post, author_path, save_images)
                    saved_files.append(os.path.join(author_path, filename))
                except Exception as e:
                    print(f"保存文章失败 {post.get('url', '')}: {e}")
    else:
        # 不分组，全部保存在一个文件夹
        print(f"正在保存 {len(posts)} 篇文章...")
        
        for post in posts:
            try:
                if file_format == "md":
                    filename = save_post_markdown(post, save_path, save_images)
                else:
                    filename = save_post_txt(post, save_path, save_images)
                saved_files.append(os.path.join(save_path, filename))
            except Exception as e:
                print(f"保存文章失败 {post.get('url', '')}: {e}")
    
    print(f"总共保存了 {len(saved_files)} 个文件")
    return saved_files
