# -*- coding: utf-8 -*-
"""
文件保存模块
"""
import os
import re
import requests
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
    content = post_info.get("content", "")
    
    # 处理图片
    img_urls = post_info.get("img_urls", [])
    illustration = post_info.get("illustration", [])
    all_images = img_urls + illustration
    
    image_links_text = ""
    if all_images:
        image_links_text = "\n\n图片链接：\n"
        for i, img_url in enumerate(all_images, 1):
            image_links_text += f"图{i}: {img_url}\n"
    
    # 构建完整内容
    full_content = file_head + "\n\n" + content + image_links_text
    
    # 生成文件名
    title_safe = sanitize_filename(title)
    author_name_safe = sanitize_filename(author_name)
    filename = f"{title_safe} by {author_name_safe}.txt"
    
    # 检查文件名是否重复
    filename = filename_check(filename, full_content, save_path, "txt")
    
    # 保存文件
    file_path = os.path.join(save_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    
    # 保存图片文件
    if save_images and all_images:
        base_name = filename.rsplit(".", 1)[0]
        for i, img_url in enumerate(all_images, 1):
            try:
                img_response = requests.get(img_url, headers=get_headers(), timeout=10)
                if img_response.status_code == 200:
                    # 判断图片类型
                    img_ext = "jpg"
                    if "gif" in img_url.lower():
                        img_ext = "gif"
                    elif "png" in img_url.lower():
                        img_ext = "png"
                    
                    img_filename = f"{base_name}_picture{i}.{img_ext}"
                    img_path = os.path.join(save_path, img_filename)
                    
                    with open(img_path, "wb") as img_f:
                        img_f.write(img_response.content)
                    print(f"已保存图片: {img_filename}")
            except Exception as e:
                print(f"保存图片失败 {img_url}: {e}")
    
    return filename


def save_post_markdown(post_info, save_path, save_images=True):
    """
    保存文章为Markdown格式
    :param post_info: 文章信息字典
    :param save_path: 保存路径
    :param save_images: 是否下载并嵌入图片
    :return: 保存的文件名
    """
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)
    
    # 构建Markdown内容
    title = post_info.get("title", "无标题")
    author_name = post_info.get("author_name", "未知作者")
    author_ip = post_info.get("author_ip", "")
    publish_time = post_info.get("publish_time", "")
    url = post_info.get("url", "")
    
    md_content = f"# {title}\n\n"
    md_content += f"**作者**: {author_name}[{author_ip}]\n\n"
    md_content += f"**发表时间**: {publish_time}\n\n"
    md_content += f"**原文链接**: {url}\n\n"
    md_content += "---\n\n"
    
    # 添加正文内容
    content = post_info.get("content", "")
    md_content += content + "\n\n"
    
    # 处理图片
    img_urls = post_info.get("img_urls", [])
    illustration = post_info.get("illustration", [])
    all_images = img_urls + illustration
    
    if all_images:
        md_content += "## 图片\n\n"
        
        if save_images:
            # 下载图片并嵌入
            base_name = sanitize_filename(title)
            for i, img_url in enumerate(all_images, 1):
                try:
                    img_response = requests.get(img_url, headers=get_headers(), timeout=10)
                    if img_response.status_code == 200:
                        # 判断图片类型
                        img_ext = "jpg"
                        if "gif" in img_url.lower():
                            img_ext = "gif"
                        elif "png" in img_url.lower():
                            img_ext = "png"
                        
                        img_filename = f"{base_name}_picture{i}.{img_ext}"
                        img_path = os.path.join(save_path, img_filename)
                        
                        # 保存图片文件
                        with open(img_path, "wb") as img_f:
                            img_f.write(img_response.content)
                        
                        # 在Markdown中引用图片
                        md_content += f"![图{i}]({img_filename})\n\n"
                except Exception as e:
                    print(f"下载图片失败 {img_url}: {e}")
                    # 如果下载失败，使用链接
                    md_content += f"![图{i}]({img_url})\n\n"
        else:
            # 只保存链接
            for i, img_url in enumerate(all_images, 1):
                md_content += f"![图{i}]({img_url})\n\n"
    
    # 生成文件名
    title_safe = sanitize_filename(title)
    author_name_safe = sanitize_filename(author_name)
    filename = f"{title_safe} by {author_name_safe}.md"
    
    # 检查文件名是否重复
    filename = filename_check(filename, md_content, save_path, "md")
    
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
