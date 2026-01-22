# -*- coding: utf-8 -*-
"""
工具函数
"""
import re
import random


def get_headers():
    """获取请求头"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
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


def filename_check(filename, file_content, path, file_type):
    """检查文件名是否重复，如果重复则添加序号"""
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
    
    # 如果文件内容不同，添加序号
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


def sleep_random(min_sec=0.5, max_sec=2.0):
    """随机休眠"""
    import time
    time.sleep(random.uniform(min_sec, max_sec))
