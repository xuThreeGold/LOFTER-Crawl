# -*- coding: utf-8 -*-
"""
工具函数
"""
import re
import random


def get_headers():
    """获取请求头（网页版）"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }


def get_app_style_headers():
    """
    获取模拟 LOFTER App 的请求头（参考 Loftify-main/lib/Utils/request_header_util.dart）
    
    这些 header 可能被服务器用来识别"这是来自官方 App 的请求"，
    从而返回更完整的数据（比如已解锁的彩蛋内容）。
    """
    import base64
    import json
    import random
    import string
    
    # 生成随机请求ID（参考 Loftify 的 getXReqId）
    def random_string(length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    # 生成 portrait（JWT payload，参考 Loftify 的 getPortrait）
    # 注意：这里只是模拟格式，不是真正的 JWT 签名
    portrait_payload = {
        "imei": "3451efd56bgg6h47",
        "androidId": "3451efd56bgg6h47",
        "oaid": "32b4d2c348650842",
        "mac": "02:00:00:00:00:00",
        "phone": "15934867293",
    }
    # 简单 base64 编码（Loftify 用的是 JWT，但这里先简化）
    portrait_encoded = base64.b64encode(json.dumps(portrait_payload).encode('utf-8')).decode('utf-8')
    
    return {
        'User-Agent': 'LOFTER-Android 8.0.12 (23127PN0CC; Android 14; null) WIFI',
        'x-device': 'qv+Dz73SObtbEFG7P0Gq12HkjzNb+iOK6KHWTPKHBTEZu26C6MJOMukkAG7dETo2',
        'lofproduct': 'lofter-android-8.0.12',
        'market': 'xiaomi',
        'deviceid': '3451efd56bgg6h47',
        'dadeviceid': '2ef9ea6c17b7c6881c71915a4fefd932edc01af0',
        'androidid': '3451efd56bgg6h47',
        'x-reqid': random_string(8),
        'portrait': portrait_encoded,
    }


def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    # 替换非法字符
    filename = filename.replace("/", "&").replace("|", "&").replace("\\", "&") \
        .replace("<", "《").replace(">", "》").replace(":", "：") \
        .replace('"', '"').replace("?", "？").replace("*", "·") \
        .replace("\n", "").replace("(", "（").replace(")", "）") \
        .replace("\t", " ").replace("\r", " ").strip()
    # 移除控制字符
    filename = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]').sub(' ', filename)
    return filename


def filename_check(filename, file_content, path, file_type, publish_time=None):
    """
    检查文件名是否重复，如果重复则根据时间判断是否覆盖或添加序号
    :param filename: 文件名
    :param file_content: 新文件内容
    :param path: 保存路径
    :param file_type: 文件类型
    :param publish_time: 发表时间（用于判断是否覆盖）
    :return: 最终文件名
    """
    import os
    
    if not os.path.exists(os.path.join(path, filename)):
        return filename
    
    # 如果文件已存在，读取文件内容
    exist_file_path = os.path.join(path, filename)
    if file_type == "txt" or file_type == "md":
        try:
            with open(exist_file_path, "r", encoding="utf-8") as f:
                exist_file = f.read()
        except:
            exist_file = ""
    else:
        try:
            with open(exist_file_path, "rb") as f:
                exist_file = f.read()
        except:
            exist_file = b""
    
    # 如果文件内容相同，返回原文件名
    if exist_file == file_content:
        return filename
    
    # 如果提供了发表时间，检查已存在文件的时间
    if publish_time and (file_type == "txt" or file_type == "md"):
        try:
            # 从已存在文件的开头提取时间
            # 文件头格式：{title} by {author_name}[{author_ip}]\n发表时间：{publish_time}\n...
            exist_time_match = re.search(r'发表时间：([^\n]+)', exist_file)
            if exist_time_match:
                exist_time = exist_time_match.group(1).strip()
                # 如果时间相同，返回原文件名（用于覆盖）
                if exist_time == publish_time:
                    return filename
        except:
            pass
    
    # 如果文件内容不同且时间不同，添加序号
    num = 2
    base_name = filename.rsplit(".", 1)[0]
    extension = filename.rsplit(".", 1)[1] if "." in filename else ""
    
    while True:
        if extension:
            new_filename = f"{base_name}({num}).{extension}"
        else:
            new_filename = f"{base_name}({num})"
        
        new_file_path = os.path.join(path, new_filename)
        if not os.path.exists(new_file_path):
            return new_filename
        
        # 检查内容是否相同
        if file_type == "txt" or file_type == "md":
            try:
                with open(new_file_path, "r", encoding="utf-8") as f:
                    exist_file = f.read()
            except:
                exist_file = ""
        else:
            try:
                with open(new_file_path, "rb") as f:
                    exist_file = f.read()
            except:
                exist_file = b""
        
        if exist_file == file_content:
            return new_filename
        
        num += 1


def decode_unicode_escape(text):
    """解码unicode转义字符"""
    try:
        return text.encode('latin-1').decode('unicode_escape', errors="replace")
    except:
        return text


def extract_author_info(url):
    """从URL中提取作者信息"""
    match = re.search(r"http[s]{0,1}://(.*?)\.lofter\.com", url)
    if match:
        return match.group(1)
    return ""


def normalize_post_url(url):
    """
    将 LOFTER 文章 URL 规范化为可比较形式（去掉查询参数，统一 https）。
    用于判断两篇是否为同一篇文章。
    """
    if not url or ".lofter.com/post/" not in url:
        return ""
    url = url.strip().replace("http://", "https://")
    # 去掉 ?incantation=xxx 等查询参数
    base = url.split("?")[0]
    return base.rstrip("/")


def extract_lofter_post_links_from_html(html):
    """
    从 HTML 中提取所有 LOFTER 文章链接（仅包含 /post/ 的链接，即单篇文章）。
    返回去重后的规范化 URL 列表。
    """
    if not html:
        return []
    # 匹配 href="https://xxx.lofter.com/post/..." 或 href='...'
    pattern = re.compile(
        r'href\s*=\s*["\'](https?://[^"\']+\.lofter\.com/post/[^"\']+)["\']',
        re.IGNORECASE
    )
    found = pattern.findall(html)
    # 解码可能的 HTML 实体
    decoded = []
    for u in found:
        u = u.replace("&amp;", "&").strip()
        norm = normalize_post_url(u)
        if norm and norm not in decoded:
            decoded.append(norm)
    return decoded


def sleep_random(min_sec=0.5, max_sec=2.0):
    """随机休眠"""
    import time
    time.sleep(random.uniform(min_sec, max_sec))


def img_fliter(imgs_url, blog_type):
    """
    过滤图片链接（参考lofterSpider-master的l4_author_img.py）
    :param imgs_url: 图片URL列表
    :param blog_type: 博客类型 "img", "text", "article"
    :return: 过滤后的图片URL列表
    """
    filtered_imgs_url = []
    for img_url in imgs_url:
        # 移除HTML实体编码
        img_url = img_url.replace('&amp;', '&')
        
        # 按链接格式过滤掉头像图片和推荐图片
        # blog_type目前有3种，img、text、article，img的图片链接需要过滤掉有"&amp"的，text和article不用
        if "&amp;" in img_url:
            if blog_type == "img":
                continue
            else:
                re_amp = re.search(r"\d\d&amp", img_url)
                if re_amp:
                    continue
        
        # 过滤小尺寸图片（头像等）- 更严格的过滤
        # 匹配16x16, 64x64, 96x96等小尺寸图片
        re_url = re.search(r"[1649]{2}[xy][1649]{2}", img_url)
        if re_url:
            continue
        
        # 过滤包含avatar、head、icon等关键词的图片（可能是头像）
        if any(keyword in img_url.lower() for keyword in ['avatar', 'head', 'icon', 'logo']):
            continue
        
        # 删除图片链接中的大小参数，获取时会默认最高画质
        # 但保留基础URL路径
        img_url = img_url.split("imageView")[0]
        # 如果还有?watermark等参数，也移除
        if '?watermark' in img_url:
            img_url = img_url.split('?watermark')[0]
        
        # 去重
        if img_url not in filtered_imgs_url:
            filtered_imgs_url.append(img_url)
    
    return filtered_imgs_url
