# -*- coding: utf-8 -*-
"""
合并lofter爬取的文件
支持合并txt或md格式的文件，按发表时间排序或按章节号智能排序
"""
import os
import re
import yaml
from datetime import datetime
from typing import List, Tuple, Optional, Dict


def extract_publish_time_txt(file_path: str) -> Optional[str]:
    """
    从TXT文件中提取发表时间
    :param file_path: 文件路径
    :return: 发表时间字符串（YYYY-MM-DD格式），如果提取失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取前几行查找发表时间
            for i, line in enumerate(f):
                if i > 10:  # 只检查前10行
                    break
                if '发表时间：' in line or '发表时间:' in line:
                    # 提取日期格式 YYYY-MM-DD
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                    if match:
                        return match.group(1)
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    return None


def extract_publish_time_md(file_path: str) -> Optional[str]:
    """
    从MD文件中提取发表时间（从YAML Front-Matter中）
    :param file_path: 文件路径
    :return: 发表时间字符串（YYYY-MM-DD格式），如果提取失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 查找YAML Front-Matter
            if content.startswith('---'):
                # 提取第一个---到第二个---之间的内容
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter_str = parts[1]
                    try:
                        front_matter = yaml.safe_load(front_matter_str)
                        if front_matter and 'date' in front_matter:
                            date_str = str(front_matter['date']).strip()
                            # 移除可能的引号
                            date_str = date_str.strip("'\"")
                            # 提取日期部分（可能包含时间）
                            match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
                            if match:
                                return match.group(1)
                    except yaml.YAMLError:
                        pass
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    return None


def get_file_publish_time(file_path: str, file_format: str) -> Optional[datetime]:
    """
    获取文件的发表时间
    :param file_path: 文件路径
    :param file_format: 文件格式 'txt' 或 'md'
    :return: datetime对象，如果提取失败返回None
    """
    if file_format == 'txt':
        time_str = extract_publish_time_txt(file_path)
    else:  # md
        time_str = extract_publish_time_md(file_path)
    
    if time_str:
        try:
            return datetime.strptime(time_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    # 如果提取失败，使用文件修改时间作为后备
    try:
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    except:
        return datetime.min


def get_file_content(file_path: str, file_format: str) -> str:
    """
    获取文件内容（去除文件头）
    :param file_path: 文件路径
    :param file_format: 文件格式 'txt' 或 'md'
    :return: 文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if file_format == 'txt':
            # 对于TXT格式，跳过文件头
            lines = content.split('\n')
            # 查找"原文链接："行，之后的内容才是正文
            content_start = 0
            for i, line in enumerate(lines):
                if '原文链接：' in line or '原文链接:' in line:
                    content_start = i + 1
                    break
            # 跳过空行
            while content_start < len(lines) and not lines[content_start].strip():
                content_start += 1
            # 如果没找到"原文链接："，尝试跳过前3行（标题、时间、链接）
            if content_start == 0:
                content_start = 3
                # 跳过空行
                while content_start < len(lines) and not lines[content_start].strip():
                    content_start += 1
            return '\n'.join(lines[content_start:])
        else:  # md
            # 对于MD格式，跳过YAML Front-Matter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    body = parts[2].lstrip('\n')
                    return body
            return content
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return ""


def get_filename_without_ext(file_path: str) -> str:
    """
    获取不带扩展名的文件名
    :param file_path: 文件路径
    :return: 不带扩展名的文件名
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def chinese_number_to_int(chinese_num: str) -> Optional[int]:
    """
    将中文数字转换为整数
    支持：一、二、三...十、十一、十二...百、千、万、十万等
    :param chinese_num: 中文数字字符串
    :return: 对应的整数，如果无法转换返回None
    """
    if not chinese_num:
        return None
    
    # 中文数字映射
    digit_map = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9
    }
    
    # 处理特殊情况：单独的"十"表示10
    if chinese_num == '十':
        return 10
    
    try:
        result = 0
        temp = 0
        i = 0
        length = len(chinese_num)
        
        while i < length:
            char = chinese_num[i]
            
            if char in digit_map:
                temp = digit_map[char]
            elif char == '十':
                # "十"的处理：十一=11, 十二=12, 十=10
                if temp == 0:
                    # 单独的"十"或"十X"格式
                    if i + 1 < length and chinese_num[i+1] in digit_map:
                        # "十X"格式，如"十一"、"十二"
                        temp = 10 + digit_map[chinese_num[i+1]]
                        i += 1  # 跳过下一个字符
                    else:
                        temp = 10
                else:
                    # "X十"格式，如"二十"、"三十"
                    temp = temp * 10
            elif char == '百':
                if temp == 0:
                    temp = 100
                else:
                    temp = temp * 100
            elif char == '千':
                if temp == 0:
                    temp = 1000
                else:
                    temp = temp * 1000
            elif char == '万':
                if temp == 0:
                    temp = 10000
                else:
                    temp = temp * 10000
                result = result + temp
                temp = 0
            else:
                # 无法识别的字符
                break
            
            i += 1
        
        result = result + temp
        return result if result > 0 else None
    except:
        return None


def extract_chapter_info(filename: str) -> Optional[Dict]:
    """
    从文件名中提取章节信息
    支持多种章节命名规则：
    1. 数字：2, 3完结, （1）, （4）, （完结）, 5完, 5完结, （完结 5）, （5 完结）
    2. 上下中：（上）, （中）, （下）, （上下）, （中下）, （下上）, （下下下 完）
    3. 番外/论坛体/其他题材：（番外1）, （论坛体1）, （捡手机文学1）, （福利番外1）等
    4. 中文数字：（一）, （二）, （三）...（十一）, （十二 完）
    5. 特殊分隔符：空格、-、之等，如"标题 12"、"标题-12"、"标题之12"
    6. 特殊：无章节号（第一章）
    :param filename: 文件名（不含扩展名）
    :return: 包含章节信息的字典，格式：{'type': str, 'number': int/float, 'subtype': str, 'raw': str, 'theme': str}
             如果无法识别，返回None
    """
    if not filename:
        return None
    
    # 移除作者名部分（最后一个-后面的内容，但保留文件名中的-）
    parts = filename.rsplit('-', 1)
    if len(parts) == 2 and len(parts[1]) < 30:  # 作者名通常较短
        name_part = parts[0]
    else:
        name_part = filename
    
    # 模式1: 完结标记（优先匹配，因为可能包含数字）
    # 匹配：（完结）, （完结 5）, （5 完结）, （完结5）, （5完结）
    end_patterns = [
        (r'[（(]完结\s*(\d+)[）)]', 'end_with_num'),  # （完结 5）或（完结5）
        (r'[（(](\d+)\s*完结[）)]', 'end_with_num'),  # （5 完结）或（5完结）
        (r'[（(]完结[）)]', 'end'),  # （完结）
    ]
    
    for pattern, match_type in end_patterns:
        match = re.search(pattern, name_part)
        if match:
            if match_type == 'end_with_num':
                num = int(match.group(1))
                return {'type': 'chapter', 'number': num, 'subtype': 'end', 'raw': match.group(0), 'theme': 'normal'}
            elif match_type == 'end':
                return {'type': 'chapter', 'number': 999999, 'subtype': 'end', 'raw': match.group(0), 'theme': 'normal'}
    
    # 模式2: 纯数字（在文件名末尾或括号中，或通过分隔符连接）
    patterns = [
        (r'[（(](\d+)(完|完结)[）)]', 'number'),
        (r'[（(](\d+)[）)]', 'number'),
        (r'[\s\-之]+(\d+)(完|完结)?$', 'number'),
        (r'(\d+)(完|完结)$', 'number'),
        (r'(\d+)$', 'number'),
    ]
    
    for pattern, match_type in patterns:
        match = re.search(pattern, name_part)
        if match:
            if match_type == 'number':
                num = int(match.group(1))
                return {'type': 'chapter', 'number': num, 'subtype': 'normal', 'raw': match.group(0), 'theme': 'normal'}
    
    # 模式3: 中文数字（一、二、三...）
    chinese_pattern = r'[（(]([一二三四五六七八九十百千万]+)[）)]'
    match = re.search(chinese_pattern, name_part)
    if match:
        chinese_num = match.group(1)
        chinese_num = re.sub(r'[完结\s]+$', '', chinese_num)
        num = chinese_number_to_int(chinese_num)
        if num is not None:
            return {'type': 'chapter', 'number': num, 'subtype': 'chinese', 'raw': match.group(0), 'theme': 'normal'}
    
    # 模式4: 上下中系列
    direction_pattern = r'[（(]([上下中]+)[）)]'
    match = re.search(direction_pattern, name_part)
    if match:
        direction = match.group(1)
        base_num = 0
        detail = 0
        
        if direction == '上':
            base_num = 1
        elif direction == '中':
            base_num = 2
        elif direction == '下':
            base_num = 3
        elif direction == '上下':
            base_num = 1
            detail = 0.5
        elif direction == '中下':
            base_num = 2
            detail = 0.5
        elif direction == '下上':
            base_num = 3
            detail = 0.1
        elif direction == '下中':
            base_num = 3
            detail = 0.2
        elif '下' in direction:
            base_num = 3
            down_count = direction.count('下')
            detail = (down_count - 1) * 0.1
        elif '中' in direction:
            base_num = 2
        elif '上' in direction:
            base_num = 1
        
        num = base_num + detail
        return {'type': 'chapter', 'number': num, 'subtype': 'direction', 'raw': match.group(0), 'theme': 'normal'}
    
    # 模式5: 题材系列（番外、论坛体、捡手机文学、福利番外、日记系列等）
    theme_keywords_in_brackets = ['番外', '论坛体', '捡手机', '福利', '日记', '小剧场', '彩蛋', '文学', '系列']
    theme_pattern = r'[（(]([^）)]+?)(\d+)[）)]'
    match = re.search(theme_pattern, name_part)
    if match:
        theme_name = match.group(1).strip()
        num = int(match.group(2))
        is_theme = any(keyword in theme_name for keyword in theme_keywords_in_brackets) or \
                   (len(theme_name) > 1 and not re.match(r'^[上下中\d一二三四五六七八九十百千万]+$', theme_name))
        
        if is_theme:
            if '完结' in theme_name:
                num_match = re.search(r'(\d+)', theme_name)
                if num_match:
                    num = int(num_match.group(1))
                clean_theme = theme_name.replace('完结', '').strip()
                return {'type': 'theme', 'number': num, 'subtype': 'theme_end', 'raw': match.group(0), 'theme': clean_theme or 'normal'}
            else:
                return {'type': 'theme', 'number': num, 'subtype': 'theme', 'raw': match.group(0), 'theme': theme_name}
    
    theme_end_pattern = r'[（(]([^）)]+?)完结[）)]'
    match = re.search(theme_end_pattern, name_part)
    if match:
        theme_name = match.group(1).strip()
        is_theme = any(keyword in theme_name for keyword in theme_keywords_in_brackets) or \
                   (len(theme_name) > 1 and not re.match(r'^[上下中\d一二三四五六七八九十百千万]+$', theme_name))
        if is_theme:
            return {'type': 'theme', 'number': 999999, 'subtype': 'theme_end', 'raw': match.group(0), 'theme': theme_name}
    
    # 模式6: 特殊标题（如"绿茶番外：鳏夫日记"、"番外：鳏夫日记"等）
    # 支持"番外"关键词在中间或前面的情况
    theme_keywords = ['番外', '论坛体', '捡手机', '福利', '日记', '小剧场', '彩蛋']
    for keyword in theme_keywords:
        if keyword in name_part:
            # 提取题材名称（可能是"番外"或"绿茶番外"等）
            # 尝试提取更完整的题材名称，如"绿茶番外"
            theme_name = keyword
            # 匹配"X番外："或"番外："格式，提取X部分
            theme_match = re.search(r'([^：:]*?' + re.escape(keyword) + r'[^：:]*)', name_part)
            if theme_match:
                theme_name = theme_match.group(1).strip()
            
            # 检查是否有数字后缀（如"绿茶番外：鳏夫日记2"）
            theme_num_match = re.search(r'(\d+)(完|完结)?$', name_part)
            if theme_num_match:
                num = int(theme_num_match.group(1))
                return {'type': 'theme', 'number': num, 'subtype': 'special', 'raw': name_part, 'theme': theme_name}
            else:
                # 检查是否有完结标记
                if '完结' in name_part or '完' in name_part:
                    return {'type': 'theme', 'number': 999999, 'subtype': 'special', 'raw': name_part, 'theme': theme_name}
                else:
                    return {'type': 'theme', 'number': 0, 'subtype': 'special', 'raw': name_part, 'theme': theme_name}
    
    # 模式7: 无章节号（可能是第一章）
    theme_keywords_all = ['番外', '论坛体', '捡手机', '福利', '日记', '小剧场', '彩蛋', '完结']
    has_theme_keyword = any(keyword in name_part for keyword in theme_keywords_all)
    
    if not re.search(r'[（(][上下中\d一二三四五六七八九十百千万]+[）)]', name_part) and \
       not re.search(r'[\s\-之]+\d+(完|完结)?$', name_part) and \
       not re.search(r'\d+(完|完结)?$', name_part) and \
       not has_theme_keyword:
        return {'type': 'chapter', 'number': 1, 'subtype': 'first', 'raw': '', 'theme': 'normal'}
    
    return None


def sort_files_by_chapter(file_info_list: List[Tuple[str, datetime, str]]) -> List[Tuple[str, datetime, str]]:
    """
    按章节号智能排序文件列表
    支持按题材分组，题材内按章节排序，题材间按第一篇文的发表时间排序
    :param file_info_list: 文件信息列表
    :return: 排序后的文件信息列表
    """
    # 提取每个文件的章节信息
    files_with_info = []
    for file_info in file_info_list:
        chapter_info = extract_chapter_info(file_info[2])
        files_with_info.append((file_info, chapter_info))
    
    # 按题材分组
    # 区分正文（normal）和番外类题材，确保番外和正文分开
    # 保留原始题材名称用于区分不同番外系列，但在排序时统一处理
    theme_groups = {}
    for file_info, chapter_info in files_with_info:
        if chapter_info:
            theme = chapter_info.get('theme', 'normal')
            # 保留原始题材名称，用于区分不同番外系列
        else:
            theme = 'unknown'
        
        if theme not in theme_groups:
            theme_groups[theme] = []
        theme_groups[theme].append((file_info, chapter_info))
    
    # 对每个题材内的文件进行排序
    sorted_groups = []
    for theme, files in theme_groups.items():
        if theme == 'normal':
            sorted_files = sorted(files, key=lambda x: (
                x[1]['number'] if x[1] else 0,
                x[0][1]
            ))
        elif theme == 'unknown':
            sorted_files = sorted(files, key=lambda x: x[0][1])
        else:
            # 番外类题材，按章节号排序
            sorted_files = sorted(files, key=lambda x: (
                x[1]['number'] if x[1] else 0,
                x[0][1]
            ))
        
        first_time = sorted_files[0][0][1] if sorted_files else datetime.max
        sorted_groups.append((theme, sorted_files, first_time))
    
    # 按题材排序：normal优先，所有番外类题材在后面
    # 确保正文和番外完全分开，正文全部在前面，番外全部在后面
    def get_theme_sort_key(group):
        theme, files, first_time = group
        if theme == 'normal':
            # 正文题材，使用(0, ...)确保所有正文都在最前面
            return (0, datetime.min, '')
        elif theme == 'unknown':
            return (999, datetime.max, '')
        else:
            # 判断是否为番外类题材
            is_fanwai = '番外' in theme or any(kw in theme for kw in ['论坛体', '捡手机', '福利', '日记', '小剧场', '彩蛋'])
            if is_fanwai:
                # 所有番外类题材统一使用(1, ...)确保都在正文后面
                # 番外类题材之间按第一篇文的时间排序，相同时间按题材名称排序
                # 这样可以保持不同番外系列的相对顺序
                return (1, first_time, theme)
            else:
                # 其他非番外类题材（如果有的话）
                return (2, first_time, theme)
    
    sorted_groups.sort(key=get_theme_sort_key)
    
    # 合并所有题材的文件
    # 先合并所有normal题材的文件，然后合并所有番外类题材的文件
    # 确保正文和番外完全分开
    result = []
    normal_group = None
    fanwai_groups = []
    other_groups = []
    
    for theme, files, first_time in sorted_groups:
        if theme == 'normal':
            normal_group = (theme, files, first_time)
        elif theme == 'unknown':
            other_groups.append((theme, files, first_time))
        else:
            # 判断是否为番外类题材
            is_fanwai = '番外' in theme or any(kw in theme for kw in ['论坛体', '捡手机', '福利', '日记', '小剧场', '彩蛋'])
            if is_fanwai:
                fanwai_groups.append((theme, files, first_time))
            else:
                other_groups.append((theme, files, first_time))
    
    # 先合并正文
    if normal_group:
        theme, files, first_time = normal_group
        for file_info, chapter_info in files:
            result.append(file_info)
    
    # 然后合并所有番外（按题材分组，每个番外系列内部按章节号排序）
    for theme, files, first_time in fanwai_groups:
        for file_info, chapter_info in files:
            result.append(file_info)
    
    # 最后合并其他题材
    for theme, files, first_time in other_groups:
        for file_info, chapter_info in files:
            result.append(file_info)
    
    return result


def check_file_contains_keywords(file_path: str, keywords: List[str], match_mode: str = "or", file_format: str = "txt") -> bool:
    """
    检查文件是否包含指定的关键词
    :param file_path: 文件路径
    :param keywords: 关键词列表
    :param match_mode: 匹配模式，"and"表示所有关键词都要包含，"or"表示包含任一关键词即可
    :param file_format: 文件格式 'txt' 或 'md'
    :return: 如果文件包含关键词则返回True，否则返回False
    """
    if not keywords:
        return True  # 如果没有关键词，则所有文件都匹配
    
    try:
        # 获取文件名（不含扩展名）
        filename = get_filename_without_ext(file_path)
        
        # 移除作者名部分（最后一个-后面的内容）
        parts = filename.rsplit('-', 1)
        if len(parts) == 2 and len(parts[1]) < 30:  # 作者名通常较短
            name_part = parts[0]
        else:
            name_part = filename
        
        # 在文件名中搜索关键词（只在文件名中搜索，不在文件内容中搜索）
        found_keywords = []
        for keyword in keywords:
            if keyword in name_part:
                found_keywords.append(keyword)
        
        # 根据匹配模式判断
        if match_mode.lower() == "and":
            # 所有关键词都要找到
            return len(found_keywords) == len(keywords)
        else:  # "or"
            # 至少找到一个关键词
            return len(found_keywords) > 0
    except Exception as e:
        print(f"检查文件 {file_path} 时出错: {e}")
        return False


def generate_toc(file_info_list: List[Tuple[str, datetime, str]], file_format: str, toc_links: bool = True) -> str:
    """
    生成目录
    :param file_info_list: 文件信息列表，每个元素为(file_path, publish_time, filename)
    :param file_format: 文件格式 'txt' 或 'md'
    :param toc_links: 如果是MD格式，是否生成可跳转的链接（默认True）
    :return: 目录字符串
    """
    toc_lines = []
    
    if file_format == 'txt':
        toc_lines.append("目录\n")
        toc_lines.append("=" * 50 + "\n\n")
        for chapter_num, (_, _, filename) in enumerate(file_info_list, 1):
            chapter_title = f"第{chapter_num}章-{filename}"
            toc_lines.append(f"{chapter_num}. {chapter_title}\n")
    else:  # md
        toc_lines.append("# 目录\n\n")
        for chapter_num, (_, _, filename) in enumerate(file_info_list, 1):
            chapter_title = f"第{chapter_num}章-{filename}"
            if toc_links:
                # 生成Markdown链接（使用章节标题作为锚点）
                # 大多数Markdown解析器（如GitHub Flavored Markdown）会自动为标题生成锚点
                # 锚点格式：将标题转换为小写，空格和特殊字符替换为连字符
                # 对于中文标题，大多数现代解析器（如GitHub、GitLab）会保留中文字符
                # 使用标准格式以确保兼容性
                import re
                anchor = chapter_title.lower()
                # 移除特殊字符（保留字母、数字、中文字符、空格、连字符）
                anchor = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', anchor)
                # 将空格和连字符统一为单个连字符
                anchor = re.sub(r'[-\s]+', '-', anchor)
                # 移除首尾连字符
                anchor = anchor.strip('-')
                toc_lines.append(f"{chapter_num}. [{chapter_title}](#{anchor})\n")
            else:
                toc_lines.append(f"{chapter_num}. {chapter_title}\n")
        toc_lines.append("\n---\n\n")
    
    return ''.join(toc_lines)


def merge_files(
    input_folder: str,
    output_folder: Optional[str] = None,
    output_filename: Optional[str] = None,
    file_format: str = "txt",
    add_toc: bool = False,
    toc_links: bool = True,
    keywords: Optional[List[str]] = None,
    match_mode: str = "or",
    sort_mode: str = "time"
):
    """
    合并文件夹中的所有文件
    :param input_folder: 输入文件夹路径（包含所有要合并的文件）
    :param output_folder: 输出文件夹路径，如果为None则使用项目根目录下的result文件夹
    :param output_filename: 输出文件名（不含扩展名），如果为None则使用输入文件夹名
    :param file_format: 文件格式 'txt' 或 'md'（默认'txt'）
    :param add_toc: 是否在开头添加目录（默认False）
    :param toc_links: 如果是MD格式，是否生成可跳转的目录链接（默认True，仅在add_toc=True且file_format='md'时有效）
    :param keywords: 关键词列表，如果提供则只合并包含这些关键词的文件（在文件名或内容中搜索）
    :param match_mode: 匹配模式，"and"表示所有关键词都要包含，"or"表示包含任一关键词即可（默认"or"）
    :param sort_mode: 排序模式，"time"表示按发表时间排序，"chapter"表示按章节号智能排序（默认"time"）
    """
    # 验证输入文件夹
    if not os.path.isdir(input_folder):
        raise ValueError(f"输入文件夹不存在: {input_folder}")
    
    # 确定输出文件夹（默认为项目根目录下的result文件夹）
    if output_folder is None:
        # 获取项目根目录（merge文件夹的父目录）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        output_folder = os.path.join(project_root, "result")
    
    # 确定输出文件名
    if output_filename is None:
        output_filename = os.path.basename(os.path.abspath(input_folder))
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有文件
    all_files = []
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if os.path.isfile(file_path):
            # 检查文件扩展名
            ext = os.path.splitext(filename)[1].lower()
            if file_format == 'txt' and ext == '.txt':
                all_files.append(file_path)
            elif file_format == 'md' and ext == '.md':
                all_files.append(file_path)
    
    if not all_files:
        print(f"在文件夹 {input_folder} 中没有找到 {file_format.upper()} 格式的文件")
        return
    
    print(f"找到 {len(all_files)} 个 {file_format.upper()} 文件")
    
    # 如果指定了关键词，进行过滤
    if keywords:
        print(f"关键词过滤: {keywords}, 匹配模式: {match_mode}")
        filtered_files = []
        for file_path in all_files:
            if check_file_contains_keywords(file_path, keywords, match_mode, file_format):
                filtered_files.append(file_path)
        
        print(f"过滤后剩余 {len(filtered_files)} 个文件")
        if not filtered_files:
            print("没有文件包含指定的关键词，合并终止")
            return
        
        all_files = filtered_files
    
    # 提取每个文件的发表时间
    file_info_list: List[Tuple[str, datetime, str]] = []
    for file_path in all_files:
        publish_time = get_file_publish_time(file_path, file_format)
        filename = get_filename_without_ext(file_path)
        file_info_list.append((file_path, publish_time, filename))
    
    # 根据排序模式进行排序
    if sort_mode == "chapter":
        # 按章节号智能排序（支持按题材分组）
        file_info_list = sort_files_by_chapter(file_info_list)
        print(f"按章节号智能排序完成")
        # 统计能识别章节的文件数量和题材分布
        recognized = 0
        theme_count = {}
        for info in file_info_list:
            chapter_info = extract_chapter_info(info[2])
            if chapter_info:
                recognized += 1
                theme = chapter_info.get('theme', 'normal')
                theme_count[theme] = theme_count.get(theme, 0) + 1
        
        print(f"识别到章节信息的文件: {recognized}/{len(file_info_list)}")
        if theme_count:
            themes_str = ', '.join([f"{k}: {v}" for k, v in theme_count.items()])
            print(f"题材分布: {themes_str}")
        if recognized < len(file_info_list):
            print(f"注意: {len(file_info_list) - recognized} 个文件无法识别章节信息，已按时间排序放在最后")
    else:
        # 按发表时间排序（默认）
        file_info_list.sort(key=lambda x: x[1])
        print(f"按发表时间排序完成，最早: {file_info_list[0][1].strftime('%Y-%m-%d')}, "
              f"最晚: {file_info_list[-1][1].strftime('%Y-%m-%d')}")
    
    # 合并文件内容
    merged_content = []
    
    # 如果启用目录，先添加目录
    if add_toc:
        toc_content = generate_toc(file_info_list, file_format, toc_links)
        merged_content.append(toc_content)
    
    for chapter_num, (file_path, publish_time, filename) in enumerate(file_info_list, 1):
        print(f"处理第 {chapter_num} 章: {filename}")
        content = get_file_content(file_path, file_format)
        
        # 添加章节标题
        chapter_title = f"第{chapter_num}章-{filename}"
        
        if file_format == 'txt':
            merged_content.append(f"\n\n{'='*50}\n")
            merged_content.append(f"{chapter_title}\n")
            merged_content.append(f"{'='*50}\n\n")
        else:  # md
            merged_content.append(f"\n\n## {chapter_title}\n\n")
        
        merged_content.append(content)
    
    # 写入合并后的文件
    output_ext = file_format
    output_path = os.path.join(output_folder, f"{output_filename}.{output_ext}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(merged_content))
    
    print(f"\n合并完成！")
    print(f"输出文件: {output_path}")
    print(f"共合并 {len(file_info_list)} 个文件")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='合并lofter爬取的文件')
    parser.add_argument('input_folder', type=str, help='输入文件夹路径（包含所有要合并的文件）')
    parser.add_argument('-o', '--output', type=str, default=None, 
                       help='输出文件夹路径（默认为项目根目录下的result文件夹）')
    parser.add_argument('-n', '--name', type=str, default=None,
                       help='输出文件名（不含扩展名），如果未指定则使用输入文件夹名')
    parser.add_argument('-f', '--format', type=str, choices=['txt', 'md'], default='txt',
                       help='文件格式：txt或md（默认为txt）')
    parser.add_argument('--add-toc', action='store_true',
                       help='在开头添加目录')
    parser.add_argument('--no-toc-links', action='store_true',
                       help='如果合并MD文件且添加目录，不使用可跳转的链接（默认使用可跳转链接）')
    parser.add_argument('-k', '--keywords', type=str, nargs='+', default=None,
                       help='关键词列表，只合并包含这些关键词的文件（在文件名或内容中搜索）')
    parser.add_argument('-m', '--match-mode', type=str, choices=['and', 'or'], default='or',
                       help='匹配模式：and表示所有关键词都要包含，or表示包含任一关键词即可（默认or）')
    parser.add_argument('-s', '--sort-mode', type=str, choices=['time', 'chapter'], default='time',
                       help='排序模式：time表示按发表时间排序，chapter表示按章节号智能排序（默认time）')
    
    args = parser.parse_args()
    
    # 如果指定了--no-toc-links，则toc_links为False，否则为True（默认）
    toc_links = not args.no_toc_links
    
    merge_files(
        input_folder=args.input_folder,
        output_folder=args.output,
        output_filename=args.name,
        file_format=args.format,
        add_toc=args.add_toc,
        toc_links=toc_links,
        keywords=args.keywords,
        match_mode=args.match_mode,
        sort_mode=args.sort_mode
    )
